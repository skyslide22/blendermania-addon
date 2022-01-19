import bpy
import os.path
import string
import webbrowser
from pprint import pprint
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from .TM_Functions      import *
from .TM_Items_Convert  import *
from . import bl_info


class TM_OT_Settings_AutoFindNadeoIni(Operator):
    bl_idname = "view3d.tm_autofindnadeoini"
    bl_description = "Automatic find NadeoIni"
    bl_label = "Automatic find NadeoIni"
        
    def execute(self, context):
        autoFindNadeoIni()
        return {"FINISHED"}


class TM_OT_Settings_OpenDocumentation(Operator):
    bl_idname = "view3d.tm_opendoc"
    bl_description = "Open the documentation website"
    bl_label = "Open Documentation"
        
    def execute(self, context):
        openHelp("documentation")
        return {"FINISHED"}

class TM_OT_Settings_OpenGithub(Operator):
    bl_idname = "view3d.tm_opengithub"
    bl_description = "Open github website"
    bl_label = "Open github website"
        
    def execute(self, context):
        openHelp("github")
        return {"FINISHED"}

class TM_OT_Settings_InstallNadeoImporter(Operator):
    bl_idname = "view3d.tm_installnadeoimporter"
    bl_description = "Open github website"
    bl_label = "Check if nadeoimporter is installed"
        
    def execute(self, context):
        installNadeoImporter()
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

class TM_OT_Settings_DebugALL(Operator):
    bl_idname = "view3d.tm_debugall"
    bl_description = "debug print all addon python variable values"
    bl_label = "Debug print"
        
    def execute(self, context):
        debugALL()
        return {"FINISHED"}


class TM_OT_Settings_UpdateAddonResetSettings(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_resetaddonupdatesettings"
    bl_description = "Reset settings after update"
    bl_icon = 'MATERIAL'
    bl_label = "Reset settings after update"
        
    def execute(self, context):
        tm_props = getTmProps()
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
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}


class TM_OT_Settings_UpdateAddonOpenChangelog(Operator):
    bl_idname = "view3d.tm_updateaddonopenchangelog"
    bl_description = "fetch latest version from github, install, save and restart blender"
    bl_label = "Update addon"
    bl_options = {"REGISTER"}
        
    def execute(self, context):
        openHelp("changelog")
        return {"FINISHED"}


class TM_OT_Settings_UpdateAddonCheckForNewRelease(Operator):
    bl_idname = "view3d.tm_checkfornewaddonrelease"
    bl_description = "check if new addon release is available"
    bl_label = "check for new release"
    bl_options = {"REGISTER"}
        
    def execute(self, context):
        update_available = AddonUpdate.checkForNewRelease()
        if not update_available:
            makeReportPopup(
                "No update available", 
                [
                    f"your version: {AddonUpdate.addon_version}",
                    f"new version: {AddonUpdate.new_addon_version}",
                ])
        return {"FINISHED"}





class TM_PT_Settings(Panel):
    bl_label = "Settings"
    bl_idname = "TM_PT_Settings"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_options = set() # default is closed, open as default


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="SETTINGS")


    def draw(self, context):

        blender_version = bpy.app.version
        addon_version   = bl_info["version"]
        is_blender_3    = blender_version[0] >= 3
        layout          = self.layout
        tm_props        = getTmProps()
        

        box = layout.box()
        box.separator(factor=0)
        row = box.row(align=True)
        row.scale_y=.5
        row.alert = not is_blender_3
        row.label(text=f"Blender: {blender_version}", icon="BLENDER")
        row = box.row(align=True)
        row.label(text=f"""Addon: {addon_version}""", icon="FILE_SCRIPT")
        row.operator("view3d.tm_checkfornewaddonrelease", text="", icon="FILE_REFRESH")
        if not is_blender_3:
            row = box.row()
            row.alert = False
            row.label(text="Blender 3.0+ required!")

        update_available = tm_props.CB_addonUpdateAvailable

        if update_available:

            next_version = AddonUpdate.new_addon_version

            col = box.column(align=True)
            col.alert = BLENDER_INSTANCE_IS_DEV
            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = tm_props.CB_addonUpdateDLshow is False
            row.operator("view3d.tm_updateaddonrestartblender", text=f"Update to {next_version}", icon="FILE_REFRESH")
            row = col.row(align=True)
            row.operator("view3d.tm_updateaddonopenchangelog", text="Open changelog", icon="WORLD")
            dl_msg     = tm_props.ST_addonUpdateDLmsg
            show_panel = tm_props.CB_addonUpdateDLshow

            if show_panel:
                row = col.row(align=True)
                row.alert = "error" in dl_msg.lower()
                row.prop(tm_props, "NU_addonUpdateDLProgress", text=f"{dl_msg}" if dl_msg else "Download progress")


        row = box.row(align=True)
        row.operator("view3d.tm_opendoc",      text="Help",         )#icon="URL")
        row.operator("view3d.tm_opengithub",   text="Github",       )#icon="FILE_SCRIPT")
        row.operator("view3d.tm_debugall",     text="Debug",        )#icon="FILE_TEXT")


        row = layout.row()
        row.prop(tm_props, "ST_author")

        row = layout.row()
        row.enabled = True if not tm_props.CB_converting else False
        row.prop(tm_props, "LI_gameType", text="Game")

        box = layout.box()
        ini = "ST_nadeoIniFile_MP" if isGameTypeManiaPlanet() else "ST_nadeoIniFile_TM"
        row = box.row()
        row.prop(tm_props, ini, text="Ini file")
        row.alert=True

        row = box.row()
        row.operator("view3d.tm_autofindnadeoini", text="Try autofind Nadeo.ini", icon="VIEWZOOM")




        # layout.row().separator(factor=UI_SPACER_FACTOR)




        if not isSelectedNadeoIniFilepathValid():
            requireValidNadeoINI(self)
            return


        box = layout.box()
        if isSelectedNadeoIniFilepathValid():
            op_row = box.row()
            op_row.enabled = tm_props.CB_nadeoImporterDLRunning is False
            op_row.scale_y = 1.5
            if not tm_props.CB_nadeoImporterIsInstalled:
                row = box.row()
                row.alert = True
                row.label(text="NadeoImporter.exe not installed!")
                
                op_row.operator("view3d.tm_installnadeoimporter", text="Install NadeoImporter", icon="IMPORT")

            else:
                op_row.operator("view3d.tm_installnadeoimporter", text="Update NadeoImporter", icon="FILE_REFRESH")
                
            
            error     = tm_props.ST_nadeoImporterDLError
            show_panel = tm_props.CB_nadeoImporterDLshow

            if show_panel:
                row = box.row()
                row.alert = error != ""
                row.prop(tm_props, "NU_nadeoImporterDLProgress", text="ERROR: " + error if error != "" else "Download progress")
            

            

        # layout.separator(factor=UI_SPACER_FACTOR)






        envi         = tm_props.LI_DL_TextureEnvi #if isGameTypeManiaPlanet() else getTmProps().LI_gameType
        game         = getTmProps().LI_gameType
        dlTexRunning = tm_props.CB_DL_TexturesRunning is False

        box = layout.box()
        col = box.column(align=True)
        row = col.row()
        row.label(text="Game textures & assets library")

        row = col.row(align=True)
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgametextures", text=f"Install {envi} textures", icon="TEXTURE")

        if isGameTypeManiaPlanet():
            row = col.row(align=True)
            row.prop(tm_props, "LI_DL_TextureEnvi", text="Envi", icon="WORLD")
        
        row = col.row()
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgameassetslibrary", text=f"Install asset library", icon="ASSET_MANAGER")

        dlTexError          = tm_props.ST_DL_TexturesErrors
        statusText          = "Downloading..." if not dlTexRunning else "Done" if not dlTexError else dlTexError
        showDLProgressbar   = tm_props.CB_DL_TexturesShow

        if showDLProgressbar:
            row=box.row()
            row.enabled = False
            row.prop(tm_props, "NU_DL_Textures", text=statusText)

        layout.separator(factor=UI_SPACER_FACTOR)









def autoFindNadeoIni()->None:
    tm_props          = getTmProps()
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

    debug("Try to find Nadeo.ini in most used installation paths:")

    for path in paths:
        debug(path)
        if os.path.isfile(path):
            ini = path
            debug("Found!")
            break
            
    if ini == "": 
        ini="NOT FOUND, help?"
        debug("Nadeo.ini not found!")

    #change inifile
    if isGameTypeManiaPlanet():
        tm_props.ST_nadeoIniFile_MP = ini
    
    if isGameTypeTrackmania2020():
        tm_props.ST_nadeoIniFile_TM = ini



def updateAddon() -> None:
    """update the addon if a new version exist and restart blender to use new version"""    

    # TODO create check for new update on startup && dynamic version text in UI
    # if has_new_release:
    #     addon.doUpdate()
    
    AddonUpdate.doUpdate()





def openHelp(helptype: str) -> None:
    """open exporer or webbrowser by given helptype"""
    cmd = "" #+path
    
    if   helptype == "workitemsfolder": cmd += getDocPathWorkItems()
    elif helptype == "itemsfolder":     cmd += getDocPathItems()
    elif helptype == "assetfolder":     cmd += getDocPathItemsAssets()
    
    elif helptype == "documentation": webbrowser.open(URL_DOCUMENTATION)
    elif helptype == "github":        webbrowser.open(URL_GITHUB)
    elif helptype == "changelog":     webbrowser.open(URL_CHANGELOG)
    elif helptype == "checkregex":    webbrowser.open(URL_REGEX)
    elif helptype == "convertreport": subprocess.Popen(['start', fixSlash(PATH_CONVERT_REPORT)], shell=True)
    
        
    if cmd != "":
        cmd = f'explorer "{cmd}"'
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("\\\\", "\\")
        debug(cmd)
        subprocess.Popen(cmd, stdout=subprocess.PIPE)





