import bpy
from bpy.props import *

class ConvertingItemsProperties(bpy.types.PropertyGroup):
    """trackmania properties generated for pivots (item xml)"""
    name              : StringProperty(name="ITEM NAME ... ", default="ITEM NAME ... ")
    name_raw          : StringProperty(name="COL NAME ... ",  default="COL NAME ... ")
    icon              : StringProperty(name="Icon name",      default="TIME")
    failed            : BoolProperty(name="Convert failed?",  default=False)
    converted         : BoolProperty(name="Item converted?",  default=False)
    convert_duration  : IntProperty(name="Convert duration",  default=0, min=0, max=10000)