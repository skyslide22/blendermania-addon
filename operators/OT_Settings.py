import bpy
import os.path
import string
import webbrowser
import addon_utils
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

from ..utils.Constants      import *
from ..utils.Functions      import *
from ..utils.NadeoXML       import (
    add_itemxml_template
)

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






def autoFindNadeoIni()->None:
    tm_props          = get_global_props()
    program_data_paths= [ fix_slash(PATH_PROGRAM_FILES_X86), fix_slash(PATH_PROGRAM_FILES) ]
    mp_envis          = ["TMStadium", "TMCanyon", "SMStorm", "TMValley", "TMLagoon"]
    alphabet          = list(string.ascii_lowercase) #[a-z]
    paths             = []
    ini               = ""
    

    if is_game_maniaplanet(): 

        for pd_path in program_data_paths:
            paths.append(f"{pd_path}/ManiaPlanet/Nadeo.ini".replace("/", "\\"))
    
        for char in alphabet:
            paths.append(fr"{char}:\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Games\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Spiele\ManiaPlanet\Nadeo.ini")

        for envi in mp_envis:
            for pd_path in program_data_paths:
                paths.append(f"{pd_path}/Steam/steamapps/common/ManiaPlanet_{envi}/Nadeo.ini".replace("/", "\\"))


    if is_game_trackmania2020():

        for pd_path in program_data_paths:
            paths.append(f"{pd_path}/Ubisoft/Ubisoft Game Launcher/games/Trackmania/Nadeo.ini".replace("/", "\\"))
            paths.append(f"{pd_path}/Epic Games/TrackmaniaNext/Nadeo.ini".replace("/", "\\"))
            paths.append(f"{pd_path}/Trackmania/Nadeo.ini".replace("/", "\\"))

        for char in alphabet:
            paths.append(fr"{char}:\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Games\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Ubisoft\Ubisoft Game Launcher\games\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Ubisoft Games\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Ubisoft Game Launcher\games\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Epic Games\TrackmaniaNext\Nadeo.ini")
            paths.append(fr"{char}:\games\uplay\Trackmania\Nadeo.ini")

    debug("Try to find Nadeo.ini in most used installation paths:")

    for path in paths:
        debug(path)
        if os.path.isfile(path):
            ini = path
            debug("Found!")
            break
            
    if ini == "": 
        ini=MSG_ERROR_NADEO_INI_NOT_FOUND
        debug("Nadeo.ini not found!")

    #change inifile
    if is_game_maniaplanet():
        tm_props.ST_nadeoIniFile_MP = ini
    
    if is_game_trackmania2020():
        tm_props.ST_nadeoIniFile_TM = ini


# TODO snake_case & rename & separate get_defaults()
def getDefaultSettingsJSON() -> dict:
    file_exist = is_file_existing(PATH_DEFAULT_SETTINGS_JSON)

    def get_defaults() -> str:
        return  {
            SETTINGS_AUTHOR_NAME:               os.getlogin(), #TODO DOTNET, current windows username (C:/Users/<>/...)
            SETTINGS_NADEO_INI_TRACKMANIA2020:  "",
            SETTINGS_NADEO_INI_MANIAPLANET:     "",
            SETTINGS_BLENDER_GRID_SIZE:         "",
            SETTINGS_BLENDER_GRID_DIVISION :    "",
            SETTINGS_ITEM_XML_TEMPLATES:        [],
            SETTINGS_NEW_BLEND_PREFERRED_GAME:  "",
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
    fromjson_new_blend_pref_game= data.get(SETTINGS_NEW_BLEND_PREFERRED_GAME)

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



def saveDefaultSettingsJSON() -> None:
    debug("save default settings.json")
    tm_props = get_global_props()
    old_data = getDefaultSettingsJSON()
    with open(PATH_DEFAULT_SETTINGS_JSON, "w+") as settingsfile:
        new_data = {
            SETTINGS_AUTHOR_NAME                : tm_props.ST_author or old_data[SETTINGS_AUTHOR_NAME],
            SETTINGS_NADEO_INI_MANIAPLANET      : tm_props.ST_nadeoIniFile_MP or old_data[SETTINGS_NADEO_INI_MANIAPLANET],
            SETTINGS_NADEO_INI_TRACKMANIA2020   : tm_props.ST_nadeoIniFile_TM or old_data[SETTINGS_NADEO_INI_TRACKMANIA2020],
            SETTINGS_BLENDER_GRID_SIZE          : tm_props.LI_blenderGridSize or old_data[SETTINGS_BLENDER_GRID_SIZE],
            SETTINGS_BLENDER_GRID_DIVISION      : tm_props.LI_blenderGridSizeDivision or old_data[SETTINGS_BLENDER_GRID_DIVISION],
            SETTINGS_ITEM_XML_TEMPLATES         : [temp.to_dict() for temp in bpy.context.scene.tm_props_itemxml_templates],
            SETTINGS_NEW_BLEND_PREFERRED_GAME   : get_game()
        }
        
            
        debug("new settings.json data:")
        debug(new_data, pp=True, raw=True)
        settingsfile.write(json.dumps(new_data, indent=4, sort_keys=True))






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
    subprocess.Popen(['start', fix_slash(PATH_CONVERT_REPORT)], shell=True)







