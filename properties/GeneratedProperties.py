import bpy
from bpy.props import *


class GeneratedProperties(bpy.types.PropertyGroup):
    """trackmania properties generated"""
    ST_matPhysicsId : StringProperty(name="PhysicsId",             default="Concrete")
    ST_matName      : StringProperty(name="Mat Name",              default="")
    ST_matModel     : StringProperty(name="Mat Model",             default="TDSN")
    ST_matBTex      : StringProperty(name="Mat BaseTexture",       default="StadiumPlatform")
    CB_matBool      : BoolProperty(name="mat name not set yet",    default=False)