import bpy
from bpy.props import *

from .AttachmentProperties import AttachmentOptionProperties


class VariantProperties(bpy.types.PropertyGroup):
    """settings of a collection of type Variant"""
    tags: PointerProperty(
        name="Tags",
        description="Key/value pairs (same keys as an attachment option). The variant is chosen when an attachment point of the item it is placed on matches all of them",
        type=AttachmentOptionProperties,
    )
    hidden_in_manual_cycle: BoolProperty(
        name="Hidden In Manual Cycle",
        description="Skip this variant when cycling through the variants manually in the editor",
        default=False,
    )
