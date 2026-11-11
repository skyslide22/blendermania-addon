"""
Variants: an item in Variants mode is made of Variant collections placed directly inside the item collection.
Each variant is a full model (own meshes, lights, instances, attachments), tagged with key/value pairs.
Everything outside the variant collections is shared and exported without a variant.

Collection layout:
    Item                    (item mode: Variants)
        _variant_Red        (Variant, has tags)
            meshes, lights, instances, containers, moving groups, _attachments_
        _variant_Blue
        shared objects      (optional, exported without a variant)
"""
from __future__ import annotations

import re

import bpy

from ..properties.AttachmentProperties import get_option_dict
from ..properties.PropertyIdentifiers import CollectionProp
from .CollectionTypes import ITEM_MODE_SINGLE, ITEM_MODE_VARIANTS, get_type_def
from .Constants import COLLECTION_GROUP_VARIANT
from .FunctionsV2 import (
    get_parent_collection, is_collection_ignored, is_group_collection, is_helper_collection, is_variant_collection,
)
from .Functions import strip_ignore_prefix
from .ItemsExportV2Models import VariantConfig


# -----------------------------
# item / variant lookup
# -----------------------------
def is_variant_item(item: bpy.types.Collection | None) -> bool:
    """item collection in Variants mode"""
    return (item is not None
            and not is_group_collection(item)
            and getattr(item, CollectionProp.ITEM_MODE, ITEM_MODE_SINGLE) == ITEM_MODE_VARIANTS)

def get_variant_name(col: bpy.types.Collection) -> str:
    """name of the variant: collection name without ignore prefix and type infix"""
    name = strip_ignore_prefix(col.name)
    infix = get_type_def(COLLECTION_GROUP_VARIANT).infix
    if infix:
        name = re.sub(re.escape(infix), "", name, flags=re.IGNORECASE)
    return name.strip("_ ") or col.name

def get_item_variant_collections(item: bpy.types.Collection) -> list[bpy.types.Collection]:
    """variant collections directly inside the item, not ignored, in outliner order"""
    return [c for c in item.children if is_variant_collection(c) and not is_collection_ignored(c)]

def get_variant_by_name(item: bpy.types.Collection, name: str) -> bpy.types.Collection | None:
    for col in get_item_variant_collections(item):
        if get_variant_name(col) == name:
            return col
    return None

class VariantResolver:
    """
    answers "which variant does this collection / object belong to" for one item, None means shared.
    Built once per item (walks down from the variants, so no per object parent lookups).
    """
    def __init__(self, item: bpy.types.Collection):
        self._by_collection: dict[str, str] = {}
        if not is_variant_item(item):
            return
        for variant in get_item_variant_collections(item):
            name = get_variant_name(variant)
            self._by_collection[variant.name] = name
            for col in variant.children_recursive:
                self._by_collection.setdefault(col.name, name)

    @property
    def active(self) -> bool:
        return bool(self._by_collection)

    def of_collection(self, col: bpy.types.Collection | None) -> str | None:
        return self._by_collection.get(col.name) if col is not None else None

    def of_object(self, obj: bpy.types.Object) -> str | None:
        for col in obj.users_collection:
            name = self._by_collection.get(col.name)
            if name is not None:
                return name
        return None


# -----------------------------
# config
# -----------------------------
def get_variant_configs(item: bpy.types.Collection) -> list[VariantConfig]:
    if not is_variant_item(item):
        return []
    configs: list[VariantConfig] = []
    for col in get_item_variant_collections(item):
        props = getattr(col, CollectionProp.VARIANT, None)
        configs.append(VariantConfig(
            Name=get_variant_name(col),
            Tags=get_option_dict(props.tags) if props is not None else {},
            HiddenInManualCycle=bool(props.hidden_in_manual_cycle) if props is not None else False,
        ))
    return configs


# -----------------------------
# conversion / validation
# -----------------------------
def can_convert_to_variant_collection(col: bpy.types.Collection) -> bool:
    if col is None:
        return False
    # like every group: may not contain items (default collections)
    return all(is_group_collection(child) for child in col.children)

def get_misplaced_variant_collections(item: bpy.types.Collection) -> list[bpy.types.Collection]:
    """variant collections below the item that are not directly inside it (inside a container, a moving group or another variant)"""
    misplaced: list[bpy.types.Collection] = []

    def walk(col: bpy.types.Collection) -> None:
        for child in col.children:
            if is_collection_ignored(child):
                continue
            if is_variant_collection(child) and col != item:
                misplaced.append(child)
            if is_group_collection(child):
                walk(child)

    walk(item)
    return misplaced

def get_variant_issues(item: bpy.types.Collection) -> tuple[list[str], list[str]]:
    """(errors, warnings) of the variant setup of an item, errors must stop the export"""
    errors: list[str] = []
    warnings: list[str] = []

    for col in get_misplaced_variant_collections(item):
        errors.append(f"Variant '{col.name}' must be directly inside the item collection")

    if not is_variant_item(item):
        if any(is_variant_collection(c) for c in item.children):
            warnings.append("Item has Variant collections but item mode is not Variants, they are exported like containers")
        return errors, warnings

    variants = get_item_variant_collections(item)
    if not variants:
        errors.append("Item mode is Variants but the item has no Variant collection")
        return errors, warnings

    names: dict[str, str] = {}
    for col in variants:
        name = get_variant_name(col)
        if name in names:
            errors.append(f"Variants '{names[name]}' and '{col.name}' have the same name '{name}'")
        names[name] = col.name
        if not any(not is_helper_collection(c) and len(c.objects) for c in [col, *col.children_recursive]):
            warnings.append(f"Variant '{col.name}' contains no objects")

    return errors, warnings
