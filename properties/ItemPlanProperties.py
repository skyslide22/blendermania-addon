import bpy
from bpy.props import CollectionProperty, StringProperty, PointerProperty, IntProperty, BoolProperty, FloatProperty
from ..properties.PropertyIdentifiers import ObjectProp




def _apply_lightmap_size(self, context):
    """Runs whenever the group's value changes (UI or Python)."""
    for n in self.nodes:
        if n.obj is not None:
            setattr(n.obj, ObjectProp.LIGHTMAP_SIZE, self.lightmap_size)

def _apply_override_lightmap_size(self, context):
    """Runs whenever the group's value changes (UI or Python)."""
    for n in self.nodes:
        if n.obj is not None:
            setattr(n.obj, ObjectProp.OVERRIDE_LIGHTMAP_SIZE, self.override_lightmap_size)

class FBXPlanNodeProperties(bpy.types.PropertyGroup):
    name: StringProperty()
    obj: PointerProperty(type=bpy.types.Object)
    lod_indices: StringProperty()

class FbxGbxPlanGroupProperties(bpy.types.PropertyGroup):
    key: StringProperty()
    group_type: StringProperty()
    original_group_id: StringProperty()
    lod_distances: StringProperty()
    nodes: CollectionProperty(type=FBXPlanNodeProperties)
    show_expanded: BoolProperty(default=False)
    lightmap_size: FloatProperty(
        name="Lightmap Size",
        default=100.0, min=0.0,
        update=_apply_lightmap_size,
    )
    override_lightmap_size: BoolProperty(
        name="Override Lightmap Size",
        default=False,
        update=_apply_override_lightmap_size,
    )

class FbxGbxPlanProperties(bpy.types.PropertyGroup):
    groups: CollectionProperty(type=FbxGbxPlanGroupProperties)
    is_valid: BoolProperty(default=False)
    is_stale: BoolProperty(default=False)

