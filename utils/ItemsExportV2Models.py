from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from enum import Enum, IntFlag
from typing import Any


# -----------------------------
# Flexible enum-like aliases
# -----------------------------
# In C#, these come from GBX.NET enums.
# Keep as str for now to avoid locking wrong value sets.
MaterialId = str
GameplayId = str
LegacyGameplayId = str
PlacementPatchGroup = str
AnimEase = str


class EWaypointType(str, Enum):
    Start = "Start"
    Checkpoint = "Checkpoint"
    Finish = "Finish"
    StartFinish = "StartFinish"


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
        return f"{self.X} {self.Y} {self.Z}"


@dataclass
class Quat:
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
    FillAlign: int = 0
    FillDir: int = 1
    NormedPos: float = 0.5
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
    AnchorNodeName: str | None = None
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
    SpotEmissionSizeX: float = 0.0
    SpotEmissionSizeY: float = 0.0


@dataclass
class SubAnimFunc:
    Ease: AnimEase = "Linear"
    Reverse: bool = False
    Duration: int = 0  # milliseconds, uint in C#


@dataclass
class TextureAnim:
    Duration: int = 0  # milliseconds, uint in C#
    TextureID: int = 0


@dataclass
class MovingTextureConfig:
    NbSubTexture: int = 0
    NbSubTexturePerLine: int = 0
    NbSubTexturePerColumn: int = 0
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
    AnchorPosition: Vec3 | None = None
    KinematicMovement: KinematicMovement = field(default_factory=KinematicMovement)
    KinematicModelConfig: KinematicModelConfig = field(default_factory=KinematicModelConfig)


@dataclass
class ItemConfig:
    Type: str = "StaticObject"
    Collection: str = "Stadium"
    AuthorName: str = ""
    Name: str | None = None
    Description: str | None = None
    Waypoint: Waypoint | None = None
    PlacementParams: PlacementConfig | None = None
    Scale: float = 1.0
    MaterialConfiguration: list[MaterialConfig] = field(default_factory=list)
    MeshConfiguration: list[MeshConfig] = field(default_factory=list)
    Lights: list[LightConfig] = field(default_factory=list)
    MovingGroups: list[MovingGroupConfig] = field(default_factory=list)
    LodParameters: LodParameters | None = None
    ConversionOptions: ItemConversionOptions = ItemConversionOptions.None_


# -----------------------------
# JSON-ready conversion helpers
# -----------------------------
def _encode(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _encode(v) for k, v in asdict(value).items()}
    if isinstance(value, IntFlag):
        if type(value) is MeshFlags:
            if value == MeshFlags.None_:
                return "None"
            names = [flag.name for flag in MeshFlags if flag != MeshFlags.None_ and (value & flag)]
            return "|".join(names)
        return int(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_encode(v) for v in value]
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
    if item.PlacementParams is None:
        data.pop("PlacementParams", None)
    if item.LodParameters is None:
        data.pop("LodParameters", None)

    return _drop_nones(data) if drop_none else data