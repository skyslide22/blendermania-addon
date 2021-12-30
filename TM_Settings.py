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

class TM_OT_Settings_DebugALL(Operator):
    bl_idname = "view3d.tm_debugall"
    bl_description = "debug print all addon python variable values"
    bl_label = "Debug print"
        
    def execute(self, context):
        debugALL()
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
        layout = self.layout
        tm_props = getTmProps()
        
        box = layout.box()
        row = box.row()
        row.scale_y=.5
        row.label(text=f"""Addon: {addon_version}""", icon="FILE_SCRIPT")
        row = box.row()
        row.alert = not is_blender_3
        row.label(text=f"Blender: {blender_version}", icon="BLENDER")
        if not is_blender_3:
            row = box.row()
            row.alert = False
            row.label(text="Blender 3.0+ required!")


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

            if not tm_props.CB_nadeoImporterIsInstalled:
                row = box.row()
                row.alert = True
                row.label(text="NadeoImporter.exe not installed!")
                
                op_row.operator("view3d.tm_installnadeoimporter", text="Install NadeoImporter", icon="IMPORT")

            else:
                op_row.operator("view3d.tm_installnadeoimporter", text="Update NadeoImporter", icon="FILE_REFRESH")
                
            
            error     = tm_props.ST_nadeoImporterDLError
            showPanel = tm_props.CB_nadeoImporterDLshow

            if showPanel:
                row = box.row()
                row.enabled = False
                row.alert = error != ""
                row.prop(tm_props, "NU_nadeoImporterDLProgress", text="ERROR: " + error if error != "" else "Download progress")
            

            

        # layout.separator(factor=UI_SPACER_FACTOR)






        dlTexRunning = tm_props.CB_DL_TexturesRunning is False

        box = layout.box()
        row=box.row()
        row.label(text="Game textures for materials")

        col = box.column(align=True)
        col.enabled = dlTexRunning

        if isGameTypeManiaPlanet():
            col.row().prop(tm_props, "LI_DL_TextureEnvi", text="Envi", icon="WORLD")

        envi = tm_props.LI_DL_TextureEnvi if isGameTypeManiaPlanet() else "Stadium"

        row = box.row()
        # row.scale_y=1.5
        row.enabled = dlTexRunning
        row.operator("view3d.tm_installgametextures", text=f"Install {envi} textures", icon="TEXTURE")


        dlTexError          = tm_props.ST_DL_TexturesErrors
        statusText          = "Downloading..." if not dlTexRunning else "Done" if not dlTexError else dlTexError
        showDLProgressbar   = tm_props.CB_DL_TexturesShow

        if showDLProgressbar:
            row=box.row()
            row.enabled = False
            row.prop(tm_props, "NU_DL_Textures", text=statusText)

        layout.separator(factor=UI_SPACER_FACTOR)









def autoFindNadeoIni()->None:
    tm_props= getTmProps()
    game    = str(getTmProps().LI_gameType).lower()
    base    = fixSlash(PATH_PROGRAM_FILES_X86)
    mp_envis= ["TMStadium", "TMCanyon", "SMStorm", "TMValley", "TMLagoon"]
    alphabet= list(string.ascii_lowercase) #[a-z]
    paths   = []
    ini     = ""
    
    if isGameTypeManiaPlanet(): 
        paths.append(f"{base}/ManiaPlanet/Nadeo.ini".replace("/", "\\"))
    
        for char in alphabet:
            paths.append(fr"{char}:\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Games\ManiaPlanet\Nadeo.ini")
            paths.append(fr"{char}:\Spiele\ManiaPlanet\Nadeo.ini")

        for envi in mp_envis:
            paths.append(f"{base}/Steam/steamapps/common/ManiaPlanet_{envi}/Nadeo.ini".replace("/", "\\"))

    if isGameTypeTrackmania2020():
        paths.append(f"{base}/Ubisoft/Ubisoft Game Launcher/games/Trackmania/Nadeo.ini".replace("/", "\\"))
        paths.append(f"{base}/Epic Games/TrackmaniaNext/Nadeo.ini".replace("/", "\\"))
        paths.append(f"{PATH_PROGRAM_FILES_X86}/Trackmania/Nadeo.ini".replace("/", "\\"))
        for char in alphabet:
            paths.append(fr"{char}:\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Games\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Ubisoft\Ubisoft Game Launcher\games\Trackmania\Nadeo.ini")


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




def openHelp(helptype: str) -> None:
    """open exporer or webbrowser by given helptype"""
    cmd = "" #+path
    
    if   helptype == "workitemsfolder": cmd += getDocPathWorkItems()
    elif helptype == "itemsfolder":     cmd += getDocPathItems()
    elif helptype == "assetfolder":     cmd += getDocPathItemsAssets()
    
    elif helptype == "documentation": webbrowser.open(URL_DOCUMENTATION)
    elif helptype == "github":        webbrowser.open(URL_GITHUB)
    elif helptype == "checkregex":    webbrowser.open(URL_REGEX)
    elif helptype == "convertreport": subprocess.Popen(['start', fixSlash(PATH_CONVERT_REPORT)], shell=True)
    
        
    if cmd != "":
        cmd = f'explorer "{cmd}"'
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("\\\\", "\\")
        debug(cmd)
        subprocess.Popen(cmd, stdout=subprocess.PIPE)





