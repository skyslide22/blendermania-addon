import bpy
from bpy.types import (Operator)
from ..utils.Functions import (
    get_global_props,
)

class TM_OT_AddMaterialOverride(Operator):
    bl_idname = "view3d.add_material_override"
    bl_label = "Add"

    def execute(self, context):
        get_global_props().DICT_MaterialsOverrides.add()

        return {'FINISHED'}

class TM_OT_RemoveMaterialOverride(Operator):
    bl_idname = "view3d.remove_material_override"
    bl_label = "Remove"

    index: bpy.props.IntProperty(0)
        
    def execute(self, context):
        get_global_props().DICT_MaterialsOverrides.remove(self.index)
        return {"FINISHED"}