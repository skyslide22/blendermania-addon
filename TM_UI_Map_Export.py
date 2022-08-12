from bpy.types import (Operator)

from .TM_Dotnet         import *
from .TM_Functions      import *
from .TM_Items_Export   import *

class TMUIExportAndCreateMap(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map gbx"
    bl_label = "Save as map"
        
    def execute(self, context):
        if saveBlendFile():
            export_and_place_on_map("C:/Users/Vladimir/Documents/Trackmania/Maps/Debuger/TestMap.Map.Gbx")
        else:
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}


# External methods
def export_and_place_on_map(map_path: str):
    dotnet_items = list[DotnetItem]()
    exported_items = exportAndOrConvert()

    for item in exported_items:
        dotnet_items.append(item.to_dotnet_item())
    
    return run_place_objects_on_map(map_path, dotnet_items)