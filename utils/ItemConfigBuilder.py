"""
Builds the ItemConfig (the json the converter reads) of an exported item.

generate_item_config() is the only entry point, everything below is split by what it builds:
    item level      waypoint, lods, scale, placement
    placement       pivots / magnets (also inside instanced collections)
    meshes, lights, materials, instances, moving groups
Variants: meshes, lights, instances and attachments get the Variant name of the variant collection they live in
(see utils/Variants.py), None means shared by every variant.
"""
from __future__ import annotations

import math
import re

import bpy
from mathutils import Matrix, Quaternion, Vector

from . import Constants
from .Attachments import get_attachment_configs
from .FunctionsV2 import *
from .ItemsExportV2Models import *
from .Variants import VariantResolver, get_variant_configs
from ..properties.PropertyIdentifiers import CollectionProp, LightProp, ObjectProp


# -----------------------------
# entry point
# -----------------------------
def generate_item_config(item: ExportedItem) -> ItemConfig:
    cfg = ItemConfig()
    tm_props = get_global_props()

    collection = item.collection
    variants = VariantResolver(collection)

    cfg.AuthorName = tm_props.ST_author or "blendermania"
    cfg.Collection = tm_props.LI_materialCollection if getattr(tm_props, "LI_materialCollection", None) else cfg.Collection
    cfg.Name = collection.name
    cfg.Description = collection.get("description", "N/A")
    cfg.LodParameters = _get_lod_parameters(collection)
    cfg.Waypoint = _get_waypoint(collection)
    cfg.Placement = generate_placement_config(collection)
    instanced = _get_instanced_objects_with_world(item.objects)   # (object, world matrix) per instance occurrence
    _add_pivots_to_placement(cfg.Placement, item.objects, instanced)
    _add_magnets_to_placement(cfg.Placement, item.objects, instanced)
    cfg.Attachments = get_attachment_configs(collection, item.objects, variants)
    cfg.Variants = get_variant_configs(collection)
    cfg.Scale = item.scale
    # objects living in instanced collections share the flat Materials/Lights/Meshes lists (object names are unique in blender)
    all_objs = list(item.objects) + get_instanced_template_objects(item.objects)
    cfg.Materials = _get_material_configs(all_objs)
    cfg.Lights = _get_light_configs(all_objs, variants)
    cfg.Meshes = _get_mesh_configs(all_objs, collection, variants)
    cfg.Instances = _get_instance_configs(item.objects, variants)
    cfg.InstanceCollections = _get_instance_collection_configs(item.objects)
    cfg.MovingGroups = _get_moving_group_configs(collection, get_instanced_collections(item.objects))
    _apply_plan_lightmap_overrides(cfg.Meshes, collection)
    cfg.ScaleOptions = _get_scale_config(collection)

    cfg.DisableAutoCreateSound = getattr(collection, CollectionProp.DISABLE_AUTO_CREATE_SOUND, False)

    return cfg


# -----------------------------
# item level
# -----------------------------
def _get_lod_parameters(collection: bpy.types.Collection) -> LodParameters | None:
    distances = [float(lod.distance) for lod in getattr(collection, CollectionProp.LODS, [])]
    if not distances:
        return None
    return LodParameters(MaxLodDistances=distances)

def _get_waypoint_type(collection: bpy.types.Collection) -> EWaypointType | None:
    match getattr(collection, CollectionProp.WAYPOINT_TYPE, None):
        case Constants.WAYPOINT_NAME_CHECKPOINT:
            return EWaypointType.Checkpoint
        case Constants.WAYPOINT_NAME_START:
            return EWaypointType.Start
        case Constants.WAYPOINT_NAME_FINISH:
            return EWaypointType.Finish
        case Constants.WAYPOINT_NAME_STARTFINISH:
            return EWaypointType.StartFinish
        case _:
            return None

def _get_waypoint(collection: bpy.types.Collection) -> Waypoint | None:
    waypoint_type = _get_waypoint_type(collection)
    if not waypoint_type:
        return None

    wp = Waypoint()
    wp.Type = waypoint_type
    wp.NoRespawn = getattr(collection, CollectionProp.NO_RESPAWN, False)
    wp.TorqueX = getattr(collection, CollectionProp.TORQUE_X)
    wp.TorqueDuration = getattr(collection, CollectionProp.TORQUE_DURATION)
    wp.DefaultGravitySpawn = Vec3.from_seq(getattr(collection, CollectionProp.DEFAULT_GRAVITY_SPAWN))
    return wp

def _get_scale_config(collection: bpy.types.Collection) -> ScaleConfig | None:
    if getattr(collection, CollectionProp.SCALE_ITEM, False) is False:
        return None
    return ScaleConfig(
        ScaleAnimationDistance=getattr(collection, CollectionProp.SCALE_ANIMATION_DISTANCE, True),
        ScaleAnimationTime=getattr(collection, CollectionProp.SCALE_ANIMATION_TIME, False),
        ScalePivots=getattr(collection, CollectionProp.SCALE_PIVOTS, True),
        ScaleMagnets=getattr(collection, CollectionProp.SCALE_MAGNETS, True),
        ScaleLightRadius=getattr(collection, CollectionProp.SCALE_LIGHT_DISTANCE, True),
        ScaleLightmapSizeOverrides=getattr(collection, CollectionProp.SCALE_LIGHTMAP_SIZE, True),
    )

def _apply_plan_lightmap_overrides(meshes: list[MeshConfig], collection: bpy.types.Collection) -> None:
    """
    Lightmap size overrides set on the groups of the analyzed plan win over the object overrides.
    Nodes are mapped to their source object through original_node. Meshes of instanced collections
    are shared by all instances, so the last overriding group wins for those.
    """
    plan = getattr(collection, CollectionProp.ANALYZED_FBXGBX_PLAN, None)
    if plan is None or not plan.is_valid:
        return
    by_name = {m.Name: m for m in meshes}
    for group in plan.groups:
        if not group.override_lightmap_size:
            continue
        for node in group.nodes:
            mesh = by_name.get(node.original_node or node.name)
            if mesh is not None:
                mesh.LightmapSize = group.lightmap_size


# -----------------------------
# instances
# -----------------------------
def _get_instance_configs(objs, variants: VariantResolver) -> list[InstanceConfig]:
    """flat list of all instancing empties: the ones of the item and the nested ones inside instanced collections"""
    empties: dict[str, bpy.types.Object] = {o.name: o for o in objs if is_collection_instance(o)}
    for col in get_instanced_collections(objs):
        for o in col.all_objects:
            if is_collection_instance(o):
                empties.setdefault(o.name, o)

    configs = []
    for name in sorted(empties):
        empty = empties[name]
        moving_group = get_object_moving_group(empty)
        lods = []
        if getattr(empty, ObjectProp.ENABLE_LODS, False):
            lods = [int(lod.value) for lod in getattr(empty, ObjectProp.LOD_INDEXES, [])]
        configs.append(InstanceConfig(
            Name=name,
            Collection=empty.instance_collection.name,
            MovingGroup=moving_group.name if moving_group else None,
            Lods=lods,
            Variant=variants.of_object(empty),
        ))
    return configs

def _get_instance_collection_configs(objs) -> list[InstanceCollectionConfig]:
    """one entry per instanced collection (nested ones included), however often it is instanced"""
    return [
        InstanceCollectionConfig(
            Name=col.name,
            Meshes=sorted(o.name for o in col.all_objects if o.type == EXPORTABLE_OBJECT_MESH),
            Lights=sorted(o.name for o in col.all_objects if o.type == EXPORTABLE_OBJECT_LIGHT),
            Instances=sorted(o.name for o in col.all_objects if is_collection_instance(o)),
        )
        for col in get_instanced_collections(objs)
    ]

def _get_instanced_objects_with_world(objs) -> list[tuple[bpy.types.Object, Matrix]]:
    """
    (object, world matrix) of every object inside instanced collections, once per instance occurrence,
    nested instances included. Matrices are rebuilt from local values (see fresh_world_matrix).
    """
    result = []
    for inst in sorted((o for o in objs if is_collection_instance(o)), key=lambda o: o.name):
        result += _walk_instance(inst, fresh_world_matrix(inst), ())
    return result

def _walk_instance(inst: bpy.types.Object, inst_world: Matrix, stack: tuple) -> list[tuple[bpy.types.Object, Matrix]]:
    col = inst.instance_collection
    if col.name in stack:   # instance cycle
        return []
    to_world = inst_world @ Matrix.Translation(-Vector(col.instance_offset))
    result = []
    for o in col.all_objects:
        world = to_world @ fresh_world_matrix(o)
        if is_collection_instance(o):
            result += _walk_instance(o, world, stack + (col.name,))
        else:
            result.append((o, world))
    return result


# -----------------------------
# placement: pivots and magnets
# -----------------------------
def _collect_marked_objects(objs, instanced, prop: str) -> list[tuple[bpy.types.Object, Matrix, bool]]:
    """(object, world matrix, is_instanced) of all objects with the given flag set, direct ones first"""
    marked = [(o, fresh_world_matrix(o), False) for o in objs
              if getattr(o, prop, False) and not getattr(o, ObjectProp.IGNORE, False)]
    marked += [(o, w, True) for o, w in instanced
               if getattr(o, prop, False) and not getattr(o, ObjectProp.IGNORE, False)]
    return marked

def _add_pivots_to_placement(placement: PlacementConfig, objs: list[bpy.types.Object], instanced=()) -> None:
    """append all objects marked as pivot (also inside instanced collections) to the placement pivots (position relative to the item origin)"""
    pivots = _collect_marked_objects(objs, instanced, ObjectProp.PIVOT)
    if not pivots:
        return

    offset = get_offset_from_item_origin(objs) or [0.0, 0.0, 0.0]

    if placement.PivotPositions is None:
        placement.PivotPositions = []
    if placement.PivotRotations is None:
        placement.PivotRotations = []

    # keep rotations aligned with positions
    while len(placement.PivotRotations) < len(placement.PivotPositions):
        placement.PivotRotations.append(Quaternion())

    for _obj, world, _ in pivots:
        # matrix_world can be stale here: the export moved the objects by the origin offset and back again
        # without a depsgraph update, so the offset would be subtracted twice. world is rebuilt from the current local values.
        loc = world.translation
        placement.PivotPositions.append(Vec3(loc.x - offset[0], loc.y - offset[1], loc.z - offset[2]))
        placement.PivotRotations.append(world.to_euler('XYZ').to_quaternion())

def _add_magnets_to_placement(placement: PlacementConfig, objs: list[bpy.types.Object], instanced=()) -> None:
    """append all objects marked as magnet (also inside instanced collections) to the placement magnets (position relative to the item origin)"""
    magnets = _collect_marked_objects(objs, instanced, ObjectProp.MAGNET)
    if not magnets:
        return

    offset = get_offset_from_item_origin(objs) or [0.0, 0.0, 0.0]

    if placement.MagnetPositions is None:
        placement.MagnetPositions = []
    if placement.MagnetRotations is None:
        placement.MagnetRotations = []

    # keep rotations aligned with positions
    while len(placement.MagnetRotations) < len(placement.MagnetPositions):
        placement.MagnetRotations.append(Vec3())

    for obj, world, is_instanced in magnets:
        loc = world.translation
        placement.MagnetPositions.append(Vec3(loc.x - offset[0], loc.y - offset[1], loc.z - offset[2]))
        rot = world.to_euler('XYZ') if is_instanced else obj.rotation_euler
        placement.MagnetRotations.append(Vec3.from_seq([math.degrees(v) for v in rot]))


# -----------------------------
# lights
# -----------------------------
def _get_light_configs(objs: list[bpy.types.Object], variants: VariantResolver) -> list[LightConfig]:
    light_configs = []

    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_LIGHT:
            continue

        light: bpy.types.Light = obj.data
        light_is_spot = light.type == LIGHT_TYPE_SPOT
        light_is_point = light.type == LIGHT_TYPE_POINT

        if not (light_is_spot or light_is_point):
            continue

        light_cfg = LightConfig()

        light_cfg.Name = obj.name
        light_cfg.Type = light.type
        light_cfg.Variant = variants.of_object(obj)

        light_cfg.Color = f"{int(light.color[0]*255):02x}{int(light.color[1]*255):02x}{int(light.color[2]*255):02x}"
        light_cfg.Intensity = light.energy
        light_cfg.NightOnly = getattr(light, LightProp.LIGHT_NIGHT_ONLY, False)
        light_cfg.Distance = light.shadow_soft_size

        light_cfg.PointEmissionRadius = getattr(light, LightProp.LIGHT_EMITTING_RADIUS, 0)
        light_cfg.PointEmissionLength = getattr(light, LightProp.LIGHT_EMITTING_LENGTH, 0)
        light_cfg.SpotEmissionRadius = getattr(light, LightProp.LIGHT_EMITTING_RADIUS, 0)
        light_cfg.SpotEmissionLength = getattr(light, LightProp.LIGHT_EMITTING_LENGTH, 0)

        spot_size_degree = math.degrees(light.spot_size) if light_is_spot else 0.0
        light_cfg.SpotInnerAngle = spot_size_degree * getattr(light, "spot_blend", 0)
        light_cfg.SpotOuterAngle = spot_size_degree

        if getattr(light, LightProp.LIGHT_CONFIG_TYPE, False) == "ADVANCED":
            light_cfg.Advanced = AdvancedLightConfig(
                LightingEnabled=getattr(light, LightProp.LIGHT_ENABLED, True),
                SpecularEnabled=getattr(light, LightProp.LIGHT_ENABLE_SPECULAR, True),
                CastShadows=getattr(light, "use_shadow", True),
                AttenuationTension=getattr(light, LightProp.LIGHT_ATTENUATION_TENSION, 0.3),
                AttenuationDerivativeAtZero=getattr(light, LightProp.LIGHT_ATTENUATION_DERIVATIVE_AT_ZERO, -1.5),
                AttenuationHdrRadiusCoefficient=getattr(light, LightProp.LIGHT_ATTENUATION_HDR_RADIUS_COEFF, 0.015625),
            )
            if getattr(light, LightProp.LIGHT_INVERTED, False):
                light_cfg.Intensity *= -1.0

        light_configs.append(light_cfg)

    return light_configs


# -----------------------------
# materials
# -----------------------------
def _get_material_configs(objs: list[bpy.types.Object]) -> list[MaterialConfig]:
    material_configs = []

    materials = set()
    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_MESH:
            continue
        for mat_slot in obj.material_slots:
            materials.add(mat_slot.material)

    for mat in materials:
        if mat is None:
            continue
        mat_game_is_tm2020      = mat.gameType.lower() == "trackmania2020"
        mat_game_is_maniaplanet = mat.gameType.lower() == "maniaplanet"
        mat_physic_id           = mat.physicsId
        mat_use_physicid        = mat.usePhysicsId and mat_physic_id # can be empty
        mat_link                = mat.link
        mat_basetexture         = fix_slash(mat.baseTexture)
        mat_basetexture         = re.sub(r"(?i)items/(?:_+|\-+)", r"Items/", mat_basetexture)
        mat_color               = mat.diffuse_color     # extract diffuse collor by default

        if mat.use_nodes: # replace with BSDF color
            if "cus_color" in mat.node_tree.nodes:
                mat_color = mat.node_tree.nodes["cus_color"].outputs[0].default_value
            else:
                mat_color = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

        mat_custom_color     = rgb_to_hex(mat_color, "", True) # convert to Hex with gamma correction
        mat_use_custom_color = mat_color[3] > 0                # use custom color only if material color has Alpha > 0

        # maniaplanet related (external texture in Maniaplanet/Items/blabla_D.dds)
        if mat_basetexture:
            mat_basetexture = fix_slash(mat_basetexture)
            mat_basetexture = re.sub(r".*/Items/|_?(D|N|S|I)\.dds", "", mat_basetexture, flags=re.IGNORECASE)
            mat_basetexture = "/Items/" + mat_basetexture
        else:
            mat_basetexture = mat_link

        mat_config = MaterialConfig()
        mat_config.Name = mat.name

        if mat_game_is_tm2020:
            if mat.isLibraryMaterial: # new materiallib flow: explicit "use color" checkbox
                use_custom_color_attr = mat.useColor
            else:                     # legacy flow
                use_custom_color_attr = mat_use_custom_color and mat_link.lower().startswith("custom")
            mat_config.Link = mat_link
            if use_custom_color_attr:
                mat_config.Color = mat_custom_color
            if mat_use_physicid:
                mat_config.PhysicsId = mat_physic_id
            if mat.useGameplayId:
                mat_config.GameplayId = mat.gameplayId
        elif mat_game_is_maniaplanet:
            mat_config.Model = mat.model
            mat_config.BaseTexture = mat_basetexture
            mat_config.PhysicsId = mat_physic_id

        material_configs.append(mat_config)

    return material_configs


# -----------------------------
# meshes
# -----------------------------
def _get_mesh_flags(obj: bpy.types.Object) -> MeshFlags:
    flags = MeshFlags.None_
    for prop, flag in (
        (ObjectProp.NON_COLLIDABLE,   MeshFlags.NonCollidable),
        (ObjectProp.INVISIBLE,        MeshFlags.Invisible),
        (ObjectProp.TRIGGER_WAYPOINT, MeshFlags.TriggerWaypoint),
        (ObjectProp.TRIGGER_EFFECT,   MeshFlags.TriggerEffect),
        (ObjectProp.SOCKET,           MeshFlags.Socket),
        (ObjectProp.NO_MERGE,         MeshFlags.SingleMesh),
    ):
        if getattr(obj, prop, False):
            flags |= flag
    return flags

def _get_mesh_configs(objs: list[bpy.types.Object], collection: bpy.types.Collection, variants: VariantResolver) -> list[MeshConfig]:
    mesh_configs = []

    for obj in objs:
        if obj.type != EXPORTABLE_OBJECT_MESH:
            continue

        mesh_cfg = MeshConfig()
        mesh_cfg.Name = obj.name
        mesh_cfg.Variant = variants.of_object(obj)

        mesh_flags = _get_mesh_flags(obj)

        gameplay_dir = Vector(getattr(obj, ObjectProp.GAMEPLAY_MAIN_DIR, None))
        gameplay_dir.normalize()
        gameplay_strength = getattr(obj, ObjectProp.GAMEPLAY_STRENGTH, 1.0)
        mesh_cfg.GameplayMainDir = Vec3.from_seq(gameplay_dir * gameplay_strength)

        if mesh_flags & MeshFlags.TriggerWaypoint:
            mesh_cfg.WaypointType = _get_waypoint_type(collection)
        if mesh_flags & MeshFlags.TriggerEffect:
            mesh_cfg.TriggerEffect = getattr(obj, ObjectProp.TRIGGER_EFFECT_TYPE, None)

        if getattr(obj, ObjectProp.ENABLE_LODS, False):
            mesh_cfg.Lods = [int(lod.value) for lod in getattr(obj, ObjectProp.LOD_INDEXES, [])]

        if getattr(obj, ObjectProp.OVERRIDE_LIGHTMAP_SIZE, False):
            mesh_cfg.LightmapSize = getattr(obj, ObjectProp.LIGHTMAP_SIZE, None)

        moving_group = get_object_moving_group(obj)
        if moving_group is not None:
            mesh_cfg.MovingGroup = moving_group.name
            mesh_flags |= MeshFlags.Moving

        mesh_cfg.MeshFlags = mesh_flags
        mesh_configs.append(mesh_cfg)

    return mesh_configs


# -----------------------------
# moving groups
# -----------------------------
def _get_sub_anims(anims) -> list[SubAnimFunc]:
    return [SubAnimFunc(Ease=AnimEase(p.ease), Reverse=bool(p.reverse), Duration=max(0, p.duration)) for p in anims]

def _get_moving_group_config(col: bpy.types.Collection) -> MovingGroupConfig:
    cfg = MovingGroupConfig()
    cfg.MovingGroupId = col.name
    relative_moving_group = getattr(col, CollectionProp.RELATIVE_MOVING_GROUP, None)
    if relative_moving_group:
        cfg.ParentMovingGroupId = relative_moving_group.name
    anchor = getattr(col, CollectionProp.MOVING_ANCHOR, None)
    if anchor:
        cfg.RotationAnchorNode = anchor.name

    cfg.KinematicModel = KinematicModelConfig(
        CastStaticShadow=getattr(col, CollectionProp.KINEMATIC_CAST_SHADOW),
        IsKinematic=getattr(col, CollectionProp.KINEMATIC_IS_KINEMATIC),
        PeriodicSc=getattr(col, CollectionProp.KINEMATIC_PERIODIC_SC),
        PeriodicScMax=getattr(col, CollectionProp.KINEMATIC_PERIODIC_SC_MAX),
        Phase01=getattr(col, CollectionProp.KINEMATIC_PHASE_01),
        Phase01Max=getattr(col, CollectionProp.KINEMATIC_PHASE_01_MAX),
        TextureId=getattr(col, CollectionProp.KINEMATIC_TEXTURE_ID),
    )

    movement = KinematicMovement(
        TransAxis=getattr(col, CollectionProp.KINEMATIC_TRANS_AXIS),
        TransMin=getattr(col, CollectionProp.KINEMATIC_TRANS_MIN),
        TransMax=getattr(col, CollectionProp.KINEMATIC_TRANS_MAX),
        RotAxis=getattr(col, CollectionProp.KINEMATIC_ROT_AXIS),
        AngleMinDeg=math.degrees(getattr(col, CollectionProp.KINEMATIC_ROT_MIN)),
        AngleMaxDeg=math.degrees(getattr(col, CollectionProp.KINEMATIC_ROT_MAX)),
        TranslationAnims=_get_sub_anims(getattr(col, CollectionProp.KINEMATIC_TRANS_ANIMS)),
        RotationAnims=_get_sub_anims(getattr(col, CollectionProp.KINEMATIC_ROT_ANIMS)),
    )
    if getattr(col, CollectionProp.KINEMATIC_HAS_MOVING_TEXTURE):
        movement.MovingTexture = MovingTextureConfig(
            SubTextures=getattr(col, CollectionProp.KINEMATIC_MOVING_TEXTURE_NUM),
            SubTexturesPerLine=getattr(col, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_LINE),
            SubTexturePerColumn=getattr(col, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_COLUMN),
            TopToBottom=getattr(col, CollectionProp.KINEMATIC_MOVING_TEXTURE_TOP_TO_BOTTOM),
            TextureAnims=[
                TextureAnim(TextureID=int(p.textureIndex), Duration=int(p.duration))
                for p in getattr(col, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS)
            ],
        )
    cfg.KinematicMovement = movement
    return cfg

def _get_moving_group_configs(collection: bpy.types.Collection, instanced_collections=()) -> list[MovingGroupConfig]:
    groups = get_item_moving_groups(collection)
    known = {c.name for c in groups}
    groups += [c for c in get_instanced_moving_groups(list(instanced_collections)) if c.name not in known]
    return [_get_moving_group_config(col) for col in groups if is_moving_group_collection(col)]
