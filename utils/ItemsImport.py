import bpy
import re
import math
import os
import glob
from pathlib import Path

from .Constants import WAYPOINTS
from .Materials import fix_material_names, assign_mat_json_to_mat
from .Functions import (
    fix_slash,
    deselect_all_objects,
    get_waypoint_type_of_FBX,
    get_active_collection,
    ireplace,
    get_global_props,
    is_game_trackmania2020,
)
from .Dotnet import run_convert_item_to_obj
from .BlenderObjects import create_collection_in, move_obj_to_coll
from ..utils.Materials import create_material_nodes

def _load_asset_mats(mats: list[str]):
    mateirals = []
    prefs = bpy.context.preferences
    filepaths = prefs.filepaths
    asset_libraries = filepaths.asset_libraries

    for asset_library in asset_libraries:
        library_path = Path(asset_library.path)
        blend_files = [fp for fp in library_path.glob("**/*.blend") if fp.is_file()]
        for blend_file in blend_files:
            with bpy.data.libraries.load(str(blend_file), assets_only=True) as (data_from, data_to):
                for mat in mats:
                    name = mat+"_asset"
                    if name in data_from.materials and name not in data_to.materials and name not in bpy.data.materials:
                        data_to.materials += [name]

    return mateirals

def _create_or_update_material(name: str, link: str):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    elif name+"_asset" in bpy.data.materials:
        return bpy.data.materials[name+"_asset"]

    MAT = bpy.data.materials.new(name=name)

    MAT.gameType      = get_global_props().LI_gameType
    MAT.environment   = get_global_props().LI_materialCollection
    MAT.usePhysicsId  = False
    MAT.useGameplayId = False
    MAT.model         = "TDSN"
    MAT.link          = link
    MAT.baseTexture   = ""
    MAT.name          = name
    MAT.surfaceColor  = (0,0,0)
    
    create_material_nodes(MAT)

    return MAT

def _get_material_name(name: str):
    parts = name.split("\\")
    clean_name = parts[len(parts) - 1]
    clean_name = re.sub(r'\.[0-9]{3}$', "", clean_name)
    link = clean_name

    if is_game_trackmania2020():
        clean_name = f"TM_{clean_name}"
    else:
        clean_name = f"MP_{get_global_props().LI_materialCollection}_{clean_name}"

    return clean_name, link


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

def import_items_gbx_folder(folder_path: str):
    folder_path = fix_slash(folder_path)
    parts = folder_path.split("/")
    base_coll = create_collection_in(bpy.context.collection, parts[len(parts) - 2])
    for item_path in glob.iglob(folder_path + '**/*.gbx', recursive=True):
        item_path = fix_slash(item_path)
        if not item_path.lower().endswith("gbx"):
            continue

        name = Path(item_path).stem
        name = ireplace(".item", "", name)

        path = item_path.replace(folder_path, "")
        coll = base_coll
        for part in path.split("/"):
            if part.lower().endswith(".gbx"):
                break

            new_name = coll.name+"_"+part
            if new_name in coll.children:
                coll = coll.children[new_name]
            else:
                coll = create_collection_in(coll, new_name)
        
        import_item_gbx(item_path, name, coll)

def import_item_gbx(item_path: str, name: str = None, coll: bpy.types.Collection = None):
    if coll == None:
        coll = bpy.context.collection

    if name == None:
        name = Path(item_path).stem
        name = ireplace(".item", "", name)


    output_dir = os.path.dirname(item_path)

    res = run_convert_item_to_obj(item_path, output_dir)
    if not res.success:
        return res.message

    bpy.ops.import_scene.obj(filepath=res.message)
    objs = bpy.context.selected_objects
    _clean_up_imported_item_gbx(objs, name, coll)

    os.remove(res.message)

    return None

def _clean_up_imported_item_gbx(objs: list[bpy.types.Object], item_name: str, dest_coll: bpy.types.Collection):
    coll = create_collection_in(dest_coll, item_name)

    for obj in objs:
        obj:bpy.types.Object = obj
        move_obj_to_coll(obj, coll)
        obj.name = f"{item_name} {obj.name}"

        # materials
        mats:list[str]= []
        for slot in obj.material_slots:
            name, link = _get_material_name(slot.material.name)
            mats.append(name)

        _load_asset_mats(mats)

        for slot in obj.material_slots:
            old_mat = slot.material
            name, link = _get_material_name(slot.material.name)
            mat = _create_or_update_material(name, link)
            slot.material = mat
            bpy.data.materials.remove(old_mat)

        # fix UV
        if len(obj.data.uv_layers) > 0:
            obj.data.uv_layers[0].name = "BaseMaterial"

        # auto smooth
        obj.data.polygons.foreach_set('use_smooth',  [True] * len(obj.data.polygons))
        obj.data.use_auto_smooth = 1
        obj.data.auto_smooth_angle = math.pi/6  # 45 degrees

        # TODO try to add info about Start/Finish/CP?
        # TODO try to add vis/col flags and assign correct prefix?
        # TODO check what would happen with other layer types (deformation, scale etc)

    return None