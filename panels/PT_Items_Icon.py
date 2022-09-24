import bpy
import os.path
import re
import math
import statistics as stats
from bpy.types import (
    Panel,
    Operator,
)
from ..utils.Functions import *
from ..utils.Constants import * 
from ..properties.Functions import *


    
class TM_PT_Items_Icon(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_Icon"
    bl_parent_id = "TM_PT_Items_Export"
    # endregion
    
    @classmethod
    def poll(cls, context):
        return not is_convert_panel_active()
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row()
        row.enabled = tm_props.CB_icon_genIcons
        row.label(text="Item Icon")
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        col.enabled = tm_props.CB_icon_genIcons
        col.prop(tm_props, "CB_icon_overwriteIcons",   text="", icon=ICON_UPDATE)
        col = row.column(align=True)
        col.prop(tm_props, "CB_icon_genIcons",         text="", icon=ICON_CHECKED,)
        row=layout.row()


    
    def draw(self, context):
        scene  = context.scene
        layout = self.layout
        tm_props        = scene.tm_props
        tm_props_pivots = scene.tm_props_pivots
        useTransparentBG= scene.render.film_transparent

        layout.row().label(text="Camera direction is positive Y")

        row = layout.row()
        row.prop(tm_props, "LI_icon_perspective", text="Cam")

        #bpy.context.scene.view_settings.view_transform = 'Standard'

        row = layout.row()
        row.prop(scene.view_settings, "view_transform", text="Style")

        row = layout.row()
        row.prop(tm_props, "NU_icon_padding", text="Fill space", expand=True)

        row = layout.row(align=True)
        row2= row.row(align=True)
        row2.label(text="Bground")
        
        row2 = row.row(align=True)
        row2.prop(scene.render, "film_transparent", text="None", toggle=True, icon="GHOST_DISABLED")
        
        row3 = row.row(align=True)
        row3.enabled = True if not useTransparentBG else False
        row3.prop(tm_props, "NU_icon_bgColor",  text="")


        row = layout.row(align=True)
        row2= row.row(align=True)
        row2.label(text="Size")
        
        row2 = row.row(align=True)
        row2.prop(tm_props, "LI_icon_pxDimension", expand=True)

        layout.separator(factor=UI_SPACER_FACTOR)

        row = layout.row()
        row.scale_y = 1
        row.operator("view3d.tm_make_test_icon", text="Do a test render", icon=ICON_ICON)

        
        
        
        
 