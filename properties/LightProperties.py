import bpy
from bpy.props import *
from .PropertyIdentifiers import LightProp

SIMPLE_OR_ADVANCED_ITEMS = [
    ('SIMPLE',  "Simple",  "Simple Light"),
    ('ADVANCED', "Advanced", "Advanced Light"),
]

def register_light_properties():
        setattr(bpy.types.Light, 
                LightProp.LIGHT_EMITTING_RADIUS, 
                FloatProperty(name="Area Emitting Radius", description="", default=0.0, step=100))

        setattr(bpy.types.Light, 
                LightProp.LIGHT_EMITTING_LENGTH, 
                FloatProperty(name="Area Emitting Length", description="", default=0.0, step=100))

        setattr(bpy.types.Light, 
                LightProp.LIGHT_NIGHT_ONLY, 
                BoolProperty(name="Night Only", description="", default=False))


        setattr(bpy.types.Light, 
                LightProp.LIGHT_CONFIG_TYPE, 
                EnumProperty(name="Enable Advanced", description="", items=SIMPLE_OR_ADVANCED_ITEMS, default='SIMPLE'))
        
        setattr(bpy.types.Light, 
                LightProp.LIGHT_INVERTED, 
                BoolProperty(name="Inverted", description="", default=False))
        setattr(bpy.types.Light, 
                LightProp.LIGHT_ENABLED, 
                BoolProperty(name="Enabled", description="", default=True))
        setattr(bpy.types.Light, 
                LightProp.LIGHT_ENABLE_SPECULAR, 
                BoolProperty(name="Enable Specular", description="", default=True))
        setattr(bpy.types.Light, 
                LightProp.LIGHT_ATTENUATION_TENSION, 
                FloatProperty(name="Attenuation Tension", description="", default=0.3, precision=3,))
        setattr(bpy.types.Light, 
                LightProp.LIGHT_ATTENUATION_DERIVATIVE_AT_ZERO, 
                FloatProperty(name="Attenuation Derivative At Zero", description="", default=-1.5, precision=3, step=1))
        setattr(bpy.types.Light, 
                LightProp.LIGHT_ATTENUATION_HDR_RADIUS_COEFF, 
                FloatProperty(name="Attenuation HDR Radius Coeff", description="", default=0.015625, step=0.001, precision=6))


def unregister_light_properties():
    for prop in LightProp:
        if hasattr(bpy.types.Light, prop):
            delattr(bpy.types.Light, prop)