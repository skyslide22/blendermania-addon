import bpy
from bpy.props import CollectionProperty, StringProperty, PointerProperty, IntProperty, BoolProperty, FloatProperty


class FBXPlanNodeProperties(bpy.types.PropertyGroup):
    name: StringProperty()           # node name in the exported fbx (generated for collection instances)
    original_node: StringProperty()  # name of the blender object the node was created from
    obj: PointerProperty(type=bpy.types.Object)   # the original object
    lod_indices: StringProperty()

    has_uv_overlap: BoolProperty(
        name="Has UV Overlap",
        default=False,
    )

class FbxGbxPlanGroupProperties(bpy.types.PropertyGroup):
    key: StringProperty()
    group_type: StringProperty()
    original_group_id: StringProperty()
    lod_distances: StringProperty()
    nodes: CollectionProperty(type=FBXPlanNodeProperties)
    show_expanded: BoolProperty(default=False)
    # applied to the mesh configs of the group's nodes on export, the objects stay untouched
    lightmap_size: FloatProperty(
        name="Lightmap Size",
        default=100.0, min=0.0,
    )
    override_lightmap_size: BoolProperty(
        name="Override Lightmap Size",
        default=False,
    )

    has_uv_overlap: BoolProperty(
        name="Has UV Overlap",
        default=False,
    )
    num_uv_overlap_faces: IntProperty(
        name="Number of UV Overlap Faces",
        default=0,
    )

class FbxGbxPlanProperties(bpy.types.PropertyGroup):
    groups: CollectionProperty(type=FbxGbxPlanGroupProperties)
    is_valid: BoolProperty(default=False)
    is_stale: BoolProperty(default=False)

