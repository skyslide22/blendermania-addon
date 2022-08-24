import bpy
from ..utils.Constants import MAP_OBJECT_ITEM, MAP_OBJECT_BLOCK
from ..utils.Functions import get_global_props, get_obj_potential_item_path

def on_update_map_obj_props(self, context):
    tm_props = get_global_props()
    obj = tm_props.PT_map_object.object_item
    if obj:
        if "tm_map_object_kind" in obj:
            tm_props.PT_map_object.object_type = obj["tm_map_object_kind"]
            tm_props.PT_map_object.object_path = obj["tm_map_object_path"]
        else:
            if tm_props.PT_map_object.object_type == MAP_OBJECT_BLOCK:
                tm_props.PT_map_object.object_path = ""
            else:
                tm_props.PT_map_object.object_path = get_obj_potential_item_path(obj)
    else:
        tm_props.PT_map_object.object_path = ""

def on_update_map_obj_kind(self, context):
    tm_props = get_global_props()
    tm_props.PT_map_object.object_path = ""

class MapObjectProperties(bpy.types.PropertyGroup):
    object_item: bpy.props.PointerProperty(type=bpy.types.Object, update=on_update_map_obj_props)
    object_type: bpy.props.EnumProperty(
        items=(
            (MAP_OBJECT_BLOCK, "Block", ""),
            (MAP_OBJECT_ITEM, "Item", ""),
        ),
        name="Use link to Item or Block",
        default=MAP_OBJECT_ITEM,
        update=on_update_map_obj_kind
    )
    object_path: bpy.props.StringProperty(name="Name/path of Item or Block", subtype="FILE_PATH")