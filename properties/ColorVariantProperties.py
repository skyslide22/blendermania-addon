import bpy
from bpy.props import (
    StringProperty,
    FloatVectorProperty,
    IntProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
)


class TM_ColorVariantItem(bpy.types.PropertyGroup):
    """Single color variant with name and color value"""
    name: StringProperty(
        name="Variant Name",
        description="Name for this color variant (e.g., 'Red', 'Blue')",
        default="Color"
    )
    color: FloatVectorProperty(
        name="Color",
        description="Color value for this variant",
        subtype='COLOR',
        min=0.0,
        max=1.0,
        size=3,
        default=(1.0, 0.0, 0.0)
    )
    enabled: BoolProperty(
        name="Enabled",
        description="Include this variant in export",
        default=True
    )


class TM_ColorVariantSettings(bpy.types.PropertyGroup):
    """Settings for multi-color export feature"""
    enabled: BoolProperty(
        name="Enable Multi-Color Export",
        description="Export items with multiple color variants",
        default=False
    )
    target_material: PointerProperty(
        name="Target Material",
        description="The material whose color will be varied",
        type=bpy.types.Material
    )
    variants: CollectionProperty(
        type=TM_ColorVariantItem,
        name="Color Variants"
    )
    active_variant_index: IntProperty(
        name="Active Variant Index",
        default=0
    )
