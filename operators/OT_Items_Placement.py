from bpy.types import (Operator)
from ..utils.Placement import load_placement_class_template, placement_class_template_items
from ..properties.PlacementProperties import PlacementProperties
from ..properties.AttachmentProperties import ATTACHMENT_PRESETS, ATTACHMENTS_PRESETS, apply_attachment_preset
from ..properties.PropertyIdentifiers import CollectionProp
from ..utils.Constants import COLLECTION_GROUP_ATTACHMENT
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


class TM_OT_Items_Attachment_LoadPreset(Operator):
    bl_idname = "view3d.tm_load_attachment_preset"
    bl_label = "Insert Attachment Preset"
    bl_description = "Choose a predefined attachment config and add its options"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty(default="", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        attachment = getattr(context, "tm_attachment", None)
        if attachment is None:
            self.report({'ERROR'}, "No attachment in context")
            return {'CANCELLED'}
        if self.preset:
            return self.execute(context)

        def draw(menu, _context):
            menu.layout.context_pointer_set("tm_attachment", attachment)
            for name in ATTACHMENT_PRESETS:
                menu.layout.operator(self.bl_idname, text=name).preset = name

        context.window_manager.popup_menu(draw, title="Insert Attachment Preset")
        return {'FINISHED'}

    def execute(self, context):
        attachment = getattr(context, "tm_attachment", None)
        if attachment is None or not apply_attachment_preset(attachment, self.preset):
            self.report({'ERROR'}, "Preset could not be applied")
            return {'CANCELLED'}
        return {'FINISHED'}


class TM_OT_Items_Attachment_HidePlaceholder(Operator):
    bl_idname = "view3d.tm_attachment_hide_placeholder"
    bl_label = "Hide Placeholder"
    bl_description = "Hide the placeholder models of this attachment (viewport preview and particle render objects)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = getattr(context, "tm_attachment_collection", None)
        if col is None:
            self.report({'ERROR'}, "No attachment collection in context")
            return {'CANCELLED'}
        from ..utils.Attachments import PLACEHOLDER_OBJECT_PREFIX
        col["tm_placeholder_hidden"] = True
        for obj in col.objects:
            for psys in obj.particle_systems:
                settings = psys.settings
                inst = settings.instance_object
                if settings.render_type == 'OBJECT' and inst is not None and inst.name.startswith(PLACEHOLDER_OBJECT_PREFIX):
                    settings.instance_object = None
                    settings.render_type = 'NONE'
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class TM_OT_Items_Attachment_ParticlePlaceholder(Operator):
    bl_idname = "view3d.tm_attachment_particle_placeholder"
    bl_label = "Show Placeholder on Particles"
    bl_description = "Show the placeholder model matching the attachment type (Spectator for PilotSlot, car for Slot) at the attachment points"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = getattr(context, "tm_attachment_collection", None)
        if col is None:
            self.report({'ERROR'}, "No attachment collection in context")
            return {'CANCELLED'}
        from ..utils.Attachments import apply_particle_placeholder, get_particle_placeholder, get_attachment_placeholder_kind
        from ..utils.FunctionsV2 import is_attachment_collection
        # create the placeholders of all attachments of the scene (the viewport preview of empties needs them)
        for c in [col, *context.scene.collection.children_recursive]:
            if is_attachment_collection(c):
                kind = get_attachment_placeholder_kind(getattr(c, CollectionProp.ATTACHMENT, None))
                if kind:
                    get_particle_placeholder(kind)
        kind = get_attachment_placeholder_kind(getattr(col, CollectionProp.ATTACHMENT, None))
        if kind is None:
            self.report({'INFO'}, "No placeholder model for this attachment type")
        apply_particle_placeholder([o for o in col.objects if o.particle_systems], kind)
        col["tm_placeholder_hidden"] = False
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class TM_OT_Items_Attachments_LoadPreset(Operator):
    bl_idname = "view3d.tm_load_attachments_preset"
    bl_label = "Insert Attachments Preset"
    bl_description = "Choose a predefined set of attachments and create one attachment sub-collection for each"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty(default="", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        parent = getattr(context, "tm_attachments_collection", None)
        if parent is None:
            self.report({'ERROR'}, "No attachments collection in context")
            return {'CANCELLED'}
        if self.preset:
            return self.execute(context)

        def draw(menu, _context):
            menu.layout.context_pointer_set("tm_attachments_collection", parent)
            for name in ATTACHMENTS_PRESETS:
                menu.layout.operator(self.bl_idname, text=name).preset = name

        context.window_manager.popup_menu(draw, title="Insert Attachments Preset")
        return {'FINISHED'}

    def execute(self, context):
        parent = getattr(context, "tm_attachments_collection", None)
        names = ATTACHMENTS_PRESETS.get(self.preset)
        if parent is None or names is None:
            self.report({'ERROR'}, "Preset could not be applied")
            return {'CANCELLED'}
        for preset_name, slot in names:
            name = f"{preset_name} {slot:02d}" if slot is not None else preset_name
            col = bpy.data.collections.new(name)
            parent.children.link(col)
            setattr(col, CollectionProp.COLLECTION_TYPE, COLLECTION_GROUP_ATTACHMENT)   # also adds the name infix
            attachment = getattr(col, CollectionProp.ATTACHMENT)
            apply_attachment_preset(attachment, preset_name, slot)
            # attachment point at the 3D cursor, move/rotate it afterwards
            empty = bpy.data.objects.new(f"{name} Point", None)
            empty.empty_display_type = 'ARROWS'
            empty.empty_display_size = 1.0
            empty.location = context.scene.cursor.location
            col.objects.link(empty)
        return {'FINISHED'}



