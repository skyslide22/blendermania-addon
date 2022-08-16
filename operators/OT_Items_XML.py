from bpy.types import (Operator)
from ..utils.Functions import *
from ..utils.NadeoXML import * 
    
class TM_OT_Items_ItemXML_SaveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_save_item_placement_template"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add Item XML Template"

        
    def execute(self, context):
        tm_props = get_global_props()
        temp_name = tm_props.ST_xml_item_template_add_name
    
        for template in ítemxml_templates:
            if temp_name == template.name:
                show_report_popup(f"Name {temp_name} already exists, cancelled")
                return {"CANCELLED"}


        add_itemxml_template()
        return {"FINISHED"}


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = get_global_props()
        layout   = self.layout
        layout.prop(tm_props, "ST_xml_item_template_add_name", text="Name")


class TM_OT_Items_ItemXML_RemoveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_remove_item_placement_template"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"

    template_name: bpy.props.StringProperty("")
        
    def execute(self, context):
        remove_itemxml_template(self.template_name)
        return {"FINISHED"}


    # TODO make popup ask for name of placement

class TM_OT_Items_ItemXML_RemovePivot(Operator):
    bl_idname = "view3d.tm_removepivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"

    pivot_index: bpy.props.IntProperty(0)
        
    def execute(self, context):
        # add_or_remove_pivot("DEL")
        remove_pivot_at_index(self.pivot_index)
        return {"FINISHED"}
    
    
class TM_OT_Items_ItemXML_AddPivot(Operator):
    bl_idname = "view3d.tm_addpivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add a pivot"
        
    def execute(self, context):
        add_pivot_at_end()
        return {"FINISHED"}



def remove_pivot_at_index(index: int) -> None:
    pivots = get_pivot_props()
    pivots.remove(index)


def add_pivot_at_end() -> None:
    tm_props_pivots = get_pivot_props()
    tm_props_pivots.add()
    

def draw_nightonly_option(self, context):
    layout = self.layout
    # return
    layout.split()
    row=layout.row()
    # row.alert = True
    row.prop(context.object.data, "night_only", text="Night & Sunset only")









