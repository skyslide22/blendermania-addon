import bpy
import json
import subprocess

from .TM_Constants      import *
from .TM_Functions      import *

# Dotnet types
class DotnetVector3:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetItem:
    def __init__(self, name: str, path: str, position: DotnetVector3, rotation: DotnetVector3 = DotnetVector3(), pivot: DotnetVector3 = DotnetVector3()):
        self.name = name
        self.path = path
        self.position = position
        self.rotation = rotation
        self.pivot = pivot
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class DotnetPlaceObjectsOnMap:
    def __init__(self, map_path: str, items: list[DotnetItem]):
        self.map_path = map_path
        self.items = items
        # TODO blocks

    def toJSON(self):
        dct = self.__dict__
        dct["MapPath"] = self.map_path
        return json.dumps(dct, default=lambda o: o.__dict__)

# TODO move it to functions
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'toJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

# Dotnet commands
def run_place_objects_on_map(map_path: str, items: list[DotnetItem]):
    return _run_dotnet(PLACE_OBJECTS_ON_MAP, json.dumps(DotnetPlaceObjectsOnMap(map_path, items).toJSON(), cls=ComplexEncoder))

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