import json
import os
import bpy
from bpy.props import EnumProperty


from ..properties import PlacementProperties


from ..utils.FunctionsV2 import get_addon_templates_path

from ..utils.ItemsExportV2Models import FILL_ALIGN_MAP, FILL_DIR_MAP, PlacementClass, _decode


_template_cache = None


def placement_class_template_items(self, context):
    """built-in and local placement class templates (utils/TemplateLibrary)"""
    from . import TemplateLibrary as TL
    global _template_cache
    _template_cache = [(e.id, e.label, TL.SOURCE_LABELS[e.source]) for e in TL.file_entries(TL.KIND_PLACEMENT_CLASS)]
    return _template_cache

def invalidate_placement_class_templates():
    global _template_cache
    _template_cache = None


_FILL_DIR_NAMES = {0: "U", 1: "V"}            # numbers as written by get_placement_config_from_properties
_FILL_ALIGN_NAMES = {0: "Center", 1: "Begin", 2: "End"}

def placement_class_dict(placement_parameter: PlacementProperties) -> dict:
    """attachment configuration as a template (same layout as assets/templates/placement_class/*.json)"""
    from .ItemsExportV2Models import placement_class_from_properties, _encode
    d = _encode(placement_class_from_properties(placement_parameter))
    for pl in d.get("PatchLayouts") or []:
        pl["FillDir"] = _FILL_DIR_NAMES.get(pl.get("FillDir"), pl.get("FillDir"))
        pl["FillAlign"] = _FILL_ALIGN_NAMES.get(pl.get("FillAlign"), pl.get("FillAlign"))
    d.pop("GroupCurPatchLayouts", None)
    return d

def apply_placement_class_dict(placement_parameter: PlacementProperties, data: dict):
    if placement_parameter is None or not isinstance(data, dict):
        return
    apply_placement_class_template(placement_parameter, _decode(PlacementClass, data))

def load_placement_class_template(placement_parameter: PlacementProperties, template_name: str):
    """insert a built-in template by file name (kept for callers of the old API)"""
    from . import TemplateLibrary as TL
    entry = TL.find_entry(TL.KIND_PLACEMENT_CLASS, f"{TL.SOURCE_BUILTIN}|{template_name}")
    if entry is not None:
        apply_placement_class_dict(placement_parameter, TL.read(entry))

def apply_placement_class_template(placement_properties: PlacementProperties, placement_class: PlacementClass):    
    if placement_properties is None or placement_class is None:
        return
    placement_properties.ST_sizeGroup = placement_class.SizeGroup
    placement_properties.CB_alwaysUp = placement_class.AlwaysUp
    placement_properties.CB_alignToInterior = placement_class.AlignToInterior
    placement_properties.CB_alignToWorldDir = placement_class.AlignToWorldDir
    placement_properties.PT_worldDir = (placement_class.WorldDir.X, placement_class.WorldDir.Y, placement_class.WorldDir.Z)
    
    placement_properties.LI_compatibleGroups.clear()
    for group in placement_class.CompatibleGroupsIds:
        placement_properties.LI_compatibleGroups.add().name = group

    placement_properties.LI_patchLayouts.clear()
    for i, patch_layout in enumerate(placement_class.PatchLayouts):
        pl = placement_properties.LI_patchLayouts.add()
        pl.name = f"Patch Layout {i+1}"
        pl.autoItemCount = patch_layout.ItemCount == 0
        pl.itemCount = patch_layout.ItemCount
        pl.itemSpacing = patch_layout.ItemSpacing
        pl.fillAlignment = FILL_ALIGN_MAP[patch_layout.FillAlign]
        pl.fillDirection = FILL_DIR_MAP[patch_layout.FillDir]
        pl.fillOffsetU = patch_layout.FillOffsetU
        pl.fillOffsetV = patch_layout.FillOffsetV
        pl.normedPos = patch_layout.NormedPos
        pl.altitude = patch_layout.Altitude

        pl.validForGroups.clear()
        for group in patch_layout.OnlyOnGroups:
            pl.validForGroups.add().name = group
    

def register_placement_templates():
    bpy.types.WindowManager.tm_placement_class_templates = EnumProperty(
        name="Template",
        items=placement_class_template_items,
    )

def unregister_placement_templates():
    del bpy.types.WindowManager.tm_placement_class_templates