
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 

class TM_OT_Selection_ViewLayerToggle(Operator):
    bl_idname = "view3d.tm_viewlayerselection"
    bl_description = f"Toggle selection in the ViewLayer"
    bl_label = f"Toggle selection"
    
    subname: bpy.props.StringProperty()
    
    def execute(self, context):
        toggle_name_selection_in_viewlayer(self.subname)
        return {"FINISHED"}

class TM_OT_Selection_CollectionToggle(Operator):
    bl_idname = "view3d.tm_collectionselection"
    bl_description = f"Toggle selection in the Collection"
    bl_label = f"Toggle selection"
    
    subname: bpy.props.StringProperty()
    
    def execute(self, context):
        toggle_name_selection_in_collection(self.subname)
        return {"FINISHED"}

def toggle_name_selection_in_viewlayer(subname: str) -> None:
    if is_all_selected_in_viewlayer(subname):
        for obj in bpy.context.view_layer.objects:
            if subname in obj.name.lower():
                obj.select_set(False)
    else:
        for obj in bpy.context.view_layer.objects:
            if subname in obj.name.lower():
                obj.select_set(True)

def toggle_name_selection_in_collection(subname: str) -> None:
    coll = get_active_collection_of_selected_object()
    if is_all_selected_in_collection(subname):
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.select_set(False)
    else:
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.select_set(True)