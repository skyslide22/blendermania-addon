import bpy
import json
import subprocess

from .Constants      import *
from .Functions      import *

# Dotnet types
class DotnetVector3:
    def __init__(self, X: float = 0, Y: float = 0, Z: float = 0) -> None:
        self.X = X
        self.Y = Y
        self.Z = Z

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetItem:
    def __init__(self, Name: str, Path: str, Position: DotnetVector3, Rotation: DotnetVector3 = DotnetVector3(), Pivot: DotnetVector3 = DotnetVector3()):
        self.Name = Name
        self.Path = Path
        self.Position = Position
        self.Rotation = Rotation
        self.Pivot = Pivot
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetPlaceObjectsOnMap:
    def __init__(self, MapPath: str, Items: list[DotnetItem]):
        self.MapPath = MapPath
        self.Items = Items
        # TODO blocks

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

# TODO move it to functions
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'to_json'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

# Dotnet commands
def run_place_objects_on_map(map_path: str, items: list[DotnetItem]):
    return _run_dotnet(PLACE_OBJECTS_ON_MAP, json.dumps(DotnetPlaceObjectsOnMap(map_path, items).to_json(), cls=ComplexEncoder))

# TODO better error handling
def _run_dotnet(command: str, payload: str):
    print(command)
    print(payload)

    # TODO use .exe from propper source
    proc = subprocess.Popen(args=[
        "D:/Art/Blender/blendermania-dotnet/blendermania-dotnet/bin/Release/net6.0/win-x64/publish/blendermania-dotnet.exe",
        command,
        payload.strip('"'),
    ])
    proc.stdout = subprocess.PIPE
    proc.wait()

    debug("returncode: ", proc.returncode)