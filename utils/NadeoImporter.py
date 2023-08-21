import cgi
import html
import re
import time
import bpy
import os.path
import subprocess
import threading
import xml.etree.ElementTree as ET

from .Models import ExportedItem

from .Constants import PATH_CONVERT_REPORT, NADEO_IMPORTER_ICON_OVERWRITE_VERSION, URL_DOCUMENTATION
from ..utils.NadeoXML import generate_mesh_XML, generate_item_XML
from ..utils.Functions import (
    debug,
    timer,
    Timer,
    fix_slash,
    in_new_thread,
    is_file_existing,
    get_addon_path,
    get_global_props,
    show_report_popup,
    show_windows_toast,
    get_path_filename,
    get_convert_items_props,
    get_nadeo_importer_path,
    is_game_maniaplanet,
)
from .SetIcon import set_icon

class ConvertStep():
    def __init__(self, title, additional_infos: tuple=()):
        self.title = title
        self.additional_infos = (info for info in additional_infos)


class ConvertResult():
    def __init__(self):
        self.relative_fbx_filepath = None
        self.name_raw = None
        self.mesh_returncode = None
        self.mesh_error_message = None
        self.item_returncode = None
        self.item_error_message = None
        self.convert_has_failed = None
        self.convert_steps = ()
        self.mesh_xml = ""
        self.item_xml = ""


class ItemConvert(threading.Thread):
    def __init__(self, fbxfilepath: str, game: str, physic_hack=True, icon_path: str="") -> None:
        super(ItemConvert, self).__init__() #need to call init from Thread, otherwise error
        
        
        # relative (Items/...) & absolute (C:/Users...) fbx filepaths
        self.fbx_filepath           = fix_slash( fbxfilepath ) 
        self.fbx_filepath_relative  = fix_slash("Items/" + fbxfilepath.split("/Work/Items/")[-1]) 
        
        # xm filepaths located in next to the fbx file
        self.xml_meshparams_filepath    = self.fbx_filepath.replace(".fbx", ".MeshParams.xml")
        self.xml_item_filepath          = self.fbx_filepath.replace(".fbx", ".Item.xml")
        self.xml_item_filepath_relative = self.fbx_filepath_relative.replace(".fbx", ".Item.xml")
        
        # gbx filepaths located in Documents/Items/
        self.gbx_filepath            = self.fbx_filepath.replace("/Work/Items/", "/Items/")
        self.gbx_mesh_filepath       = self.gbx_filepath.replace(".fbx", ".Mesh.Gbx")
        self.gbx_item_filepath       = self.gbx_filepath.replace(".fbx", ".Item.Gbx")
        self.gbx_shape_filepath      = self.gbx_filepath.replace(".fbx", ".Shape.Gbx")
        self.gbx_shape_filepath_old  = self.gbx_filepath.replace(".fbx", ".Shape.Gbx.old")
        self.icon_path               = icon_path
        
        # name to display in UI and error report
        self.name     = self.fbx_filepath.split("/")[-1]
        self.name_raw = self.name.replace(".fbx", "")

        # convert statistics
        self.convert_message_mesh_shape_gbx    = None   
        self.convert_message_item_gbx          = None   
        self.convert_returncode_item_gbx       = 0      # 0 good, 1 and above bad
        self.convert_returncode_mesh_shape_gbx = 0      # 0 good, 1 and above bad
        self.convert_progress:ConvertStep      = []

        self.game = game
        self.game_is_trackmania2020 = game == "Trackmania2020"
        self.game_is_maniaplanet    = game == "ManiaPlanet"

        self.physic_hack = physic_hack

        self.convert_is_done    = False
        self.convert_has_failed = False

    
    def add_progress_step(self, step: str, additional_infos: tuple=()) -> None:
        self.convert_progress.append(ConvertStep(
                # title=f"{self.name_raw}: {step}",
                title=f"{step}",
                additional_infos = additional_infos
            ))

        if not additional_infos:
            debug(step)
        else:
            debug(step, additional_infos)
        
    
    def run(self) -> None:
        """method called when method start() is called on an instance of this class"""
        debug()
        self.add_progress_step(f"""Start convert to game {self.game}""")

        tm_props = get_global_props()
        
        # trackmania 2020 convert process
        if self.game_is_trackmania2020:
            self.convert_item_gbx()
            
            if tm_props.CB_generateMeshAndShapeGBX and not self.convert_has_failed:
                self.convert_mesh_and_shape_gbx()
            
            if not self.convert_has_failed:
                self.pascalcase_gbx_filenames()

            if not self.convert_has_failed \
                and self.icon_path != "" \
                and not is_game_maniaplanet() \
                and tm_props.CB_icon_genIcons \
                and tm_props.ST_nadeoImporter_TM_current == NADEO_IMPORTER_ICON_OVERWRITE_VERSION:
                self.overwrite_icon_item_gbx()
            
        
        # maniaplanet convert process
        if self.game_is_maniaplanet:
            self.convert_mesh_and_shape_gbx() 
            
            if not self.convert_has_failed and self.physic_hack:
                self.hack_shape_gbx()

            if not self.convert_has_failed: 
                self.convert_item_gbx()
            
            
        if not self.convert_has_failed:
            self.add_progress_step("Convert succeeded\n\n")
        else:
            mesh_returncode = self.convert_returncode_mesh_shape_gbx
            mesh_error_msg  = bytes(self.convert_message_mesh_shape_gbx or "", "utf-8").decode("unicode_escape")
            item_returncode = self.convert_returncode_item_gbx
            item_error_msg  = bytes(self.convert_message_item_gbx or "", "utf-8").decode("unicode_escape") 

            errors = []

            if item_returncode > 0:
                errors.append(f"Returncode: {item_returncode}")
                errors.append(f"Original Response: {item_error_msg}")
            
            if mesh_returncode > 0:
                errors.append(f"Returncode: {mesh_returncode}")
                errors.append(f"Original Response: {mesh_error_msg}")
            
            self.add_progress_step("Convert failed\n\n", errors)
 
        def updateUI() -> int:
            try:
                update_convert_status_numbers_in_ui(convert_failed=self.convert_has_failed, obj_name=self.name)
                return None
            except:
                return 0.2

        timer(updateUI, 0)


    def pascalcase_gbx_filenames(self) -> None:
        try:   os.rename(self.gbx_item_filepath  , re.sub(r"item\.gbx$",  "Item.Gbx",  self.gbx_item_filepath  , flags=re.IGNORECASE))
        except FileNotFoundError: pass
        try:   os.rename(self.gbx_mesh_filepath  , re.sub(r"mesh\.gbx$",  "Mesh.Gbx",  self.gbx_mesh_filepath  , flags=re.IGNORECASE))
        except FileNotFoundError: pass
        try:   os.rename(self.gbx_shape_filepath , re.sub(r"shape\.gbx$", "Shape.Gbx", self.gbx_shape_filepath , flags=re.IGNORECASE))
        except FileNotFoundError: pass
    

    def convert_mesh_and_shape_gbx(self) -> None:
        """convert fbx to shape/mesh.gbx"""
        self.add_progress_step(f"""Convert .fbx => .Mesh.gbx and Shape.gbx""")
        
        cmd = f""""{get_nadeo_importer_path()}" Mesh "{self.fbx_filepath_relative}" """ # ex: NadeoImporter.exe Mesh /Items/myblock.fbx
        self.add_progress_step(f"""Command: {cmd}""")
        
        convert_process  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        mesh_output      = convert_process.communicate() 
        mesh_returncode  = convert_process.returncode
        convert_process.wait()
        
        self.convert_has_failed                = True if mesh_returncode > 0 else False
        self.convert_message_mesh_shape_gbx    = str(mesh_output[0], encoding="ascii")
        self.convert_returncode_mesh_shape_gbx = int(mesh_returncode)

        if not self.convert_has_failed:
            self.add_progress_step(f"""Convert to .Mesh.gbx and Shape.gbx successfully""")
        else:
            self.add_progress_step(f"""Convert to .Mesh.gbx and Shape.gbx failed""")

    
    
    def convert_item_gbx(self) -> None:
        """convert fbx to item.gbx"""
        self.add_progress_step(f"""Convert .fbx => .Item.gbx""")
        
        # ex: "NadeoImporter.exe" Item "/Items/myblock.Item.xml"
        cmd = f""""{get_nadeo_importer_path()}" Item "{self.xml_item_filepath_relative}" """ 
        self.add_progress_step(f"""Command: {cmd}""")

        convert_process  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        item_output     = convert_process.communicate() 
        item_returncode = convert_process.returncode
        convert_process.wait()

        self.convert_has_failed          = True if item_returncode > 0 else False
        self.convert_message_item_gbx    = str(item_output[0], encoding="ascii")
        self.convert_returncode_item_gbx = int(item_returncode)

        if not self.convert_has_failed:
            self.add_progress_step(f"""Convert to .Item.gbx successfully""")
        else:
            self.add_progress_step(f"""Convert to .Item.gbx failed""")




    def hack_shape_gbx(self) -> None:
        """
        Hacking the shape.gbx file, only necessary for maniaplanet,
        To use custom physics with nadeo materials like StadiumPlatform,
        we need to use a workaround:
        1. convert .Mesh.gbx and .Shape.gbx, while using BaseTexture=Link in .MeshParams.xml,
        2. The generated .Mesh.gbx is now invalid, but the .Shape.gbx is valid 
        3. replace BaseTexture=Link with Link=Link in .MeshParams.xml
        4. rename the generated .Shape.gbx to .Shape.gbx.old 
        5. convert .Mesh.gbx and .Shape.gbx again with valid settings (Link=Link)
        6. replace new generated .Shape.gbx with .Shape.gbx.old
        """

        self.add_progress_step(f"""Hacking .Shape.gbx for custom physic id""")            
        self.add_old_suffix_to_shape_gbx()

        self.add_progress_step(f"""Parsing .Item.xml""")
        tree = ET.parse(self.xml_meshparams_filepath)
        root = tree.getroot()
        data = root.findall(".Materials/Material")
        
        # replace BaseTexture=xyz with Link=xyz
        for mat in data:
            if "BaseTexture" in mat.attrib:
                if not "/" in mat.get("BaseTexture", ""):
                    self.add_progress_step(f"""Replace BaseTexture= with Link= for {mat.get("name")}""")
                    mat.set("Link", mat.get("BaseTexture"))
                    del mat.attrib["BaseTexture"]   # obsolete if Link is used
                    del mat.attrib["Model"]         # obsolete if Link is used
                    del mat.attrib["PhysicsId"]     # obsolete if Link is used

        self.add_progress_step(f"""Write changes to .Item.xml""")
        tree.write(self.xml_meshparams_filepath)

        if not self.convert_has_failed: self.convert_mesh_and_shape_gbx()
        if not self.convert_has_failed: self.use_old_shape_gbx()
        # end hacking
    

    def delete_old_shape_gbx(self) -> None:
        if is_file_existing(self.gbx_shape_filepath_old):
            os.remove(self.gbx_shape_filepath_old)
            self.add_progress_step(""".Shape.gbx.old deleted""")


    def deleteShapeGbx(self) -> None:
        if is_file_existing(self.gbx_shape_filepath):
            os.remove(self.gbx_shape_filepath)
            self.add_progress_step(""".Shape.gbx deleted""")


    def use_old_shape_gbx(self) -> None:
        try:
            self.deleteShapeGbx()
            os.rename(self.gbx_shape_filepath_old, self.gbx_shape_filepath)
            self.add_progress_step(f"""Renamed .Shape.gbx.old to .Shape.gbx""")
        except FileNotFoundError as e:
            self.add_progress_step(f"""Renaming .Shape.gbx.old to .Shape.gbx failed""", [e])
            self.convert_has_failed = True
            

    def add_old_suffix_to_shape_gbx(self) -> None:
        self.delete_old_shape_gbx()
        try:
            os.rename(self.gbx_shape_filepath, self.gbx_shape_filepath_old)
            self.add_progress_step(f"""Renamed .Shape.gbx to .Shape.gbx.old""")
        except FileNotFoundError as e:
            self.add_progress_step(f"""Renaming .Shape.gbx to .Shape.gbx.old failed""", [e])
            self.convert_has_failed = True
    
    def overwrite_icon_item_gbx(self) -> None:
        """fix icon in item.gbx"""
        self.add_progress_step(f"""Overwrite icon in .Item.gbx""")
        
        (error, msg) = set_icon(self.gbx_item_filepath, self.icon_path)
        
        self.convert_has_failed          = error != 0
        self.convert_message_item_gbx    = msg
        self.convert_returncode_item_gbx = error

        if not self.convert_has_failed:
            self.add_progress_step(f"""Overwrite icon .Item.gbx successfully""")
        else:
            self.add_progress_step(f"""Overwrite icon .Item.gbx failed""")

        










def update_convert_status_numbers_in_ui(convert_failed: bool, obj_name: str) -> None:
    """updates the numbers for converting which are displaed in the ui panel"""
    tm_props = get_global_props()

    if not convert_failed:
        tm_props.NU_convertedSuccess += 1
    
    else:       
        tm_props.NU_convertedError += 1
        tm_props.ST_convertedErrorList += f"%%%{obj_name}"

    tm_props.NU_convertedRaw += 1
    tm_props.NU_converted     = int(tm_props.NU_convertedRaw / tm_props.NU_convertCount * 100)

def _start_convert_timer():
    tm_props = get_global_props()
    def timer():
        tm_props.NU_convertDurationSinceStart = int(time.perf_counter()) - tm_props.NU_convertStartedAt
        if tm_props.CB_converting is False: 
            return None
        else: 
           return 1

    bpy.app.timers.register(timer, first_interval=1)

def _write_convert_report(results: list[ConvertResult]) -> None:
    """genertate status html file of converted fbx files"""
    errors      = 0
    converted   = len(results)
    
    for result in results:
        if result.convert_has_failed:
            errors += 1

    try:
        with open( fix_slash(PATH_CONVERT_REPORT), "w", encoding="utf-8") as f:
            
            result_list = ""
            for converted_item in results:

                # skip success ones
                if converted_item.convert_has_failed is False:
                    continue

                progress_LIs = ""
                for step in converted_item.convert_steps:

                    sub_steps = step.additional_infos
                    sub_steps_LIs = ""
                    sub_steps_UL  = ""
                    for sub_step in sub_steps:
                        sub_steps_LIs += f"<li>{sub_step}</li>"
                    
                    if sub_steps_LIs:
                        sub_steps_UL = f"<ul>{sub_steps_LIs}</ul>"
                    
                    progress_LIs += f"""<li class="">{step.title}{sub_steps_UL}</li> """

                item_full_hierachy = converted_item.relative_fbx_filepath
                item_full_hierachy = item_full_hierachy.replace("/", "<span class='slash'>/</span>")

                error_msg_item = converted_item.item_error_message
                error_msg_mesh = converted_item.mesh_error_message

                mesh_has_error = converted_item.mesh_returncode > 0
                item_has_error = converted_item.item_returncode > 0

                
                mesh_image = ""
                item_image = ""

                html_item_error = ""
                if item_has_error:
                    pretty,\
                    original,\
                    item_image = _beautify_nadeoimporter_error_response(error_msg_item) if item_has_error else ("", "", "")
                    html_item_error = pretty

                html_mesh_error = ""
                if mesh_has_error:
                    pretty, \
                    original, \
                    mesh_image = _beautify_nadeoimporter_error_response(error_msg_mesh) if mesh_has_error else ("", "", "")
                    html_mesh_error = pretty
                


                result_list += f"""
                    <div class="result-wrapper">
                        <div class="result-text">
                            <h2 class="item-name">{converted_item.name_raw}</h2>
                            <p class="item-path">{item_full_hierachy}</p>
                            <hr>


                            <h3>Item Code: <small>{str(converted_item.item_returncode)}{
                                
                                " <span class='success'>(success)</span>" 
                                if converted_item.item_returncode == 0 
                                
                                else
                                " <span class='error'>(error)</span>"
                                
                            }</small></h3>

                            <p class='item-error-message'>
                                {html_item_error}
                            </p>
                            {f"<img src='{item_image}'>" if item_image else ""}

                            <hr />

                            

                            <h3>Mesh Code: <small>{str(converted_item.mesh_returncode)}{
                            
                                " <span class='success'>(success)</span>" 
                                if converted_item.mesh_returncode == 0 
                            
                                else 
                                " <span class='error'>(error)</span>"

                            }</small></h3>
                            
                            <p class='item-error-message'>
                                {html_mesh_error}
                            </p>
                            {f"<img src='{mesh_image}'>" if mesh_image else ""}
                            
                            <hr />
                            



                            <h3>Conversion Log:</h3>
                            <ul class="progress-steps">
                                {progress_LIs}
                            </ul>
                        </div>   

                        <div class="result-codes">
                            
                            <div>
                                <div class="file-type">.MeshParams.xml</div>
                                <div class="result-code">
                                    <!--?prettify lang=xml linenums=false?-->
                                    <pre class="prettyprint">
                                        <code>
{html.escape(converted_item.mesh_xml)}
                                        </code>
                                    </pre>
                                </div>
                            </div>
                        
                            <div>
                                <div class="file-type">.Item.xml</div>
                                <div class="result-code">
                                    <!--?prettify lang=xml linenums=false?-->
                                    <pre class="prettyprint">
                                        <code>
{html.escape(converted_item.item_xml)}
                                        </code>
                                    </pre>
                                </div>
                            </div>

                        </div>
                    </div>
                    """
                



            
            fullHTML = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Convert Report</title>
                    <link rel="stylesheet" href="file://{get_addon_path()}assets/convert_report/google-code-prettify/prettify.css">
                    <script src="file://{get_addon_path()}assets/convert_report/google-code-prettify/run_prettify.js?autoload=true&amp;skin=sunburst&amp;lang=css"></script>
                    <link rel="stylesheet" href="file://{get_addon_path()}assets/convert_report/google-code-prettify/sunburst.css">
                    <link rel="stylesheet" href="file://{get_addon_path()}assets/convert_report/report.css">
                    
                </head>
                <body>
                    <main>
                        <header>
                            <h1>
                                Failed converts: {errors} of {converted}
                            </h1>
                        </header>

                        {result_list}  

                    </main>

                    <div id="this-is-fine"></div>
                    
                    <div id="help-buttons">
                        <a href="https://discord.com/channels/891279104794574948/921509901077975060" class="btn" target="_blank" id="ask-for-help">
                            Help on Discord
                        </a>
                        <a href="https://github.com/skyslide22/blendermania-addon/wiki/06.-Converting-Troubleshooting" target="_blank" class="btn" id="documentation">
                            Open Documentation
                        </a>
                        <a href="#" target="_blank" onclick="focusBlenderAndCloseErrorReport(); return false;" class="btn" id="close-page">
                            Back to Blender
                        </a>
                    </div>
                    


                    <script>
                    window.focusBlenderAndCloseErrorReport = async function()
                    {{
                        try
                        {{
                            await fetch("http://localhost:42069/focus_blender")
                            window.close()
                        }}
                        catch
                        {{
                            // alert("blender server is not running, close anyway")
                            // window.close()
                            alert("error: blender server is not running")
                        }}
                    }}
                    </script>
                    
                </body>
                </html>
                """
            f.write(fullHTML)
        
    except FileNotFoundError as e:
        show_report_popup(
            "Writing file failed", 
            [
                "Can not write report file in user dir",
                "Try to run Blender once as admindistator" 
            ])

def _beautify_nadeoimporter_error_response(error: str) -> tuple[str, str, str]:
    """proper description from nadeoimporter return string"""
        
    image = ""
    prettymsg = ""
    errlower = error.lower()

    if ("uv layer not found" in errlower 
    or "not enough uvlayers" in errlower): 
        prettymsg = f"""A mandatory UV Layer was not found. Are you sure that all MESH objects in your exported collection have a uv layer named "BaseMaterial" and "LightMap" ? Those are the most common ones! """
        image = "uv-layers.jpg"

    elif "material" in errlower and "physicsid" in errlower and "invalid value" in errlower: 
        prettymsg= f"""The "PhysicsId" attribute of a material is invalid (might be empty)! Make sure that all used materials in your object use a valid PhysicId. You could also disable the use of a custom PhysicId, if so, the default will be used. Fix: update the broken material(s) with the addon, or manipulate the material properties by hand in the "Custom Properties" section in the material panel(below Viewport Display) """
        image="physicid-invalid-value.jpg"

    elif ("file not found in" in errlower
    and   ".fbx" in errlower):
        prettymsg= f"""The mandatory .fbx file was not found, make sure your collection got exported in the correct folder (relative paths such as ../../Items/ are not supported)"""
        image="relative-path.jpg"

    elif ("file not found in" in errlower
    and   ".xml" in errlower) or "common" in errlower:
        prettymsg= f"""A mandatory .xml file was not found, make sure your collection has xml files generated, enable this in the export panel"""
        image = "xml-required.jpg"

    elif "no material" in errlower:
        prettymsg= f"""Atleast one object of has no material (_trigger & _socket do not need materials)"""
    
    elif "texcoord" in errlower:
        prettymsg= f"""Make sure all your faces are unwrapped in your lightmap. Check for faces that are scaled to 0 (usually in the bottom left corner of the Lightmap) and make sure to unwrap those faces"""
        image = "lightmap-uvcoord-is-null.jpg"
    
    #TODO 3221225477 error return code occours when material was not found in mat lib
    # elif "" in errlower:
        # prettymsg= f""" """

    if image:
        image = f"file://{get_addon_path()}assets/convert_report/{image}"

    if prettymsg:
        prettymsg = "<span style='color: orange; font-weight: 700'>Info: </span>" + prettymsg

    return (prettymsg, error, image)




@in_new_thread
def start_batch_convert(items: list[ExportedItem]) -> None:
    """convert each fbx one after one, create a new thread for it"""
    tm_props_convertingItems = get_convert_items_props()
    tm_props        = get_global_props()
    results         = []
    game            = "ManiaPlanet" if is_game_maniaplanet() else "Trackmania2020"
    notify          = tm_props.CB_notifyPopupWhenDone
    use_multithread = tm_props.CB_convertMultiThreaded 

    tm_props.CB_showConvertPanel = True
    tm_props.NU_convertStartedAt = int(time.perf_counter())
    
    _start_convert_timer()

    tm_props_convertingItems.clear()

    items_convert_index = {}
    counter = 0

    fail_count    = 0
    success_count = 0
    atleast_one_convert_failed = fail_count > 0

    for item_to_convert in items:
        name = get_path_filename(item_to_convert.fbx_path, remove_extension=True)
        item = tm_props_convertingItems.add()
        item.name = name
        item.name_raw = item_to_convert.name_raw #fixing name to name_raw costed me 30 min ahhh
        items_convert_index[ name ] = counter
        counter += 1

        
    def convert_fbx(item: ExportedItem) -> None:
        nonlocal items_convert_index
        nonlocal counter
        nonlocal fail_count
        nonlocal success_count
        nonlocal atleast_one_convert_failed

        if tm_props.CB_xml_genItemXML: generate_item_XML(item)
        if tm_props.CB_xml_genMeshXML: generate_mesh_XML(item)

        name = get_path_filename(item.fbx_path, remove_extension=True)

        current_convert_timer = Timer()
        current_convert_timer.start()
        
        conversion = ItemConvert(fbxfilepath=item.fbx_path, game=game, physic_hack=item.physic_hack, icon_path=item.icon_path)
        conversion.start() #start the convert (call internal run())
        conversion.join()  #waits until the thread terminated (function/convert is done..)
        
        result = ConvertResult()
        result.name_raw = conversion.name_raw
        result.relative_fbx_filepath = conversion.fbx_filepath_relative
        result.mesh_error_message    = conversion.convert_message_mesh_shape_gbx
        result.mesh_returncode       = conversion.convert_returncode_mesh_shape_gbx
        result.item_error_message    = conversion.convert_message_item_gbx
        result.item_returncode       = conversion.convert_returncode_item_gbx
        result.convert_steps         = conversion.convert_progress
        result.convert_has_failed    = conversion.convert_has_failed
        result.mesh_xml              = item.mesh_xml
        result.item_xml              = item.item_xml
        results.append(result)

        failed              = True if conversion.convert_has_failed else False
        icon                = "CHECKMARK" if not failed else "FILE_FONT"
        current_item_index  = items_convert_index[ name ] # number

        if failed: fail_count    += 1
        else:      success_count += 1


        @in_new_thread
        def set_item_props():
            tm_props_convertingItems[ current_item_index ].name             = name
            tm_props_convertingItems[ current_item_index ].icon             = icon
            tm_props_convertingItems[ current_item_index ].failed           = failed
            tm_props_convertingItems[ current_item_index ].converted        = True
            tm_props_convertingItems[ current_item_index ].convert_duration = int(current_convert_timer.stop())



        try:
            set_item_props()
        except AttributeError as e: #bpy context assignment is not thread save
            time.sleep(.1) 
            set_item_props()


    # init converts
    # init converts
    # init converts

    threads = []

    if use_multithread:
        for item in items:
            thread = threading.Thread(target=convert_fbx, args=[item,])
            thread.start()
            threads.append(thread)

    else:
        for item in items:
            convert_fbx(item)
            if tm_props.CB_stopAllNextConverts is True:
                debug("Convert stopped, aborted by user (UI CHECKBOX)")
                break

    
    for threads in threads:
        thread.join()

    tm_props.CB_converting = False
    tm_props.NU_prevConvertDuration = tm_props.NU_convertDurationSinceStart



    if notify:
        convert_count    = fail_count + success_count
        convert_errors   = fail_count
        convert_duration = tm_props.NU_currentConvertDuration

        if atleast_one_convert_failed:
            title=f"""Convert failed"""
            text =f"""{convert_errors} of {convert_count} converts failed\nDuration: {convert_duration}s"""
            icon ="Error"
        else:
            title=f"""Convert successfully"""
            text =f"""{convert_count} of {convert_count} items successfully converted \nDuration: {convert_duration}s"""
            icon ="Info"

        show_windows_toast(title, text, icon, 7000)
    
    _write_convert_report(results=results)
