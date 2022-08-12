import bpy
from bpy.types import (
    Panel,
    Operator,
)
import webbrowser

from ..utils.Functions  import *
from ..utils.Constants  import * 
from ..operators.OT_NinjaRipper import *

class TM_PT_NinjaImporter(Panel):
    bl_label = "Import RIP"
    bl_idname = "TM_PT_NinjaImporter"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_options = set() # default is closed, open as default

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
            row.operator(NINJA_RIPPER_17_ADDON_ID_NAME, text=f"Import Ninja Ripper 1.7.1 .rip files", icon="IMPORT")
        else:
            row.operator(TM_OT_Ninja17Install.bl_idname, text=f"Install Ninja Ripper 1.7.1 addon", icon="IMPORT")

        row = col.row(align=True)
        row.scale_y = 1.5

        if NINJA_RIPPER_18_ADDON_NAME in bpy.context.preferences.addons:
            row.operator(NINJA_RIPPER_18_ADDON_ID_NAME, text=f"Import Ninja Ripper 2.0.x .nr files", icon="IMPORT")
        else:
            row.operator(TM_OT_Ninja20Install.bl_idname, text=f"Install Ninja Ripper 2.0.x addon", icon="IMPORT")