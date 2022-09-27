
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 
from ..operators.OT_VisibilitySelection import *

class TM_PT_VisibilitySelection(Panel):
    bl_label   = "Visibility/Selection"
    bl_idname  = "TM_PT_VisibilitySelection"
    bl_parent_id = "TM_PT_ObjectManipulations"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_VIS_SEL)
    
    def draw_header_preset(self,context):
        tm_props = get_global_props()
        is_visibility = tm_props.CB_visSel_use_visibility
        layout = self.layout
        vis_sel_icon = ICON_VISIBLE if is_visibility else ICON_SELECT
        layout.prop(tm_props, 'CB_visSel_use_visibility', icon= vis_sel_icon)
        
    def draw(self, context):
        
        layout = self.layout
        tm_props = get_global_props()
        is_visibility = tm_props.CB_visSel_use_visibility
        
        current_viewlayer_name  = context.view_layer.name
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"
        
        layout_row = layout.row(align=True)
        length = len(SPECIAL_NAMES_TO_DRAW)
        
        for use_collection in [False,True]:
            icon = ICON_COLLECTION if use_collection else ICON_VIEWLAYER
            label = (current_collection_name.split("_#SCALE")[0] + "") if use_collection else current_viewlayer_name
            box = layout_row.box()
            
            row = box.row()
            column = row.column(align=True)
            column.label(text='',icon=icon)
            
            column = row.column(align=True)
            row = column.row(align=True)
            row.label(text=label)
            if use_collection == False or current_collection is not None:
                new_vissel_operator(row,ALL_OBJECTS,'',use_collection)
            
            if use_collection and current_collection is None:
                return
            
            column = box.column(align=True)
            row = column.row(align=True)
            for i in range(length):
                subname = list(SPECIAL_NAMES_TO_DRAW.keys())[i]
                icon = list(SPECIAL_NAMES_TO_DRAW.values())[i]
                if ((length %2) == 1 and i == 0) or (i % 2) == 0:
                    new_vissel_operator(row,subname,icon,use_collection)
                    if i != length -1:
                       row = column.row(align=True)
                else:
                    new_vissel_operator(row,subname,icon,use_collection)
    
def new_vissel_operator(parent_ui:bpy.types.UILayout,subname:str,icon:str,use_collection:bool):
    tm_props = get_global_props()
    is_visibility = tm_props.CB_visSel_use_visibility
    operator:TM_OT_VisibilitySelection_Toggle
    if subname == ALL_OBJECTS:
        operator = parent_ui.operator(
            TM_OT_VisibilitySelection_Toggle.bl_idname,
            text = 'ALL'
            )
    else:
        operator = parent_ui.operator(
            TM_OT_VisibilitySelection_Toggle.bl_idname,
            text = subname,
            icon = icon
            )
    operator.subname = subname
    operator.use_collection = use_collection