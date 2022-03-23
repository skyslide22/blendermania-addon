import time
import bpy
import os.path
import subprocess
from threading import Thread
import xml.etree.ElementTree as ET

from .TM_Functions import *


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


class CONVERT_ITEM(Thread):
    
    def __init__(self, fbxfilepath: str, game: str) -> None:
        super(CONVERT_ITEM, self).__init__() #need to call init from Thread, otherwise error
        
        
        # relative (Items/...) & absolute (C:/Users...) fbx filepaths
        self.fbx_filepath           = fixSlash( fbxfilepath ) 
        self.fbx_filepath_relative  = fixSlash("Items/" + fbxfilepath.split("/Work/Items/")[-1]) 
        
        # xm filepaths located in next to the fbx file
        self.xml_meshparams_filepath    = self.fbx_filepath.replace(".fbx", ".MeshParams.xml")
        self.xml_item_filepath          = self.fbx_filepath.replace(".fbx", ".Item.xml")
        self.xml_item_filepath_relative = self.fbx_filepath_relative.replace(".fbx", ".Item.xml")
        
        # gbx filepaths located in Documents/Items/
        self.gbx_filepath            = self.fbx_filepath.replace("/Work/Items/", "/Items/")
        self.gbx_mesh_filepath       = self.gbx_filepath.replace(".fbx", ".Mesh.gbx")
        self.gbx_item_filepath       = self.gbx_filepath.replace(".fbx", ".Item.gbx")
        self.gbx_shape_filepath      = self.gbx_filepath.replace(".fbx", ".Shape.gbx")
        self.gbx_shape_filepath_old  = self.gbx_filepath.replace(".fbx", ".Shape.gbx.old")
        
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

        self.convert_is_done    = False
        self.convert_has_failed = False

    
    def addProgressStep(self, step: str, additional_infos: tuple=()) -> None:
        self.convert_progress.append(ConvertStep(
                title=f"{self.name_raw}: {step}",
                additional_infos = additional_infos
            ))

        if not additional_infos:
            debug(step)
        else:
            debug(step, additional_infos)
        
    
    def run(self) -> None:
        """method called when method start() is called on an instance of this class"""
        debug()
        self.addProgressStep(f"""Start convert to game {self.game}""")
        
        # trackmania 2020 convert process
        if self.game_is_trackmania2020:
            self.convertItemGBX()
            if getTmProps().CB_generateMeshAndShapeGBX:
                if not self.convert_has_failed: self.convertMeshAndShapeGBX()
            
        
        # maniaplanet convert process
        if self.game_is_maniaplanet:
            if not self.convert_has_failed: self.convertMeshAndShapeGBX() 
            if not self.convert_has_failed: self.hackShapeGBX()
            if not self.convert_has_failed: self.convertItemGBX()
            
            
        if not self.convert_has_failed:
            self.addProgressStep("Convert succeeded\n\n")
        else:
            mesh_returncode = self.convert_returncode_mesh_shape_gbx
            mesh_error_msg  = self.convert_message_mesh_shape_gbx
            item_returncode = self.convert_returncode_item_gbx
            item_error_msg  = self.convert_message_item_gbx 

            errors = []

            if item_returncode > 0:
                errors.append(f"item returncode: {item_returncode}")
                errors.append(f"item error msg:  {item_error_msg}")
            
            if mesh_returncode > 0:
                errors.append(f"mesh returncode: {mesh_returncode}")
                errors.append(f"mesh error msg:  {mesh_error_msg}")
            
            self.addProgressStep("Convert failed\n\n", errors)
 
        def updateUI() -> int:
            try:
                updateConvertStatusNumbersInUI(convert_failed=self.convert_has_failed, obj_name=self.name)
                return None
            except:
                return 0.2

        timer(updateUI, 0)


    

    def convertMeshAndShapeGBX(self) -> None:
        """convert fbx to shape/mesh.gbx"""
        self.addProgressStep(f"""Convert .fbx to .Mesh.gbx and Shape.gbx""")
        
        cmd = f"""{getNadeoImporterPath()} Mesh "{self.fbx_filepath_relative}" """ # ex: NadeoImporter.exe Mesh /Items/myblock.fbx
        self.addProgressStep(f"""Command: {cmd}""")
        
        convert_process  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        mesh_output      = convert_process.communicate() 
        mesh_returncode  = convert_process.returncode
        convert_process.wait()
        
        self.convert_has_failed                = True if mesh_returncode > 0 else False
        self.convert_message_mesh_shape_gbx    = str(mesh_output[0], encoding="ascii")
        self.convert_returncode_mesh_shape_gbx = int(mesh_returncode)

        if not self.convert_has_failed:
            self.addProgressStep(f"""Convert to .Mesh.gbx and Shape.gbx successfully""")
        else:
            self.addProgressStep(f"""Convert to .Mesh.gbx and Shape.gbx failed""")

    
    
    def convertItemGBX(self) -> None:
        """convert fbx to item.gbx"""
        self.addProgressStep(f"""Convert .fbx to .Item.gbx""")
        
        cmd = f"""{getNadeoImporterPath()} Item "{self.xml_item_filepath_relative}" """ # ex: NadeoImporter.exe Item /Items/myblock.Item.xml
        self.addProgressStep(f"""Command: {cmd}""")

        convert_process  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        item_output     = convert_process.communicate() 
        item_returncode = convert_process.returncode
        convert_process.wait()

        self.convert_has_failed          = True if item_returncode > 0 else False
        self.convert_message_item_gbx    = str(item_output[0], encoding="ascii")
        self.convert_returncode_item_gbx = int(item_returncode)

        if not self.convert_has_failed:
            self.addProgressStep(f"""Convert to .Item.gbx successfully""")
        else:
            self.addProgressStep(f"""Convert to .Item.gbx failed""")




    def hackShapeGBX(self) -> None:
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

        self.addProgressStep(f"""Hacking .Shape.gbx for custom physic id""")            
        self.addOldSuffixToShapeGbx()

        self.addProgressStep(f"""Parsing .Item.xml""")
        tree = ET.parse(self.xml_meshparams_filepath)
        root = tree.getroot()
        data = root.findall(".Materials/Material")
        
        # replace BaseTexture=xyz with Link=xyz
        for mat in data:
            if "BaseTexture" in mat.attrib:
                if not "/" in mat.get("BaseTexture", ""):
                    self.addProgressStep(f"""Replace BaseTexture= with Link= for {mat.get("name")}""")
                    mat.set("Link", mat.get("BaseTexture"))
                    del mat.attrib["BaseTexture"]   # obsolete if Link is used
                    del mat.attrib["Model"]         # obsolete if Link is used
                    del mat.attrib["PhysicsId"]     # obsolete if Link is used

        self.addProgressStep(f"""Write changes to .Item.xml""")
        tree.write(self.xml_meshparams_filepath)

        if not self.convert_has_failed: self.convertMeshAndShapeGBX()
        if not self.convert_has_failed: self.useOldShapeGbx()
        # end hacking
    

    def deleteOldShapeGbx(self) -> None:
        if doesFileExist(self.gbx_shape_filepath_old):
            os.remove(self.gbx_shape_filepath_old)
            self.addProgressStep(""".Shape.gbx.old deleted""")


    def deleteShapeGbx(self) -> None:
        if doesFileExist(self.gbx_shape_filepath):
            os.remove(self.gbx_shape_filepath)
            self.addProgressStep(""".Shape.gbx deleted""")


    def useOldShapeGbx(self) -> None:
        try:
            self.deleteShapeGbx()
            os.rename(self.gbx_shape_filepath_old, self.gbx_shape_filepath)
            self.addProgressStep(f"""Renamed .Shape.gbx.old to .Shape.gbx""")
        except FileNotFoundError as e:
            self.addProgressStep(f"""Renaming .Shape.gbx.old to .Shape.gbx failed""", [e])
            self.convert_has_failed = True
            

    def addOldSuffixToShapeGbx(self) -> None:
        self.deleteOldShapeGbx()
        try:
            os.rename(self.gbx_shape_filepath, self.gbx_shape_filepath_old)
            self.addProgressStep(f"""Renamed .Shape.gbx to .Shape.gbx.old""")
        except FileNotFoundError as e:
            self.addProgressStep(f"""Renaming .Shape.gbx to .Shape.gbx.old failed""", [e])
            self.convert_has_failed = True

        










def updateConvertStatusNumbersInUI(convert_failed: bool, obj_name: str) -> None:
    """updates the numbers for converting which are displaed in the ui panel"""
    tm_props = getTmProps()

    if not convert_failed:
        tm_props.NU_convertedSuccess += 1
    
    else:       
        tm_props.NU_convertedError += 1
        tm_props.ST_convertedErrorList += f"%%%{obj_name}"

    tm_props.NU_convertedRaw += 1
    tm_props.NU_converted     = int(tm_props.NU_convertedRaw / tm_props.NU_convertCount * 100)



def updateConvertTimes()->None:
    """update the remaining and elapsed time in the ui for the convert"""
    tm_props = getTmProps()
    
    converts_cancelled           = tm_props.CB_stopAllNextConverts
    convert_is_done              = tm_props.CB_converting is False
    last_convert_duration        = tm_props.NU_lastConvertDuration
    convert_started_at           = tm_props.NU_convertStartedAt
    convert_start_now            = int(time.perf_counter())
    convert_duration_since_start = convert_start_now - convert_started_at

    remaining_time = last_convert_duration - convert_duration_since_start

    if last_convert_duration == -1 or convert_is_done or converts_cancelled:
        return

    # debug(f"conv dura: start={convert_started_at}, current?={convert_start_now}, elapsed?={convert_duration_since_start}")

    tm_props.NU_convertDurationSinceStart = int(convert_duration_since_start) 
    tm_props.NU_remainingConvertTime      = int(remaining_time) 


@newThread
def startBatchConvert(fbxfilepaths: list[exportFBXModel]) -> None:
    """convert each fbx one after one, create a new thread for it"""
    tm_props_convertingItems = getTmConvertingItemsProp()
    tm_props = getTmProps()
    results  = []
    game     = "ManiaPlanet" if isGameTypeManiaPlanet() else "Trackmania2020"
    notify   = tm_props.CB_notifyPopupWhenDone

    tm_props.CB_showConvertPanel = True
    tm_props.NU_convertStartedAt = int(time.perf_counter())

    timer = Timer(callback=updateConvertTimes)
    timer.start()

    tm_props_convertingItems.clear()

    items_convert_index = {}
    counter = 0

    fail_count    = 0
    success_count = 0
    atleast_one_convert_failed = fail_count > 0
    

    for exported_fbx in fbxfilepaths:
        name = getFilenameOfPath(exported_fbx.filepath, remove_extension=True)
        item = tm_props_convertingItems.add()
        item.name = name
        items_convert_index[ name ] = counter
        counter += 1

    for exported_fbx in fbxfilepaths:
        fbxfilepath = exported_fbx.filepath
        name        = getFilenameOfPath(exported_fbx.filepath, remove_extension=True)

        current_convert_timer = Timer()
        current_convert_timer.start()
        
        convertTheFBX = CONVERT_ITEM(fbxfilepath=fbxfilepath, game=game)
        convertTheFBX.start() #start the convert (call internal run())
        convertTheFBX.join()  #waits until the thread terminated (function/convert is done..)
        
        result = ConvertResult()
        result.name_raw = convertTheFBX.name_raw
        result.relative_fbx_filepath = convertTheFBX.fbx_filepath_relative
        result.mesh_error_message    = convertTheFBX.convert_message_mesh_shape_gbx
        result.mesh_returncode       = convertTheFBX.convert_returncode_mesh_shape_gbx
        result.item_error_message    = convertTheFBX.convert_message_item_gbx
        result.item_returncode       = convertTheFBX.convert_returncode_item_gbx
        result.convert_steps         = convertTheFBX.convert_progress
        result.convert_has_failed    = convertTheFBX.convert_has_failed
        results.append(result)

        failed              = True if convertTheFBX.convert_has_failed else False
        icon                = "CHECKMARK" if not failed else "FILE_FONT"
        current_item_index  = items_convert_index[ name ] # number

        if failed: fail_count    += 1
        else:      success_count += 1

        tm_props_convertingItems[ current_item_index ].name             = name
        tm_props_convertingItems[ current_item_index ].icon             = icon
        tm_props_convertingItems[ current_item_index ].failed           = failed
        tm_props_convertingItems[ current_item_index ].converted        = True
        tm_props_convertingItems[ current_item_index ].convert_duration = int(current_convert_timer.stop())

        if tm_props.CB_stopAllNextConverts is True:
            debug("Convert stopped, aborted by user (UI CHECKBOX)")
            break

    @newThread
    def RandomAttributeErrorWritingToIDclassesInThisContextIsNotAllowedBlaBla():
        def inner():
            try:
                convertDurationTime = math.ceil(timer.stop())
                tm_props.CB_converting = False
                tm_props.NU_currentConvertDuration = int(convertDurationTime)
                
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

                    makeToast(title, text, icon, 7000)

            except AttributeError as err:
                time.sleep(.02)
                debug(err)
                inner()
        inner()

    # only if vscode is opened ??
    RandomAttributeErrorWritingToIDclassesInThisContextIsNotAllowedBlaBla()

    

    writeConvertReport(results=results)
    









def writeConvertReport(results: list) -> None:
    """genertate status html file of converted fbx files"""
    errors      = 0
    converted   = len(results)
    
    for result in results:
        if result.convert_has_failed:
            errors += 1

    try:
        with open( fixSlash(PATH_CONVERT_REPORT), "w", encoding="utf-8") as f:
            
            resultList = ""
            for result in results:

                progress_LIs = ""
                for step in result.convert_steps:

                    sub_steps = step.additional_infos
                    sub_steps_LIs = ""
                    sub_steps_UL  = ""
                    for sub_step in sub_steps:
                        sub_steps_LIs += f"<li>{sub_step}</li>"
                    
                    if sub_steps_LIs:
                        sub_steps_UL = f"<ul>{sub_steps_LIs}</ul>"
                    
                    progress_LIs += f"""<li class="">{step.title}{sub_steps_UL}</li> """

                objName = result.relative_fbx_filepath
                objName = objName.replace(result.name_raw, f"""<i>{result.name_raw}</i>""")

                error_msg_item = result.item_error_message
                error_msg_mesh = result.mesh_error_message

                mesh_has_error = result.mesh_returncode > 0
                item_has_error = result.item_returncode > 0

                error_msg_mesh_pretty, \
                error_msg_mesh_original = beautifyError(error_msg_mesh) if mesh_has_error else ("", "")
                
                error_msg_item_pretty,\
                error_msg_item_original = beautifyError(error_msg_item) if item_has_error else ("", "")

                html_item_error = f"""
                    <li class="item-error"><b><h2>{error_msg_item_pretty}</h2><b> </li>
                    <li class="item-error original"><b>Original NadeoImporter.exe response:</b> <br />{error_msg_item_original} </li>
                    <hr>
                """ if item_has_error else ""

                html_mesh_error = f"""
                    <li class="mesh-error"><b><h2>{error_msg_mesh_pretty}</h2><b> </li>
                    <li class="mesh-error original"><b>Original NadeoImporter.exe response:</b> <br />{error_msg_mesh_original} </li>
                    <hr>
                """ if mesh_has_error else ""

                resultList += f"""
                    <li class="{"error" if result.convert_has_failed else "success"}">
                        <ul class="result-object">
                            <li class="item"><b>Item:</b> {objName}  </li>
                            <hr>
                            {html_item_error}
                            {html_mesh_error}
                            <li class="item-error"><b>Convert steps until convert failed:</b></li>
                            <ul class="progress-steps">
                                {progress_LIs}
                            </ul>
                        </ul>    
                    </li>
                    """
            
            fullHTML = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Convert Report</title>
                    <link rel="stylesheet" href="file://{getAddonPath()}assets/report.css">
                </head>
                <body>
                    <header>
                        <div>
                            Failed converts: {errors} of {converted}
                        </div>
                    </header>
                    <ul id="result-list">
                    {resultList}           
                    </ul>
                </body>
                </html>
                """
            f.write(fullHTML)
        
    except FileNotFoundError as e:
        makeReportPopup(
            "Writing file failed", 
            [
                "Can not write report file on desktop",
                "Try to run Blender once as admindistator" 
            ])


        
        
def beautifyError(error: str):
    """proper description from nadeoimporter return string"""
    LMMissing       = "lightmap"
    BMMissing       = "basematerial"
    MatMissing      = "no material"
    missingUV       = "uvlayers"
    commonNotFound  = "common"
    itemXMLMissing  = "item.xml"       
    
    error = error.replace("(b'", "")
    error = error.replace("\\r",  "<br />")
    error = error.replace("\\n'", "<br />")
    error = error.replace("\\n",  "<br />")
    error = error.replace("\\",   "/")
    error = error.replace(", None)", "")
        
    prettymsg = ""
    if LMMissing        in error.lower(): prettymsg="Lightmap uv layer is missing"
    if BMMissing        in error.lower(): prettymsg="Basematerial uv layer is missing"
    if MatMissing       in error.lower(): prettymsg="No material found, use atleast 1"
    if LMMissing        in error.lower(): prettymsg="Not enough UvLayers, BaseMaterial/Lightmap missing?"
    if missingUV        in error.lower(): prettymsg="Not enough UvLayers, BaseMaterial/Lightmap/Decal missing?"
    if commonNotFound   in error.lower(): prettymsg="Collection COMMON not found, does meshParams.xml exist?"
    if itemXMLMissing   in error.lower(): prettymsg="Item.xml not found, does it exists?"
    if prettymsg == "":                   prettymsg=error 

    return prettymsg, error

    
    
    



















        
        
        
        