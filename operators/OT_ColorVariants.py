import bpy
from bpy.types import Operator


class TM_OT_ColorVariant_Add(Operator):
    """Add a new color variant"""
    bl_idname = "view3d.tm_colorvariant_add"
    bl_label = "Add Color Variant"
    bl_description = "Add a new color variant for export"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color_settings = context.scene.tm_props_color_variants
        variant = color_settings.variants.add()

        # Generate unique default name
        existing_names = [v.name for v in color_settings.variants]
        base_name = "Color"
        counter = 1
        name = base_name
        while name in existing_names[:-1]:  # Exclude the just-added one
            counter += 1
            name = f"{base_name}{counter}"
        variant.name = name

        color_settings.active_variant_index = len(color_settings.variants) - 1
        return {'FINISHED'}


class TM_OT_ColorVariant_Remove(Operator):
    """Remove the active color variant"""
    bl_idname = "view3d.tm_colorvariant_remove"
    bl_label = "Remove Color Variant"
    bl_description = "Remove the selected color variant"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        color_settings = context.scene.tm_props_color_variants
        return len(color_settings.variants) > 0

    def execute(self, context):
        color_settings = context.scene.tm_props_color_variants
        index = color_settings.active_variant_index

        if 0 <= index < len(color_settings.variants):
            color_settings.variants.remove(index)
            # Adjust active index
            if color_settings.active_variant_index >= len(color_settings.variants):
                color_settings.active_variant_index = max(0, len(color_settings.variants) - 1)

        return {'FINISHED'}


class TM_OT_ColorVariant_MoveUp(Operator):
    """Move color variant up in the list"""
    bl_idname = "view3d.tm_colorvariant_moveup"
    bl_label = "Move Up"
    bl_description = "Move the selected color variant up"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        color_settings = context.scene.tm_props_color_variants
        return color_settings.active_variant_index > 0

    def execute(self, context):
        color_settings = context.scene.tm_props_color_variants
        index = color_settings.active_variant_index
        color_settings.variants.move(index, index - 1)
        color_settings.active_variant_index -= 1
        return {'FINISHED'}


class TM_OT_ColorVariant_MoveDown(Operator):
    """Move color variant down in the list"""
    bl_idname = "view3d.tm_colorvariant_movedown"
    bl_label = "Move Down"
    bl_description = "Move the selected color variant down"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        color_settings = context.scene.tm_props_color_variants
        return color_settings.active_variant_index < len(color_settings.variants) - 1

    def execute(self, context):
        color_settings = context.scene.tm_props_color_variants
        index = color_settings.active_variant_index
        color_settings.variants.move(index, index + 1)
        color_settings.active_variant_index += 1
        return {'FINISHED'}
