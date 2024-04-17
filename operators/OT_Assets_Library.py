
import bpy
import uuid
import time
from pathlib import Path

from bpy.types import (
    Operator,
)

from ..utils.Materials import create_material_shader

from ..utils.Functions          import *
from ..operators.OT_Materials   import *
from ..utils.Constants          import * 

class TM_OT_Materials_Create_Asset_Lib(Operator):
    bl_idname = "view3d.tm_createassetlib"
    bl_label = "create assets library"
    bl_description = "Create assets library, ignores previously created materials with the same name"
   
    def execute(self, context):
        if save_blend_file():
            _create_assets_lib()
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}



def _create_assets_lib() -> None:
    #currentFile = bpy.data.filepath

    if not is_game_trackmania2020():
        return

    _create_assets_catalog_file(get_game_doc_path_items_assets())
    
    fileName = ""
    if is_game_trackmania2020():
        fileName = get_global_props().LI_gameType+"_assets.blend"
        generate2020Assets()

    # save as new blend file for assets libraray
    create_folder_if_necessary(get_game_doc_path_items_assets())
    if not save_blend_file_as(fix_slash(get_game_doc_path_items_assets()+"/"+fileName)):
        show_report_popup("Can not create new blend file", ["Something went wrong during creation of a new blend file"], "ERROR")

    return

def generate2020Assets() -> None:
    get_or_create_catalog(get_game_doc_path_items_assets(), get_global_props().LI_gameType)
    get_or_create_catalog(get_game_doc_path_items_assets(), get_global_props().LI_gameType+"/Stadium")
    get_or_create_catalog(get_game_doc_path_items_assets(), get_global_props().LI_gameType+"/Stadium/Materials")

    for key in MATERIALS_MAP_TM2020:
        matNameNew = "TM_"+key+"_asset" 

        color = (0.0,0.319,0.855)
        if "DefaultColorRGB" in MATERIALS_MAP_TM2020[key]:
            color = hex_to_rgb(MATERIALS_MAP_TM2020[key]["DefaultColorRGB"])   
        mat = _create_material_asset(matNameNew, key, color)

        if mat.use_nodes:
            image_path = None
            if f"tex_over_I" in mat.node_tree.nodes and mat.node_tree.nodes["tex_over_I"].image and mat.node_tree.nodes["tex_over_I"].image.filepath:
                image_path = mat.node_tree.nodes["tex_over_I"].image.filepath
            elif f"tex_M" in mat.node_tree.nodes and mat.node_tree.nodes["tex_M"].image and mat.node_tree.nodes["tex_M"].image.filepath:
                image_path = mat.node_tree.nodes["tex_M"].image.filepath
            elif f"tex_D" in mat.node_tree.nodes and mat.node_tree.nodes["tex_D"].image and mat.node_tree.nodes["tex_D"].image.filepath:
                image_path = mat.node_tree.nodes["tex_D"].image.filepath
            elif f"tex_I" in mat.node_tree.nodes and mat.node_tree.nodes["tex_I"].image and mat.node_tree.nodes["tex_I"].image.filepath:
                image_path = mat.node_tree.nodes["tex_I"].image.filepath

            if "Custom" in mat.name and "CustomMod" not in mat.name:
                image_path = None

            if "Invisible" not in mat.name and (
                "PlatformIce_OpenTechBorders" in mat.name or "PlatformIce_PlatformTech" in mat.name or "RoadIce" in mat.name
            ):
                image_path = mat.node_tree.nodes["tex_D"].image.filepath

            if image_path and get_game_doc_path_items_assets() not in fix_slash(image_path):
                image_path = fix_slash(get_game_doc_path_items_assets() + fix_slash(image_path))

            with bpy.context.temp_override(id=mat):
                if image_path:
                    bpy.ops.ed.lib_id_load_custom_preview(filepath=image_path)
                else:
                    # short delay to let materials become registered
                    # otherwise preview is not generating
                    time.sleep(0.05)
                    bpy.ops.ed.lib_id_generate_preview()

        print("created asset", mat.name)
        mat.asset_mark()

        catName = MATERIALS_MAP_TM2020[key]["MatLibParams"]["Category"]
        
        uid = get_or_create_catalog(get_game_doc_path_items_assets(), get_global_props().LI_gameType+"/Stadium/Materials/"+catName)
        if uid:
            mat.asset_data.catalog_id = uid



def _create_material_asset(name: str, link: str, color: tuple[float, float, float]) -> bpy.types.Material:
    MAT:bpy.types.Material
    if name in bpy.data.materials:
        MAT = bpy.data.materials[name]
    else:
        MAT = bpy.data.materials.new(name=name)

    MAT.gameType      = get_global_props().LI_gameType
    MAT.environment   = get_global_props().LI_materialCollection
    MAT.usePhysicsId  = False
    MAT.useGameplayId = False
    MAT.model         = "TDSN"
    MAT.link          = link
    MAT.baseTexture   = ""
    MAT.name          = name
    MAT.surfaceColor  = color
    
    create_material_shader(MAT)
    
    return MAT
        


def _create_assets_catalog_file(path: str) -> None:
    pathToAssets = os.path.join(path, "blender_assets.cats.txt")
    if not os.path.exists(pathToAssets):
        f = open(pathToAssets, "x")
        f.write("VERSION 1\n\n")
        f.close()



def getCatalogsList(path: str) -> dict:
    catList = {}
    with open(os.path.join(path, "blender_assets.cats.txt")) as f:
        for line in f.readlines():
            if line.startswith(("#", "VERSION", "\n")):
                continue
            
            parts = line.split(":")
            catList[parts[1]] = parts[0]

    return catList



# returns catalog UUID
def get_or_create_catalog(path: str, name: str) -> str:
    catList = getCatalogsList(path)
    if name in catList:
        return catList[name]
    else:
        with open(os.path.join(path, "blender_assets.cats.txt"), "a") as f:
            uid = uuid.uuid4()
            f.write(f"{uid}:{name}:{name.replace('/', '-', -1)}\n")
            return f"{uid}"