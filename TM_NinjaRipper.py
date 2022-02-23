import bpy
from bpy.types import (
    Panel,
    Operator,
)
import webbrowser

from .TM_Functions      import *


NINJA_RIPPER_17_ADDON_NAME = "ninjaripper-blender-import-main"
NINJA_RIPPER_17_ADDON_ID_NAME = "import_scene.rip"
NINJA_RIPPER_18_ADDON_NAME = "io_import_nr"
NINJA_RIPPER_18_ADDON_ID_NAME = "import_mesh.nr"

class TM_OT_Ninja17Install(Operator):
    bl_idname = "view3d.install_ninja_17_addon"
    bl_label = "Install ninja 1.7.1 addon"

    def execute(self, context):
        bpy.ops.preferences.addon_install(filepath = getAddonAssetsAddonsPath() + 'ninjaripper-blender-import-17.zip', overwrite = True)
        bpy.ops.preferences.addon_enable(module = NINJA_RIPPER_17_ADDON_NAME)
        return {'FINISHED'}



class TM_OT_Ninja20Install(Operator):
    bl_idname = "view3d.install_ninja_20_addon"
    bl_label = "Install ninja 2.0.X addon"

    def execute(self, context):
        webbrowser.open('https://www.ninjaripper.com/', new=2)
        return {'FINISHED'}



class TM_PT_NinjaImporter(Panel):
    bl_label = "RIP Importer"
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