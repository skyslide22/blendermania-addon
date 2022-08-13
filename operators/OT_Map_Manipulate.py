from bpy.types import (Operator, Panel)

from ..utils.Models import ExportedItem

from ..utils.Dotnet         import *
from ..utils.Functions      import *
from ..utils.Constants      import * 
from ..operators.OT_Items_Export   import *


class OT_UIExportAndCreateMap(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map gbx"
    bl_label = "Save as map"
        
    def execute(self, context):
        if save_blend_file():
            export_and_place_on_map(get_global_props().ST_map_filepath)
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}


# External methods
def export_and_place_on_map(map_path: str):
    def callback(exported_items: list[ExportedItem]):
        dotnet_items = list[DotnetItem]()
        for item in exported_items:
            dotnet_items.append(item.to_dotnet_item())
        
        return run_place_objects_on_map(map_path, dotnet_items)

    exportAndOrConvert(callback)