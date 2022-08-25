import bpy
import re
import os
from pathlib import Path

from .Constants import WAYPOINTS
from .Materials import fix_material_names, assign_mat_json_to_mat
from .Functions import (
    deselect_all_objects,
    get_waypoint_type_of_FBX,
    get_active_collection,
    ireplace,
)
from .Dotnet import run_convert_item_to_obj
from .BlenderObjects import create_collection_in, move_obj_to_coll


def import_item_FBXs(files: list[str]) -> None:
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

def import_item_gbx(item_path: str):
    output_dir = os.path.dirname(item_path)

    obj_path, err = run_convert_item_to_obj(item_path, output_dir)
    if err:
        return err

    bpy.ops.import_scene.obj(filepath=obj_path)
    objs = bpy.context.selected_objects
    _clean_up_imported_item_gbx(item_path, objs)

    os.remove(obj_path)

    return None

def _clean_up_imported_item_gbx(item_path:str, objs: list[bpy.types.Object]):
    item_name = Path(item_path).stem
    item_name = ireplace(".item", "", item_name)

    coll = create_collection_in(bpy.context.collection, item_name)

    for obj in objs:
        move_obj_to_coll(obj, coll)
        obj.name = f"{item_name} {obj.name}"
        # TODO go over materials and create presented mats
        # TODO fix UVs names
        # TODO try to add info about Start/Finish/CP?
        # TODO try to add vis/col flags and assign correct prefix?
        # TODO check what would happen with other layer types (deformation, scale etc)

    return None