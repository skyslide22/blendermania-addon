import bpy
import math
import json
import subprocess

from .Constants      import *
from .Functions      import *


DOTNET_BLOCKS_DIRECTION = (
    DOTNET_BLOCKS_DIRECTION_NORTH   := 0,
    DOTNET_BLOCKS_DIRECTION_EAST    := 1,
    DOTNET_BLOCKS_DIRECTION_SOUTH   := 2,
    DOTNET_BLOCKS_DIRECTION_WEST    := 3,
)

DOTNET_ITEM_ANIMATION_PHASE_OFFSETS = (
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_NONE := "None",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_ONE8TH := "One8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_TWO8TH := "Two8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_THREE8TH := "Three8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_FOUR8TH := "Four8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_FIVE8TH := "Five8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_SIX8TH := "Six8th",
    DOTNET_ITEM_ANIMATION_PHASE_OFFSET_SEVEN8TH := "Seven8th"
)

DOTNET_ITEM_DIFFICULTY_COLORS = (
    DOTNET_ITEM_DIFFICULTY_COLOR_DEFAULT := "Default",
    DOTNET_ITEM_DIFFICULTY_COLOR_WHITE := "White",
    DOTNET_ITEM_DIFFICULTY_COLOR_GREEN := "Green",
    DOTNET_ITEM_DIFFICULTY_COLOR_BLUE := "Blue",
    DOTNET_ITEM_DIFFICULTY_COLOR_RED := "Red",
    DOTNET_ITEM_DIFFICULTY_COLOR_BLACK := "Black"
)

DIFFICULTYCOLOR_ICON_MAP = {
    DOTNET_ITEM_DIFFICULTY_COLOR_DEFAULT: ICON_COLOR_GRAY,
    DOTNET_ITEM_DIFFICULTY_COLOR_WHITE: ICON_COLOR_WHITE,
    DOTNET_ITEM_DIFFICULTY_COLOR_GREEN: ICON_COLOR_GREEN,
    DOTNET_ITEM_DIFFICULTY_COLOR_BLUE: ICON_COLOR_BLUE,
    DOTNET_ITEM_DIFFICULTY_COLOR_RED: ICON_COLOR_RED,
    DOTNET_ITEM_DIFFICULTY_COLOR_BLACK: ICON_COLOR_BLACK,
}

DOTNET_ITEM_LIGHTMAP_QUALITIES = (
    DOTNET_ITEM_LIGHTMAP_QUALITY_NORMAL := "Normal",
    DOTNET_ITEM_LIGHTMAP_QUALITY_HIGH := "High",
    DOTNET_ITEM_LIGHTMAP_QUALITY_VERYHIGH := "VeryHigh",
    DOTNET_ITEM_LIGHTMAP_QUALITY_HIGHEST := "Highest",
    DOTNET_ITEM_LIGHTMAP_QUALITY_LOW := "Low",
    DOTNET_ITEM_LIGHTMAP_QUALITY_VERYLOW := "VeryLow",
    DOTNET_ITEM_LIGHTMAP_QUALITY_LOWEST := "Lowest",
)

def get_block_dir_for_angle(angle: int) -> int:
    print(math.copysign(angle%360, angle))
    return DOTNET_BLOCKS_DIRECTION_EAST


class DotnetExecResult:
    success: bool
    message: str
    def __init__(self, message: str, success: bool):
        self.success = success
        self.message = message


# Dotnet types
class DotnetVector3:
    def __init__(self, X: float = 0, Y: float = 0, Z: float = 0) -> None:
        self.X = X
        self.Y = Y
        self.Z = Z

    def jsonable(self):
        return self.__dict__


class DotnetInt3:
    def __init__(self, X: int = 0, Y: int = 0, Z: int = 0) -> None:
        self.X = X
        self.Y = Y
        self.Z = Z

    def jsonable(self):
        return self.__dict__


class DotnetBlock:
    def __init__(self, Name: str, Direction: int, Position: DotnetInt3):
        if Direction > 3:
            Direction = 0

        self.Name = Name
        self.Dir = Direction
        self.Position = Position
    
    def jsonable(self):
        return self.__dict__


class DotnetItem:
    def __init__(self, 
                 Name: str,
                Path: str,
                Position: DotnetVector3,
                Rotation: DotnetVector3 = DotnetVector3(),
                Pivot: DotnetVector3 = DotnetVector3(),
                AnimPhaseOffset: str = "",
                DifficultyColor: str = "",
                LightmapQuality: str = ""):
        self.Name = Name
        self.Path = Path
        self.Position = Position
        self.Rotation = Rotation
        self.Pivot = Pivot
        self.AnimPhaseOffset = AnimPhaseOffset
        self.DifficultyColor = DifficultyColor
        self.LightmapQuality = LightmapQuality
    
    def jsonable(self):
        return self.__dict__


class DotnetMediatrackerClip:
    def __init__(
        self, 
        Name: str, 
        Positions: list[DotnetVector3]):
            self.Name = Name
            self.Positions = Positions
    
    def jsonable(self):
        return self.__dict__


class DotnetPlaceObjectsOnMap:
    def __init__(
        self,
        MapPath: str,
        Blocks: list[DotnetBlock],
        Items: list[DotnetItem],
        ShouldOverwrite: bool = False,
        MapSuffix: str = "_modified",
        CleanBlocks: bool = True,
        CleanItems: bool = True,
        Env: str = "Stadium2020"):
            self.MapPath = MapPath
            self.Blocks = Blocks
            self.Items = Items
            self.ShouldOverwrite = ShouldOverwrite
            self.MapSuffix = MapSuffix
            self.CleanBlocks = CleanBlocks
            self.CleanItems = CleanItems
            self.Env = Env

    def jsonable(self):
        return self.__dict__


class DotnetPlaceMediatrackerClipsOnMap:
    def __init__(
        self,
        MapPath: str,
        Clips: list[DotnetItem]):
            self.MapPath = MapPath
            self.Clips = Clips

    def jsonable(self):
        return self.__dict__


class DotnetConvertItemToObj:
    def __init__(
        self,
        ItemPath: str,
        OutputDir: str,
    ):
        self.ItemPath = ItemPath
        self.OutputDir = OutputDir

    def jsonable(self):
        return self.__dict__

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'jsonable'):
            return obj.jsonable()
        else:
            return json.JSONEncoder.default(self, obj)


# Dotnet commands
def run_place_objects_on_map(
    map_path: str,
    blocks: list[DotnetBlock] = [],
    items: list[DotnetItem] = [],
    should_overwrite: bool = False,
    map_suffix: str = "_modified",
    clean_blocks: bool = True,
    clean_items: bool = True,
    env: str = True,
) -> DotnetExecResult:
    config_path = fix_slash(os.path.dirname(get_abs_path(map_path)))+'/map-export.json'
    with open(config_path, 'w+', encoding='utf-8') as outfile:
        json.dump(DotnetPlaceObjectsOnMap(
                map_path,
                blocks,
                items,
                should_overwrite,
                map_suffix,
                clean_blocks,
                clean_items,
                env,
        ), outfile, cls=ComplexEncoder, ensure_ascii=False, indent=4)
        outfile.close()

        res = _run_dotnet(PLACE_OBJECTS_ON_MAP, config_path)
        debug("run place objects on map: ", res.message, res.success)
        if not BLENDER_INSTANCE_IS_DEV:
            try:
                os.remove(config_path)
            except FileNotFoundError:
                pass
        return res


def run_convert_item_to_obj(
    item_path: str,
    output_dir: str,
) -> DotnetExecResult:
    config_path = fix_slash(os.path.dirname(get_abs_path(item_path)))+'/convert-item.json'
    with open(config_path, 'w+', encoding='utf-8') as outfile:
        json.dump(DotnetConvertItemToObj(item_path, output_dir), outfile, cls=ComplexEncoder, ensure_ascii=False, indent=4)
        outfile.close()

        res = _run_dotnet(CONVERT_ITEM_TO_OBJ, config_path)
        res.message = res.message.replace("SUCCESS: ", "")
        print(res)
        if not BLENDER_INSTANCE_IS_DEV:
            try:
                os.remove(config_path)
            except FileNotFoundError:
                pass
        return res


def run_get_mediatracker_clips(map_path: str) -> DotnetExecResult:
    return _run_dotnet(GET_MEDIATRACKER_CLIPS, map_path)

def run_place_mediatracker_clips_on_map(
    map_path: str,
    clips: list[DotnetMediatrackerClip] = [],
) -> DotnetExecResult:
    config_path = fix_slash(os.path.dirname(get_abs_path(map_path)))+'/mediatracker-export.json'
    with open(config_path, 'w+', encoding='utf-8') as outfile:
        json.dump(
            DotnetPlaceMediatrackerClipsOnMap(map_path, clips), 
            outfile, 
            cls=ComplexEncoder, 
            ensure_ascii=False, 
            indent=4)
        outfile.close()

        res = _run_dotnet(PLACE_MEDIATRACKER_CLIPS_ON_MAP, config_path)
        if not BLENDER_INSTANCE_IS_DEV:
            try:
                os.remove(config_path)
            except FileNotFoundError:
                pass
        return res


def _run_dotnet(command: str, payload: str) -> DotnetExecResult:
    #print(payload)
    dotnet_exe = get_blendermania_dotnet_path()

    process = subprocess.Popen(args=[
        dotnet_exe,
        command,
        payload.strip('"'),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out, err = process.communicate()
    if len(err) != 0:
        return DotnetExecResult(message=err.decode("utf-8") , success=False)
    
    res = out.decode("utf-8").strip()
    if process.returncode != 0:
        return DotnetExecResult(message="Unknown Error", success=False) if len(res) == 0 else res

    return DotnetExecResult(message=res, success=True)