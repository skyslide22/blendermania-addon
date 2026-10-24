from bpy.types import (Operator)
from ..utils.Placement import load_placement_class_template, placement_class_template_items
from ..properties.PlacementProperties import PlacementProperties
from ..properties.Functions import *
from ..utils.Functions import *
from ..utils.NadeoXML import * 
from ..utils.ItemsExportV2Models import *
    
class TM_OT_Items_ItemConfig_SaveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_save_item_config_placement_template"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add Item Config Template"

    template_name: bpy.props.StringProperty("")
    overwrite: bpy.props.BoolProperty(name="Overwrite existing", default=False)


    def invoke(self, context, event):
        self._placement = getattr(context, "tm_placement", None)
        if self._placement is None:
            self.report({'ERROR'}, "No placement in context")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        placement = getattr(self, "_placement", None)
        if placement is None:
            self.report({'ERROR'}, "No placement")
            return {'CANCELLED'}

        if not self.template_name:
            self.report({'ERROR'}, "Name cannot be empty")
            return {'CANCELLED'}

        local_names = [t.name for t in context.window_manager.tm_local_placement_templates]
        if self.template_name in local_names and not self.overwrite:
            self.report({'ERROR'}, f"'{self.template_name}' already exists locally (tick Overwrite)")
            return {'CANCELLED'}

        from .OT_Settings import save_local_placement_template
        save_local_placement_template(self.template_name, placement)
        return {'FINISHED'}
    
    def draw(self, context):
        tm_props = get_global_props()
        layout   = self.layout
        layout.prop(self, "template_name", text="Name")
        if self.template_name in [t.name for t in context.window_manager.tm_local_placement_templates]:
            layout.label(text="A local template with this name exists.", icon='ERROR')
            layout.prop(self, "overwrite")

class TM_OT_Items_ItemConfig_RemoveItemPlacementTemplate(Operator):
    bl_idname = "view3d.tm_remove_item_config_placement_template"
    bl_description = "Remove the selected template from where it is stored (blend file or local disk)"
    bl_icon = 'ADD'
    bl_label = "Remove Item Config Template"

    template_name: bpy.props.StringProperty("")

        
    def execute(self, context):
        source, template = find_placement_template(self.template_name)
        if template is None:
            return {"CANCELLED"}
        if source == TEMPLATE_SOURCE_LOCAL:
            from .OT_Settings import remove_local_placement_template
            remove_local_placement_template(template.name)
        else:
            remove_itemconfig_placement_template(template.name)
        return {"FINISHED"}

class TM_OT_Items_ItemConfig_CopyPlacementTemplateToLocal(Operator):
    bl_idname = "view3d.tm_copy_item_config_placement_template_to_local"
    bl_description = "Save the selected blend file template to your local templates"
    bl_label = "Save Template Locally"

    template_name: bpy.props.StringProperty("")

    def execute(self, context):
        source, template = find_placement_template(self.template_name)
        if template is None or source != TEMPLATE_SOURCE_BLEND:
            return {"CANCELLED"}
        from .OT_Settings import save_local_placement_template
        save_local_placement_template(template.name, template.config)
        return {"FINISHED"}
    
class _PlacementTemplatePicker:
    """Base for operators that pop up a list of templates and apply the chosen one to context.tm_placement.
    Subclasses implement get_template_names(context) and load(placement)."""
    picker_title = "Insert Template"
    template_name: bpy.props.StringProperty(default="", options={'SKIP_SAVE'})

    def get_template_names(self, context):
        return []

    def load(self, placement):
        pass

    def invoke(self, context, event):
        placement = getattr(context, "tm_placement", None)
        if placement is None:
            self.report({'ERROR'}, "No placement in context")
            return {'CANCELLED'}
        if self.template_name:
            return self.execute(context)

        names = self.get_template_names(context)
        idname = self.bl_idname

        def draw(menu, _context):
            layout = menu.layout
            if not names:
                layout.label(text="No templates found", icon='INFO')
                return
            layout.context_pointer_set("tm_placement", placement)
            for name in names:
                layout.operator(idname, text=name.replace("_", " ")).template_name = name

        context.window_manager.popup_menu(draw, title=self.picker_title)
        return {'FINISHED'}

    def execute(self, context):
        placement = getattr(context, "tm_placement", None)
        if placement is None:
            self.report({'ERROR'}, "No placement in context")
            return {'CANCELLED'}
        self.load(placement)
        return {'FINISHED'}


class TM_OT_Items_ItemConfig_LoadPlacementTemplate(_PlacementTemplatePicker, Operator):
    bl_idname = "view3d.tm_load_item_config_placement_template"
    bl_label = "Load Template"
    bl_description = "Choose a template and insert its values into the custom placement"

    def get_template_names(self, context):
        return [tid for tid, _, _ in list_placement_templates()]

    def load(self, placement):
        load_itemconfig_placement_template(placement, self.template_name)

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


class TM_OT_Items_ItemConfig_LoadPlacementClassTemplate(_PlacementTemplatePicker, Operator):
    bl_idname = "view3d.tm_load_item_config_placement_class_template"
    bl_label = "Load Item Config Template Class"
    bl_description = "Choose a template and insert its values into the attachment configuration"
    picker_title = "Insert Attachment Template"

    def get_template_names(self, context):
        return [item[0] for item in placement_class_template_items(self, context)]

    def load(self, placement):
        load_placement_class_template(placement, self.template_name)




