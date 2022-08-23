from pydoc import text
import bpy
from bpy.types import Panel

from .PT_DownloadProgress import render_donwload_progress_bar
from ..utils.Functions      import *
from ..utils.Dotnet         import *
from ..utils.Constants      import *
from .. import bl_info


class TM_PT_Textures(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Textures"
    bl_idname = "TM_PT_Textures"
    # endregion
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_TEXTURE)

    def draw(self, context):

        layout = self.layout
        tm_props         = get_global_props()
        is_bmd_installed = is_blendermania_dotnet_installed()

        if not is_selected_nadeoini_file_existing():
            draw_nadeoini_required_message(self)
            return

        envi = tm_props.LI_DL_TextureEnvi

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Game textures & assets library")

        if is_game_maniaplanet():
            row = col.row(align=True)
            row.prop(tm_props, "LI_DL_TextureEnvi", text="Envi", icon=ICON_ENVIRONMENT)

        dlTexRunning = tm_props.CB_DL_ProgressRunning is False

        row = col.row(align=True)
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgametextures", text=f"Install {envi} textures", icon=ICON_TEXTURE)
        
        row = col.row()
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgameassetslibrary", text=f"Install asset library", icon=ICON_ASSETS)

        row = col.row()
        row.enabled = dlTexRunning and not is_bmd_installed
        row.scale_y = 1.5
        text = f"Install blendermania-dotnet"
        row.operator("view3d.tm_install_blendermania_dotnet", text=text, icon=ICON_UGLYPACKAGE)

        render_donwload_progress_bar(layout)

        layout.separator(factor=UI_SPACER_FACTOR)