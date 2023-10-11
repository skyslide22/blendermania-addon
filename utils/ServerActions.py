import bpy, bmesh
import subprocess
from typing import List

from ..utils.Constants import EDITORTRAILS_OBJECT_NAME

from ..operators.OT_Items_Export import close_convert_panel

from ..utils.Functions import (
    deselect_all_objects,
    editmode,
    get_addon_assets_path,
    objectmode,
    select_obj,
    set_active_object
)


def focus_blender() -> bool:
    try:
        subprocess.Popen([
            get_addon_assets_path() + "/convert_report/focus_blender.bat",
            "blender"
        ])
        return True
    
    except Exception as err:
        return False

    finally:
        close_convert_panel()



class EditorTrail:
    path_x: float
    path_y: float
    path_z: float
    
    velo_x: float
    velo_y: float
    velo_z: float

    time: float



def update_editortrails(trails: List[EditorTrail]) -> bool:
    curve = bpy.data.curves.get(EDITORTRAILS_OBJECT_NAME, None)
    if curve:
        bpy.data.curves.remove(curve)

    coords_list = []

    for i, trail in enumerate(trails):
        coords_list.append([
            trail.path_z, # / 32,
            trail.path_x, # / 32,
            trail.path_y, # / 32,
        ])

    curve = bpy.data.curves.new(EDITORTRAILS_OBJECT_NAME, 'CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new(type='NURBS')
    spline.points.add(len(coords_list) - 1) 

    for point, new_coord in zip(spline.points, coords_list):
        point.co = (new_coord + [1.0])  # (add nurbs 

    obj = bpy.data.objects.new(EDITORTRAILS_OBJECT_NAME, curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    return True



