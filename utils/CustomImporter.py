import io
import zipfile

import bpy
import queue
import threading
import time
from mathutils import Vector, Quaternion
import html, json

from ..properties.PropertyIdentifiers import LightProp

from ..utils.NadeoImporter import BinaryReader, HeaderChunk

from ..utils import Constants


from ..utils.ItemsExportV2Models import * 
from ..utils.Dotnet import *
from ..utils.FunctionsV2 import *

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
        self.config = None
        self.embed_size = 0.0

class ItemConvert(threading.Thread):
    def __init__(self, fbxfilepath: str, 
                game: str,
                icon_path: str="",
                material_lib_path: str="") -> None:
        super(ItemConvert, self).__init__() #need to call init from Thread, otherwise error
        
        
        # relative (Items/...) & absolute (C:/Users...) fbx filepaths
        self.fbx_filepath           = fix_slash( fbxfilepath ) 
        self.fbx_filepath_relative  = fix_slash("Items/" + fbxfilepath.split("/Work/Items/")[-1]) 
        
        # xm filepaths located in next to the fbx file
        # self.xml_meshparams_filepath    = self.fbx_filepath.replace(".fbx", ".MeshParams.xml")
        # self.xml_item_filepath          = self.fbx_filepath.replace(".fbx", ".Item.xml")
        # self.xml_item_filepath_relative = self.fbx_filepath_relative.replace(".fbx", ".Item.xml")
        self.cfg_filepath = self.fbx_filepath.replace(".fbx", ".json")
        
        # gbx filepaths located in Documents/Items/
        self.gbx_filepath            = self.fbx_filepath.replace("/Work/Items/", "/Items/")
        self.gbx_mesh_filepath       = self.gbx_filepath.replace(".fbx", ".Mesh.Gbx")
        self.gbx_item_filepath       = self.gbx_filepath.replace(".fbx", ".Item.Gbx")
        self.gbx_trigger_filepath    = self.gbx_filepath.replace(".fbx", ".Trigger.Shape.Gbx")
        self.gbx_shape_filepath      = self.gbx_filepath.replace(".fbx", ".Shape.Gbx")
        self.gbx_shape_filepath_old  = self.gbx_filepath.replace(".fbx", ".Shape.Gbx.old")
        self.icon_path               = icon_path
        self.material_lib_path       = material_lib_path
        
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

        #self.physic_hack = physic_hack

        self.convert_is_done    = False
        self.convert_has_failed = False

        self.embed_size = 0.0

    
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
            
        
        # maniaplanet convert process
        # if self.game_is_maniaplanet:
        #     self.convert_mesh_and_shape_gbx() 
            
        #     if not self.convert_has_failed and self.physic_hack:
        #         self.hack_shape_gbx()

        #     if not self.convert_has_failed: 
        #         self.convert_item_gbx()

        #     if not self.convert_has_failed:
        #         self.pascalcase_gbx_filenames()
            
            
        if not self.convert_has_failed:
            self.embed_size = self.get_item_embed_size()
            self.add_progress_step(f"Convert succeeded - size = {self.embed_size}\n\n")
        else:
            mesh_returncode = self.convert_returncode_mesh_shape_gbx
            mesh_error_msg  = bytes(self.convert_message_mesh_shape_gbx or "", "utf-8").decode("unicode_escape")
            item_returncode = self.convert_returncode_item_gbx
            item_error_msg  = self.convert_message_item_gbx #bytes(self.convert_message_item_gbx or "", "utf-8").decode("unicode_escape") 

            errors = []

            if item_returncode > 0:
                errors.append(f"Returncode: {item_returncode}")
                errors.append(f"Original Response: {item_error_msg}")
            
            if mesh_returncode > 0:
                errors.append(f"Returncode: {mesh_returncode}")
                errors.append(f"Original Response: {mesh_error_msg}")
            
            self.add_progress_step("Convert failed\n\n", errors)
 


    def pascalcase_gbx_filenames(self) -> None:
        try:   os.rename(self.gbx_item_filepath  , re.sub(r"item\.gbx$",  "Item.Gbx",  self.gbx_item_filepath  , flags=re.IGNORECASE))
        except FileNotFoundError: pass
        try:   os.rename(self.gbx_mesh_filepath  , re.sub(r"mesh\.gbx$",  "Mesh.Gbx",  self.gbx_mesh_filepath  , flags=re.IGNORECASE))
        except FileNotFoundError: pass
        try:   os.rename(self.gbx_shape_filepath , re.sub(r"shape\.gbx$", "Shape.Gbx", self.gbx_shape_filepath , flags=re.IGNORECASE))
        except FileNotFoundError: pass
        try:   os.rename(self.gbx_trigger_filepath , re.sub(r"trigger\.shape\.gbx$", "Trigger.Shape.Gbx", self.gbx_trigger_filepath , flags=re.IGNORECASE))
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


        material_library_path = self.material_lib_path
        target : ItemModel = ItemModel.Prefab

        optimization: OptimizationOptions = OptimizationOptions.PreferNadeoImporterStructure

        self.add_progress_step(f"""Run: run_convert_fbx_to_gbx""")
        result = run_convert_fbx_to_gbx(
            fbx_path=self.fbx_filepath,
            material_library_path=material_library_path,
            item_output_path=self.gbx_item_filepath,
            icon_path=self.icon_path,
            target=target,
            optimization=optimization
        )
        self.convert_has_failed          = not result.success
        self.convert_message_item_gbx    = result.message
        #self.convert_returncode_item_gbx = result.returncode

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


    def get_item_embed_size(self):
        
        files = []

        if is_file_existing(self.gbx_item_filepath):     files.append(self.gbx_item_filepath)
        if is_file_existing(self.gbx_mesh_filepath):     files.append(self.gbx_mesh_filepath)
        if is_file_existing(self.gbx_shape_filepath):    files.append(self.gbx_shape_filepath)
        if is_file_existing(self.gbx_trigger_filepath):  files.append(self.gbx_trigger_filepath)

        total_size = 0.0

        # debug(f"Calculating embed size for item: {self.gbx_item_filepath}")

        try:
            for gbxfile in files:

                with open(gbxfile, "r+b") as f_item:
                    # read item file
                    item_data = f_item.read()
                    
                    try:
                        byter = BinaryReader(item_data)

                        # check version
                        (version,) = byter.unpack("<3xH")
                        if version != 6:
                            raise ValueError()
                        
                        # check class_id
                        (class_id, ) = byter.unpack("<4xI")
                        if class_id != 0x2e002000:
                            raise ValueError()

                        # header chunks
                        (user_data_size, num_headerchunks) = byter.unpack("<II")

                        chunks = []
                        icon_chunk_idx = -1

                        for i in range(num_headerchunks):
                            (chunk_id, chunk_size) = byter.unpack("<II")

                            chunk_size &= 0x7FFFFFFF # remove heavy flag
                            chunks.append(HeaderChunk(chunk_id, chunk_size))

                            if chunk_id == 0x2e001004:
                                icon_chunk_idx = i

                        if icon_chunk_idx < 0:
                            raise ValueError()

                        # read until icon chunk
                        for chunk in chunks[:icon_chunk_idx]:
                            byter.index += chunk.size

                        # overwrite icon chunk
                        old_icon_chunk_size = chunks[icon_chunk_idx].size

                        gbxfile_bytes = bytearray(
                            item_data[:byter.index] + 
                            item_data[byter.index + chunks[icon_chunk_idx].size:]
                        )
                    
                    except ValueError as err:
                        gbxfile_bytes = item_data

            
                    zip_buffer = io.BytesIO()



                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        zip_file.writestr("the-item-or-something", gbxfile_bytes)
                        zipped_size = zip_file.getinfo("the-item-or-something").compress_size / 1000 #kb
                        total_size +=  zipped_size
                        print(gbxfile.split("/")[-1] + " = " +  str(zipped_size))

        except PermissionError as err:
            total_size = -1.0
            debug(err.strerror)

        # debug(f"Total embed size for item {self.gbx_item_filepath}: {total_size}kb")

        return total_size



_CONVERT_QUEUE = queue.Queue()
_CONVERT_THREADS = []
_convert_timer_running = False

_CONVERT_RESULTS = []

_CONVERT_STEP_UPDATE = "update"
_CONVERT_STEP_COMPLETE = "complete"

def start_batch_convert(items: list[ExportedItem]):
    """convert each fbx one after one, create a new thread for it"""
    tm_props_convertingItems = get_convert_items_props()
    tm_props        = get_global_props()

    _reset_convert_progress_values()

    tm_props.CB_converting = True
    tm_props.CB_showConvertPanel = True
    tm_props.NU_convertStartedAt = int(time.perf_counter()) 

    tm_props_convertingItems.clear()
    counter = 0

    debug(f"Starting batch convert of {len(items)} items")

    for item_to_convert in items:
        name = get_path_filename(item_to_convert.fbx_path, remove_extension=True)
        item = tm_props_convertingItems.add()
        item.name = name
        item.name_raw = item_to_convert.name_raw
        item_to_convert.assigned_index = counter

        counter += 1

    global _CONVERT_THREADS
    _CONVERT_THREADS.clear()

    debug("Generating config and starting convert threads...")

    for item in items:
        item.game = GAMETYPE_TRACKMANIA2020 if is_game_trackmania2020() else GAMETYPE_MANIAPLANET

        item.material_lib_path = get_global_props().ST_materialLibPath
        generate_and_save_item_config(item)

        thread = threading.Thread(target=convert_fbx, args=[item])
        _CONVERT_THREADS.append(thread)
        thread.start()

    debug("All convert threads started.")
    global _CONVERT_RESULTS
    _CONVERT_RESULTS.clear()

    bpy.app.timers.register(_process_convert_queue, first_interval=0.5)

def plan_item(item: ExportedItem) -> dict | None:
    """save config next to the (already exported) fbx and run the dotnet planner, no gbx is generated"""
    item.game = GAMETYPE_TRACKMANIA2020 if is_game_trackmania2020() else GAMETYPE_MANIAPLANET
    item.material_lib_path = get_global_props().ST_materialLibPath
    generate_and_save_item_config(item)

    res = run_plan_fbx_to_gbx(
        fbx_path=item.fbx_path,
        material_library_path=item.material_lib_path,
        item_output_path=item.item_path,
        icon_path=item.icon_path,
        target=ItemModel.Prefab,
        optimization=OptimizationOptions.PreferNadeoImporterStructure,
    )
    if not res.success:
        debug(f"plan failed for {item.name}: {res.message}")
        return None
    return json.loads(res.stdout)  # stdout only, never res.message

def generate_and_save_item_config(item: ExportedItem) -> None:
    """generate item config and save it to json file next to the fbx"""
    item.config = _generate_item_config(item)
    cfg_save_path = item.fbx_path.replace(".fbx", ".json")
    _save_item_config(item.config, cfg_save_path)

def _save_item_config(config: ItemConfig, filepath: str) -> None:
    """save item config to json file"""
    cfg_dict = item_config_to_dict(config)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cfg_dict, f, ensure_ascii=False, indent=4)

def _process_convert_queue():
    """
    Timer callback on main thread. Apply queued updates to bpy safely.
    Return a float to reschedule, or None to stop.
    """
    debug("_process_convert_queue")

    tm_props = get_global_props()
    tm_props.NU_convertDurationSinceStart = int(time.perf_counter()) - tm_props.NU_convertStartedAt
    if tm_props.CB_converting is False: 
        return None
    
    failobjs = get_convert_items_failed_props().objects

    tm_props = get_global_props()

    global _convert_timer_running, _CONVERT_THREADS, _CONVERT_RESULTS

    try:
        tm_props_convertingItems = bpy.context.scene.tm_props_convertingItems
    except Exception:
        debug("context not available yet, try later")
        # if context not available yet, try later
        return 0.5


    while not _CONVERT_QUEUE.empty():
        print("processing convert queue...")
        msg = _CONVERT_QUEUE.get_nowait()
        # msg example: ("item_update", index, dict_of_values)

        convert_step = msg[0]

        if convert_step == _CONVERT_STEP_UPDATE:
            idx = msg[1]
            vals = msg[2]
            result = msg[3]
            obj = msg[4] 

            debug(f"update convert queue: {idx} {vals}")
            
            _CONVERT_RESULTS.append( result )
            
            # ensure index still valid
            try:
                entry = tm_props_convertingItems[idx]
            except Exception:
                continue
            # update properties (safe on main thread)
            for k, v in vals.items():
                setattr(entry, k, v)

            failed = vals.get("failed", False)

            debug(f"update convert status numbers in ui: failed={failed} for {entry.name}")
            debug(f"failcount before: {tm_props.NU_convertedError}")

            tm_props.NU_convertedRaw += 1
            tm_props.NU_converted = int(tm_props.NU_convertedRaw / tm_props.NU_convertCount * 100)
            if failed:
                tm_props.NU_convertedError += 1 
                failobjs.add().object = obj
            else:
                tm_props.NU_convertedSuccess += 1


        elif convert_step == _CONVERT_STEP_COMPLETE:
            # optional: do final UI updates, show report, etc. later i guess
            pass

    # check if any worker still alive
    any_alive = any(t.is_alive() for t in _CONVERT_THREADS)
    if any_alive or not _CONVERT_QUEUE.empty():
        # keep polling
        _convert_timer_running = True
        debug("_process_convert_queue: still converting, continue polling")
        return 0.5
    
    debug("_process_convert_queue: all done")
    
    tm_props.CB_converting = False
    tm_props.NU_prevConvertDuration = tm_props.NU_convertDurationSinceStart

    _write_convert_report(results=_CONVERT_RESULTS)

    _convert_timer_running = False
    _CONVERT_THREADS.clear()
    return None
    
import html
import json

REPORT_EXTRA_CSS = """
.result-wrapper {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.5fr);
    gap: 16px 24px;
    align-items: start;
}
.result-wrapper .full-row { grid-column: 1 / -1; }
.config-box {
    font-family: Consolas, Menlo, monospace;
    font-size: 0.85rem;
    line-height: 1.45;
    padding: 12px 16px;
    background: rgba(0,0,0,.35);
    border-radius: 6px;
    max-height: 600px;
    overflow: auto;
    box-sizing: border-box;
}
.config-box div { white-space: pre-wrap; overflow-wrap: anywhere; }
pre.item-error-message {
    white-space: pre-wrap !important;
    word-break: break-word;
    padding: 10px 12px;
    border-left: 3px solid #e55;
    background: rgba(255,80,80,.08);
}
@media (max-width: 1000px) {
    .result-wrapper { grid-template-columns: minmax(0, 1fr); }
}
"""


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _html_steps(steps) -> str:
    out = ""
    for step in steps:
        subs = "".join(
            f"<li>{_esc(s).replace(chr(10), '<br />')}</li>"
            for s in step.additional_infos
        )
        sub_ul = f"<ul>{subs}</ul>" if subs else ""
        out += f"<li>{_esc(step.title)}{sub_ul}</li>"
    return out


def _html_error(r: "ConvertResult") -> str:
    msg = (r.item_error_message or "").strip()
    if not msg:
        return "<h3>Error</h3><p>Convert failed, no error message returned.</p>"
    return f"""
        <h3>Error</h3>
        <pre class="item-error-message">{_esc(msg)}</pre>"""


def _config_to_text(config) -> str:
    cfg = item_config_to_dict(config)

    # in case the converter already returned a JSON string
    if isinstance(cfg, str):
        try:
            cfg = json.loads(cfg)
        except ValueError:
            return cfg

    return json.dumps(cfg, indent=2, default=str, ensure_ascii=False)


def _html_config(config) -> str:
    if config is None:
        return ""
    try:
        text = _config_to_text(config)
    except Exception as e:
        text = f"<config could not be serialized: {e}>"

    lines = []
    for line in text.split("\n"):
        indent  = len(line) - len(line.lstrip(" "))
        content = html.escape(line.strip()) or "&nbsp;"
        lines.append(f'<div style="padding-left:{indent}ch">{content}</div>')

    return f"""
        <h3>Config</h3>
        <div class="config-box">{"".join(lines)}</div>"""


def _html_result(r: "ConvertResult") -> str:
    path  = _esc(r.relative_fbx_filepath).replace("/", "<span class='slash'>/</span>")
    steps = _html_steps(r.convert_steps)

    steps_block = f"""
        <div class="result-text full-row">
            <h3>Conversion Log:</h3>
            <ul class="progress-steps">{steps}</ul>
        </div>""" if steps else ""

    return f"""
    <div class="result-wrapper">
        <div class="result-text full-row">
            <h2 class="item-name">{_esc(r.name_raw)}</h2>
            <p class="item-path">{path}</p>
            <hr>
        </div>

        <div class="result-text">
            {_html_error(r)}
        </div>

        <div class="result-text">
            {_html_config(r.config)}
        </div>

        {steps_block}
    </div>"""

def _write_convert_report(results: list["ConvertResult"]) -> None:
    """generate status html file of converted fbx files"""
    failed      = [r for r in results if r.convert_has_failed]
    errors      = len(failed)
    converted   = len(results)
    result_list = "".join(_html_result(r) for r in failed)
    addon       = get_addon_path()

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Convert Report</title>
    <link rel="stylesheet" href="file://{addon}assets/convert_report/google-code-prettify/prettify.css">
    <script src="file://{addon}assets/convert_report/google-code-prettify/run_prettify.js?autoload=true&amp;skin=sunburst&amp;lang=css"></script>
    <link rel="stylesheet" href="file://{addon}assets/convert_report/google-code-prettify/sunburst.css">
    <link rel="stylesheet" href="file://{addon}assets/convert_report/report.css">
    <style>{REPORT_EXTRA_CSS}</style>
</head>
<body>
    <main>
        <header><h1>Failed converts: {errors} of {converted}</h1></header>
        {result_list}
    </main>

    <div id="this-is-fine"></div>

    <div id="help-buttons">
        <a href="https://discord.com/channels/891279104794574948/921509901077975060" class="btn" target="_blank" id="ask-for-help">Help on Discord</a>
        <a href="https://github.com/skyslide22/blendermania-addon/wiki/06.-Converting-Troubleshooting" target="_blank" class="btn" id="documentation">Open Documentation</a>
        <a href="#" onclick="focusBlenderAndCloseErrorReport(); return false;" class="btn" id="close-page">Back to Blender</a>
    </div>

    <script>
    window.focusBlenderAndCloseErrorReport = async function() {{
        try {{
            await fetch("http://localhost:42069/focus_blender");
            window.close();
        }} catch {{
            alert("error: blender server is not running");
        }}
    }};
    </script>
</body>
</html>"""

    try:
        with open(fix_slash(PATH_CONVERT_REPORT), "w", encoding="utf-8") as f:
            f.write(full_html)
    except FileNotFoundError:
        show_report_popup(
            "Writing file failed",
            [
                "Can not write report file in user dir",
                "Try to run Blender once as administrator",
            ],
        )

def convert_fbx(item: ExportedItem) -> None:

    name = get_path_filename(item.fbx_path, remove_extension=True)

    current_convert_timer = Timer()
    current_convert_timer.start()
    
    conversion = ItemConvert(
        fbxfilepath=item.fbx_path, 
        game=item.game, 
        icon_path=item.icon_path,
        material_lib_path=item.material_lib_path)
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
    result.config                = item.config
    result.embed_size            = conversion.embed_size

    debug(f"convert done for index {item.assigned_index}, embed size: {result.embed_size}kb")

    failed = True if conversion.convert_has_failed else False
    icon   = "CHECKMARK" if not failed else "FILE_FONT"
    

    update = {
        "name": name,
        "icon": icon,
        "failed": failed,
        "converted": True,
        "convert_duration": int(current_convert_timer.stop()),
        "embed_size": result.embed_size,
    }

    _CONVERT_QUEUE.put( (_CONVERT_STEP_UPDATE, item.assigned_index, update, result, next(iter(item.objects))) )



def _reset_convert_progress_values() -> None:
    """reset all convert related properties in the ui"""
    
    fails = get_convert_items_failed_props()
    fails.objects.clear()

    tm_props = get_global_props()
    tm_props.NU_converted        = 0
    tm_props.NU_convertedRaw     = 0
    tm_props.NU_convertedSuccess = 0
    tm_props.NU_convertedError   = 0
    tm_props.NU_convertDurationSinceStart = 0
    tm_props.ST_convertedErrorList = ""
    tm_props.CB_showConvertPanel = False

    global _CONVERT_RESULTS, _CONVERT_THREADS, _convert_timer_running, _CONVERT_QUEUE
    _CONVERT_RESULTS.clear()
    _CONVERT_THREADS.clear()
    _convert_timer_running = False
    _CONVERT_QUEUE.queue.clear()


# config

def _generate_item_config(item: ExportedItem) -> ItemConfig:
    cfg = ItemConfig()
    tm_props = get_global_props()

    collection = item.collection

    cfg.AuthorName = tm_props.ST_author or "blendermania"
    cfg.Collection = tm_props.LI_materialCollection if getattr(tm_props, "LI_materialCollection", None) else cfg.Collection
    cfg.Name = collection.name
    cfg.Description = collection.get("description", "N/A")
    cfg.LodParameters = _get_lod_parameters_from_collection(collection)
    cfg.Waypoint = _get_waypoint_from_collection(collection)
    cfg.Placement = generate_placement_config(collection)
    _add_pivot_objects_to_placement(cfg.Placement, item.objects)
    _add_magnet_objects_to_placement(cfg.Placement, item.objects)
    cfg.Scale = item.scale
    cfg.Materials = _get_material_configs_from_collection(item.objects, collection)
    cfg.Lights = _get_light_configs_from_collection(item.objects, collection)
    cfg.Meshes = _get_mesh_configs_from_collection(item.objects, collection)
    cfg.MovingGroups = _get_moving_group_configs_from_collection(collection)
    cfg.ScaleOptions = _get_scale_config_from_collection(collection)

    #TODO: conversion options



    return cfg

def _add_pivot_objects_to_placement(placement: PlacementConfig, objs: list[bpy.types.Object]) -> None:
    """append all objects marked as pivot to the placement pivots (position relative to the item origin)"""
    pivot_objs = [
        obj for obj in objs
        if getattr(obj, ObjectProp.PIVOT, False) and not getattr(obj, ObjectProp.IGNORE, False)
    ]
    if not pivot_objs:
        return

    offset = get_offset_from_item_origin(objs) or [0.0, 0.0, 0.0]

    if placement.PivotPositions is None:
        placement.PivotPositions = []
    if placement.PivotRotations is None:
        placement.PivotRotations = []

    # keep rotations aligned with positions
    while len(placement.PivotRotations) < len(placement.PivotPositions):
        placement.PivotRotations.append(Quaternion())

    for obj in pivot_objs:
        # matrix_world can be stale here: the export moved the objects by the origin offset and back again
        # without a depsgraph update, so the offset would be subtracted twice. Rebuild from the current local values.
        world = _fresh_world_matrix(obj)
        loc = world.translation
        placement.PivotPositions.append(Vec3(
            loc.x - offset[0],
            loc.y - offset[1],
            loc.z - offset[2],
        ))
        placement.PivotRotations.append(world.to_euler('XYZ').to_quaternion())

def _add_magnet_objects_to_placement(placement: PlacementConfig, objs: list[bpy.types.Object]) -> None:
    """append all objects marked as magnet to the placement magnets (position relative to the item origin)"""
    magnet_objs = [
        obj for obj in objs
        if getattr(obj, ObjectProp.MAGNET, False) and not getattr(obj, ObjectProp.IGNORE, False)
    ]
    if not magnet_objs:
        return

    offset = get_offset_from_item_origin(objs) or [0.0, 0.0, 0.0]

    if placement.MagnetPositions is None:
        placement.MagnetPositions = []
    if placement.MagnetRotations is None:
        placement.MagnetRotations = []

    # keep rotations aligned with positions
    while len(placement.MagnetRotations) < len(placement.MagnetPositions):
        placement.MagnetRotations.append(Vec3())

    for obj in magnet_objs:
        # matrix_world can be stale here: the export moved the objects by the origin offset and back again
        # without a depsgraph update, so the offset would be subtracted twice. Rebuild from the current local values.
        world = _fresh_world_matrix(obj)
        loc = world.translation
        placement.MagnetPositions.append(Vec3(
            loc.x - offset[0],
            loc.y - offset[1],
            loc.z - offset[2],
        ))
        rot = obj.rotation_euler
        rot_deg = [math.degrees(v) for v in rot]
        placement.MagnetRotations.append(Vec3.from_seq(rot_deg))


def _fresh_world_matrix(obj: bpy.types.Object):
    """world matrix built from the current location/rotation/scale of the object and its parents"""
    matrix = obj.matrix_basis.copy()
    if obj.parent is not None:
        matrix = _fresh_world_matrix(obj.parent) @ obj.matrix_parent_inverse @ matrix
    return matrix

def _get_lod_parameters_from_collection(collection: bpy.types.Collection) -> LodParameters:
    params = LodParameters()
    params.MaxLodDistances = [
        float(lod_prop.distance)
        for lod_prop in getattr(collection, CollectionProp.LODS, [])
    ]
    if len(params.MaxLodDistances) == 0:
        return None
    return params

def _get_waypoint_from_collection(collection: bpy.types.Collection) -> Waypoint | None:

    coll_wp_type = _get_waypoint_type_from_collection(collection)

    if not coll_wp_type:
        return None

    wp = Waypoint()
    wp.Type = coll_wp_type
    wp.NoRespawn = getattr(collection, CollectionProp.NO_RESPAWN, False)

    wp.TorqueX = getattr(collection, CollectionProp.TORQUE_X)
    wp.TorqueDuration = getattr(collection, CollectionProp.TORQUE_DURATION)
    wp.DefaultGravitySpawn = Vec3.from_seq(getattr(collection, CollectionProp.DEFAULT_GRAVITY_SPAWN))


    return wp

def _get_waypoint_type_from_collection(collection: bpy.types.Collection) -> EWaypointType | None:
    coll_cp_type = getattr(collection, CollectionProp.WAYPOINT_TYPE, None)

    match coll_cp_type:
        case Constants.WAYPOINT_NAME_CHECKPOINT:
            return EWaypointType.Checkpoint
        case Constants.WAYPOINT_NAME_START:
            return EWaypointType.Start
        case Constants.WAYPOINT_NAME_FINISH:
            return EWaypointType.Finish
        case Constants.WAYPOINT_NAME_STARTFINISH:
            return EWaypointType.StartFinish
        case _:
            return None

def _get_light_configs_from_collection(objs: list[bpy.types.Object], collection: bpy.types.Collection) -> list[LightConfig]:
    light_configs = []
    
    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_LIGHT:
            continue
        
        light: bpy.types.Light = obj.data
        light_is_spot = light.type == LIGHT_TYPE_SPOT
        light_is_point = light.type == LIGHT_TYPE_POINT

        if not (light_is_spot or light_is_point):
            continue

        light_cfg = LightConfig()

        light_cfg.Name  = obj.name
        light_cfg.Type  = light.type
        
        light_cfg.Color     = f"{int(light.color[0]*255):02x}{int(light.color[1]*255):02x}{int(light.color[2]*255):02x}"
        light_cfg.Intensity = light.energy
        light_cfg.NightOnly = getattr(light, LightProp.LIGHT_NIGHT_ONLY, False) # custom prop
        light_cfg.Distance  = light.shadow_soft_size


        light_cfg.PointEmissionRadius = getattr(light, LightProp.LIGHT_EMITTING_RADIUS, 0)
        light_cfg.PointEmissionLength = getattr(light, LightProp.LIGHT_EMITTING_LENGTH, 0)

        light_cfg.SpotEmissionRadius = getattr(light, LightProp.LIGHT_EMITTING_RADIUS, 0)
        light_cfg.SpotEmissionLength = getattr(light, LightProp.LIGHT_EMITTING_LENGTH, 0)


        # convert euler to degree
        spot_size_degree = light.spot_size * (180.0 / math.pi) if light_is_spot else 0.0

        light_cfg.SpotInnerAngle = spot_size_degree * getattr(light, "spot_blend", 0)
        light_cfg.SpotOuterAngle = spot_size_degree

        is_advanced = getattr(light, LightProp.LIGHT_CONFIG_TYPE, False) == "ADVANCED"
        if is_advanced:
            light_cfg.Advanced = AdvancedLightConfig()
            light_cfg.Advanced.LightingEnabled = getattr(light, LightProp.LIGHT_ENABLED, True)
            light_cfg.Advanced.SpecularEnabled = getattr(light, LightProp.LIGHT_ENABLE_SPECULAR, True)
            light_cfg.Advanced.CastShadows = getattr(light,"use_shadow", True)
            light_cfg.Advanced.AttenuationTension = getattr(light, LightProp.LIGHT_ATTENUATION_TENSION, 0.3)
            light_cfg.Advanced.AttenuationDerivativeAtZero = getattr(light, LightProp.LIGHT_ATTENUATION_DERIVATIVE_AT_ZERO, -1.5)
            light_cfg.Advanced.AttenuationHdrRadiusCoefficient = getattr(light, LightProp.LIGHT_ATTENUATION_HDR_RADIUS_COEFF, 0.015625)

            if getattr(light, LightProp.LIGHT_INVERTED, False):
                light_cfg.Intensity *= -1.0


        light_configs.append(light_cfg)

    return light_configs


def _get_material_configs_from_collection(objs: list[bpy.types.Object], collection: bpy.types.Collection) -> list[MaterialConfig]:
    material_configs = []

    materials   = set()
    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_MESH:
            continue
        
        for mat_slot in obj.material_slots:
           for mat_slot in obj.material_slots:
                materials.add(mat_slot.material)

    for mat in materials:
        if mat is None:
            continue
        mat_name    = mat.name
        mat_game_is_tm2020      = mat.gameType.lower() == "trackmania2020"
        mat_game_is_maniaplanet = mat.gameType.lower() == "maniaplanet"
        mat_physic_id           = mat.physicsId
        mat_use_physicid        = mat.usePhysicsId and mat_physic_id # can be empty
        mat_gameplay_id         = mat.gameplayId
        mat_use_gameplay_id     = mat.useGameplayId
        mat_model               = mat.model
        mat_envi_collection     = mat.environment
        mat_link                = mat.link
        mat_basetexture         = fix_slash(mat.baseTexture)
        mat_basetexture         = re.sub(r"(?i)items/(?:_+|\-+)", r"Items/", mat_basetexture)
        mat_color               = mat.diffuse_color     # extract diffuse collor by default

        if mat.use_nodes: # replace with BSDF color
            if "cus_color" in mat.node_tree.nodes:
                mat_color = mat.node_tree.nodes["cus_color"].outputs[0].default_value
            else:
                mat_color = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

        mat_custom_color     = rgb_to_hex(mat_color, "", True) # convert to Hex with gamma correction
        mat_use_custom_color = mat_color[3] > 0                # use custom color only if material color has Alpha > 0
        
        # maniaplanet relateed (external texture in Maniaplanet/Items/blabla_D.dds)
        if mat_basetexture:
            mat_basetexture = fix_slash( mat_basetexture )
            mat_basetexture = re.sub(r".*/Items/|_?(D|N|S|I)\.dds", "", mat_basetexture, flags=re.IGNORECASE)
            mat_basetexture = "/Items/" + mat_basetexture
        else: 
            mat_basetexture = mat_link

        mat_config = MaterialConfig()
        mat_config.Name = mat_name

        if mat_game_is_tm2020:
            if mat.isLibraryMaterial: # new materiallib flow: explicit "use color" checkbox
                use_custom_color_attr = mat.useColor
            else:                     # legacy flow
                use_custom_color_attr = mat_use_custom_color and mat_link.lower().startswith("custom")
            mat_config.Link = mat_link
            if use_custom_color_attr:
                mat_config.Color = mat_custom_color
            if mat_use_physicid:
                mat_config.PhysicsId = mat_physic_id
            if mat_use_gameplay_id:
                mat_config.GameplayId = mat_gameplay_id
        elif mat_game_is_maniaplanet:
            mat_config.Model = mat_model
            mat_config.BaseTexture = mat_basetexture
            mat_config.PhysicsId = mat_physic_id
        
        material_configs.append(mat_config)


    return material_configs

def _get_mesh_configs_from_collection(objs: list[bpy.types.Object], collection: bpy.types.Collection) -> list[MeshConfig]:
    mesh_configs = []

    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_MESH:
            continue
        
        mesh_cfg = MeshConfig()
        mesh_cfg.Name = obj.name

        mesh_flags = MeshFlags.None_
        if getattr(obj, ObjectProp.NON_COLLIDABLE, False):
            mesh_flags |= MeshFlags.NonCollidable
        if getattr(obj, ObjectProp.INVISIBLE, False):
            mesh_flags |= MeshFlags.Invisible
        if getattr(obj, ObjectProp.TRIGGER_WAYPOINT, False):
            mesh_flags |= MeshFlags.TriggerWaypoint
        if getattr(obj, ObjectProp.TRIGGER_EFFECT, False):
            mesh_flags |= MeshFlags.TriggerEffect
        if getattr(obj, ObjectProp.SOCKET, False):
            mesh_flags |= MeshFlags.Socket
        if getattr(obj, ObjectProp.NO_MERGE, False):
            mesh_flags |= MeshFlags.SingleMesh

       
        gameplay_dir = Vector(getattr(obj, ObjectProp.GAMEPLAY_MAIN_DIR, None))
        gameplay_dir.normalize()
        gameplay_strength = getattr(obj, ObjectProp.GAMEPLAY_STRENGTH, 1.0)
        mesh_cfg.GameplayMainDir = Vec3.from_seq(gameplay_dir * gameplay_strength)
        
        if mesh_flags & MeshFlags.TriggerWaypoint:
            mesh_cfg.WaypointType = _get_waypoint_type_from_collection(collection)
        if mesh_flags & MeshFlags.TriggerEffect:
            mesh_cfg.TriggerEffect = getattr(obj, ObjectProp.TRIGGER_EFFECT_TYPE, None)
           

        if getattr(obj, ObjectProp.ENABLE_LODS, False):
            mesh_cfg.Lods = [int(lod.value) for lod in getattr(obj, ObjectProp.LOD_INDEXES, [])]

        if getattr(obj, ObjectProp.OVERRIDE_LIGHTMAP_SIZE, False):
            mesh_cfg.LightmapSize = getattr(obj, ObjectProp.LIGHTMAP_SIZE, None)


        is_moving_group = False
        obj_col = get_object_moving_group(obj)
        if obj_col is not None:
            is_moving_group = True
        if is_moving_group:
            mesh_cfg.MovingGroup = obj_col.name
            mesh_flags |= MeshFlags.Moving
        
        mesh_cfg.MeshFlags = mesh_flags

        mesh_configs.append(mesh_cfg)

    return mesh_configs

def _get_moving_group_configs_from_collection(collection: bpy.types.Collection) -> list[MovingGroupConfig]:
    moving_groups_configs = []

    col_children = get_item_moving_groups(collection)

    for child_col in col_children:
        if getattr(child_col, CollectionProp.MOVING_GROUP, False):
            moving_group_cfg = MovingGroupConfig()
            moving_group_cfg.MovingGroupId = child_col.name
            relative_moving_group = getattr(child_col, CollectionProp.RELATIVE_MOVING_GROUP, None)
            if relative_moving_group:
                moving_group_cfg.ParentMovingGroupId = relative_moving_group.name
            anchor = getattr(child_col, CollectionProp.MOVING_ANCHOR, None)
            if anchor:
                moving_group_cfg.RotationAnchorNode = anchor.name

            kinematic_model_config = KinematicModelConfig()
            kinematic_model_config.CastStaticShadow = getattr(child_col, CollectionProp.KINEMATIC_CAST_SHADOW)
            kinematic_model_config.IsKinematic = getattr(child_col, CollectionProp.KINEMATIC_IS_KINEMATIC)
            kinematic_model_config.PeriodicSc = getattr(child_col, CollectionProp.KINEMATIC_PERIODIC_SC)
            kinematic_model_config.PeriodicScMax = getattr(child_col, CollectionProp.KINEMATIC_PERIODIC_SC_MAX)
            kinematic_model_config.Phase01 = getattr(child_col, CollectionProp.KINEMATIC_PHASE_01)
            kinematic_model_config.Phase01Max = getattr(child_col, CollectionProp.KINEMATIC_PHASE_01_MAX)
            kinematic_model_config.TextureId = getattr(child_col, CollectionProp.KINEMATIC_TEXTURE_ID)

            moving_group_cfg.KinematicModel = kinematic_model_config

            kinematic_movement = KinematicMovement()
            kinematic_movement.TransAxis = getattr(child_col, CollectionProp.KINEMATIC_TRANS_AXIS)
            kinematic_movement.TransMin = getattr(child_col, CollectionProp.KINEMATIC_TRANS_MIN)
            kinematic_movement.TransMax = getattr(child_col, CollectionProp.KINEMATIC_TRANS_MAX)
            kinematic_movement.RotAxis = getattr(child_col, CollectionProp.KINEMATIC_ROT_AXIS)
            kinematic_movement.AngleMinDeg = math.degrees(getattr(child_col, CollectionProp.KINEMATIC_ROT_MIN))
            kinematic_movement.AngleMaxDeg = math.degrees(getattr(child_col, CollectionProp.KINEMATIC_ROT_MAX))
            kinematic_movement.TranslationAnims = [
                SubAnimFunc(
                    Ease=AnimEase(p.ease),
                    Reverse=bool(p.reverse),
                    Duration=max(0, p.duration),
                )
                for p in getattr(child_col, CollectionProp.KINEMATIC_TRANS_ANIMS)
            ]
            kinematic_movement.RotationAnims = [
                SubAnimFunc(
                    Ease=AnimEase(p.ease),
                    Reverse=bool(p.reverse),
                    Duration=max(0, p.duration),
                )
                for p in getattr(child_col, CollectionProp.KINEMATIC_ROT_ANIMS)
            ]

            if getattr(child_col, CollectionProp.KINEMATIC_HAS_MOVING_TEXTURE):
                moving_texture = MovingTextureConfig()
                moving_texture.SubTextures = getattr(child_col, CollectionProp.KINEMATIC_MOVING_TEXTURE_NUM)
                moving_texture.SubTexturesPerLine = getattr(child_col, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_LINE)
                moving_texture.SubTexturePerColumn = getattr(child_col, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_COLUMN)
                moving_texture.TopToBottom = getattr(child_col, CollectionProp.KINEMATIC_MOVING_TEXTURE_TOP_TO_BOTTOM)
                moving_texture.TextureAnims = [
                    TextureAnim(
                        TextureID=int(p.textureIndex),
                        Duration=int(p.duration),
                    )
                    for p in getattr(child_col, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS)
                ]
                kinematic_movement.MovingTexture = moving_texture

            moving_group_cfg.KinematicMovement = kinematic_movement

            
            moving_groups_configs.append(moving_group_cfg)
  

    return moving_groups_configs

def _get_scale_config_from_collection(collection: bpy.types.Collection) -> ScaleConfig | None:
    if getattr(collection, CollectionProp.SCALE_ITEM, False) is False:
        return None
    scale_cfg = ScaleConfig()
    scale_cfg.ScaleAnimationDistance = getattr(collection, CollectionProp.SCALE_ANIMATION_DISTANCE, True)
    scale_cfg.ScaleAnimationTime = getattr(collection, CollectionProp.SCALE_ANIMATION_TIME, False)
    scale_cfg.ScalePivots = getattr(collection, CollectionProp.SCALE_PIVOTS, True)
    scale_cfg.ScaleMagnets = getattr(collection, CollectionProp.SCALE_MAGNETS, True)
    scale_cfg.ScaleLightRadius = getattr(collection, CollectionProp.SCALE_LIGHT_DISTANCE, True)
    scale_cfg.ScaleLightmapSizeOverrides = getattr(collection, CollectionProp.SCALE_LIGHTMAP_SIZE, True)
    return scale_cfg
