import bpy
import bmesh
import json
from ..utils.Functions import (
    get_global_props,
)

from ..utils.Dotnet import (
    run_read_mediatracker,
    DotnetVector4,
    DotnetVector3,
    DotnetMediaTrackerTriangle,
    MediaTrackerBlockTriangleKey,
    DotnetInt3,
    DotnetMediatrackerClips,
    run_place_triangle_on_map,
)

from ..utils.BlenderObjects import (
    create_collection_in
)

from ..properties.Functions import (
    EnumProps
)


def get_mt_types()->list:
    return EnumProps().add(
        id   = "INTRO",
        name = "Intro",
        desc = "MT Intro",
    ).add(
        id   = "INGAME",
        name = "In Game",
        desc = "MT In Game",
    ).add(
        id   = "ENDRACE",
        name = "End Race",
        desc = "MT End Race",
    ).add(
        id   = "PODIUM",
        name = "Podium",
        desc = "MT Podium",
    ).add(
        id   = "AMBIENCE",
        name = "Ambience",
        desc = "MT Ambience",
    ).to_list()

MT_ONLY_2D_TRIANGLES = ["AMBIENCE"]
MT_TRIGGER_REQUIRED = ["INGAME", "ENDRACE"]

def _WIP_read_mediatracker() -> str:
    tm_props = get_global_props()
    map_path = tm_props.ST_map_filepath
    map_coll = tm_props.PT_map_collection
    
    res = run_read_mediatracker(map_path)
    if res.success:
        data:DotnetMediatrackerClips = json.loads(res.message)

        return None


    return res.message

def _triangulate_object(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    bm.to_mesh(me)
    bm.free()

def _get_object_location_frames(obj: bpy.types.Object) -> list[int]:
    frames:list[float] = []
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path.endswith(('location','scale','rotation_euler')):
            for key in fc.keyframe_points:
                fr = key.co[0]
                if fr not in frames:
                    frames.append(int(fr))

    print(frames)
    return frames

def _get_positions_at_frame(obj: bpy.types.Object, length: int, frame: int) -> list[DotnetVector3]:
    positions = [DotnetVector3()]*length
    
    bpy.context.scene.frame_set(frame)
    i = 0
    for f in obj.data.polygons:
        for idx in f.vertices:
            loc = obj.matrix_world @ obj.data.vertices[idx].co
            positions[i] = DotnetVector3(loc[1], loc[2]+8, loc[0])
            i = i + 1

    return positions

def export_object_as_triangle(obj: bpy.types.Object, map_path: str, sequence: str) -> str:
    _triangulate_object(obj)
    frames = _get_object_location_frames(obj)
    matrix = obj.matrix_world
    vertices:list[DotnetVector4] = []
    triangles:list[DotnetInt3] = []
    keys:list[MediaTrackerBlockTriangleKey] = []

    for f in obj.data.polygons:
        if len(f.vertices) != 3:
            return "One of the faces is not/con not be triangulated"
        
        triangle = [0,0,0]
        i = 0
        for idx in f.vertices:
            vertices.append(DotnetVector4(1,1,1,1))
            triangle[i] = len(vertices) - 1
            i = i+1

        triangles.append(DotnetInt3(triangle[0], triangle[1], triangle[2]))

    if len(frames) < 2:
        positions = _get_positions_at_frame(obj, len(vertices), 0)
        keys.append(MediaTrackerBlockTriangleKey(0, positions))
        keys.append(MediaTrackerBlockTriangleKey(3000, positions))
    else:
        for frame in frames:
            positions = _get_positions_at_frame(obj, len(vertices), frame)
            keys.append(MediaTrackerBlockTriangleKey(frame*1000, positions))

        bpy.context.scene.frame_set(0)

    res = run_place_triangle_on_map(map_path, sequence, obj.name, "3D", DotnetMediaTrackerTriangle(0, keys, vertices, triangles))
    return res.message
    #return "TEST"