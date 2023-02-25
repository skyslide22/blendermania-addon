import bpy
from .Functions import (getMaterialPhysicIds, get_global_props, get_linked_materials)

def get_material_links(self, context)-> list:
    tm_props     = get_global_props()
    materials    = []
    selected     = []
   
    for kek in tm_props.DICT_MaterialsOverrides:
        selected.append(kek.material)

    for mat in get_linked_materials():
        #print(mat in list(tm_props.DICT_MaterialsOverrides))
        #if mat.name not in selected:
        materials.append((mat.name, mat.name, mat.name))
    
    materials.sort()
    return materials

def on_update_mat_link(self,context):
    self.material = self.link

class MaterialPhysicsOverride(bpy.types.PropertyGroup):
    link      : bpy.props.EnumProperty(name="Link", items=get_material_links, update=on_update_mat_link)
    # the same as link, used for filtering
    material  : bpy.props.StringProperty(name="Material")
    physic_id : bpy.props.EnumProperty(name="PhysicId", items=getMaterialPhysicIds)
    enabled   : bpy.props.BoolProperty(name="Enabled", default=True)