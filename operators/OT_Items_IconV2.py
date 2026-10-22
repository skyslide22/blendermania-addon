import bpy
from bpy.types import (Operator)

from ..utils.ItemsIconV2 import generate_collection_icon
from ..utils.FunctionsV2 import *

class TM_OT_Items_Icon_TestV2(Operator):
    """generate test icon, no save"""
    bl_idname = "view3d.tm_make_test_icon_v2"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Open convert report"
        
    def execute(self, context):
        if bpy.context.object:
            item_collection = get_active_item_collection_of_selected_object()
            generate_collection_icon(item_collection)
        else:
            show_report_popup("Icon test failed", ["No object selected"], "ERROR")

        return {"FINISHED"}
