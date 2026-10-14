import bpy
from bpy.props import *

from ..properties.Functions import get_item_config_template_names_enum

from ..properties.PlacementProperties import PlacementProperties

MODE_ITEMS = [
    ('INHERIT',  "Auto",  "Use the template chosen in the export panel"),
    ('TEMPLATE', "Template", "Use a specific template"),
    ('CUSTOM',   "Custom",   "Use this item's own config"),
]

class PlacementPropertiesRef(bpy.types.PropertyGroup):
    mode: EnumProperty(items=MODE_ITEMS)
    template: EnumProperty(name="Template", items=get_item_config_template_names_enum)
    placement: PointerProperty(type=PlacementProperties)

class ItemPlacementTemplate(bpy.types.PropertyGroup):
    name: str = "default_template_name"
    #config: bpy.props.StringProperty()
    config: bpy.props.PointerProperty(type=PlacementProperties)



class ItemConfigProperties(bpy.types.PropertyGroup):      
    placement: PointerProperty(type=PlacementPropertiesRef)
    # light
    # scale
    # ...





