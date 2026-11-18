"""Validation of tree model collections (see CollectionTypes: TreeModel)."""
from __future__ import annotations

import bpy

from .FunctionsV2 import get_item_collection_objects, get_item_tree_models, is_collection_ignored, is_moving_group_collection


def is_texture_set_material(mat: bpy.types.Material | None) -> bool:
    props = getattr(mat, "tm_asset_properties", None)
    return props is not None and props.is_asset and props.asset_type == "TEXTURESET"


def get_tree_model_issues(item: bpy.types.Collection, objs=()) -> list[str]:
    """errors of all tree models of the item (and of the collections it instances)"""
    errors: list[str] = []
    for tree_model in get_item_tree_models(item, objs):
        for child in tree_model.children:
            if not is_collection_ignored(child) and is_moving_group_collection(child):
                errors.append(f"{tree_model.name}: tree models can not contain moving groups ({child.name})")
        for obj in get_item_collection_objects(tree_model):
            if obj.type != 'MESH':
                continue
            if not obj.material_slots:
                errors.append(f"{tree_model.name}: <{obj.name}> has no texture set material")
            for slot in obj.material_slots:
                if not is_texture_set_material(slot.material):
                    name = slot.material.name if slot.material else "empty slot"
                    errors.append(f"{tree_model.name}: <{obj.name}> material <{name}> is not a texture set")
    return list(dict.fromkeys(errors))
