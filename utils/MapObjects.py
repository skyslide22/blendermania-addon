import bpy
import math

from ..utils.Dotnet import (
    DotnetInt3,
    DotnetItem,
    DotnetBlock,
    DotnetVector3,
    run_place_objects_on_map,
    get_block_dir_for_angle,
)
from ..utils.BlenderObjects import duplicate_object_to
from ..utils.Functions import (
    is_file_exist,
    get_global_props,
    set_active_object,
    get_game_doc_path_items,
    is_game_trackmania2020,
)
from ..utils.Constants import (
    MAP_OBJECT_ITEM,
    MAP_OBJECT_BLOCK,
)

def create_update_map_object():
    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    object_item:bpy.types.Object     = tm_props.PT_map_object.object_item
    object_type:str                  = tm_props.PT_map_object.object_type
    object_path:str                  = tm_props.PT_map_object.object_path
    items_path                       = get_game_doc_path_items()
    
    if not map_coll:
        return "No map collection selected"

    obj_to_update:bpy.types.Object = None

    if items_path in object_path:
        if not is_file_exist(object_path):
            return f"There is no item with path {object_path}. You have to export it first"

    if len(object_path) == 0:
        return f"Name/Path can not be empty"

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
    short_name = object_path.replace(items_path, "")
    obj_to_update.name = f"{prefix}_{object_type.upper()}: {short_name}"

    obj_to_update["tm_map_object_kind"] = object_type
    obj_to_update["tm_map_object_path"] = object_path

    set_active_object(obj_to_update)

def validate_map_collection() -> str:
    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    items_path                       = get_game_doc_path_items()
    
    if not map_coll:
        return "No map collection!"

    for obj in map_coll.all_objects:
        obj:bpy.types.Object = obj

        if "tm_map_object_kind" not in obj or "tm_map_object_path" not in obj:
            return f"Map collection contains invalid object: {obj.name}"

        if obj["tm_map_object_kind"] == MAP_OBJECT_BLOCK:
            if min(obj.location) < 0:
                return f"Block position can not be negative! Object: {obj.name}"
            
            if (
                round(obj.location[0]) % 32 != 0 or
                round(obj.location[1]) % 32 != 0 or
                round(obj.location[2]) % 32 != 0
            ):
                return f"Block origin position must be multiple of 32! Object: {obj.name}"

            if obj.rotation_euler[0] != 0 or obj.rotation_euler[1] != 0:
                return f"Only rotation on Z axis supported! Object: {obj.name}"
            
            if (round(math.degrees(obj.rotation_euler[2]))) % 90 != 0:
                return f"Rotation on Z must be multiple of 90deg! Object: {obj.name}"
        
        if obj["tm_map_object_kind"] == MAP_OBJECT_ITEM:
            if items_path in obj["tm_map_object_path"] and not is_file_exist(obj["tm_map_object_path"]):
                return f"Item with path: {obj['tm_map_object_path']} does not exist. Object name: {obj.name}"

def export_map_collection() -> str:
    err = validate_map_collection()
    if err: return err

    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    items_path                       = get_game_doc_path_items()
    dotnet_items                     = list[DotnetItem]()
    dotnet_blocks                    = list[DotnetBlock]()

    for obj in map_coll.all_objects:
        obj:bpy.types.Object = obj

        if obj["tm_map_object_kind"] == MAP_OBJECT_ITEM:
            name = obj["tm_map_object_path"]
            if items_path in name:
                name = "Items/"+name.replace(items_path, "")
            else:
                name = name.replace(".Item", "").replace(".Gbx", "")

            dotnet_items.append(DotnetItem(
                Name=name,
                Path=obj["tm_map_object_path"] if items_path in name else "",
                Position=DotnetVector3(obj.location[1], obj.location[2]+8, obj.location[0]),
                Rotation=DotnetVector3(obj.rotation_euler[2], obj.rotation_euler[1], obj.rotation_euler[0]),
                Pivot=DotnetVector3(0),
            ))
        elif obj["tm_map_object_kind"] == MAP_OBJECT_BLOCK:
            dotnet_blocks.append(DotnetBlock(
                Name=obj["tm_map_object_path"],
            Direction=get_block_dir_for_angle(math.degrees(obj.rotation_euler[2])),
                Position=DotnetInt3(int(int(obj.location[1])/32), int(int(obj.location[2])/32)+9, int(int(obj.location[0])/32)),
            ))

    return run_place_objects_on_map(get_global_props().ST_map_filepath, dotnet_blocks, dotnet_items)