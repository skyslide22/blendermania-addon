from bpy.types import Operator
from ..utils.Dotnet import DotnetItem, DotnetVector3, run_place_objects_on_map
from ..utils.Functions import get_global_props, save_blend_file, show_report_popup

class OT_UICollectionToMap(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map"
    bl_label = "Export collection to the map"
        
    def execute(self, context):
        if save_blend_file():
            place_objects_on_map(get_global_props().ST_map_filepath)
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}

class OT_UIValidateMapCollection(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_validate_mao_coll"
    bl_description = "Validate map collection"
    bl_label = "Validate map collection"
        
    def execute(self, context):
        # TODO
        return {"FINISHED"}


# External methods
def place_objects_on_map(map_path: str):
    dotnet_items = list[DotnetItem]((
        DotnetItem(
            Name="Items/BumpRoad.Item.Gbx",
            Path="C:/Users/Vladimir/Documents/Trackmania/Items/BumpRoad.Ite1m.Gbx",
            Position=DotnetVector3(),
            Rotation=DotnetVector3(),
            Pivot=DotnetVector3(),
        ), DotnetItem(
            Name="Items/BumpRoad.Item.Gbx",
            Path="C:/Users/Vladimir/Documents/Trackmania/Items/BumpRoad.Item.Gbx",
            Position=DotnetVector3(32, 32, 0),
            Rotation=DotnetVector3(),
            Pivot=DotnetVector3(),
        )
    ))
        
    res = run_place_objects_on_map(map_path, [], dotnet_items)
    print(res)