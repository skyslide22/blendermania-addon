import bpy
from ..utils.Constants import MAP_OBJECT_ITEM
from ..utils.Functions import get_global_props

def on_update_map_obj_props(self, context):
    tm_props = get_global_props()
    if tm_props.PT_map_object.object_item:
        tm_props.PT_map_object.object_path = tm_props.PT_map_object.object_item.name

class ExportedItem: 
    name:         str = ""
    r_path:       str = "" # relative path in Items/ folder or Work/Items w/o extension
    item_path:    str = ""
    icon_path:    str = ""
    fbx_path:     str = ""
    coll:         bpy.types.Collection = None
    scale:        int = 1
    physic_hack:  True

    def __init__(self, coll: bpy.types.Collection):
        self.coll = coll

class MapObjectProperties(bpy.types.PropertyGroup):
    object_item: bpy.props.PointerProperty(type=bpy.types.Object, update=on_update_map_obj_props)
    object_type: bpy.props.EnumProperty(
        items=(
            #(MAP_OBJECT_BLOCK, "Block", ""), GBX.NET can't place free blocks yet, come back to it later
            (MAP_OBJECT_ITEM, "Item", ""),
        ),
        name="Use link to Item (soon Block)",
        default=MAP_OBJECT_ITEM,
    )
    object_path: bpy.props.StringProperty(name="Name/path of Item")