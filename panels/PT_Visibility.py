
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 



class TM_PT_Visibility(Panel):
    bl_label   = "Visibility"
    bl_idname  = "TM_PT_Visibility"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_VISIBLE)
        
    def draw(self, context):
        
        layout = self.layout
        
        current_viewlayer_name  = context.view_layer.name
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"
        
        # ViewLayer visibility
        layer_box = layout.box()
        
        row = layer_box.row()
        layer_icon = row.column(align=True)
        layer_icon.label(text="", icon=ICON_VIEWLAYER)
        
        layer_text = row.column(align=True)
        row = layer_text.row(align=True)
        row.label(text=current_viewlayer_name)
        
        layer_btns = layer_box.column(align=True)
        row = layer_btns.row(align=True)
        row.operator(#ignore
            "view3d.tm_viewlayervisibilityignore",
            text=SPECIAL_NAME_PREFIX_IGNORE,
            icon=ICON_IGNORE
        )
        
        row = layer_btns.row(align=True)
        row.operator(#origin
            "view3d.tm_viewlayervisibilityorigin",
            text=SPECIAL_NAME_INFIX_ORIGIN,
            icon=ICON_ORIGIN
        )
        row.operator(#pivot
            "view3d.tm_viewlayervisibilitypivot",
            text=SPECIAL_NAME_INFIX_PIVOT,
            icon=ICON_PIVOTS
        )
        
        row = layer_btns.row(align=True)
        row.operator(#trigger
            "view3d.tm_viewlayervisibilitytrigger",
            text=SPECIAL_NAME_PREFIX_TRIGGER,
            icon=ICON_TRIGGER
        )
        row.operator(#socket
            "view3d.tm_viewlayervisibilitysocket",
            text=SPECIAL_NAME_PREFIX_SOCKET,
            icon=ICON_SOCKET
        )
        
        row = layer_btns.row(align=True)
        row.operator(#Lod0
            "view3d.tm_viewlayervisibilitylod0",
            text=SPECIAL_NAME_SUFFIX_LOD0,
            icon=ICON_LOD_0
        )
        row.operator(#Lod1
            "view3d.tm_viewlayervisibilitylod1",
            text=SPECIAL_NAME_SUFFIX_LOD1,
            icon=ICON_LOD_1
        )
        
        row = layer_btns.row(align=True)
        row.operator(#not visible
            "view3d.tm_viewlayervisibilitynotvisible",
            text=SPECIAL_NAME_PREFIX_NOTVISIBLE,
            icon=ICON_HIDDEN
        )
        row.operator(#not collidable
            "view3d.tm_viewlayervisibilitynotcollidable",
            text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
            icon=ICON_IGNORE
        )
        
        
        # visibility in collection
        col_box = layout.box()
        
        row = col_box.row()
        col_icon = row.column(align=True)
        col_icon.label(text="", icon=ICON_COLLECTION)
        
        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=current_collection_name.split("_#SCALE")[0] + "")
        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).col_name = current_collection_name
        
        if current_collection is None:
            return
        
        col_btns = col_box.column(align=True)
        row = col_btns.row(align=True)
        row.operator(#ignore
            "view3d.tm_collectionvisibilityignore",
            text=SPECIAL_NAME_PREFIX_IGNORE,
            icon=ICON_IGNORE
        )
        
        row = col_btns.row(align=True)
        row.operator(#origin
            "view3d.tm_collectionvisibilityorigin",
            text=SPECIAL_NAME_INFIX_ORIGIN,
            icon=ICON_ORIGIN
        )
        row.operator(#pivot
            "view3d.tm_collectionvisibilitypivot",
            text=SPECIAL_NAME_INFIX_PIVOT,
            icon=ICON_PIVOTS
        )
        
        row = col_btns.row(align=True)
        row.operator(#trigger
            "view3d.tm_collectionvisibilitytrigger",
            text=SPECIAL_NAME_PREFIX_TRIGGER,
            icon=ICON_TRIGGER
        )
        row.operator(#socket
            "view3d.tm_collectionvisibilitysocket",
            text=SPECIAL_NAME_PREFIX_SOCKET,
            icon=ICON_SOCKET
        )
        
        row = col_btns.row(align=True)
        row.operator(#Lod0
            "view3d.tm_collectionvisibilitylod0",
            text=SPECIAL_NAME_SUFFIX_LOD0,
            icon=ICON_LOD_0
        )
        row.operator(#Lod1
            "view3d.tm_collectionvisibilitylod1",
            text=SPECIAL_NAME_SUFFIX_LOD1,
            icon=ICON_LOD_1
        )
        
        row = col_btns.row(align=True)
        row.operator(#not visible
            "view3d.tm_collectionvisibilitynotvisible",
            text=SPECIAL_NAME_PREFIX_NOTVISIBLE,
            icon=ICON_HIDDEN
        )
        row.operator(#not collidable
            "view3d.tm_collectionvisibilitynotcollidable",
            text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
            icon=ICON_IGNORE
        )