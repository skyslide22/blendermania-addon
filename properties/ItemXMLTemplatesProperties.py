import bpy
from bpy.props import *

from .Functions import get_itemxml_template_names_enum

class ItemXMLTemplatesProperties(bpy.types.PropertyGroup):
    from ..utils.NadeoXML import ItemXMLTemplate # circular import else

    templates_ui:   EnumProperty(items=get_itemxml_template_names_enum)
    templates =     CollectionProperty(type=ItemXMLTemplate)
    # templates_ui = EnumProps()
    # templates_ui: list
