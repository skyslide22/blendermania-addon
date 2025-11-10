import bpy
from bpy.types import Panel

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from .PT_DownloadProgress import render_donwload_progress_bar
from ..utils.Functions import is_selected_nadeoini_file_name_ok
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS, BLENDER_INSTANCE_IS_DEV
from ..operators.OT_NinjaRipper import *
from ..operators.OT_Imports import TM_OT_ImportItem

class TM_PT_Imports(Panel):
    bl_label = "Imports"
    bl_idname = "TM_PT_Imports"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="GHOST_DISABLED")

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Import Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure importing of RIP and GBX files",
            "-> NinjaRipper is a program to extract geometry of games",
            "----> v1.7.1 is free and ships with the addon",
            "----> v2.0.x is paid, website will open",
            "-> You can import GBX files too, experimental",
        )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.5

        if NINJA_RIPPER_17_ADDON_NAME in bpy.context.preferences.addons:
            row.operator(NINJA_RIPPER_17_ADDON_ID_NAME, text=f"Import Ninja Ripper 1.7.1 .rip files", icon=ICON_IMPORT)
        else:
            row.operator(TM_OT_Ninja17Install.bl_idname, text=f"Install Ninja Ripper 1.7.1 addon", icon=ICON_IMPORT)

        row = col.row(align=True)
        row.scale_y = 1.5

        if NINJA_RIPPER_18_ADDON_NAME in bpy.context.preferences.addons:
            row.operator(NINJA_RIPPER_18_ADDON_ID_NAME, text=f"Import Ninja Ripper 2.0.x .nr files", icon=ICON_IMPORT)
        else:
            row.operator(TM_OT_Ninja20Install.bl_idname, text=f"Install Ninja Ripper 2.0.x addon", icon=ICON_IMPORT)


        # col = box.column(align=True)
        # row = col.row()
        # row.scale_y = 0.8
        # row.label(text="Import trackmania Item.Gbx")


    
        # if not is_blendermania_dotnet_installed():
        #     row = col.row()
        #     row.alert = True
        #     row.label(text="Blendermania dotnet installation required")
            
        #     row = col.row()
        #     row.scale_y = 1.5
        #     text = f"Install blendermania-dotnet"
        #     row.operator("view3d.tm_install_blendermania_dotnet", text=text, icon=ICON_UGLYPACKAGE)

        #     render_donwload_progress_bar(layout)
        #     return
        # else:
        #     row = col.row()
        #     row.alert = True
        #     row.scale_y = 0.7
        #     row.label(text="Experimental feature, not all items can be imported")

        #     row = col.row(align=True)
        #     row.scale_y = 1.5
        #     row.operator(TM_OT_ImportItem.bl_idname, text=f"Import .Item.Gbx", icon=ICON_IMPORT)
