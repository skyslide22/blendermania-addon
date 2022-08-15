import bpy
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

# Dotnet types
class DotnetVector3:
    def __init__(self, X: float = 0, Y: float = 0, Z: float = 0) -> None:
        self.X = X
        self.Y = Y
        self.Z = Z

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetInt3:
    def __init__(self, X: int = 0, Y: int = 0, Z: int = 0) -> None:
        self.X = X
        self.Y = Y
        self.Z = Z

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetBlock:
    def __init__(self, Name: str, Direction: int, Position: DotnetInt3):
        if Direction > 3:
            Direction = 0

        self.Name = Name
        self.Dir = Direction
        self.Position = Position
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetItem:
    def __init__(self, Name: str, Path: str, Position: DotnetVector3, Rotation: DotnetVector3 = DotnetVector3(), Pivot: DotnetVector3 = DotnetVector3()):
        self.Name = Name
        self.Path = Path
        self.Position = Position
        self.Rotation = Rotation
        self.Pivot = Pivot
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetPlaceObjectsOnMap:
    def __init__(self, MapPath: str, Blocks: list[DotnetBlock], Items: list[DotnetItem]):
        self.MapPath = MapPath
        self.Blocks = Blocks
        self.Items = Items
        # TODO blocks

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

# TODO move it to functions
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'toJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

# Dotnet commands
def run_place_objects_on_map(map_path: str, blocks: list[DotnetBlock] = [], items: list[DotnetItem] = []):
    return _run_dotnet(PLACE_OBJECTS_ON_MAP, json.dumps(DotnetPlaceObjectsOnMap(map_path, blocks, items).toJSON(), cls=ComplexEncoder))

# TODO better error handling
def _run_dotnet(command: str, payload: str) -> str | None:
    # TODO use .exe from propper source
    process = subprocess.Popen(args=[
        "D:/Art/Blender/blendermania-dotnet/blendermania-dotnet/bin/Release/net6.0/win-x64/publish/blendermania-dotnet.exe",
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