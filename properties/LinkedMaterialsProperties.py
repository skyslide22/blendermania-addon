
import bpy
from bpy.props import *

class LinkedMaterialsProperties(bpy.types.PropertyGroup):
    """for material creation panel, stores materials from the game's nadeoimportermateriallib.txt (linked)"""
    name : StringProperty(name="Linked mat name", default="")