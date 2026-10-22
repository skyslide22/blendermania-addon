import json
import os
import bpy
from bpy.props import EnumProperty


from ..properties import PlacementProperties


from ..utils.FunctionsV2 import get_addon_templates_path

from ..utils.ItemsExportV2Models import FILL_ALIGN_MAP, FILL_DIR_MAP, PlacementClass, _decode


_template_cache = None


def get_placement_class_template_path():
    return get_addon_templates_path() + "placement_class/"

def _scan_placement_class_templates():
    found = []
    placement_class_templates = get_placement_class_template_path()
    if not os.path.isdir(placement_class_templates):
        return found
    for f in sorted(os.listdir(placement_class_templates)):
        if f.endswith(".json"):
            stem = f[:-5]
            found.append((stem, stem.replace("_", " "), ""))
    return found

def invalidate_placement_class_templates():
    global _template_cache
    _template_cache = None

def placement_class_template_items(self, context):
    global _template_cache
    if _template_cache is None:
        _template_cache =_scan_placement_class_templates()
    return _template_cache



def load_placement_class_template(placement_parameter: PlacementProperties, template_name: str):
    if placement_parameter is None:
        return
    template_path = get_placement_class_template_path() + template_name + ".json"
    if not os.path.isfile(template_path):
        return
    with open(template_path, "r") as f:
        pc = _decode(PlacementClass, json.load(f))

    apply_placement_class_template(placement_parameter, pc)

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