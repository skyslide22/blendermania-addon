import bpy
from bpy.props import * 
from bpy.types import PropertyGroup

class ExportedItem: 
    name:                   str  = ""
    name_raw:               str  = ""
    r_path:                 str  = "" # relative path in Items/ folder or Work/Items w/o extension
    item_path:              str  = ""
    icon_path:              str  = ""
    fbx_path:               str  = ""
    objects:                list[bpy.types.Object] = None
    color_tag:              str  = ""
    tm_itemxml_template:    str  = ""
    scale:                  int  = 1
    force_scale:            bool = False
    physic_hack:            bool = True
    mesh_xml:               str  = "Not generated!"
    item_xml:               str  = "Not generated!"
    game_is_trackmania2020: bool = False
    game_is_maniaplanet:    bool = False
    game:                   str  = ""
    is_single_item:         bool = False


# bpy.types does not work for CollectionProperty(type=X)
# so create a class which contains a bpy.types object ... eh

class FailedConvertObject(PropertyGroup):
    object: PointerProperty(type=bpy.types.Object)

class FailedConvertCollection(PropertyGroup):
    collection: PointerProperty(type=bpy.types.Collection)

class FailedConverts(PropertyGroup):
    objects:        CollectionProperty(type=FailedConvertObject)
    # collections:    CollectionProperty(type=FailedConvertCollection)