
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 

class TM_OT_VisibilitySelection_Toggle(Operator):
    bl_idname = "view3d.tm_visibilityselection_toggle"
    bl_description = f"Toggle"
    bl_label = f"Toggle"
    
    subname: bpy.props.StringProperty()
    use_collection: bpy.props.BoolProperty()
    
    @classmethod
    def description(self, context, properties):
        tm_props = get_global_props()
        is_visibility = tm_props.CB_visSel_use_visibility
        action = "visibility" if is_visibility else "selection"
        name = "every object" if self.subname == ALL_OBJECTS else self.subname
        area = "Collection" if self.use_collection else "ViewLayer"
        return f"Toggle {action} of {name} in {area}"
    
    def execute(self, context):
        toggle_name_visibility_selection(self.subname,self.use_collection)
        return {"FINISHED"}
        
def toggle_name_visibility_selection(subname:str,use_collection:bool) -> None:
    coll = get_active_collection_of_selected_object()
    objects = coll.objects if use_collection else bpy.context.view_layer.objects
    objects = coll.objects if use_collection else bpy.context.view_layer.objects
    tm_props = get_global_props()
    is_visibility = tm_props.CB_visSel_use_visibility
    for_all = subname == ALL_OBJECTS
    if is_visibility:
        if is_name_visible(subname,use_collection):
            for obj in objects:
                if subname.lower() in obj.name.lower() or for_all:
                    obj.hide_set(True)
        else:
            for obj in objects:
                if subname.lower() in obj.name.lower() or for_all:
                    obj.hide_set(False)
    else:
        if is_name_all_selected(subname,use_collection):
            for obj in objects:
                if subname.lower() in obj.name.lower() or for_all:
                    obj.select_set(False)
        else:
            for obj in objects:
                if subname.lower() in obj.name.lower() or for_all:
                    obj.select_set(True)