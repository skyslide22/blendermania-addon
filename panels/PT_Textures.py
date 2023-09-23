from asyncore import poll
from pydoc import text
import bpy
from bpy.types import Panel

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..operators.OT_Textures import is_selected_modwork_enabled

from .PT_DownloadProgress import render_donwload_progress_bar
from ..utils.Functions      import *
from ..utils.Dotnet         import *
from ..utils.Constants      import *
from .. import bl_info


class TM_PT_Textures(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Textures"
    bl_idname = "TM_PT_Textures"
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_TEXTURE)

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Textures Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure the texture sources",
            "-> This is optional and can be kept empty (defaults will be used)",
            "-> Select a source folder to load all textures from",
            "----> You can also re-link all used textures, or reset to default"
            "----> Default textures are located in Items/_BlenderAssets/Textures/", 
            "",
            "Install & Update",
            "-> You can install the game textures from a CDN",
            "-> You can install pre defined materials which are part of an asset library",
            "",
            "ModWork Folder",
            "-> Is used for development only, located in /Skins/<ENVIRONMENT>/ModWork",
            "-> Acts like a custom mod, but will be forced over EVERY map in-game",
            "-> Updates textures in real time in-game, .. well, if the game is not crashing..",
            "-> Runs only locally on your machine",
            "-> Is not zipped, should have a child folder named Image with DDS textures inside",
            "-> Can be enabled or disabled here (rename = disable)",
            # "----> ", 
            # "----> ", 
            # "----> ", 

        )

    def draw(self, context):

        layout = self.layout
        tm_props = get_global_props()

        tex_source = tm_props.ST_TextureSource

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(tm_props, "ST_TextureSource", text="Source")
        row = col.row(align=True)
        col = row.column(align=True)
        col.operator("view3d.tm_reset_texture_source", text="Reset", icon=ICON_UPDATE)
        col = row.column(align=True)
        col.enabled = tex_source != ""
        col.operator("view3d.tm_update_texture_source", text="Update", icon=ICON_UPDATE)


class TM_PT_Textures_ModWork(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "ModWork Folder"
    bl_idname = "TM_PT_Textures_ModWork"
    bl_parent_id = "TM_PT_Textures"
    
    def draw(self, context):

        layout = self.layout
        tm_props = get_global_props()

        col = layout.column(align=True)

        modwork_enabled = is_selected_modwork_enabled()

        text = "Enable" if not modwork_enabled else "Disable"
        text = text + " modwork folder"

        row = col.row(align=True)
        row.label(text=text)

        row = col.row(align=True)
        scol = row.column(align=True)
        scol.operator("view3d.tm_toggle_modwork", text="ModWork", icon=ICON_TEXTURE, depress=modwork_enabled)
        scol = row.column(align=True)
        scol.operator("view3d.tm_open_folder",    text="", icon=ICON_FOLDER).folder = get_game_doc_path_skins_envi()

        if is_game_maniaplanet():
            scol = row.column(align=True)
            scol.scale_x = 0.8
            scol.prop(tm_props, "LI_DL_TextureEnvi", text="",)




class TM_PT_Textures_Install(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Install & Update"
    bl_idname = "TM_PT_Textures_Install"
    bl_parent_id = "TM_PT_Textures"
    
    def draw(self, context):

        layout  = self.layout
        tm_props= get_global_props()
        envi    = tm_props.LI_DL_TextureEnvi

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Game textures & assets library")

        dlTexRunning = tm_props.CB_DL_ProgressRunning is False

        row = col.row(align=True)
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgametextures", text=f"Install {envi} Textures", icon=ICON_TEXTURE)
        
        row = col.row()
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgameassetslibrary", text=f"Install Complete Asset Library", icon=ICON_ASSETS)

        render_donwload_progress_bar(layout)

        layout.separator(factor=UI_SPACER_FACTOR)