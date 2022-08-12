from pydoc import text
import bpy
import os.path
import string
import webbrowser
import addon_utils
from pprint import pprint
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup,
)
from bpy.props import StringProperty

from ..utils.Functions      import *
from ..utils.Constants      import * 
from ..operators.OT_Items_Convert  import *

class TM_OT_Settings_AutoFindNadeoIni(Operator):
    bl_idname = "view3d.tm_autofindnadeoini"
    bl_description = "Automatic find NadeoIni"
    bl_label = "Automatic find NadeoIni"
        
    def execute(self, context):
        autoFindNadeoIni()
        return {"FINISHED"}


class TM_OT_Settings_ExecuteHelp(Operator):
    bl_idname = "view3d.tm_execute_help"
    bl_description = "Execute help"
    bl_label = "Execute help"

    command: StringProperty("")
        
    def execute(self, context):
        openHelp(self.command)
        return {"FINISHED"}



class TM_OT_Settings_InstallNadeoImporter(Operator):
    bl_idname = "view3d.tm_installnadeoimporter"
    bl_description = "install nando importerino"
    bl_label = "Check if nadeoimporter is installed"
        
    def execute(self, context):
        # installNadeoImporter()
        installNadeoImporterFromLocalFiles()
        return {"FINISHED"}

class TM_OT_Settings_InstallGameTextures(Operator):
    bl_idname = "view3d.tm_installgametextures"
    bl_description = "Download game textures and install in /Items/Textures/<>"
    bl_label = "Download Game Textures"
        
    def execute(self, context):
        installGameTextures()
        return {"FINISHED"}

class TM_OT_Settings_InstallGameAssetsLIbrary(Operator):
    bl_idname = "view3d.tm_installgameassetslibrary"
    bl_description = "Download assets library (download textures as well to see them in blender)"
    bl_label = "Download Game Assets Library"
        
    def execute(self, context):
        installGameAssetsLibrary()
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
        if saveBlendFile():
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
        update_available = AddonUpdate.checkForNewRelease()
        if not update_available:
            show_report_popup(
                "No update available", 
                [
                    f"your version: {AddonUpdate.addon_version}",
                    f"new version: {AddonUpdate.new_addon_version}",
                ])
        return {"FINISHED"}






def autoFindNadeoIni()->None:
    tm_props          = get_global_props()
    program_data_paths= [ fixSlash(PATH_PROGRAM_FILES_X86), fixSlash(PATH_PROGRAM_FILES) ]
    mp_envis          = ["TMStadium", "TMCanyon", "SMStorm", "TMValley", "TMLagoon"]
    alphabet          = list(string.ascii_lowercase) #[a-z]
    paths             = []
    ini               = ""
    

    if isGameTypeManiaPlanet(): 

        for pd_path in program_data_paths:
            paths.append(f"{pd_path}/ManiaPlanet/Nadeo.ini".replace("/", "\\"))
    
        for char in alphabet:
            paths.append(fr"{char}:\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Games\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Spiele\ManiaPlanet\Nadeo.ini")

        for envi in mp_envis:
            for pd_path in program_data_paths:
                paths.append(f"{pd_path}/Steam/steamapps/common/ManiaPlanet_{envi}/Nadeo.ini".replace("/", "\\"))


    if isGameTypeTrackmania2020():

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
    if isGameTypeManiaPlanet():
        tm_props.ST_nadeoIniFile_MP = ini
    
    if isGameTypeTrackmania2020():
        tm_props.ST_nadeoIniFile_TM = ini


def getDefaultSettingsJSON() -> dict:
    if not doesFileExist(PATH_DEFAULT_SETTINGS_JSON):
        debug("default settings file does not exist, create file")
        default_settings = {
            "author_name":            os.getlogin(), # current windows username (C:/Users/<>/...)
            "nadeo_ini_path_tm":      "",
            "nadeo_ini_path_mp":      "",
            "blender_grid_size":      "",
            "blender_grid_division" : ""
        }
        debug(default_settings, pp=True)
        with open(PATH_DEFAULT_SETTINGS_JSON, "w") as settingsfile:
            settingsfile.write(json.dumps(default_settings))
    
    with open(PATH_DEFAULT_SETTINGS_JSON, "r") as settingsfile:
        data = settingsfile.read()
        data = dict(json.loads(data))
        return data




def loadDefaultSettingsJSON() -> None:
    debug("load default settings.json")
    tm_props = get_global_props()
    # create settings.json if not exist
    data = getDefaultSettingsJSON()
    fromjson_author_name   = data.get("author_name")
    fromjson_nadeoini_tm   = data.get("nadeo_ini_path_tm")
    fromjson_nadeoini_mp   = data.get("nadeo_ini_path_mp")
    fromjson_grid_size     = data.get("blender_grid_size")
    fromjson_grid_division = data.get("blender_grid_division")


    if doesFileExist(fromjson_nadeoini_tm):
        tm_props.ST_nadeoIniFile_TM = fromjson_nadeoini_tm
    else:
        tm_props.ST_nadeoIniFile_TM = MSG_ERROR_NADEO_INI_NOT_FOUND


    if doesFileExist(fromjson_nadeoini_mp):
        tm_props.ST_nadeoIniFile_MP = fromjson_nadeoini_mp
    else:
        tm_props.ST_nadeoIniFile_MP = MSG_ERROR_NADEO_INI_NOT_FOUND
    

    tm_props.ST_author                  = fromjson_author_name   or tm_props.ST_author
    tm_props.LI_blenderGridSize         = fromjson_grid_size     or tm_props.LI_blenderGridSize 
    tm_props.LI_blenderGridSizeDivision = fromjson_grid_division or tm_props.LI_blenderGridSizeDivision 

    debug("default settings loaded, data:")
    debug(data, pp=True, raw=True)

    if isGameTypeManiaPlanet()    and tm_props.ST_nadeoIniFile_MP == ""\
    or isGameTypeTrackmania2020() and tm_props.ST_nadeoIniFile_TM:
        debug("nadeo ini path not found, search now")
        autoFindNadeoIni()



def saveDefaultSettingsJSON() -> None:
    debug("save default settings.json")
    tm_props = get_global_props()
    old_data = getDefaultSettingsJSON()
    with open(PATH_DEFAULT_SETTINGS_JSON, "w+") as settingsfile:
        new_data = {
            "author_name"           : tm_props.ST_author or old_data["author_name"],
            "nadeo_ini_path_mp"     : tm_props.ST_nadeoIniFile_MP or old_data["nadeo_ini_path_mp"],
            "nadeo_ini_path_tm"     : tm_props.ST_nadeoIniFile_TM or old_data["nadeo_ini_path_tm"],
            "blender_grid_size"     : tm_props.LI_blenderGridSize or old_data["blender_grid_size"],
            "blender_grid_division" : tm_props.LI_blenderGridSizeDivision or old_data["blender_grid_division"],
        }
        debug("new settings.json data:")
        debug(new_data, pp=True, raw=True)
        settingsfile.write(json.dumps(new_data))





def updateAddon() -> None:
    """update the addon if a new version exist and restart blender to use new version"""    
    AddonUpdate.doUpdate()




UVPACKER_ADDON_NAME = "UV-Packer"

def installUvPackerAddon() -> None:
    addon_is_installed = False
    for mod in addon_utils.modules():
        if(mod.bl_info.get('name') == UVPACKER_ADDON_NAME):
            addon_is_installed = True
    
    debug(f"UVPacker addon installed: {addon_is_installed}")
    if not addon_is_installed:
        debug(f"install now")
        bpy.ops.preferences.addon_install(filepath=getAddonAssetsAddonsPath() + 'UV-Packer-Blender-Addon_1.01.01.zip', overwrite=True)
        debug(f"installed")

    debug(f"enable addon")
    bpy.ops.preferences.addon_enable(module=UVPACKER_ADDON_NAME)
    debug(f"addon enabled")



def openHelp(helptype: str) -> None:
    """open exporer or webbrowser by given helptype"""
    cmd = "" #+path
    
    if   helptype == "open_work":           cmd = getGameDocPathWorkItems()
    elif helptype == "open_items":          cmd = getGameDocPathItems()
    elif helptype == "open_assets":         cmd = getGameDocPathItemsAssets()
    elif helptype == "debug_all":           debug_all()
    elif helptype == "open_documentation":  webbrowser.open(URL_DOCUMENTATION)
    elif helptype == "open_github":         webbrowser.open(URL_GITHUB)
    elif helptype == "open_convertreport":  subprocess.Popen(['start', fixSlash(PATH_CONVERT_REPORT)], shell=True)
    elif helptype == "open_changelog":      webbrowser.open(URL_CHANGELOG)
    elif helptype == "checkregex":          webbrowser.open(URL_REGEX)
    elif helptype == "testfunc":            unzipNewAndOverwriteOldAddon(filepath=getBlenderAddonsPath() + "blendermania-addon.zip")
    
    else:
        debug(f"Help command not found, {helptype=}")
        return

    if cmd:        
        cmd = f'explorer "{cmd}"'
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("\\\\", "\\")
        debug(cmd)
        subprocess.Popen(cmd, stdout=subprocess.PIPE)





