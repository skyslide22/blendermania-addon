import bpy
from bpy.types import (Operator)

from ..utils.ItemsIcon import generate_collection_icon
from ..utils.Functions import *

class TM_OT_Items_Icon_Test(Operator):
    """generate test icon, no save"""
    bl_idname = "view3d.tm_make_test_icon"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Open convert report"
        
    def execute(self, context):
        if bpy.context.object:
            generate_collection_icon(bpy.context.object.users_collection[0])
        else:
            show_report_popup("Icon test failed", ["No object selected"], "ERROR")

        return {"FINISHED"}
