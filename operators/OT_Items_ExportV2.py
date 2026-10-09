import bpy
from bpy.types import (Operator)

from ..utils.FunctionsV2 import *
from ..utils.ItemsExportV2 import *

class TM_OT_Items_ExportV2(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_v2"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    def execute(self, context):
        tm_props = get_global_props()

        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
        # elif not tm_props.ST_author:
            # show_report_popup("Author name is empty!", ["Please fill in your name in the author input field", "You can find it in the settings panel of blendermania."], "ERROR")
        else:
            # export_and_convert()

            export_and_convert()
        return {"FINISHED"}


class TM_OT_Items_Export_ExportAndOrConverFailedOnesV2(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_failed_ones_v2"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert the collection which failed in the last approach"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    def execute(self, context):
        tm_props = get_global_props()

        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
        else:
            export_and_convert(only_failed_ones=True)

        return {"FINISHED"}




# def close_convert_panel():
#     tm_props                              = get_global_props()
#     tm_props.CB_converting                = False
#     tm_props.CB_showConvertPanel          = False
#     tm_props.CB_stopAllNextConverts       = False
#     tm_props.CB_uv_genBaseMaterialCubeMap = False # for stupid mistakes ... :)
#     debug("CB_showConvertPanel = " + str(tm_props.CB_showConvertPanel))




