from __future__ import annotations
import math
from mathutils import Euler

from dataclasses import dataclass, field, asdict, is_dataclass, fields
from enum import Enum, IntFlag
from typing import Any, Union, get_args, get_origin, get_type_hints

from ..properties.PropertyIdentifiers import CollectionProp


    
from ..properties.PlacementProperties import PlacementProperties
from ..utils.Functions import *
from ..utils.FunctionsV2 import copy_props, props_from_dict, props_to_dict
import types



# -----------------------------
# Flexible enum-like aliases
# -----------------------------
# In C#, these come from GBX.NET enums.
# Keep as str for now to avoid locking wrong value sets.
MaterialId = str
GameplayId = str
PlacementPatchGroup = str

class LegacyGameplayId(str, Enum):
    None_ = "None"
    Turbo = "Turbo"
    Turbo2 = "Turbo2"
    TurboRoulette = "TurboRoulette"
    FreeWheeling = "FreeWheeling"
    NoGrip = "NoGrip"
    NoSteering = "NoSteering"
    ForceAcceleration = "ForceAcceleration"
    Reset = "Reset"
    SlowMotion = "SlowMotion"
    Bumper = "Bumper"
    Bumper2 = "Bumper2"
    Boost1LegacyUp = "Boost1LegacyUp"
    Fragile = "Fragile"
    Boost2LegacyUp = "Boost2LegacyUp"
    NoBrakes = "NoBrakes"
    Cruise = "Cruise"
    ReactorBoost_Oriented = "ReactorBoost_Oriented"
    ReactorBoost2_Oriented = "ReactorBoost2_Oriented"
    VehicleTransform_Reset = "VehicleTransform_Reset"
    VehicleTransform_CarSnow = "VehicleTransform_CarSnow"
    VehicleTransform_CarRally = "VehicleTransform_CarRally"
    VehicleTransform_CarDesert = "VehicleTransform_CarDesert"

class AnimEase(str, Enum):
    Constant = "Constant"
    Linear = "Linear"
    QuadIn = "QuadIn"
    QuadOut = "QuadOut"
    QuadInOut = "QuadInOut"
    # for some reason the others are not supported even though they are in gbx-net?
    # CubicIn = "CubicIn"
    # CubicOut = "CubicOut"
    # CubicInOut = "CubicInOut"
    # QuartIn = "QuartIn"
    # QuartOut = "QuartOut"
    # QuartInOut = "QuartInOut"
    # QuintIn = "QuintIn"
    # QuintOut = "QuintOut"
    # QuintInOut = "QuintInOut"
    # SineIn = "SineIn"
    # SineOut = "SineOut"
    # SineInOut = "SineInOut"
    # ExpIn = "ExpIn"
    # ExpOut = "ExpOut"
    # ExpInOut = "ExpInOut"
    # CircIn = "CircIn"
    # CircOut = "CircOut"
    # CircInOut = "CircInOut"
    # BackIn = "BackIn"
    # BackOut = "BackOut"
    # BackInOut = "BackInOut"
    # ElasticIn = "ElasticIn"
    # ElasticOut = "ElasticOut"
    # ElasticInOut = "ElasticInOut"
    # ElasticIn2 = "ElasticIn2"
    # ElasticOut2 = "ElasticOut2"
    # ElasticInOut2 = "ElasticInOut2"
    # BounceIn = "BounceIn"
    # BounceOut = "BounceOut"
    # BounceInOut = "BounceInOut"



class EWaypointType(str, Enum):
    Start = "Start"
    Checkpoint = "Checkpoint"
    Finish = "Finish"
    StartFinish = "StartFinish"

class FillAlign(str, Enum):
    Center = "Center"
    Begin = "Begin"
    End = "End"

class FillDir(str, Enum):
    U = "U"
    V = "V"
    
FILL_ALIGN_MAP = {
    FillAlign.Begin: 'FRONT',
    FillAlign.Center: 'CENTER',
    FillAlign.End: 'BACK',
}
FILL_DIR_MAP = {
    FillDir.U: 'LEFT/RIGHT',
    FillDir.V: 'FRONT/BACK',
}


class EAxis(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


class LightType(int, Enum):
    Point = 0
    Spot = 1


class ItemConversionOptions(IntFlag):
    None_ = 0
    MeshConfigFromObjectNames = 1 << 0
    IgnoreMeshesWithInvalidMaterials = 1 << 1
    SkipStaticItemGrouping = 1 << 2, # todo later



class MeshFlags(IntFlag):
    None_ = 0
    NonCollidable = 1 << 0
    Invisible = 1 << 1
    Moving = 1 << 2
    TriggerEffect = 1 << 3
    TriggerWaypoint = 1 << 4
    Socket = 1 << 5
    SingleMesh = 1 << 6  # [ItemConfig.md](http://_vscodecontentref_/1) calls this "NoMerge"
    Skip = 1 << 7


@dataclass
class Vec3:
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0

    @staticmethod
    def from_string(value: str) -> "Vec3":
        x, y, z = value.strip().split()
        return Vec3(float(x), float(y), float(z))

    def to_string(self) -> str:
        return f"{self.X:.9g} {self.Y:.9g} {self.Z:.9g}"

    @staticmethod
    def from_seq(seq) -> "Vec3":
        x, y, z = seq
        return Vec3(float(x), float(y), float(z))
    
    def to_tuple(self) -> tuple:
        return (self.X, self.Y, self.Z)


@dataclass
class Quat:

    @staticmethod
    def from_euler(vec, degrees=True, order="XYZ") -> Quat:
        angles = [math.radians(a) for a in vec] if degrees else list(vec)
        q = Euler(angles, order).to_quaternion()      # mathutils order is (w, x, y, z)
        return Quat(q.x, q.y, q.z, q.w)
    
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0
    W: float = 1.0


@dataclass
class Color:
    # RGB hex expected by converter docs, e.g. #FFAABB
    Hex: str = "#000000"


@dataclass
class Waypoint:
    Type: EWaypointType = EWaypointType.Checkpoint
    NoRespawn: bool = False
    DefaultGravitySpawn: Vec3 | None = field(default_factory=lambda: Vec3(0.0, -1.0, 0.0))
    TorqueX: float | None = 0.0
    TorqueDuration: int | None = 0


@dataclass
class PlacementPatchLayout:
    ItemCount: int = 0
    ItemSpacing: float = 0.0
    FillDir: FillDir = FillDir.U
    FillAlign: FillAlign = FillAlign.Center
    NormedPos: float = 0.5
    FillOffsetU: float = 0.0
    FillOffsetV: float = 0.0
    OnlyOnGroups: list[PlacementPatchGroup] | None = field(default_factory=list)
    Altitude: float = 0.0


@dataclass
class PlacementClass:
    SizeGroup: str | None = "0x0"  # effect unknown
    CompatibleGroupsIds: list[PlacementPatchGroup] | None = field(default_factory=list)
    AlwaysUp: bool = False
    AlignToInterior: bool = False
    AlignToWorldDir: bool = False
    WorldDir: Vec3 | None = None
    PatchLayouts: list[PlacementPatchLayout] | None = field(default_factory=list)
    GroupCurPatchLayouts: list[int] | None = field(default_factory=list)


@dataclass
class PlacementConfig:
    YawOnly: bool = False
    NotOnObject: bool = False
    AutoRotation: bool = False
    SwitchPivotManually: bool = False
    CubeCenter: Vec3 | None = None
    CubeSize: float = 0.0
    GridSnapHStep: float = 0.0
    GridSnapVStep: float = 0.0
    GridSnapHOffset: float = 0.0
    GridSnapVOffset: float = 0.0
    FlyVStep: float = 0.0
    FlyVOffset: float = 0.0
    PivotSnapDistance: float = 0.0
    PivotPositions: list[Vec3] | None = field(default_factory=list)
    PivotRotations: list[Quat] | None = field(default_factory=list)
    PlacementClass: PlacementClass | None = None


@dataclass
class MaterialConfig:
    Name: str = ""
    Link: str = ""
    Color: Color | None = None
    PhysicsId: MaterialId | None = None
    GameplayId: GameplayId | None = None
    BaseTexture: str | None = None
    Model: str | None = None


@dataclass
class LodParameters:
    MaxLodDistances: list[float] = field(default_factory=list)


@dataclass
class MeshConfig:
    Name: str = ""
    MeshFlags: MeshFlags = MeshFlags.None_
    TriggerEffect: LegacyGameplayId | None = None
    WaypointType: EWaypointType | None = None
    GameplayMainDir: Vec3 | None = None
    MovingGroup: str | None = None
    LightmapSize: float | None = None
    Lods: list[int] = field(default_factory=list)


@dataclass
class LightConfig:
    Name: str = ""
    Type: LightType = LightType.Point
    Color: Color = field(default_factory=Color)
    Intensity: float = 0.0
    Distance: float = 0.0
    NightOnly: bool = False
    PointEmissionRadius: float = 0.0
    PointEmissionLength: float = 0.0
    SpotInnerAngle: float = 40.0
    SpotOuterAngle: float = 60.0
    SpotEmissionRadius: float = 0.0
    SpotEmissionLength: float = 0.0


@dataclass
class SubAnimFunc:
    Ease: AnimEase = AnimEase.Constant
    Reverse: bool = False
    Duration: int = 0  # milliseconds, uint in C#


@dataclass
class TextureAnim:
    Duration: int = 0  # milliseconds, uint in C#
    TextureID: int = 0


@dataclass
class MovingTextureConfig:
    SubTextures: int = 0
    SubTexturesPerLine: int = 0
    SubTexturePerColumn: int = 0
    TopToBottom: bool = False
    TextureAnims: list[TextureAnim] = field(default_factory=list)


@dataclass
class KinematicMovement:
    TransAxis: EAxis = EAxis.X
    TransMin: float = 0.0
    TransMax: float = 0.0
    RotAxis: EAxis = EAxis.X
    AngleMinDeg: float = 0.0
    AngleMaxDeg: float = 0.0
    TranslationAnims: list[SubAnimFunc] = field(default_factory=list)
    RotationAnims: list[SubAnimFunc] = field(default_factory=list)
    MovingTexture: MovingTextureConfig | None = None


@dataclass
class KinematicModelConfig:
    CastStaticShadow: bool = False
    IsKinematic: bool = True
    PeriodicSc: float = 1.0
    PeriodicScMax: float = -1.0
    Phase01: float = -1.0
    Phase01Max: float = -1.0
    TextureId: int = 0


@dataclass
class MovingGroupConfig:
    MovingGroupId: str = ""
    ParentMovingGroupId: str | None = None
    RotationAnchorNode: str | None = None
    KinematicMovement: KinematicMovement = field(default_factory=KinematicMovement)
    KinematicModel: KinematicModelConfig = field(default_factory=KinematicModelConfig)


@dataclass
class ItemConfig:
    Version: int = 1
    Type: str = "StaticObject"
    Collection: str = "Stadium"
    AuthorName: str = ""
    Name: str | None = None
    Description: str | None = None
    Waypoint: Waypoint | None = None
    Placement: PlacementConfig | None = None
    Scale: float = 1.0
    Materials: list[MaterialConfig] = field(default_factory=list)
    Meshes: list[MeshConfig] = field(default_factory=list)
    Lights: list[LightConfig] = field(default_factory=list)
    MovingGroups: list[MovingGroupConfig] = field(default_factory=list)
    LodParameters: LodParameters | None = None
    ConversionOptions: ItemConversionOptions = ItemConversionOptions.None_



class ExportedItem:
    name:           str = ""
    name_raw:       str = ""
    r_path:         str = ""   # relative path, no extension
    item_path:      str = ""
    icon_path:      str = ""
    fbx_path:       str = ""
    material_lib_path: str = ""
    objects:        list[bpy.types.Object] = field(default_factory=list)
    collection:     bpy.types.Collection | None = None
    config:         "ItemConfig | None" = None
    game:           str = ""
    is_single_item: bool = False
    assigned_index: int = -1
    scale:          int  = 1

# -----------------------------
# JSON-ready conversion helpers
# -----------------------------
def _encode(value: Any) -> Any:
    if isinstance(value, Vec3):
        return value.to_string()
    if is_dataclass(value) and not isinstance(value, type):
        # shallow field walk, so nested Vec3/enums reach _encode themselves
        return {f.name: _encode(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, IntFlag):
        if type(value) is MeshFlags:
            if value == MeshFlags.None_:
                return "None"
            names = [flag.name for flag in MeshFlags if flag != MeshFlags.None_ and (value & flag)]
            return ", ".join(names)
        return int(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    return value


def _drop_nones(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _drop_nones(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_drop_nones(v) for v in obj]
    return obj


def item_config_to_dict(item: ItemConfig, drop_none: bool = True) -> dict[str, Any]:
    data = _encode(item)

    # Match docs: omit these sections when not configured.
    if item.Waypoint is None:
        data.pop("Waypoint", None)
    if item.Placement is None:
        data.pop("Placement", None)
    if item.LodParameters is None:
        data.pop("LodParameters", None)

    return _drop_nones(data) if drop_none else data


def _is_optional(tp: Any) -> bool:
    return (
        get_origin(tp) in (Union, types.UnionType)
        and type(None) in get_args(tp)
    )


def _decode_mesh_flags(value: Any) -> MeshFlags:
    if isinstance(value, int):  # tolerate raw ints
        return MeshFlags(value)
    if value in ("None", ""):
        return MeshFlags.None_
    result = MeshFlags.None_
    for name in value.split(", "):
        result |= MeshFlags[name.strip()]
    return result


def _decode(tp: Any, value: Any, exact_nones: bool = False) -> Any:
    if value is None or tp is Any:
        return value

    origin = get_origin(tp)
    args = get_args(tp)

    if origin in (Union, types.UnionType):
        for arg in args:
            if arg is type(None):
                continue
            try:
                return _decode(arg, value, exact_nones)
            except (TypeError, ValueError, KeyError, AttributeError):
                continue
        raise ValueError(f"Cannot decode {value!r} as {tp}")

    if origin in (list, set, frozenset):
        item_tp = args[0] if args else Any
        return origin(_decode(item_tp, v, exact_nones) for v in value)
    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode(args[0], v, exact_nones) for v in value)
        return tuple(_decode(t, v, exact_nones) for t, v in zip(args, value))
    if origin is dict:
        key_tp, val_tp = args if args else (Any, Any)
        return {
            _decode(key_tp, k, exact_nones): _decode(val_tp, v, exact_nones)
            for k, v in value.items()
        }

    if isinstance(tp, type):
        if tp is Vec3:  # before generic dataclass
            if isinstance(value, str):
                return Vec3.from_string(value)
            if isinstance(value, dict):  # tolerate {"X":..,"Y":..,"Z":..}
                return Vec3(float(value.get("X", 0.0)),
                            float(value.get("Y", 0.0)),
                            float(value.get("Z", 0.0)))
            if isinstance(value, (list, tuple)):
                return Vec3.from_seq(value)
            raise ValueError(f"Cannot decode {value!r} as Vec3")
        if is_dataclass(tp):
            hints = get_type_hints(tp)
            kwargs = {}
            for f in fields(tp):
                if not f.init:
                    continue
                if f.name in value:
                    kwargs[f.name] = _decode(hints[f.name], value[f.name], exact_nones)
                elif exact_nones and _is_optional(hints[f.name]):
                    kwargs[f.name] = None  # was dropped by _drop_nones
            return tp(**kwargs)
        if tp is MeshFlags:  # before generic IntFlag
            return _decode_mesh_flags(value)
        if issubclass(tp, IntFlag):  # before generic Enum
            return tp(int(value))
        if issubclass(tp, Enum):
            return tp(value)

    return value


def item_config_from_dict(data: dict[str, Any], exact_nones: bool = False) -> ItemConfig:
    return _decode(ItemConfig, data, exact_nones)

def add_or_update_itemconfig_placement_template(name: str, placement: PlacementProperties) -> None:
    templates = bpy.context.scene.tm_props_cfg_placement_templates
    template = templates.get(name) or templates.add()
    template.name = name
    copy_props(placement, template.config)

def remove_itemconfig_placement_template(template_name: str) -> None:
    templates = bpy.context.scene.tm_props_cfg_placement_templates

    for i, template in enumerate(templates):
        if template.name == template_name:
            templates.remove(i)
            break

def load_itemconfig_placement_template(placement: PlacementProperties, template_name: str) -> None:
    if placement is None:
        return
    cfg = get_item_placement_template(template_name)
    if cfg is None:
        return
    copy_props(cfg, placement)
  

def get_placement_config_from_properties(placement_props: PlacementProperties) -> PlacementConfig:
    
    pivots = placement_props.LI_pivots

    use_simple_ui       = placement_props.LI_simpleOrAdvanced.upper() == "SIMPLE"
    
    placement = PlacementConfig()
    placement.GridSnapHStep = float(placement_props.NU_gridX if not use_simple_ui else placement_props.LI_simpleGridXY)
    placement.GridSnapVStep = float(placement_props.NU_gridY if not use_simple_ui else placement_props.LI_simpleGridZ)
    placement.FlyVStep = float(placement_props.NU_leviY if not use_simple_ui else placement_props.LI_simpleGridZ)
    placement.AutoRotation = bool(placement_props.CB_autoRot)
    placement.NotOnObject = bool(placement_props.CB_notOnItem)

    if(use_simple_ui):
        return placement # early out, other properties cannot be configured in simple mode
    
    placement.YawOnly = bool(placement_props.CB_oneAxisRot)
    placement.SwitchPivotManually = bool(placement_props.CB_pivotSwitch)
    placement.GridSnapHOffset = float(placement_props.NU_gridXoffset)
    placement.GridSnapVOffset = float(placement_props.NU_gridYoffset)
    placement.FlyVOffset = float(placement_props.NU_leviXoffset)
    placement.PivotSnapDistance = float(placement_props.NU_pivotSnapDis)
    placement.CubeSize = float(placement_props.NU_cubeSize)
    placement.CubeCenter = Vec3.from_seq(placement_props.PT_cubeCenter)

    placement.PivotPositions = [
        Vec3.from_seq(p.FV_position)
        for p in pivots
    ]
    placement.PivotRotations = [
        Quat.from_euler(p.FV_rotation, degrees=False, order="XYZ")
        for p in pivots
    ]

    if bool(placement_props.CB_attachmentConfiguration):
        placement.PlacementClass = PlacementClass()
        placement.PlacementClass.SizeGroup = str(placement_props.ST_sizeGroup)
        placement.PlacementClass.AlwaysUp = bool(placement_props.CB_alwaysUp)
        placement.PlacementClass.AlignToInterior = bool(placement_props.CB_alignToInterior)
        placement.PlacementClass.AlignToWorldDir = bool(placement_props.CB_alignToWorldDir)
        world_dir = placement_props.PT_worldDir
        placement.PlacementClass.WorldDir = Vec3.from_seq(world_dir)
        placement.PlacementClass.CompatibleGroupsIds = [
                str(g.name) 
                for g in placement_props.LI_compatibleGroups
            ]
        placement.PlacementClass.PatchLayouts = []
        for plp in placement_props.LI_patchLayouts:
            patchLayout = PlacementPatchLayout()
            patchLayout.ItemCount = int(plp.itemCount) if not plp.autoItemCount else 0
            patchLayout.ItemSpacing = float(plp.itemSpacing)
            patchLayout.FillDir = {"LEFT/RIGHT": 0, "FRONT/BACK": 1}.get(plp.fillDirection, 0)
            patchLayout.FillAlign = {"FRONT": 1, "CENTER": 0, "BACK": 2}.get(plp.fillAlignment, 0)
            patchLayout.FillOffsetU = float(plp.fillOffsetU)
            patchLayout.FillOffsetV = float(plp.fillOffsetV)
            patchLayout.NormedPos = float(plp.normedPos)
            patchLayout.Altitude = float(plp.altitude)
            patchLayout.OnlyOnGroups = [g.name for g in plp.validForGroups]

            placement.PlacementClass.PatchLayouts.append(patchLayout)

    return placement

def generate_placement_config(collection: bpy.types.Collection) -> PlacementConfig:
    tm_props        = get_global_props()

    force_export_override = tm_props.CB_cfg_ignore_assigned_templates

    collection_cfg = getattr(collection,CollectionProp.CONFIG)
    placement_ref = collection_cfg.placement

    if force_export_override or placement_ref.mode == "INHERIT":
        export_cfg = tm_props.PT_cfg_export_config
        placement_ref = export_cfg.placement

    placement = placement_ref.placement
    if placement_ref.mode == "TEMPLATE":
        selected_template = placement_ref.template
        template_placement = get_item_placement_template(selected_template)
        placement = template_placement if template_placement is not None else placement

    return get_placement_config_from_properties(placement)

TEMPLATE_SOURCE_BLEND = 'BLEND'
TEMPLATE_SOURCE_LOCAL = 'LOCAL'
LOCAL_TEMPLATE_SUFFIX = " (local)"

def list_placement_templates() -> list[tuple[str, str, Any]]:
    """All selectable placement templates as (id, source, template).
    Blend-embedded templates (scene) keep their plain name; local ones (window manager, loaded from settings.json)
    are skipped when identical to the blend one and get a ' (local)' suffix when their content differs."""
    result = []
    blend_by_name = {}
    for t in bpy.context.scene.tm_props_cfg_placement_templates:
        result.append((t.name, TEMPLATE_SOURCE_BLEND, t))
        blend_by_name[t.name] = t

    for t in bpy.context.window_manager.tm_local_placement_templates:
        blend_t = blend_by_name.get(t.name)
        if blend_t is None:
            result.append((t.name, TEMPLATE_SOURCE_LOCAL, t))
        elif props_to_dict(blend_t.config) != props_to_dict(t.config):
            result.append((t.name + LOCAL_TEMPLATE_SUFFIX, TEMPLATE_SOURCE_LOCAL, t))
    return result

def find_placement_template(template_id: str):
    """(source, template) for a template id from list_placement_templates(), or (None, None)"""
    for tid, source, template in list_placement_templates():
        if tid == template_id:
            return source, template
    return None, None

def get_item_placement_template(name: str) -> PlacementProperties | None:
    _, template = find_placement_template(name)
    return template.config if template is not None else None

def embed_local_placement_templates() -> None:
    """copy local templates missing in the blend file into it (run before saving); existing blend templates are kept"""
    templates = bpy.context.scene.tm_props_cfg_placement_templates
    for local in bpy.context.window_manager.tm_local_placement_templates:
        if local.name in templates:
            continue
        props_from_dict(templates.add(), props_to_dict(local))


