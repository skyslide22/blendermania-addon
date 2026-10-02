import bpy
from bpy.props import *

class CubeCenterProperties(bpy.types.PropertyGroup):
    """trackmania properties generated for CubeCenter"""
    NU_centerX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)
    NU_centerY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)
    NU_centerZ   : FloatProperty(name="Z", default=0.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)

class WorldDirProperties(bpy.types.PropertyGroup):
    """trackmania properties generated for WorldDir"""
    NU_worldDirX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)
    NU_worldDirY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)
    NU_worldDirZ   : FloatProperty(name="Z", default=1.0, min=-1024, max=1024, soft_min=-256, soft_max=256, step=100)


class PivotsProperties(bpy.types.PropertyGroup):
    """trackmania properties generated for pivots (item xml)"""
    NU_pivotX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotZ   : FloatProperty(name="Z", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)

    NU_pivotRotX   : FloatProperty(name="X", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)
    NU_pivotRotY   : FloatProperty(name="Y", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)
    NU_pivotRotZ   : FloatProperty(name="Z", default=0.0, min=0, max=360, soft_min=0, soft_max=360, step=10)

