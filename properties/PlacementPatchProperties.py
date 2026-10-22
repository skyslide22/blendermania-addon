import bpy
from bpy.props import *
from ..utils.Functions import get_global_props
from ..utils.Constants import * 


def compatible_group_search(self, context, edit_text):
    # must return an iterable of plain strings
    return [ident for ident in PLACEMENT_KNOWN_PATCH_GROUPS
            if edit_text.lower() in ident.lower()]

def valid_for_group_search(self, context, edit_text):
    # get selected group
    tm_props = get_global_props()
    compatible_groups = [ident.name for ident in tm_props.LI_cfg_compatibleGroups]
    return [ident for ident in compatible_groups]

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

