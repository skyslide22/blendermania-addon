from typing import List
import bpy
from .Functions import *



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
    col = get_selected_collection() or get_active_collection_of_selected_object()
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
    return getattr(col, "tm_collection_ignore", WAYPOINT_NAME_NONE) != WAYPOINT_NAME_NONE