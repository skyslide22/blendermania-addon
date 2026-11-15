from typing import List
import bpy

from .Functions import *
import json
from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp
from ..properties.PropertyFunctions import get_lod_indexes
from .CollectionTypes import get_collection_type_def, get_collection_type_id, get_type_def, is_collection_of_type


def get_parent_collection(col, scene):
    for c in scene.collection.children_recursive:
        if col.name in c.children:
            return c
    # collections only used as instance source are not linked into the scene
    for c in bpy.data.collections:
        if col.name in c.children:
            return c
    return None  # directly under the scene root

# collections explicitly chosen for export: they (and their ancestors) override "ignore"
# mutated in place only, because other modules star-import this name
EXPLICIT_EXPORT_COLLECTIONS: set[str] = set()

def is_collection_ignored(col: bpy.types.Collection) -> bool:
    """ignore flag of this collection only (explicitly chosen collections are never ignored)"""
    return bool(getattr(col, CollectionProp.IGNORE, False)) and col.name not in EXPLICIT_EXPORT_COLLECTIONS

def is_collection_hierarchy_ignored(col: bpy.types.Collection) -> bool:
    """collection or any ancestor ignored; an explicitly chosen collection stops the check"""
    scene = bpy.context.scene
    while col is not None:
        if col.name in EXPLICIT_EXPORT_COLLECTIONS:
            return False
        if getattr(col, CollectionProp.IGNORE, False):
            return True
        col = get_parent_collection(col, scene)
    return False

def get_item_root(col, scene):
    while is_group_collection(col):
        parent = get_parent_collection(col, scene)
        if parent is None:   # sub-collection with no parent -> nothing to export
            return None
        col = parent
    return col


def fresh_world_matrix(obj: bpy.types.Object):
    """world matrix built from the current location/rotation/scale of the object and its parents (matrix_world can be stale)"""
    matrix = obj.matrix_basis.copy()
    if obj.parent is not None:
        matrix = fresh_world_matrix(obj.parent) @ obj.matrix_parent_inverse @ matrix
    return matrix


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
    if col is None: return
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

def get_item_collections_from_selected(context=None) -> list[bpy.types.Collection]:
    context = context or bpy.context
    scene = context.scene
    scene_root = scene.collection

    # 1) Outliner context: explicit collection selection wins
    ids = getattr(context, "selected_ids", None) or []
    cols = [i for i in ids if isinstance(i, bpy.types.Collection) and i != scene_root]
    if cols:
        return cols

    # 2) Objects selected: derive the item collections from them.
    #    Active object first, so the panel's target is stable.
    objs = list(context.selected_objects)
    active = context.view_layer.objects.active
    if active is not None and active.select_get():
        objs = [active] + [o for o in objs if o != active]

    result = []
    for obj in objs:
        root = get_item_root(obj.users_collection[0], scene)
        if root and root not in result:
            result.append(root)
    if result:
        return result

    # 3) Nothing selected: fall back to the active collection
    layer_col = context.view_layer.active_layer_collection
    if layer_col is not None and layer_col.collection != scene_root:
        return [layer_col.collection]
    return []

def get_item_collections_in_hierarchy(col: bpy.types.Collection) -> list[bpy.types.Collection]:
    """all item collections below this collection, including itself if it is an item"""
    scene = bpy.context.scene
    items: list[bpy.types.Collection] = []
    seen: set[str] = set()

    def walk(col):
        if col.name in seen:
            return
        seen.add(col.name)
        if not is_group_collection(col):
            items.append(col)
        for child in col.children:
            walk(child)

    walk(col)
    return items

# group collections (moving group / container / attachments / variant), the types themselves are defined in CollectionTypes.py

def is_moving_group_collection(col: bpy.types.Collection) -> bool:
    return is_collection_of_type(col, COLLECTION_GROUP_MOVING)

def is_container_collection(col: bpy.types.Collection) -> bool:
    return is_collection_of_type(col, COLLECTION_GROUP_CONTAINER)

def is_variant_collection(col: bpy.types.Collection) -> bool:
    """collection of type Variant (one variant of an item)"""
    return is_collection_of_type(col, COLLECTION_GROUP_VARIANT)

def is_group_collection(col: bpy.types.Collection) -> bool:
    """collection that is not an item itself (moving group, container, variant or attachments collection incl. everything below it)"""
    return col is not None and (get_collection_type_def(col).is_group or is_inside_attachments_collection(col))

def is_helper_collection(col: bpy.types.Collection) -> bool:
    """collection that only configures the item, nothing inside is exported (attachments, attachment and everything below)"""
    return col is not None and (not get_collection_type_def(col).exported or is_inside_attachments_collection(col))

# attachments

def is_attachments_collection(col: bpy.types.Collection) -> bool:
    """the _attachments_ collection itself"""
    return is_collection_of_type(col, COLLECTION_GROUP_ATTACHMENTS)

def is_inside_attachments_collection(col: bpy.types.Collection) -> bool:
    """collection below an _attachments_ collection (so a collection which defines one attachment)"""
    if col is None:
        return False
    scene = bpy.context.scene
    seen: set[str] = {col.name}
    parent = get_parent_collection(col, scene)
    while parent is not None and parent.name not in seen:
        if is_attachments_collection(parent):
            return True
        seen.add(parent.name)
        parent = get_parent_collection(parent, scene)
    return False

def is_attachment_collection(col: bpy.types.Collection) -> bool:
    """collection of type Attachment, defines one attachment (placement of the item onto blocks)"""
    return is_collection_of_type(col, COLLECTION_GROUP_ATTACHMENT)

def can_convert_to_attachments_collection(col: bpy.types.Collection) -> bool:
    if col is None: return False
    # only meant for collections that hold attachment collections, not objects
    return len(col.objects) == 0

def get_item_attachment_collections(item: bpy.types.Collection) -> list[bpy.types.Collection]:
    """all collections defining an attachment of the item, found through containers and moving groups"""
    result: list[bpy.types.Collection] = []
    seen: set[str] = set()

    def walk_attachments(col: bpy.types.Collection) -> None:
        for child in col.children:
            if child.name in seen or is_collection_ignored(child):
                continue
            seen.add(child.name)
            if is_attachment_collection(child):
                result.append(child)
            walk_attachments(child)

    def walk(col: bpy.types.Collection) -> None:
        for child in col.children:
            if is_collection_ignored(child):
                continue
            if is_attachments_collection(child):
                walk_attachments(child)
            elif is_group_collection(child):
                walk(child)

    walk(item)
    return result

def get_active_group_collection() -> bpy.types.Collection:
    col = get_active_collection()
    if is_group_collection(col):
        return col
    return None

def can_convert_to_collection_type(col: bpy.types.Collection, type_id: str) -> bool:
    """availability of a type toggle: leaving the type is always possible, entering it needs matching parent and content"""
    if col is None:
        return False
    if get_collection_type_id(col) == type_id:
        return True
    type_def = get_type_def(type_id)
    if type_def.allowed_parents is not None:
        parent = get_parent_collection(col, bpy.context.scene)
        if parent is None or is_group_collection(parent) or get_collection_type_id(parent) not in type_def.allowed_parents:
            return False
    if not type_def.exported:
        return len(col.objects) == 0   # helper types only hold collections / empties
    return all(is_group_collection(child) for child in col.children)   # groups may not contain items

def can_convert_to_moving_group_collection(col: bpy.types.Collection) -> bool:
    if col is None: return False
    # groups may not contain items (default collections)
    return all(is_group_collection(child) for child in col.children)

def can_convert_to_container_collection(col: bpy.types.Collection) -> bool:
    if col is None: return False
    # groups may not contain items (default collections)
    return all(is_group_collection(child) for child in col.children)

def get_item_collection_objects(item: bpy.types.Collection) -> list[bpy.types.Object]:
    """
    all objects belonging to the item: its own objects plus the objects of its moving groups
    and containers (containers are flattened). Nested item collections are separate items and skipped.
    Attachments collections only configure attachments, their objects are never exported.
    """
    objs: list[bpy.types.Object] = []
    seen: set[str] = set()

    def walk(col: bpy.types.Collection) -> None:
        for obj in col.objects:
            if obj.name not in seen:
                seen.add(obj.name)
                objs.append(obj)
        for child in col.children:
            if is_helper_collection(child):
                continue
            if is_group_collection(child) and not is_collection_ignored(child):
                walk(child)

    walk(item)
    return objs

def get_item_meshes_which_require_uvmaps(item: bpy.types.Collection) -> list[bpy.types.Object]:
    """meshes of the item incl. moving groups and containers that need uv maps"""
    return [obj for obj in get_item_collection_objects(item)
        if obj.type == "MESH"
        and obj.visible_get()
        and not getattr(obj, ObjectProp.SOCKET, False)]

def get_item_moving_groups(item: bpy.types.Collection) -> list[bpy.types.Collection]:
    """moving groups of the item, found through containers and other moving groups"""
    groups: list[bpy.types.Collection] = []

    def walk(col: bpy.types.Collection) -> None:
        for child in col.children:
            if is_collection_ignored(child):
                continue
            if is_moving_group_collection(child):
                groups.append(child)
                walk(child)
            elif is_container_collection(child) or is_variant_collection(child):
                walk(child)

    walk(item)
    return groups

def get_object_moving_group(obj: bpy.types.Object) -> bpy.types.Collection | None:
    """nearest moving group of the object, containers are transparent"""
    col = obj.users_collection[0] if obj.users_collection else None
    scene = bpy.context.scene
    while col is not None and is_group_collection(col):
        if is_moving_group_collection(col):
            return col
        col = get_parent_collection(col, scene)
    return None

def get_invalid_group_children(item: bpy.types.Collection) -> list[bpy.types.Collection]:
    """item (default) collections inside moving groups/containers below the item, which is not allowed"""
    invalid: list[bpy.types.Collection] = []

    def walk(col: bpy.types.Collection) -> None:
        for child in col.children:
            if is_collection_ignored(child):
                continue
            if is_group_collection(child):
                walk(child)
            elif is_group_collection(col):
                invalid.append(child)

    walk(item)
    return invalid

def is_inside_group_collection(col: bpy.types.Collection) -> bool:
    """item collections must end at a moving group/container, they can not live inside one"""
    return is_group_collection(get_parent_collection(col, bpy.context.scene))

# selected collections (outliner selection, falls back to the active collection)

def get_selected_collections(context=None) -> list[bpy.types.Collection]:
    context = context or bpy.context
    scene_root = context.scene.collection
    ids = getattr(context, "selected_ids", None) or []   # only available in the Outliner
    cols = [i for i in ids if isinstance(i, bpy.types.Collection) and i != scene_root]
    if not cols:
        layer_col = context.view_layer.active_layer_collection
        if layer_col is not None and layer_col.collection != scene_root:
            cols = [layer_col.collection]
    return cols

def get_item_collections_from_collections(cols: list[bpy.types.Collection]) -> list[bpy.types.Collection]:
    """
    resolve collections to exportable item collections:
    - item: itself and all items below it
    - moving group/container: the item it belongs to
    - plain folder: all items below it
    """
    scene = bpy.context.scene
    items: list[bpy.types.Collection] = []
    seen: set[str] = set()

    def add(col):
        if col is None or col == scene.collection or col.name in seen:
            return
        seen.add(col.name)
        items.append(col)

    def walk(col):
        if not is_group_collection(col):
            add(col)
        for child in col.children:
            walk(child)

    for col in cols:
        if is_group_collection(col):
            add(get_item_root(col, scene))
        else:
            walk(col)

    return [c for c in items if is_collection_exportable(c)]

# waypoint
def is_waypoint_collection(col: bpy.types.Collection) -> bool:
    return getattr(col, CollectionProp.WAYPOINT_TYPE, WAYPOINT_NAME_NONE) != WAYPOINT_NAME_NONE

# export

def is_collection_exportable(coll: bpy.types.Collection)->bool:
    if coll.name.lower() in NOT_ALLOWED_COLLECTION_NAMES:
        return False

    if is_collection_hierarchy_ignored(coll):
        return False
    if is_group_collection(coll):
        return False

    return any(is_object_exportable(obj) for obj in get_item_collection_objects(coll))


def is_collection_instance(obj: bpy.types.Object) -> bool:
    """empty which instances a collection (resolved to duplicated hierarchies by the fbx exporter)"""
    return obj.type == "EMPTY" and obj.instance_type == "COLLECTION" and obj.instance_collection is not None

def get_instanced_collections(objs) -> list[bpy.types.Collection]:
    """collections instanced by objs, nested instances included; unique, in discovery order"""
    result: dict[str, bpy.types.Collection] = {}

    def walk(col: bpy.types.Collection) -> None:
        if col.name in result:   # also protects against instance cycles
            return
        result[col.name] = col
        for o in col.all_objects:
            if is_collection_instance(o):
                walk(o.instance_collection)

    for obj in sorted(objs, key=lambda o: o.name):
        if is_collection_instance(obj):
            walk(obj.instance_collection)
    return list(result.values())

def get_template_objects(col: bpy.types.Collection) -> list[bpy.types.Object]:
    """meshes and lights of an instanced collection (own sub collections included, nested instances excluded)"""
    return [o for o in col.all_objects
            if o.type in (EXPORTABLE_OBJECT_MESH, EXPORTABLE_OBJECT_LIGHT)
            and not any(is_helper_collection(c) for c in o.users_collection)]

def get_instanced_moving_groups(cols: list[bpy.types.Collection]) -> list[bpy.types.Collection]:
    """moving groups defined in instanced collections: the collections themselves and the groups below them"""
    groups: dict[str, bpy.types.Collection] = {}

    def walk(col: bpy.types.Collection) -> None:
        for child in col.children:
            if is_collection_ignored(child):
                continue
            if is_moving_group_collection(child):
                groups.setdefault(child.name, child)
                walk(child)
            elif is_container_collection(child) or is_variant_collection(child):
                walk(child)

    for col in cols:
        if is_collection_ignored(col):
            continue
        if is_moving_group_collection(col):
            groups.setdefault(col.name, col)
        walk(col)
    return list(groups.values())

def get_instanced_template_objects(objs) -> list[bpy.types.Object]:
    """all meshes/lights living in collections instanced by objs (recursive), unique"""
    result: dict[str, bpy.types.Object] = {}
    for col in get_instanced_collections(objs):
        for o in get_template_objects(col):
            result.setdefault(o.name, o)
    return list(result.values())

def _is_particle_fx_node(obj: bpy.types.Object) -> bool:
    s = getattr(obj, "tm_fx", None)
    return bool(s and s.enabled)

def is_object_exportable(obj: bpy.types.Object)-> bool:
    if obj.visible_get() is False:
        return False
    if not (obj.type == EXPORTABLE_OBJECT_MESH or obj.type == EXPORTABLE_OBJECT_LIGHT or is_collection_instance(obj)
            or _is_particle_fx_node(obj)):
        return False

    if getattr(obj, ObjectProp.IGNORE, False):
        return False
    # ignored group (container/moving group) on the way up to the item root hides its objects
    col   = obj.users_collection[0] if obj.users_collection else None
    scene = bpy.context.scene
    while col is not None:
        if is_collection_ignored(col):
            return False
        if is_helper_collection(col):
            return False   # attachment helpers are never exported
        if not is_group_collection(col):
            break
        col = get_parent_collection(col, scene)
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

            if root is None:
                continue

            if root in accepted or root in rejected:
                continue

            if (root.name.lower() in NOT_ALLOWED_COLLECTION_NAMES
                    or is_collection_hierarchy_ignored(root)
                    or is_collection_excluded_or_hidden(root)):
                rejected.add(root)
                continue

            candidates.append(root)

        # object-level checks only if they could change the result
        if not candidates:
            continue
        # plain empties (attachment points, pivots, ...) are no exported geometry themselves, but selecting one
        # still selects its item; the collection is checked for exportable content later (is_collection_exportable)
        is_plain_empty = obj.type == "EMPTY" and not is_collection_instance(obj)
        if not is_plain_empty and (not obj.visible_get() or not is_object_exportable(obj)):
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
    # fallback: first mesh or collection instance
    fallback = next((obj for obj in objects if obj.type == "MESH" or is_collection_instance(obj)), None)

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


#scale
SCALE_RE = re.compile(
    r"_#SCALE_(?:(?P<from>\d+)to(?P<to>\d+)_x(?P<factor>\d+)|\((?P<values>[^)]*)\))"
)

def name_without_scale(name):
    """Collection name with the _#SCALE_... token removed."""
    return SCALE_RE.sub("", name)

def build_scale_token(coll) -> str:
    if getattr(coll, CollectionProp.SCALE_MODE) == 'LINEAR':
        f = getattr(coll, CollectionProp.SCALE_FROM)
        t = getattr(coll, CollectionProp.SCALE_TO)
        x = getattr(coll, CollectionProp.SCALE_FACTOR)
        return f"_#SCALE_{f}to{t}_x{x}"
    else:
        vals = ",".join(_fmt(i.value) for i in getattr(coll, CollectionProp.SCALE_VALUES))
        return f"_#SCALE_({vals})"
    
def _fmt(v: float) -> str:
    return f"{v:g}"

def parse_scale_from_name(name: str):
    """Returns None if no token, else a dict describing it."""
    m = SCALE_RE.search(name)
    if not m:
        return None
    if m["values"] is not None:
        vals = []
        for p in m["values"].split(","):
            p = p.strip()
            if p:
                try:
                    vals.append(float(p))
                except ValueError:
                    pass
        return {"mode": "VALUES", "values": vals}
    return {"mode": "LINEAR", "from": int(m["from"]),
            "to": int(m["to"]), "factor": int(m["factor"])}