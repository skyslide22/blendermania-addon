import bpy
from bpy.props import *
from ..utils.AssetLibraryFunctions import poll_asset
from ..utils.ItemsExportV2Models import EPlaneComputeMode
from ..properties.PropertyFunctions import enum_items

class PositionProperties(bpy.types.PropertyGroup):
    value : FloatVectorProperty(name="Position", size=3, subtype='XYZ', default=(0.0, 0.0, 0.0), step=1)

class VegetTreeProperties(bpy.types.PropertyGroup):
    """veget tree settings of a collection of type TreeModel, written to ItemConfig.VegetTrees on export (lod distances come from the item)"""

    angle_max_rot_xz_deg: FloatProperty(name="Max Rotation XZ", subtype='ANGLE', description="Maximum tilt in degrees", default=0.0, soft_min=0.0, soft_max=360.0, unit='ROTATION')
    enable_random_rotation_y: BoolProperty(name="Random Rotation Y", default=False, description="Randomly rotate the tree around the Y axis when placing")
    force_no_collision: BoolProperty(name="Force No Collision", default=False)
    impostor_all_planes_visible: BoolProperty(name="Impostor All Planes Visible", default=False)
    lod_dist_at_fov90: FloatProperty(name="Lod Distance At FOV 90", default=100.0, min=0.0)
    plane_compute_mode: EnumProperty(name="Plane Compute Mode", items=enum_items(EPlaneComputeMode), default=EPlaneComputeMode.Zero, description="How to compute the imposter planes for the tree model")
    
    enable_propagation: BoolProperty(name="Enable Propagation", default=False, description="Enable falling particles")
    propagation_base_color: PointerProperty(name="BaseColor", type=bpy.types.Material, poll=poll_asset("BITMAP"), description="Base color image for the propagation atlas")
    propagation_normal: PointerProperty(name="Normal", type=bpy.types.Material, poll=poll_asset("BITMAP"), description="Normal image for the propagation atlas")
    propagation_atlas_grid: IntVectorProperty(name="Atlas Grid", default=(1, 1), size=2, subtype='XYZ', soft_min=1, description="Number of cells in the propagation atlas")
    propagation_cone_half_angle_degree: FloatProperty(name="Cone Half Angle", subtype='ANGLE', description="Half angle of the propagation cone in degrees", default=45.0, soft_min=0.0, soft_max=180.0, unit='ROTATION')
    propagation_emission_positions: CollectionProperty(name="Emission Positions", type=PositionProperties, description="Emission positions for the propagation")
    propagation_emission_position_index: IntProperty(name="Emission Position Index", description="Index of the selected emission position", default=0)

    propagation_emission_spawn_radius: FloatProperty(name="Emission Spawn Radius", description="Radius within which emission positions are spawned", default=2.5, min=0.0)
    propagation_ground_gen_point_count: IntProperty(name="Ground Point Count", description="Number of ground generation points for the propagation", default=300, min=0)
    propagation_leaf_per_second: IntProperty(name="Leaves Per Second", description="Number of leaves emitted per second", default=20, min=0)
    propagation_leaf_size: FloatProperty(name="Leaf Size", description="Size of the leaves emitted", default=0.1, min=0.0)
    propagation_max_random_scale_reduction_per_instance: FloatProperty(name="Max Scale Reduction Per Instance", default=0.1, soft_min=0.0, description="Scale variation parameter 01")

    receive_pssm: BoolProperty(name="Receive PSSM", default=True, description="Whether the tree should receive PSSM shadows")

