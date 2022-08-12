import bpy
from bpy.types import (
    Panel,
    Operator,
)
import webbrowser

from ..utils.Functions  import *
from ..utils.Constants  import * 

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


