import bpy
from bpy.props import *

from ..properties.PlacementProperties import PlacementProperties

MODE_ITEMS = [
    ('INHERIT',  "Default",  "Use the template chosen in the export panel"),
    ('TEMPLATE', "Template", "Use a specific template"),
    ('CUSTOM',   "Custom",   "Use this item's own config"),
]

class PlacementPropertiesRef(bpy.types.PropertyGroup):
    mode: EnumProperty(items=MODE_ITEMS)
    template: StringProperty()
    placement: PointerProperty(type=PlacementProperties)


class ItemConfigProperties(bpy.types.PropertyGroup):      
    placement: PointerProperty(type=PlacementPropertiesRef)
    # light
    # scale
    # ...





