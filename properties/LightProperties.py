import bpy
from bpy.props import *
from .PropertyIdentifiers import LightProp

def register_light_properties():
    setattr(bpy.types.Light, 
            LightProp.LIGHT_EMITTING_RADIUS, 
            FloatProperty(name="Emitting Radius", description="", default=0.0, step=100))
    
    setattr(bpy.types.Light, 
            LightProp.LIGHT_EMITTING_LENGTH, 
            FloatProperty(name="Emitting Length", description="", default=0.0, step=100))

    setattr(bpy.types.Light, 
            LightProp.LIGHT_NIGHT_ONLY, 
            BoolProperty(name="Night Only", description="", default=False))

def unregister_light_properties():
    for prop in LightProp:
        if hasattr(bpy.types.Light, prop):
            delattr(bpy.types.Light, prop)