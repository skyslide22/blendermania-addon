import bpy
import os.path
import string
import webbrowser
import addon_utils
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from ..ui.widgets.progress import ProgressTaskMixin
from ..utils.Constants      import *
from ..utils.Functions      import *
from ..utils.NadeoXML       import (
    add_itemxml_template
)
from ..utils.FunctionsV2      import props_to_dict, props_from_dict

# from ..properties.ItemXMLTemplatesProperties import (
#     ItemXMLTemplate
# )

class TM_OT_Settings_AutoFindNadeoIni(Operator):
    bl_idname = "view3d.tm_autofindnadeoini"
    bl_description = "Automatic find NadeoIni"
    bl_label = "Automatic find NadeoIni"
        
    def execute(self, context):
        autoFindNadeoIni()
        return {"FINISHED"}


class TM_OT_Settings_OpenUrl(Operator):
    bl_idname = "view3d.tm_open_url"
    bl_description = "Execute help"
    bl_label = "Execute help"

    url: StringProperty("")
        
    def execute(self, context):
        open_url(self.url)
        return {"FINISHED"}

class TM_OT_Settings_OpenMessageBox(Operator):
    bl_idname = "view3d.tm_open_messagebox"
    bl_description = "Execute help"
    bl_label = "Execute help"

    @classmethod
    def get_text(*args: [str]) -> str:
        return __class__.text_splitter.join(args[1:]) # first item is bpy rna ?? skip..

    text_splitter = "%%%"

    link: StringProperty("")
    title: StringProperty("")
    infos: StringProperty("")
        
    def execute(self, context):
        if len(self.link) > 1:
            webbrowser.open(self.link, new=2)
        else:
            show_report_popup(self.title, [s for s in self.infos.split(__class__.text_splitter)], icon=ICON_INFO)
        return {"FINISHED"}


class TM_OT_Settings_OpenFolder(Operator):
    bl_idname = "view3d.tm_open_folder"
    bl_description = "Execute help"
    bl_label = "Execute help"

    folder: StringProperty("")
        
    def execute(self, context):
        open_folder(self.folder)
        return {"FINISHED"}


class TM_OT_Settings_DebugAll(Operator):
    bl_idname = "view3d.tm_debug_all"
    bl_description = "Execute help"
    bl_label = "Execute help"

    def execute(self, context):
        debug_all()
        return {"FINISHED"}


class TM_OT_Settings_OpenConvertReport(Operator):
    bl_idname = "view3d.tm_open_convert_report"
    bl_description = "Execute help"
    bl_label = "Execute help"

    def execute(self, context):
        open_convert_report()
        return {"FINISHED"}




class TM_OT_Settings_InstallNadeoImporter(Operator):
    bl_idname = "view3d.tm_installnadeoimporter"
    bl_description = "install nando importerino"
    bl_label = "Install Nadeoimporter"
        
    def execute(self, context):
        # installNadeoImporter()
        install_nadeoimporter_addon_assets()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to install the nadeoimporter?")

class TM_OT_Settings_InstallGameTextures(Operator):
    bl_idname = "view3d.tm_installgametextures"
    bl_description = "Download game textures and install in /Items/Textures/<>"
    bl_label = "Download Game Textures"
        
    def execute(self, context):
        install_game_textures()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to install the game textures?")

class TM_OT_Settings_InstallGameAssetsLIbrary(Operator):
    bl_idname = "view3d.tm_installgameassetslibrary"
    bl_description = "Download assets library (download textures as well to see them in blender)"
    bl_label = "Download Game Assets Library"
        
    def execute(self, context):
        install_game_assets_library()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to install the asset library?")

class TM_OT_Settings_InstallMaterialAssetsLibrary(ProgressTaskMixin, Operator):
    """the download runs in a thread (MaterialAssetsLibrary), the progress task only polls it: input stays free,
    ESC does not cancel (a modal sees ESC everywhere), the Cancel button does"""
    bl_idname = "view3d.tm_install_material_assets_library"
    bl_description = "Download and install the TM2020 Material Assets Library (by BigthirstyTM): registers it in the Asset Browser and selects its MaterialLib.txt"
    bl_label = "Install TM2020 Material Assets Library"

    task_title = "Installing material library"
    task_cancellable = False
    task_block_input = False
    task_wait_cursor = False
    task_timer_interval = 0.25
    task_status_hold = 10.0

    _install = None
    _sync = False

    @classmethod
    def poll(cls, context):
        from ..utils.MaterialAssetsLibrary import is_install_running
        return super().poll(context) and not is_install_running()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)  # confirmed -> execute

    def execute(self, context):
        if context.window is not None and not bpy.app.background:
            return ProgressTaskMixin.invoke(self, context, None)  # modal with progress
        self._sync = True                                         # scripts / background: blocking
        return ProgressTaskMixin.execute(self, context)

    def task_prepare(self, context):
        from ..utils.MaterialAssetsLibrary import start_install
        try:
            self._install = start_install(get_global_props().LI_DL_MaterialAssetsEdition)
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return False
        return True

    def task_steps(self, context):
        import time
        state = self._install
        while not state.done:
            with state.lock:  # copy, never yield while holding the lock (would stall the download thread)
                progress, status = state.progress, state.status
            yield progress / 100, status or "Starting..."
            if self._sync:
                time.sleep(0.2)
        if state.error:
            level = "WARNING" if state.error == "Cancelled" else "ERROR"
            self.set_result(level, f"Material library: {state.error}")
            return
        from ..utils.MaterialAssetsLibrary import finish_install
        self.set_result("INFO", finish_install(state))

    def cancel(self, context):
        """Blender ends the modal (file load, quit): stop the download as well"""
        from ..utils.MaterialAssetsLibrary import cancel_install
        cancel_install()
        super().cancel(context)

    def draw(self, context):
        from ..utils.MaterialAssetsLibrary import get_default_install_root
        edition = get_global_props().LI_DL_MaterialAssetsEdition
        size = "~2.3 GB" if edition == "materials-only" else "~3.3 GB"
        col = self.layout.column(align=True)
        col.label(text=f"Download the '{edition}' edition ({size}, twice the disk space during install)?")
        col.label(text=f"Folder: {get_default_install_root() or 'Trackmania Items folder not found!'}")
        col.label(text="The Material Lib setting is switched to the library's MaterialLib.txt.")
        col.label(text="Game assets remain property of their owners (community project).")


class TM_OT_Settings_CancelMaterialAssetsLibrary(Operator):
    bl_idname = "view3d.tm_cancel_material_assets_library"
    bl_description = "Cancel the running download/installation (finished downloads are kept for a retry)"
    bl_label = "Cancel"

    def execute(self, context):
        from ..utils.MaterialAssetsLibrary import cancel_install
        cancel_install()
        return {"FINISHED"}


class TM_OT_Settings_InstallBlendermaniaDotnet(Operator):
    bl_idname = "view3d.tm_install_blendermania_dotnet"
    bl_description = "Download blendermania-dotnet for activate map manipulation pannels"
    bl_label = "Download nlendermania-dotnet"
        
    def execute(self, context):
        install_blendermania_dotnet()
        return {"FINISHED"}



class TM_OT_Settings_UpdateAddonResetSettings(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_resetaddonupdatesettings"
    bl_description = "Reset settings after update"
    bl_icon = 'MATERIAL'
    bl_label = "Reset settings after update"
        
    def execute(self, context):
        tm_props = get_global_props()
        tm_props.CB_addonUpdateDLRunning  = False
        tm_props.NU_addonUpdateDLProgress = 0
        tm_props.ST_addonUpdateDLmsg    = ""
        tm_props.CB_addonUpdateDLshow     = False
        return {"FINISHED"}


class TM_OT_Settings_UpdateAddon(Operator):
    bl_idname = "view3d.tm_updateaddonrestartblender"
    bl_description = "fetch latest version from github, install, save and restart blender"
    bl_label = "Update addon"
    bl_options = {"REGISTER"}
        
    def execute(self, context):
        if save_blend_file():
            # if isAddonsFolderLinkedWithDevEnvi():
            #     makeReportPopup("dev environment, operator not executed", ["enable manually in TM_Settings.py:103"])
            #     return {"FINISHED"}

            updateAddon()
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}



class TM_OT_Settings_UpdateAddonCheckForNewRelease(Operator):
    bl_idname = "view3d.tm_checkfornewaddonrelease"
    bl_description = "check if new addon release is available"
    bl_label = "check for new release"
    bl_options = {"REGISTER"}
        
    def execute(self, context):
        AddonUpdate.check_for_new_release()
        if not AddonUpdate.new_addon_available:
            show_report_popup(
"No update available")
        return {"FINISHED"}




def find_nadeo_ini_trackmania2020():
    tm_props          = get_global_props()
    program_data_paths= [ fix_slash(PATH_PROGRAM_FILES_X86), fix_slash(PATH_PROGRAM_FILES) ]
    steamapps         = "Steam/steamapps/common"
    mp_envis          = ["TMStadium", "TMCanyon", "SMStorm", "TMValley", "TMLagoon"]
    alphabet          = list(string.ascii_lowercase) #[a-z]
    paths = []

    if is_file_existing(tm_props.ST_nadeoIniFile_TM):
        debug("Saved Nadeo.ini for trackmania2020 already found, keep using it.")
        return

    for pd_path in program_data_paths:
        paths.append(f"{pd_path}/Ubisoft/Ubisoft Game Launcher/games/Trackmania/Nadeo.ini".replace("/", "\\"))
        paths.append(f"{pd_path}/Epic Games/TrackmaniaNext/Nadeo.ini".replace("/", "\\"))
        paths.append(f"{pd_path}/Trackmania/Nadeo.ini".replace("/", "\\"))
        paths.append(f"{pd_path}/{steamapps}/Trackmania/Nadeo.ini".replace("/", "\\"))

    for char in alphabet:
        paths.append(fr"{char}:\Trackmania\Nadeo.ini")
        paths.append(fr"{char}:\Games\Trackmania\Nadeo.ini")
        paths.append(fr"{char}:\Ubisoft\Ubisoft Game Launcher\games\Trackmania\Nadeo.ini")
        paths.append(fr"{char}:\Ubisoft Games\Trackmania\Nadeo.ini")
        paths.append(fr"{char}:\Ubisoft Game Launcher\games\Trackmania\Nadeo.ini")
        paths.append(fr"{char}:\Epic Games\TrackmaniaNext\Nadeo.ini")
        paths.append(fr"{char}:\games\uplay\Trackmania\Nadeo.ini")

    debug("Try to find Nadeo.ini for trackmania2020 in most used installation paths:")

    ini = ""

    for path in paths:
        debug(path)
        if os.path.isfile(path):
            ini = path
            debug("Found!")
            break

    if ini == "": 
        ini=MSG_ERROR_NADEO_INI_NOT_FOUND
        debug("Nadeo.ini for trackmania2020 not found!")

    tm_props.ST_nadeoIniFile_TM = ini

    


def find_nadeo_ini_maniaplanet():
    tm_props          = get_global_props()
    program_data_paths= [ fix_slash(PATH_PROGRAM_FILES_X86), fix_slash(PATH_PROGRAM_FILES) ]
    steamapps         = "Steam/steamapps/common"
    mp_envis          = ["TMStadium", "TMCanyon", "SMStorm", "TMValley", "TMLagoon"]
    alphabet          = list(string.ascii_lowercase) #[a-z]
    paths = []

    if is_file_existing(tm_props.ST_nadeoIniFile_MP):
        debug("Saved Nadeo.ini for maniaplanet already found, keep using it.")
        return

    for pd_path in program_data_paths:
        paths.append(f"{pd_path}/ManiaPlanet/Nadeo.ini".replace("/", "\\"))

    for char in alphabet:
        paths.append(fr"{char}:\ManiaPlanet\Nadeo.ini")
        paths.append(fr"{char}:\Games\ManiaPlanet\Nadeo.ini")
        paths.append(fr"{char}:\Spiele\ManiaPlanet\Nadeo.ini")

    for envi in mp_envis:
        for pd_path in program_data_paths:
            paths.append(f"{pd_path}/{steamapps}/ManiaPlanet_{envi}/Nadeo.ini".replace("/", "\\"))

    debug("Try to find Nadeo.ini for maniaplanet in most used installation paths:")

    ini = ""

    for path in paths:
        debug(path)
        if os.path.isfile(path):
            ini = path
            debug("Found!")
            break

    if ini == "": 
        ini=MSG_ERROR_NADEO_INI_NOT_FOUND
        debug("Nadeo.ini for maniaplanet not found!")

    tm_props.ST_nadeoIniFile_MP = ini
    




def autoFindNadeoIni()->None:
    find_nadeo_ini_maniaplanet()
    find_nadeo_ini_trackmania2020()





# TODO snake_case & rename & separate get_defaults()
def getDefaultSettingsJSON() -> dict:
    file_exist = is_file_existing(PATH_DEFAULT_SETTINGS_JSON)

    def get_defaults() -> str:
        return  {
            SETTINGS_AUTHOR_NAME:               "",
            SETTINGS_NADEO_INI_TRACKMANIA2020:  "",
            SETTINGS_NADEO_INI_MANIAPLANET:     "",
            SETTINGS_BLENDER_GRID_SIZE:         "",
            SETTINGS_BLENDER_GRID_DIVISION :    "",
            SETTINGS_ITEM_XML_TEMPLATES:        [],
            SETTINGS_NEW_BLEND_PREFERRED_GAME:  "",
            SETTINGS_MATERIALLIB:                "",
            SETTINGS_PAK_EXTRACT:                "",
            SETTINGS_ITEM_PLACEMENT_TEMPLATES:  []
        }

    if not file_exist:
        debug("default settings file does not exist, use defaults")
        return get_defaults()

    else:
        with open(PATH_DEFAULT_SETTINGS_JSON, "r") as settingsfile:
            data = settingsfile.read()
            if data == "":
                return get_defaults()
            else:        
                try:
                    data = dict(json.loads(data))
                except: #  json.JSONDecodeError ??
                    data = get_defaults()
            return data




def loadDefaultSettingsJSON() -> None:
    debug("load default settings.json")
    tm_props = get_global_props()
    # create settings.json if not exist
    data = getDefaultSettingsJSON()
    fromjson_author_name        = data.get(SETTINGS_AUTHOR_NAME)
    fromjson_nadeoini_tm        = data.get(SETTINGS_NADEO_INI_TRACKMANIA2020)
    fromjson_nadeoini_mp        = data.get(SETTINGS_NADEO_INI_MANIAPLANET)
    fromjson_grid_size          = data.get(SETTINGS_BLENDER_GRID_SIZE)
    fromjson_grid_division      = data.get(SETTINGS_BLENDER_GRID_DIVISION)
    fromjson_itemxml_templates  = data.get(SETTINGS_ITEM_XML_TEMPLATES, [])
    fromjson_itemplacement_templates  = data.get(SETTINGS_ITEM_PLACEMENT_TEMPLATES, [])
    fromjson_new_blend_pref_game= data.get(SETTINGS_NEW_BLEND_PREFERRED_GAME)
    fromjson_material_lib_path  = data.get(SETTINGS_MATERIALLIB)
    tm_props["ST_pakExtractPath"] = data.get(SETTINGS_PAK_EXTRACT) or tm_props.ST_pakExtractPath  # item access: no save callback

    tm_props.ST_author                  = fromjson_author_name   or tm_props.ST_author
    tm_props.LI_blenderGridSize         = fromjson_grid_size     or tm_props.LI_blenderGridSize 
    tm_props.LI_blenderGridSizeDivision = fromjson_grid_division or tm_props.LI_blenderGridSizeDivision 

    is_new_blendfile = bpy.data.filepath == ""
    if is_new_blendfile:
        debug(f"new blendfile, load pref game: {fromjson_new_blend_pref_game}")
        if fromjson_new_blend_pref_game:
            tm_props.LI_gameType = fromjson_new_blend_pref_game
    else:
        debug(f"not a new blend file, keep selected game ({tm_props.LI_gameType})")

    debug("default settings loaded, data:")
    debug(data, pp=True, raw=True)


    # tm2020
    if is_file_existing(fromjson_nadeoini_tm):
        tm_props.ST_nadeoIniFile_TM = fromjson_nadeoini_tm
    elif is_file_existing(tm_props.ST_nadeoIniFile_TM) is False:
        autoFindNadeoIni()
    else:
        debug("tm2020 nadeo ini not found from json & blendfile")

    # maniaplanet
    if is_file_existing(fromjson_nadeoini_mp):
        tm_props.ST_nadeoIniFile_MP = fromjson_nadeoini_mp
    elif is_file_existing(tm_props.ST_nadeoIniFile_MP) is False:
        autoFindNadeoIni()
    else:
        debug("maniaplanet nadeo ini not found from json & blendfile")

    
    bpy.context.scene.tm_props_itemxml_templates.clear() # CollectionProperty

    for template_dict in fromjson_itemxml_templates:
        add_itemxml_template(template_dict)
    # placement templates: local ones are kept apart from the blend file's embedded ones
    reload_local_placement_templates()

    if is_file_existing(fromjson_material_lib_path):
        tm_props.ST_materialLibPath = fromjson_material_lib_path
    elif is_file_existing(tm_props.ST_materialLibPath) is False:
        tm_props.ST_materialLibPath = DEFAULT_MATERIAL_LIB_FILEPATH_TM2020
    else:
        debug("material lib not found from json & blendfile")



def _json_default(o):
    try:
        return list(o)  # mathutils Vector/Color/Matrix, sets, ...
    except TypeError:
        return str(o)


def reload_local_placement_templates() -> None:
    """(re)load the local placement templates (utils/TemplateLibrary: %APPDATA%/Blendermania/templates/placement)
    into the runtime-only window manager collection. Moves the old settings.json templates there once."""
    from ..utils import TemplateLibrary as TL
    try:
        moved = TL.migrate_settings_json_placement(getDefaultSettingsJSON().get(SETTINGS_ITEM_PLACEMENT_TEMPLATES, []))
        if moved:
            debug(f"moved {moved} placement template(s) from settings.json to {TL.local_dir(TL.KIND_PLACEMENT)}")
    except OSError as e:
        debug(f"moving placement templates failed: {e}")
    local = bpy.context.window_manager.tm_local_placement_templates
    local.clear()
    for entry in TL.local_entries(TL.KIND_PLACEMENT):
        try:
            data = TL.read(entry)
        except (OSError, ValueError) as e:
            debug(f"placement template {entry.path} unreadable: {e}")
            continue
        t = local.add()
        t.name = entry.name
        props_from_dict(t.config, data or {})


def save_local_placement_template(name: str, config) -> None:
    """store/overwrite local template `name` (config: PlacementProperties)"""
    from ..utils import TemplateLibrary as TL
    TL.save_local(TL.KIND_PLACEMENT, name, props_to_dict(config))
    reload_local_placement_templates()


def remove_local_placement_template(name: str) -> None:
    from ..utils import TemplateLibrary as TL
    TL.delete_local(TL.KIND_PLACEMENT, name)
    reload_local_placement_templates()


def saveDefaultSettingsJSON() -> None:
    debug("save default settings.json")
    tm_props = get_global_props()
    old_data = getDefaultSettingsJSON()
    new_data = {
            SETTINGS_AUTHOR_NAME                : tm_props.ST_author or old_data[SETTINGS_AUTHOR_NAME],
            SETTINGS_NADEO_INI_MANIAPLANET      : tm_props.ST_nadeoIniFile_MP or old_data[SETTINGS_NADEO_INI_MANIAPLANET],
            SETTINGS_NADEO_INI_TRACKMANIA2020   : tm_props.ST_nadeoIniFile_TM or old_data[SETTINGS_NADEO_INI_TRACKMANIA2020],
            SETTINGS_BLENDER_GRID_SIZE          : tm_props.LI_blenderGridSize or old_data[SETTINGS_BLENDER_GRID_SIZE],
            SETTINGS_BLENDER_GRID_DIVISION      : tm_props.LI_blenderGridSizeDivision or old_data[SETTINGS_BLENDER_GRID_DIVISION],
            SETTINGS_ITEM_XML_TEMPLATES         : [temp.to_dict() for temp in bpy.context.scene.tm_props_itemxml_templates],
            SETTINGS_ITEM_PLACEMENT_TEMPLATES   : old_data.get(SETTINGS_ITEM_PLACEMENT_TEMPLATES, []),  # blend templates are not merged into local ones

            SETTINGS_MATERIALLIB                : tm_props.ST_materialLibPath or old_data[SETTINGS_MATERIALLIB],
            SETTINGS_PAK_EXTRACT                : tm_props.ST_pakExtractPath or old_data.get(SETTINGS_PAK_EXTRACT, ""),
            SETTINGS_NEW_BLEND_PREFERRED_GAME   : get_game()
        }

    new_text = json.dumps(new_data, indent=4, sort_keys=True, default=_json_default)

    # compare serialized text (normalizes tuples/lists, key order, missing keys)
    old_text = None
    if is_file_existing(PATH_DEFAULT_SETTINGS_JSON):
        with open(PATH_DEFAULT_SETTINGS_JSON, "r") as settingsfile:
            old_text = settingsfile.read()
    if new_text == old_text:
        debug("settings.json unchanged, skip write")
        return

    debug("new settings.json data:")
    debug(new_data, pp=True, raw=True)
    with open(PATH_DEFAULT_SETTINGS_JSON, "w+") as settingsfile:
        settingsfile.write(new_text)






def updateAddon() -> None:
    """update the addon if a new version exist and restart blender to use new version"""    
    AddonUpdate.do_update()




UVPACKER_ADDON_NAME = "UV-Packer"

def installUvPackerAddon() -> None:
    try:
        addon_is_installed = False
        for mod in addon_utils.modules():
            if(mod.bl_info.get('name') == UVPACKER_ADDON_NAME):
                addon_is_installed = True
        
        debug(f"UVPacker addon installed: {addon_is_installed}")
        if not addon_is_installed:
            debug(f"install now")
            bpy.ops.preferences.addon_install(filepath=get_addon_assets_addons_path() + 'UV-Packer-Blender-Addon_1.01.01.zip', overwrite=True)
            debug(f"installed")

        debug(f"enable addon")
        bpy.ops.preferences.addon_enable(module=UVPACKER_ADDON_NAME)
        debug(f"addon enabled")
    except:
        pass # first try always fails




def open_folder(folder_abs: str) -> None:
    cmd = f"""explorer "{folder_abs}" """
    cmd = cmd.replace("/", "\\")
    cmd = cmd.replace("\\\\", "\\")
    subprocess.Popen(cmd, stdout=subprocess.PIPE)


def open_url(url: str) -> None:
    webbrowser.open(url)

def open_convert_report() -> None:
    open_url(fix_slash(PATH_CONVERT_REPORT))

# def open_convert_report() -> None:
#     subprocess.Popen(['start', fix_slash(PATH_CONVERT_REPORT)], shell=True)







