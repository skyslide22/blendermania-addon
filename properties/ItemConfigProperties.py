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
    # the template is referenced by NAME: dynamic enums store an index, which points to a different template
    # on a machine with other local templates
    template_name: StringProperty(name="Template", description="Name of the placement template used for this item")
    # legacy (index into the dynamic list), only read once to fill template_name (migrate_placement_template_refs)
    template: EnumProperty(name="Template (legacy)", items=get_item_config_template_names_enum)
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





