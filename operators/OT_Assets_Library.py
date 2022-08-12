
import bpy
import uuid
import time
from pathlib import Path

from bpy.types import (
    Operator,
    Material,
)

from ..utils.Functions          import *
from ..utils.Properties         import *
from ..operators.OT_Materials   import *
from ..utils.Constants          import * 

class TM_OT_Materials_Create_Asset_Lib(Operator):
    bl_idname = "view3d.tm_createassetlib"
    bl_label = "create assets library"
    bl_description = "Create assets library, ignores previously created materials with the same name"
   
    def execute(self, context):
        if saveBlendFile():
            createAssetsLib()
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}



def createAssetsLib() -> None:
    #currentFile = bpy.data.filepath

    # clear all possible data
    for bpy_data_iter in (
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.cameras,
            bpy.data.materials,
            bpy.data.cameras,
            bpy.data.armatures,
            bpy.data.collections,
            bpy.data.curves,
            bpy.data.images,
    ):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data, do_unlink=True)

    createAssetsCatalogFile(getGameDocPathItemsAssets())
    
    fileName = ""
    if isGameTypeTrackmania2020():
        fileName = get_global_props().LI_gameType+"_assets.blend"
        generate2020Assets()
    elif isGameTypeManiaPlanet():
        fileName = get_global_props().LI_gameType+"_assets.blend"
        generateMPAssets()  

    # save as new blend file for assets libraray
    createFolderIfNecessary(getGameDocPathItemsAssets())
    if not saveBlendFileAs(fixSlash(getGameDocPathItemsAssets()+"/"+fileName)):
        show_report_popup("Can not create new blend file", ["Something went wrong during creation of a new blend file"], "ERROR")

    # reopen original file
    # bpy.ops.wm.open_mainfile(filepath=currentFile)
    return
   



def generate2020Assets() -> None:
    getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType)
    getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium")
    getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials")

    matList = getLinkedMaterials()

    for key in matList.keys():
        if key in MATERIALS_MAP_TM2020:
            matNameNew = "TM_"+key+"_asset" 
            if matNameNew in bpy.data.materials:
                continue

            color = (0.0,0.319,0.855)
            if "Color" in MATERIALS_MAP_TM2020[key]:
                color = hexToRGB(MATERIALS_MAP_TM2020[key]["Color"])   
            mat = createMaterialAsset(matNameNew, key, color)

            if mat.use_nodes:
                if (
                    "IsSign" not in MATERIALS_MAP_TM2020[key] and
                    "tex_D" in mat.node_tree.nodes and
                    mat.node_tree.nodes["tex_D"].image and
                    mat.node_tree.nodes["tex_D"].image.filepath
                ):
                    bpy.ops.ed.lib_id_load_custom_preview(
                        {"id": mat}, 
                        filepath=mat.node_tree.nodes["tex_D"].image.filepath
                    )
                elif (
                    "tex_I" in mat.node_tree.nodes and
                    mat.node_tree.nodes["tex_I"].image and
                    mat.node_tree.nodes["tex_I"].image.filepath
                ):
                    bpy.ops.ed.lib_id_load_custom_preview(
                        {"id": mat}, 
                        filepath=mat.node_tree.nodes["tex_I"].image.filepath
                    )
                else:
                    # short delay to let materials become registered
                    # otherwise preview is not generating
                    time.sleep(0.05)
                    bpy.ops.ed.lib_id_generate_preview({"id": mat})

            mat.asset_mark()
            key = key.lower()
            if "decal" in key:
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Decals")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif key.startswith("custom"):
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Custom")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif key.startswith("road"):
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Roads")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "platformtech" in key:
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Platform")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "specialfx" in key:
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/SpecialFXs")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "_sign" in key or "specialsign" in key:
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Signs")
                if uid:
                    mat.asset_data.catalog_id = uid
            else:
                uid = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/Stadium/Materials/Rest")
                if uid:
                    mat.asset_data.catalog_id = uid



def generateMPAssets() -> None:
    for col in getMaterialCollectionTypes():
        if col[0] == "Common":
            continue
        
        getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType)
        catalogUUID = getOrCreateCatalog(getGameDocPathItemsAssets(), get_global_props().LI_gameType+"/"+col[0]+"/Materials")

        get_global_props().LI_materialCollection = col[0]
        gameTypeGotUpdated()

        matList = getLinkedMaterials()
        for matItem in matList:
            matNameNew = f"MP_{get_global_props().LI_materialCollection}_{matItem.name}_asset"
            if matNameNew in bpy.data.materials:
                continue

            mat = createMaterialAsset(matNameNew, matItem.name, (0,0,0))
            if mat.use_nodes:
                if (
                    "tex_D" in mat.node_tree.nodes and
                    mat.node_tree.nodes["tex_D"].image and
                    mat.node_tree.nodes["tex_D"].image.filepath
                ):
                    bpy.ops.ed.lib_id_load_custom_preview(
                        {"id": mat}, 
                        filepath=mat.node_tree.nodes["tex_D"].image.filepath
                    )
                elif (
                    "tex_I" in mat.node_tree.nodes and
                    mat.node_tree.nodes["tex_I"].image and
                    mat.node_tree.nodes["tex_I"].image.filepath
                ):
                    bpy.ops.ed.lib_id_load_custom_preview(
                        {"id": mat}, 
                        filepath=mat.node_tree.nodes["tex_I"].image.filepath
                    )
                else:
                    # short delay to let materials become registered
                    # otherwise preview is not generating
                    time.sleep(0.05)
                    bpy.ops.ed.lib_id_generate_preview({"id": mat})

                mat.asset_mark()
                mat.asset_data.catalog_id = catalogUUID

    return



def createMaterialAsset(name: str, link: str, color: tuple[float, float, float]) -> Material:
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
    
    createMaterialNodes(MAT)
    
    return MAT
        


def createAssetsCatalogFile(path: str) -> None:
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
def getOrCreateCatalog(path: str, name: str) -> str:
    catList = getCatalogsList(path)
    if name in catList:
        return catList[name]
    else:
        with open(os.path.join(path, "blender_assets.cats.txt"), "a") as f:
            uid = uuid.uuid4()
            f.write(f"{uid}:{name}:{name.replace('/', '-', -1)}\n")
            return f"{uid}"