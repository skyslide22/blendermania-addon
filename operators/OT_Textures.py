
import bpy
import re

from bpy.types import (Operator)

from ..utils.Functions      import *
from ..properties.Functions import *
from ..utils.Constants      import * 



class TM_OT_Textures_ToggleModwork(Operator):
    bl_idname = "view3d.tm_toggle_modwork"
    bl_description = "Toogle Modwork Folder Name (Enable/Disable)"
    bl_label = "Automatic find NadeoIni"
        
    def execute(self, context):
        toggle_modwork_folder()
        return {"FINISHED"}




def toggle_modwork_folder() -> None:
    return