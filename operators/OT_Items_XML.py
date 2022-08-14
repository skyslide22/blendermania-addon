from bpy.types import (Operator)
from ..utils.Functions import *
    
class TM_OT_Items_ItemXML_SaveItemPlacements(Operator):
    bl_idname = "view3d.tm_save_item_placements"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"
        
    def execute(self, context):
        print("test msg save item placements")
        return {"FINISHED"}

    # TODO make popup ask for name of placement

class TM_OT_Items_ItemXML_RemovePivot(Operator):
    bl_idname = "view3d.tm_removepivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"
        
    def execute(self, context):
        add_or_remove_pivot("DEL")
        return {"FINISHED"}
    
    
class TM_OT_Items_ItemXML_AddPivot(Operator):
    bl_idname = "view3d.tm_addpivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add a pivot"
        
    def execute(self, context):
        add_or_remove_pivot("ADD")
        return {"FINISHED"}

def add_or_remove_pivot(type: str) -> None:
    """add or remove a pivot for xml creation"""
    tm_props        = get_global_props()
    tm_props_pivots = get_pivot_props()
    
    pivotcount = len(tm_props_pivots)
    
    if type == "ADD":   tm_props_pivots.add()
    if type == "DEL":   tm_props_pivots.remove(pivotcount -1)

def extend_object_properties_panel_LIGHT(self, context):
    layout = self.layout
    # return
    layout.split()
    row=layout.row()
    # row.alert = True
    row.prop(context.object.data, "night_only", text="Night & Sunset only")









