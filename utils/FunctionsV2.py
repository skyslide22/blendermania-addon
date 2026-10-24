from typing import List
import bpy

from .Functions import *
import json
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

def get_exportable_collections(objs, stop_after: int | None = None) -> set:
    scene     = bpy.context.scene
    accepted  = set()
    rejected  = set()   # roots rejected for collection-level reasons
    root_of   = {}      # col -> root, so get_item_root runs once per collection

    for obj in objs:

        # collection-level checks first, cached
        candidates = []
        for col in obj.users_collection:
            root = root_of.get(col)
            if root is None:
                root = root_of[col] = get_item_root(col, scene)

            if root in accepted or root in rejected:
                continue

            if (root.name.lower() in NOT_ALLOWED_COLLECTION_NAMES
                    or getattr(root, CollectionProp.IGNORE, False)
                    or is_collection_excluded_or_hidden(root)):
                rejected.add(root)
                continue

            candidates.append(root)

        # object-level checks only if they could change the result
        if not candidates:
            continue
        if not obj.visible_get() or not is_object_exportable(obj):
            continue

        accepted.update(candidates)

        if stop_after and len(accepted) >= stop_after:
            break

    return accepted

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

# def get_offset_from_item_origin(objects: list[bpy.types.Object]) -> list[float]:
#     location: list[float] = [0,0,0]
#     offset: list[float] = []
    
#     # take first valid object and main one
#     for obj in objects:
#         if is_object_exportable(obj)\
#         and (len(offset) == 0 or getattr(obj, ObjectProp.ORIGIN, False)):
#             offset = [
#                 obj.location[0] - location[0],
#                 obj.location[1] - location[1],
#                 obj.location[2] - location[2],
#             ]
            
#     return offset


def get_offset_from_item_origin(objects: list[bpy.types.Object]) -> list[float]:
    location: list[float] = [0,0,0]
    offset: list[float] = []

    origin = next(
        (obj for obj in objects
         if obj.type in {"MESH", "EMPTY"} and getattr(obj, ObjectProp.ORIGIN, False)),
        None,
    )
    # fallback: first mesh only
    fallback = next((obj for obj in objects if obj.type == "MESH"), None)

    main = origin or fallback

    if main is not None:
        offset = [
            main.location[0] - location[0],
            main.location[1] - location[1],
            main.location[2] - location[2],
        ]
    
            
    return offset


def is_obj_visible(obj: bpy.types.Object) -> bool:
    """check if the object is not a interpreted as special"""
    return getattr(obj, ObjectProp.IGNORE, False) is False \
        and getattr(obj, ObjectProp.INVISIBLE, False) is False \
        



# other
def copy_props(src, dst):
    for p in src.bl_rna.properties:
        name = p.identifier
        if name == "rna_type":
            continue
        value = getattr(src, name)
        if p.type == 'POINTER' and isinstance(value, bpy.types.PropertyGroup):
            copy_props(value, getattr(dst, name))
        elif p.type == 'COLLECTION':
            dst_coll = getattr(dst, name)
            dst_coll.clear()
            for item in value:
                copy_props(item, dst_coll.add())
        elif not p.is_readonly:
            setattr(dst, name, value)

def props_to_dict(group):
    out = {}
    for prop in group.bl_rna.properties:
        pid = prop.identifier
        if pid == "rna_type":
            continue
        val = getattr(group, pid)
        if prop.type == 'POINTER':
            val = props_to_dict(val) if val is not None else None
        elif prop.type == 'COLLECTION':
            val = [props_to_dict(item) for item in val]
        elif prop.type == 'ENUM' and prop.is_enum_flag:
            val = list(val)
        elif getattr(prop, "array_length", 0):
            val = list(val)
        out[pid] = val
    return out

def props_from_dict(group, d):
    for pid, val in d.items():
        prop = group.bl_rna.properties.get(pid)
        if prop is None or prop.is_readonly and prop.type not in {'POINTER', 'COLLECTION'}:
            continue
        try:
            if prop.type == 'POINTER':
                if val is not None:
                    props_from_dict(getattr(group, pid), val)
            elif prop.type == 'COLLECTION':
                coll = getattr(group, pid)
                coll.clear()
                for item_d in val:
                    props_from_dict(coll.add(), item_d)
            elif prop.type == 'ENUM' and prop.is_enum_flag:
                setattr(group, pid, set(val))
            else:
                setattr(group, pid, val)
        except (TypeError, ValueError) as e:
            print(f"Could not set {pid}: {e}")


def get_addon_templates_path() -> str:
    return get_addon_assets_path() + "templates/"


def is_editor_object_mode() -> bool:
    return bpy.context.mode == 'OBJECT'
