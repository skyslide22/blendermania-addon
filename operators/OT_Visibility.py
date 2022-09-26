
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 

class TM_OT_Visibility_ViewLayerToggle(Operator):
    bl_idname = "view3d.tm_viewlayervisibility"
    bl_description = f"Toggle visibility in the ViewLayer"
    bl_label = f"Toggle Visibility"
    
    subname: bpy.props.StringProperty()
    
    def execute(self, context):
        toggle_name_visibility_in_viewlayer(self.subname)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggle(Operator):
    bl_idname = "view3d.tm_collectionvisibility"
    bl_description = f"Toggle visibility in the Collection"
    bl_label = f"Toggle Visibility"
    
    subname: bpy.props.StringProperty()
    
    def execute(self, context):
        toggle_name_visibility_in_collection(self.subname)
        return {"FINISHED"}

def toggle_name_visibility_in_viewlayer(subname: str) -> None:
    if is_name_visible_in_viewlayer(subname):
        for obj in bpy.context.view_layer.objects:
            if subname in obj.name.lower():
                obj.hide_set(True)
    else:
        for obj in bpy.context.view_layer.objects:
            if subname in obj.name.lower():
                obj.hide_set(False)

def toggle_name_visibility_in_collection(subname: str) -> None:
    coll = get_active_collection_of_selected_object()
    if is_name_visible_in_collection(subname):
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.hide_set(True)
    else:
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.hide_set(False)