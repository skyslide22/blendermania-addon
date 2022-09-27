
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
    
    # order and function of buttons
    # order matters
    subnames = [
    SPECIAL_NAME_PREFIX_IGNORE,
    SPECIAL_NAME_INFIX_ORIGIN,
    SPECIAL_NAME_INFIX_PIVOT,
    SPECIAL_NAME_PREFIX_TRIGGER,
    SPECIAL_NAME_PREFIX_SOCKET,
    SPECIAL_NAME_SUFFIX_LOD0,
    SPECIAL_NAME_SUFFIX_LOD1,
    SPECIAL_NAME_PREFIX_NOTVISIBLE,
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
    ]
    # icons that correspond to the subname with the same index in subnames
    # order matters
    subname_icons = [
    ICON_IGNORE,
    ICON_ORIGIN,
    ICON_PIVOTS,
    ICON_TRIGGER,
    ICON_SOCKET,
    ICON_LOD_0,
    ICON_LOD_1,
    ICON_HIDDEN,
    ICON_IGNORE,
    ]
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw_header(self, context):
        tm_props = get_global_props()
        is_visibility = tm_props.CB_visSel_use_visibility
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
        length = len(subnames)
        
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
            
            if use_collection and current_collection is None:
                return
            
            column = box.column(align=True)
            row = column.row(align=True)
            for i in range(length):
                if ((length %2) == 1 and i == 0) or (i % 2) == 0:
                    new_vissel_operator(row,i,use_collection)
                    if i != length -1:
                       row = column.row(align=True)
                else:
                    new_vissel_operator(row,i,use_collection)
    
    def new_vissel_operator(parent_ui:bpy.types.UILayout,index:int,use_collection:bool):
        tm_props = get_global_props()
        is_visibility = tm_props.CB_visSel_use_visibility
        operator = parent_ui.Operator(
            TM_OT_VisibilitySelection_Toggle.bl_idname,
            text = subnames[index],
            icon = subname_icons[index]
            )
        operator.subname = subnames[index]
        operator.use_collection = use_collection
        operator.is_visibility = is_visibility