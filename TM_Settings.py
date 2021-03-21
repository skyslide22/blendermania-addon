import bpy
import os.path
import string
from pprint import pprint
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from .TM_Functions      import *
from .TM_Items_Convert  import *




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




class TM_PT_Settings(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label = "Settings"
    bl_idname = "TM_PT_Settings"
    locals().update( panelClassDefaultProps )

    # endregion
    def draw(self, context):

        layout = self.layout
        tm_props = context.scene.tm_props

        row = layout.row()
        row.prop(tm_props, "ST_author")

        row = layout.row()
        row.enabled = True if not tm_props.CB_converting else False
        row.prop(tm_props, "LI_gameType", text="Game")

        ini = "ST_nadeoIniFile_MP" if isGameTypeManiaPlanet() else "ST_nadeoIniFile_TM"
        row = layout.row()
        row.prop(tm_props, ini, text="Ini file")
        row.alert=True

        row = layout.row()
        row.operator("view3d.tm_autofindnadeoini", text="Try autofind Nadeo.ini", icon="VIEWZOOM")


        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("view3d.tm_opendoc",      text="Help",         icon="URL")
        row.operator("view3d.tm_opengithub",   text="Github/Bug",   icon="FILE_SCRIPT")

        layout.row().separator(factor=spacerFac)

        if not isNadeoIniValid():
            row = layout.row()
            row.alert = True
            row.label(text=errorMsg_NADEOINI)
            return

        if isNadeoIniValid():
            if not tm_props.CB_nadeoImporter:
                row = layout.row()
                row.alert = True
                row.label(text="NadeoImporter.exe not installed!")
                
                row = layout.row()
                row.operator("view3d.tm_installnadeoimporter", text="Install NadeoImporter.exe", icon="IMPORT")

            else:
                row = layout.row()
                row.operator("view3d.tm_installnadeoimporter", text="Update NadeoImporter.exe", icon="FILE_REFRESH")
                
            error = tm_props.ST_nadeoImporterDLError
            
            row = layout.row()
            row.enabled = False
            row.alert = error != ""
            row.prop(tm_props, "NU_nadeoImporterDL", text="ERROR: " + error if error != "" else "Download progress")
            

            

        layout.separator(factor=spacerFac)






        dlTexRunning = tm_props.CB_DL_TexturesRunning == False

        row=layout.row()
        row.label(text="Download textures for uvmapping", icon="TEXTURE")

        col = layout.column(align=True)
        col.enabled = dlTexRunning

        if isGameTypeManiaPlanet():
            col.row().prop(tm_props, "LI_DL_TextureEnvi", text="Envi")

        envi = tm_props.LI_DL_TextureEnvi if isGameTypeManiaPlanet() else "Stadium"

        row = col.row()
        row.scale_y=1.5
        row.enabled = dlTexRunning
        row.operator("view3d.tm_installgametextures", text=f"Install {envi}Textures.zip")


        dlTexError = tm_props.ST_DL_TexturesErrors
        statusText = "Downloading..." if not dlTexRunning else "Done" if not dlTexError else dlTexError
        row=layout.row()
        row.enabled = False
        row.prop(tm_props, "NU_DL_Textures", text=statusText)









def autoFindNadeoIni()->None:
    game    = str(bpy.context.scene.tm_props.LI_gameType).lower()
    base    = os.environ["ProgramFiles(x86)"]
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
        for char in alphabet:
            paths.append(fr"{char}:\Trackmania\Nadeo.ini")
            paths.append(fr"{char}:\Games\Trackmania\Nadeo.ini")


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
        bpy.context.scene.tm_props.ST_nadeoIniFile_MP = ini
    
    if isGameTypeTrackmania2020():
        bpy.context.scene.tm_props.ST_nadeoIniFile_TM = ini




def openHelp(helptype: str) -> None:
    """open exporer or webbrowser by given helptype"""
    cmd = "" #+path
    
    if   helptype == "workitemsfolder": cmd += getDocPathWorkItems()
    elif helptype == "itemsfolder":     cmd += getDocPathItems()
    elif helptype == "assetfolder":     cmd += getDocPathItemsAssets()
    
    elif helptype == "documentation": webbrowser.open(website_documentation)
    elif helptype == "github":        webbrowser.open(website_github)
    elif helptype == "checkregex":    webbrowser.open(website_regex)
    elif helptype == "convertreport": subprocess.Popen(['start', fixSlash(website_convertreport)], shell=True)
    
        
    if cmd != "":
        cmd = f'explorer "{cmd}"'
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("\\\\", "\\")
        debug(cmd)
        subprocess.Popen(cmd, stdout=subprocess.PIPE)





