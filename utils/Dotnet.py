import bpy
import math
import json
import subprocess

from .Constants      import *
from .Functions      import *

DOTNET_BLOCKS_DIRECTION = (
    DOTNET_BLOCKS_DIRECTION_NORTH := 0,
    DOTNET_BLOCKS_DIRECTION_EAST := 1,
    DOTNET_BLOCKS_DIRECTION_SOUTH := 2,
    DOTNET_BLOCKS_DIRECTION_WEST := 3,
)

def get_block_dir_for_angle(angle: int) -> int:
    print(math.copysign(angle%360, angle))
    return DOTNET_BLOCKS_DIRECTION_EAST

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
    def __init__(self, Name: str, Path: str, Position: DotnetVector3, Rotation: DotnetVector3 = DotnetVector3(), Pivot: DotnetVector3 = DotnetVector3()):
        self.Name = Name
        self.Path = Path
        self.Position = Position
        self.Rotation = Rotation
        self.Pivot = Pivot
    
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
        Env: str = "Stadium2020",
    ):
        self.MapPath = MapPath
        self.Blocks = Blocks
        self.Items = Items
        self.ShouldOverwrite = ShouldOverwrite
        self.MapSuffix = MapSuffix
        self.CleanBlocks = CleanBlocks
        self.CleanItems = CleanItems
        self.Env = Env
        # TODO blocks

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
):
    with open('map-export.json', 'w', encoding='utf-8') as outfile:
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

        res = _run_dotnet(PLACE_OBJECTS_ON_MAP, get_abs_path("map-export.json"))
        os.remove("map-export.json")
        return res

def _run_dotnet(command: str, payload: str) -> str | None:
    print(payload)
    dotnet_exe = get_blendermania_dotnet_path()

    process = subprocess.Popen(args=[
        dotnet_exe,
        command,
        payload.strip('"'),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    
    out, err = process.communicate()
    if len(err) != 0:
        return err.decode("utf-8") 
    
    res = out.decode("utf-8").strip()
    if process.returncode != 0:
        return "Unknown error" if len(res) == 0 else res

    return None if len(res) == 0 else res