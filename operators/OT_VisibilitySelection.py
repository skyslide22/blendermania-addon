
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 

class TM_OT_VisibilitySelection_Toggle(Operator):
    bl_idname = "view3d.tm_visibilityselection_toggle"
    bl_description = f"Toggle"
    bl_label = f"Toggle"
    
    is_visibility = bpy.props.BoolProperty()
    subname: bpy.props.StringProperty()
    use_collection: bpy.props.BoolProperty()
    
    @classmethod
    def description(context, properties):
        action = "visibility" if self.is_visibility else "selection"
        name = "every object" if self.subname == ALL_OBJECTS else self.subname
        area = "Collection" if self.use_collection else "ViewLayer"
        return f"Toggle {action} of {name} in {area}"
    
    def execute(self, context):
        toggle_name_visibility_selection(self.subname,self.use_collection)
        return {"FINISHED"}
        
def toggle_name_visibility_selection(subname:str,use_collection:bool) -> None:
    coll = get_active_collection_of_selected_object()
    tm_props = get_global_props()
    is_visibility = tm_props.CB_visSel_use_visibility
    for_all = subname == ALL_OBJECTS
    if is_all_selected_in_collection(subname):
        for obj in coll.objects:
            if subname in obj.name.lower() or for_all:
                obj.select_set(False)
    else:
        for obj in coll.objects:
            if subname in obj.name.lower() or for_all:
                obj.select_set(True)