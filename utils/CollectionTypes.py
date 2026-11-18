"""
Single source of truth for the collection types (what kinds of collections exist and how they behave).

A collection type is one entry in COLLECTION_TYPE_DEFS. Adding a new type means:
  1. add its identifier to Constants.COLLECTION_GROUP_VALID_NAMES
  2. add a CollectionTypeDef below, plus a CollectionProp.<NAME>_GROUP identifier for its toggle button
Enum items, the toggle button properties, the name infix, the outliner color, the "is it an item" checks and the
"is its content exported" checks all derive from the definition, nothing else has to be touched for those.
"""
from __future__ import annotations

from dataclasses import dataclass

import bpy

from . import Constants as C
from ..properties.PropertyIdentifiers import CollectionProp


@dataclass(frozen=True)
class CollectionTypeDef:
    id: str
    label: str
    description: str
    infix: str | None = None             # added to the collection name, the name is the source of truth for the type
    color_tag: str | None = None         # outliner color, None: color of the waypoint type
    toggle_prop: str | None = None       # CollectionProp of the toggle button
    toggle_icon: str = 'NONE'
    is_group: bool = True                # not an item itself: belongs to the item above it
    exported: bool = True                # objects inside are exported as part of the item
    allowed_parents: tuple[str, ...] | None = None   # type ids the parent must have, None: anywhere
    show_toggle: bool = True             # toggle button in the collection panels (False: drawn by a special drawer)


COLLECTION_TYPE_DEFS: tuple[CollectionTypeDef, ...] = (
    CollectionTypeDef(
        C.COLLECTION_TYPE_DEFAULT, "Default", "Regular item collection",
        is_group=False,
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_MOVING, "Moving Group", "Collection is a moving group",
        infix="_movingGroup_", color_tag=C.COLLECTION_COLOR_TAG_PINK,
        toggle_prop=CollectionProp.MOVING_GROUP, toggle_icon="NLA_PUSHDOWN",
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_CONTAINER, "Container", "Structural only collection, has no item data",
        infix="_container_", color_tag=C.COLLECTION_COLOR_TAG_BROWN,
        toggle_prop=CollectionProp.CONTAINER_GROUP, toggle_icon="OUTLINER_COLLECTION",
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_ATTACHMENTS, "Attachments", "Holds attachment collections, nothing inside is exported as fbx",
        infix="_attachments_", color_tag=C.COLLECTION_COLOR_TAG_VIOLET,
        toggle_prop=CollectionProp.ATTACHMENTS_GROUP, toggle_icon="EMPTY_AXIS",
        exported=False,
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_ATTACHMENT, "Attachment", "Defines one attachment (layout, options, attachment points), nothing inside is exported as fbx",
        infix="_attachment_", color_tag=C.COLLECTION_COLOR_TAG_ORANGE,
        toggle_prop=CollectionProp.ATTACHMENT_GROUP, toggle_icon="EMPTY_AXIS",
        exported=False, show_toggle=False,
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_VARIANT, "Variant", "One variant of an item with variants, a full model with its own meshes, lights and attachments",
        infix="_variant_", color_tag=C.COLLECTION_COLOR_TAG_YELLOW,
        toggle_prop=CollectionProp.VARIANT_GROUP, toggle_icon="DUPLICATE",
        allowed_parents=(C.COLLECTION_TYPE_DEFAULT,),   # directly below an item collection
    ),
    CollectionTypeDef(
        C.COLLECTION_GROUP_TREE_MODEL, "Tree Model", "Vegetation tree model: meshes use texture set materials and the collection defines the veget tree",
        infix="_treeModel_", color_tag=C.COLLECTION_COLOR_TAG_GREEN,
        toggle_prop=CollectionProp.TREE_MODEL_GROUP, toggle_icon="OUTLINER_OB_GREASEPENCIL",
        allowed_parents=(C.COLLECTION_TYPE_DEFAULT, C.COLLECTION_GROUP_VARIANT, C.COLLECTION_GROUP_CONTAINER),   # item (or instanced) collection, variant, container
    ),
)

_DEFS_BY_ID: dict[str, CollectionTypeDef] = {d.id: d for d in COLLECTION_TYPE_DEFS}
DEFAULT_TYPE_DEF = _DEFS_BY_ID[C.COLLECTION_TYPE_DEFAULT]

# types that carry a name infix / have a toggle button
TYPES_WITH_INFIX = tuple(d for d in COLLECTION_TYPE_DEFS if d.infix)
TYPES_WITH_TOGGLE = tuple(d for d in COLLECTION_TYPE_DEFS if d.toggle_prop)

COLLECTION_TYPE_ENUM_ITEMS = [
    (d.id, d.label, d.description, 'NONE', i)
    for i, d in enumerate(COLLECTION_TYPE_DEFS)
]


# -----------------------------
# item mode: how an item is split into variants
# -----------------------------
ITEM_MODE_SINGLE = "SINGLE"
ITEM_MODE_VARIANTS = "VARIANTS"
ITEM_MODE_ENUM_ITEMS = [
    (ITEM_MODE_SINGLE, "Single", "One model, variant collections inside are treated like containers", 'NONE', 0),
    (ITEM_MODE_VARIANTS, "Variants", "The item is made of variant collections, the variant matching the attachment point is shown", 'NONE', 1),
]


# -----------------------------
# lookups
# -----------------------------
def get_type_def(type_id: str) -> CollectionTypeDef:
    return _DEFS_BY_ID.get(type_id, DEFAULT_TYPE_DEF)

def get_collection_type_id(col: bpy.types.Collection | None) -> str:
    if col is None:
        return C.COLLECTION_TYPE_DEFAULT
    return getattr(col, CollectionProp.COLLECTION_TYPE, C.COLLECTION_TYPE_DEFAULT)

def get_collection_type_def(col: bpy.types.Collection | None) -> CollectionTypeDef:
    return get_type_def(get_collection_type_id(col))

def is_collection_of_type(col: bpy.types.Collection | None, type_id: str) -> bool:
    return col is not None and get_collection_type_id(col) == type_id

def get_type_color_tag(type_id: str) -> str | None:
    return get_type_def(type_id).color_tag
