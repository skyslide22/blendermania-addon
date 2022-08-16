import bpy

from ..utils.BlenderObjects import duplicate_object_to

from ..utils.Functions import is_game_trackmania2020
from ..utils.Constants import SPECIAL_NAME_SUFFIX_LOD1
from ..utils.Dotnet import DotnetItem, DotnetVector3, run_place_objects_on_map
from ..utils.Functions import get_global_props, save_blend_file, show_report_popup, set_active_object

class OT_UICollectionToMap(bpy.types.Operator):
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

class OT_UIValidateMapCollection(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_validate_map_coll"
    bl_description = "Validate map collection"
    bl_label = "Validate map collection"
        
    def execute(self, context):
        # TODO
        return {"FINISHED"}

class OT_UICreateUpdateMapItemBlock(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_create_update_map_item_block"
    bl_description = "Create|Update Item|Block"
    bl_label = "Mark or update map item|block"
        
    def execute(self, context):
        err = _create_update_map_object()
        if err:
            show_report_popup("Something wrong!", [err], "ERROR")
        else:
            get_global_props().PT_map_object.object_item = None
            get_global_props().PT_map_object.object_path = ""

        return {"FINISHED"}

def _create_update_map_object():
    tm_props    = get_global_props()
    map_coll    = tm_props.PT_map_collection
    object_item = tm_props.PT_map_object.object_item
    object_type = tm_props.PT_map_object.object_type
    object_path = tm_props.PT_map_object.object_path
    
    if not map_coll:
        return "No map collection selected"

    obj_to_update:bpy.types.Object = None

    # update object if it's already map_object
    if object_item and "tm_map_object_kind" in object_item:
        obj_to_update = object_item
    else:
        if not object_item:
            bpy.ops.mesh.primitive_cube_add(size=32, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            obj_to_update = bpy.context.active_object
        else:
            obj_to_update = duplicate_object_to(object_item, map_coll)
            prefix = "TM" if is_game_trackmania2020() else "MP"
            obj_to_update.name = f"{prefix}_{object_type.upper()}: {object_path}"
    

    obj_to_update["tm_map_object_kind"] = object_type
    obj_to_update["tm_map_object_path"] = object_path

    set_active_object(obj_to_update)
    

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