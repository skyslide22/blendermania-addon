from bpy.types import (Operator)
from ..properties.Functions import *
from ..utils.Functions import *
from ..utils.NadeoXML import * 
from ..utils.ItemsExportV2Models import *
    
class TM_OT_Items_ItemConfig_SaveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_save_item_config_placement_template"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add Item Config Template"

        
    def execute(self, context):
        tm_props = get_global_props()
        templates = context.scene.tm_props_itemconfig_templates
        temp_name = tm_props.ST_cfg_item_template_add_name
    
        for template in templates:
            if temp_name == template.name:
                show_report_popup(f"Name {temp_name} already exists, cancelled")
                return {"CANCELLED"}


        add_itemconfig_template()
        return {"FINISHED"}


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = get_global_props()
        layout   = self.layout
        layout.prop(tm_props, "ST_cfg_item_template_add_name", text="Name")

class TM_OT_Items_ItemConfig_RemoveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_remove_item_config_placement_template"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove Item Config Template"

    template_name: bpy.props.StringProperty("")
        
    def execute(self, context):
        remove_itemconfig_template(self.template_name)
        return {"FINISHED"}


class TM_OT_Items_Config_AddCompatiblePatchGroup(Operator):
    bl_idname = "view3d.tm_add_compatible_patch_group"
    bl_label = "Add a compatible patch group"
    bl_description = "Add a compatible patch group"

    def execute(self, context):
        item = context.scene.tm_props.LI_cfg_compatibleGroups.add()  # empty, user picks or types
        item.value = "Border"   # default value, user can change it
        return {'FINISHED'}


class TM_OT_Items_Config_RemoveCompatiblePatchGroup(Operator):
    bl_idname = "view3d.tm_remove_compatible_patch_group"
    bl_label = "Remove compatible patch group"

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.tm_props.LI_cfg_compatibleGroups.remove(self.index)
        return {'FINISHED'}

class TM_OT_Items_Config_AddPatchLayoutGroup(bpy.types.Operator):
    bl_idname = "view3d.tm_add_patch_group_ref"
    bl_label = "Add Group"
    patch_index: bpy.props.IntProperty()

    def execute(self, context):
        tm_props = get_global_props()
        tm_props.LI_cfg_patchLayouts[self.patch_index].validForGroups.add()
        return {'FINISHED'}

class TM_OT_Items_Config_RemovePatchLayoutGroup(bpy.types.Operator):
    bl_idname = "view3d.tm_remove_patch_group_ref"
    bl_label = "Remove Group"
    patch_index: bpy.props.IntProperty()
    group_index: bpy.props.IntProperty()

    def execute(self, context):
        tm_props = get_global_props()
        tm_props.LI_cfg_patchLayouts[self.patch_index].validForGroups.remove(self.group_index)
        return {'FINISHED'}

class TM_OT_Items_Config_AddPatchLayout(bpy.types.Operator):
    bl_idname = "view3d.tm_add_patch_layout"
    bl_label = "Add Patch Layout"
    bl_description = "Add a new patch layout definition"

    def execute(self, context):
        tm_props = get_global_props()
        patch = tm_props.LI_cfg_patchLayouts.add()
        index = len(tm_props.LI_cfg_patchLayouts)
        patch.name = f"Patch Layout {index}"
        return {'FINISHED'}


class TM_OT_Items_Config_RemovePatchLayout(bpy.types.Operator):
    bl_idname = "view3d.tm_remove_patch_layout"
    bl_label = "Remove Patch Layout"
    bl_description = "Remove this patch layout definition"

    index: bpy.props.IntProperty()

    def execute(self, context):
        tm_props = get_global_props()
        if 0 <= self.index < len(tm_props.LI_cfg_patchLayouts):
            tm_props.LI_cfg_patchLayouts.remove(self.index)
        return {'FINISHED'}

def draw_nightonly_option(self, context):
    layout = self.layout
    # return
    layout.split()
    row=layout.row()
    # row.alert = True
    row.prop(context.object.data, "night_only", text="Night & Sunset only")







