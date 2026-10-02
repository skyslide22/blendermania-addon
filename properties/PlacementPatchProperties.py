import bpy
from bpy.props import *
from ..utils.Constants import * 


KNOWN_PATCH_GROUPS = [
    "Border",
    "BorderDecoWall",
    "BorderInGround",
    "BorderMultiSize",
    "BorderOpen",
    "BorderOpenCurve1",
    "BorderPlatform",
    "BorderPlatformWater",
    "BorderRallyRoadDirt",
    "BorderTrackWall",
    "BorderWaterSmall",
    "Road",
    "RoadBump",
    "RoadDirt",
    "RoadDirtTilt",
    "RoadDirtWarp",
    "RoadIce",
    "RoadIceTilt",
    "RoadIceWarp",
    "RoadNarrowCenter",
    "RoadNarrowLeft",
    "RoadNarrowRight",
    "RoadOpen",
    "RoadOpenTilt",
    "RoadOpenWarp",
    "RoadSlopeHard",
    "RoadSlopeSoft",
    "RoadTilt",
    "RoadWarp",
    "RoadWater",
    "StructureSupport",
]

def compatible_group_search(self, context, edit_text):
    # must return an iterable of plain strings
    return [ident for ident in KNOWN_PATCH_GROUPS
            if edit_text.lower() in ident.lower()]

class CompatiblePatchGroupProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Group",
        description="Compatible patch group",
        search=compatible_group_search,
        search_options={'SUGGESTION'},  # SUGGESTION = custom text allowed
    )

class PatchGroupRef(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Group")   # no search callback; prop_search handles it
    
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

    fillAlignment: bpy.props.BoolProperty(
        name="Fill Alignment",
        description="Alignment of items in this patch.",
        default=True)

    fillDirection: bpy.props.EnumProperty(
        name="Fill Direction",
        description="Direction to fill items in this patch.",
        items=[
            ('FRONT', CHAR_RIGHT +" Front", "Fill items from the front"),
            ('CENTER', CHAR_HORIZONTAL +" Center", "Fill items from the center"),
            ('BACK', CHAR_LEFT +" Back", "Fill items from the back")
        ],
        default='FRONT')

    normedPos: bpy.props.FloatProperty(
        name="Horizontal Position",
        description="Horizontal position of the item in this patch",
        default=0.5,
        min=0,
        max=1,
        step=0.1)

    altitude: bpy.props.FloatProperty(
        name="OffsetV",
        description="Altitude of the item in this patch",
        default=0,
        step=1.0)

    validForGroups: bpy.props.CollectionProperty(
        name="Patch Layouts", 
        type=PatchGroupRef,
        description="For which groups this layout is valid.")

