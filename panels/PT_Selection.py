
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 
from ..operators.OT_Selection import *



class TM_PT_Selection(Panel):
    bl_label   = "Selection"
    bl_idname  = "TM_PT_Selection"
    bl_parent_id = "TM_PT_ObjectManipulations"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_SELECT)
        
    def draw(self, context):
        
        layout = self.layout
        
        current_viewlayer_name  = context.view_layer.name
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"
        
        layout_row = layout.row(align=True)
        
        # ViewLayer selection
        layer_box = layout_row.box()
        
        row = layer_box.row()
        layer_icon = row.column(align=True)
        layer_icon.label(text="", icon=ICON_VIEWLAYER)
        
        layer_text = row.column(align=True)
        row = layer_text.row(align=True)
        row.label(text=current_viewlayer_name)
        
        layer_btns = layer_box.column(align=True)
        row = layer_btns.row(align=True)
        row.operator(#ignore
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_IGNORE,
            icon=ICON_IGNORE
        ).subname = SPECIAL_NAME_PREFIX_IGNORE
        
        row = layer_btns.row(align=True)
        row.operator(#origin
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_INFIX_ORIGIN,
            icon=ICON_ORIGIN
        ).subname = SPECIAL_NAME_INFIX_ORIGIN
        row.operator(#pivot
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_INFIX_PIVOT,
            icon=ICON_PIVOTS
        ).subname = SPECIAL_NAME_INFIX_PIVOT
        
        row = layer_btns.row(align=True)
        row.operator(#trigger
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_TRIGGER,
            icon=ICON_TRIGGER
        ).subname = SPECIAL_NAME_PREFIX_TRIGGER
        row.operator(#socket
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_SOCKET,
            icon=ICON_SOCKET
        ).subname = SPECIAL_NAME_PREFIX_SOCKET
        
        row = layer_btns.row(align=True)
        row.operator(#Lod0
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_SUFFIX_LOD0,
            icon=ICON_LOD_0
        ).subname = SPECIAL_NAME_SUFFIX_LOD0
        row.operator(#Lod1
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_SUFFIX_LOD1,
            icon=ICON_LOD_1
        ).subname = SPECIAL_NAME_SUFFIX_LOD1
        
        row = layer_btns.row(align=True)
        row.operator(#not visible
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_NOTVISIBLE,
            icon=ICON_HIDDEN
        ).subname = SPECIAL_NAME_PREFIX_NOTVISIBLE
        row.operator(#not collidable
            TM_OT_Selection_ViewLayerToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
            icon=ICON_IGNORE
        ).subname = SPECIAL_NAME_PREFIX_NOTCOLLIDABLE
        
        
        # selection in collection
        col_box = layout_row.box()
        
        row = col_box.row()
        col_icon = row.column(align=True)
        col_icon.label(text="", icon=ICON_COLLECTION)
        
        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=current_collection_name.split("_#SCALE")[0] + "")
        
        if current_collection is None:
            return
        
        col_btns = col_box.column(align=True)
        row = col_btns.row(align=True)
        row.operator(#ignore
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_IGNORE,
            icon=ICON_IGNORE
        ).subname = SPECIAL_NAME_PREFIX_IGNORE
        
        row = col_btns.row(align=True)
        row.operator(#origin
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_INFIX_ORIGIN,
            icon=ICON_ORIGIN
        ).subname = SPECIAL_NAME_INFIX_ORIGIN
        row.operator(#pivot
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_INFIX_PIVOT,
            icon=ICON_PIVOTS
        ).subname = SPECIAL_NAME_INFIX_PIVOT
        
        row = col_btns.row(align=True)
        row.operator(#trigger
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_TRIGGER,
            icon=ICON_TRIGGER
        ).subname = SPECIAL_NAME_PREFIX_TRIGGER
        row.operator(#socket
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_SOCKET,
            icon=ICON_SOCKET
        ).subname = SPECIAL_NAME_PREFIX_SOCKET
        
        row = col_btns.row(align=True)
        row.operator(#Lod0
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_SUFFIX_LOD0,
            icon=ICON_LOD_0
        ).subname = SPECIAL_NAME_SUFFIX_LOD0
        row.operator(#Lod1
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_SUFFIX_LOD1,
            icon=ICON_LOD_1
        ).subname = SPECIAL_NAME_SUFFIX_LOD1
        
        row = col_btns.row(align=True)
        row.operator(#not visible
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_NOTVISIBLE,
            icon=ICON_HIDDEN
        ).subname = SPECIAL_NAME_PREFIX_NOTVISIBLE
        row.operator(#not collidable
            TM_OT_Selection_CollectionToggle.bl_idname,
            text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
            icon=ICON_IGNORE
        ).subname = SPECIAL_NAME_PREFIX_NOTCOLLIDABLE