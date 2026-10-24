import re

import bpy
from bpy.props import *
from ..utils.Functions import get_global_props
from ..utils.Constants import * 


def compatible_group_search(self, context, edit_text):
    # must return an iterable of plain strings
    return [ident for ident in PLACEMENT_KNOWN_PATCH_GROUPS
            if edit_text.lower() in ident.lower()]

# matches the last path segment, e.g. ".validForGroups[0]" or '.patches["Name"]'
_LAST_SEGMENT = re.compile(r'\.[^.\[\]]+(?:\[(?:\d+|"[^"]*")\])?$')

def find_owner_with(prop: bpy.types.PropertyGroup, attr: str):
    """Walk up from a property group until an ancestor has `attr`."""
    id_data = prop.id_data
    path = prop.path_from_id()          # e.g. "tm_props.placement.patches[2].validForGroups[0]"
    while path:
        path = _LAST_SEGMENT.sub("", path, count=1) if _LAST_SEGMENT.search(path) else ""
        if not path:
            break
        parent = id_data.path_resolve(path)
        if hasattr(parent, attr):
            return parent
    return None

def valid_for_group_search(self, context, edit_text):
    try:
        owner = find_owner_with(self, "LI_compatibleGroups")
    except ValueError:                  # not reachable from an ID
        return []
    if owner is None:
        return []

    needle = edit_text.lower()
    return [g.name for g in owner.LI_compatibleGroups if needle in g.name.lower()]

class CompatiblePatchGroupProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Group",
        description="Compatible patch group",
        search=compatible_group_search,
        search_options={'SUGGESTION'},  # SUGGESTION = custom text allowed
    )

class PatchGroupRef(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Group",
        description="Valid for patch group",
        search=valid_for_group_search,
        search_options={'SUGGESTION'},  # SUGGESTION = custom text allowed
    )

FILL_ALIGN_ITEMS = [
    ('FRONT', CHAR_RIGHT +" Front", "Align items from the front"),
    ('CENTER', CHAR_HORIZONTAL +" Center", "Align items from the center"),
    ('BACK', CHAR_LEFT +" Back", "Align items from the back")
]
FILL_DIR_ITEMS = [
    ('LEFT/RIGHT', CHAR_HORIZONTAL +" Left/Right", "Fill items from the left/right"),
    ('FRONT/BACK', CHAR_VERTICAL +" Front/Back", "Fill items from the front/back"),
]

class PlacementPatchProperties(bpy.types.PropertyGroup):
    autoItemCount: bpy.props.BoolProperty(
        name="Auto Item Count",
        description="Automatically determine item count in this patch from spacing.",
        default=True)
    
    itemCount: bpy.props.IntProperty(
        name="Item Count",
        description="Number of items to place in this patch",
        default=0,
        min=0,
        step=1)
    
    itemSpacing: bpy.props.FloatProperty(
        name="Item Spacing",
        description="Spacing between items in this patch",
        default=0.0,
        soft_min=0,
        step=100.0)

    fillAlignment: bpy.props.EnumProperty(
        name="Fill Alignment",
        description="Alignment of items in this patch.",
        items=FILL_ALIGN_ITEMS,
        default='CENTER')

    fillDirection: bpy.props.EnumProperty(
        name="Fill Direction",
        description="Direction to fill items in this patch.",
        items=FILL_DIR_ITEMS,
        default='LEFT/RIGHT')

    fillOffsetU: bpy.props.FloatProperty(
        name="Fill Offset U",
        description="Offset in the left/right direction before filling items in this patch.",
        default=0.0,
        step=100)

    fillOffsetV: bpy.props.FloatProperty(
        name="Fill Offset V",
        description="Offset in the front/back direction before filling items in this patch.",
        default=0.0,
        step=100)

    normedPos: bpy.props.FloatProperty(
        name="Horizontal Position",
        description="Horizontal position of the item in this patch",
        subtype='FACTOR',
        default=0.5,
        min=0,
        max=1)

    altitude: bpy.props.FloatProperty(
        name="OffsetV",
        description="Altitude of the item in this patch",
        default=0,
        step=1.0)

    validForGroups: bpy.props.CollectionProperty(
        name="Patch Layouts", 
        type=PatchGroupRef,
        description="For which groups this layout is valid.")

    validForGroups_index: bpy.props.IntProperty(name="Patch Layouts", default=-1)

