from typing import List
import bpy
from .Functions import *
from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp
from ..properties.PropertyFunctions import get_lod_indexes


def get_parent_collection(col, scene):
    for c in scene.collection.children_recursive:
        if col.name in c.children:
            return c
    return None  # directly under the scene root

def get_item_root(col, scene):
    while is_group_collection(col):
        parent = get_parent_collection(col, scene)
        if parent is None:   # sub-collection with no parent -> nothing to export
            return None
        col = parent
    return col



# collection regardless of type

def get_active_collection() -> bpy.types.Collection:
    col = get_active_collection_of_selected_object() or get_selected_collection()
    return col

def get_active_collection_of_selected_object() -> bpy.types.Collection:
    objs = bpy.context.selected_objects
    col  = None
    if objs:
        obj = objs[0]
        col = obj.users_collection[0]
    return col
    



def get_selected_collection() -> bpy.types.Collection:
    col = bpy.context.collection
    return col

def get_item_collections_v2(objs: List[bpy.types.Object])->set:
    scene = bpy.context.scene
    collections = set()

    for obj in objs:

        if obj.type != "MESH":
            continue

        if obj.visible_get() is False: 
            continue

        # filter special objects, allow only real "mesh" objects, not helpers (_xyz_)
        if not is_real_object_by_name(obj.name):
            continue

        for col in obj.users_collection:
            root = get_item_root(col, scene)
            if root.name.lower() in NOT_ALLOWED_COLLECTION_NAMES: continue
            if root in collections: continue
            if is_collection_excluded_or_hidden(root): continue

            collections.add(root)
    
    return collections



# item collection (root/export)

def get_active_item_collection() -> bpy.types.Collection:
    col = get_item_root(get_active_collection(), bpy.context.scene)
    return col

def set_waypointtype_of_active_collection() -> None:
    col      = get_active_item_collection()
    waypoint = get_global_props().LI_xml_waypointtype
    
    col.color_tag = WAYPOINTS[waypoint]

def get_active_item_collection_of_selected_object() -> bpy.types.Collection:
    objs = bpy.context.selected_objects
    col  = None
    if objs:
        obj = objs[0]
        col = obj.users_collection[0]
    if col:
        col = get_item_root(col, bpy.context.scene)
    return col

# group collection (moving)

def is_group_collection(col: bpy.types.Collection) -> bool:
    return col.tm_moving_group == True

def get_active_group_collection() -> bpy.types.Collection:
    col = get_active_collection()
    if is_group_collection(col):
        return col
    return None

def can_convert_to_group_collection(col: bpy.types.Collection) -> bool:
    if col is None: return False
    if is_group_collection(col): return False
    if col.children: return False 
    return True

# waypoint
def is_waypoint_collection(col: bpy.types.Collection) -> bool:
    return getattr(col, CollectionProp.IGNORE, WAYPOINT_NAME_NONE) != WAYPOINT_NAME_NONE

# export

def is_collection_exportable(coll: bpy.types.Collection)->bool:
    if len(coll.objects) == 0\
    or coll.name.lower() in NOT_ALLOWED_COLLECTION_NAMES:
        return False

    if getattr(coll, CollectionProp.IGNORE, False):
        return False
    if getattr(coll, CollectionProp.MOVING_GROUP, False):
        return False

    is_exportable = False
    for obj in coll.objects:
        is_exportable = is_object_exportable(obj)
        if is_exportable: break
    
    return is_exportable


def is_object_exportable(obj: bpy.types.Object)-> bool:
    if (obj.type != EXPORTABLE_OBJECT_MESH and obj.type != EXPORTABLE_OBJECT_LIGHT) \
    or obj.visible_get() is False:
        return False

    if getattr(obj, ObjectProp.IGNORE, False):
        return False
    if getattr(obj.users_collection[0], CollectionProp.IGNORE, False):
        return False
    return True

def get_exportable_collections(objs: List[bpy.types.Object])->set:
    collections = set()

    for obj in objs:

        if obj.type != EXPORTABLE_OBJECT_MESH:
            continue

        if obj.visible_get() is False: 
            continue

        #TODO: actual filter necessary
        if not is_object_exportable(obj):
            continue

        for col in obj.users_collection:
            root = get_item_root(col, bpy.context.scene)
            if root.name.lower() in NOT_ALLOWED_COLLECTION_NAMES: continue
            if getattr(root, CollectionProp.IGNORE, False): continue
            if root in collections: continue
            if is_collection_excluded_or_hidden(root): continue

            collections.add(root)
    
    return collections

def get_exportable_collection_objects(objs: List[bpy.types.Object])->set:
    objects = set()
    for obj in objs:
        if not is_object_exportable(obj):
            continue
        if not has_valid_LODs(obj):
            show_report_popup("Invalid object", (f"<{obj.name}> has LODs enabled, but no declared LOD levels... skipping!",))
            continue
        objects.add(obj)
    return objects

def has_valid_LODs(obj: bpy.types.Object) -> bool:
    if not getattr(obj, ObjectProp.ENABLE_LODS, False):
        return True
    lods = get_lod_indexes(obj)
    if len(lods) == 0: return False
    return True

def get_offset_from_item_origin(objects: list[bpy.types.Object]) -> list[float]:
    location: list[float] = [0,0,0]
    offset: list[float] = []
    
    # take first valid object and main one
    for obj in objects:
        if is_object_exportable(obj)\
        and (len(offset) == 0 or getattr(obj, ObjectProp.ORIGIN, False)):
            offset = [
                obj.location[0] - location[0],
                obj.location[1] - location[1],
                obj.location[2] - location[2],
            ]
            
    return offset