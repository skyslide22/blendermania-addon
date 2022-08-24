from asyncore import poll
from pydoc import text
import bpy
from bpy.types import Panel

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

    def draw(self, context):

        layout = self.layout
        tm_props = get_global_props()

        col = layout.column(align=True)

        row = col.row(align=True)
        scol = row.column(align=True)
        scol.operator("view3d.tm_toggle_modwork", text="Toggle Modwork (WIP)")

        if is_game_maniaplanet():
            scol = row.column(align=True)
            scol.scale_x = 0.8
            scol.prop(tm_props, "LI_DL_TextureEnvi", text="",)

        box = layout.box()
        box.scale_y = 0.7
        box.alert = True
        box.label(text="modwork wip")
        box.label(text="choose between /asset/textures and /modwork")
        box.label(text="for texture source, restart blender to apply button")



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