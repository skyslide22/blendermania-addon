import bpy
import re

from .Constants import WAYPOINTS
from .Materials import fix_material_names, assign_mat_json_to_mat
from .Functions import (
    debug,
    deselect_all_objects,
    get_waypoint_type_of_FBX,
    get_active_collection,
    get_global_props,
)


def import_FBXs(files: list[str]) -> None:
    """main func for fbx import"""
    current_collection = get_active_collection()

    for filepath in files:
        deselect_all_objects()
        bpy.ops.import_scene.fbx(filepath=filepath, use_custom_props=True)
        
        objs = bpy.context.selected_objects
        mats = bpy.data.materials

        waypoint       = get_waypoint_type_of_FBX(filepath)
        waypoint_color = WAYPOINTS.get(waypoint, None)
        if waypoint_color is not None:
            current_collection.color_tag = waypoint_color


        for obj in objs:
            if "delete" in obj.name.lower():
                bpy.data.objects.remove(obj, do_unlink=True)
                continue

            for slot in obj.material_slots:
                mat    = slot.material
                if mat is None: continue

                #mat has .001
                regex = r"\.\d+$"
                if re.search(regex, mat.name):
                    noCountName = re.sub(regex, "", mat.name, re.IGNORECASE)
                    if noCountName in mats:
                        slot.material = mats[ noCountName ]
                        del mat
                        continue

                assign_mat_json_to_mat(mat)
            
            fix_material_names(obj)