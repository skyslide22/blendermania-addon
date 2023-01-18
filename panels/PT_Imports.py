import bpy
from bpy.types import Panel

from ..utils.Functions import is_selected_nadeoini_file_name_ok
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS, BLENDER_INSTANCE_IS_DEV
from ..operators.OT_NinjaRipper import *
from ..operators.OT_Imports import TM_OT_ImportItem

class TM_PT_Imports(Panel):
    bl_label = "Import RIP"
    bl_idname = "TM_PT_Imports"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="GHOST_DISABLED")

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

        col = box.column(align=True)
        row = col.row()
        row.scale_y = 0.8
        row.label(text="Trackmania:")
        row = col.row()
        row.alert = True
        row.scale_y = 0.7
        row.label(text="Only items with editable mesh supported at the moment")

        row = col.row(align=True)
        row.scale_y = 1.5
        row.operator(TM_OT_ImportItem.bl_idname, text=f"Import .Item.Gbx", icon=ICON_IMPORT)
