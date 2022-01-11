# region imports#
import bpy
import uuid
import time
from pathlib import Path

from bpy.types import (
    Operator,
    Material,
)

from .TM_Functions  import *
from .TM_Properties import *
from .TM_Materials import *
# endregion imports

class TM_OT_Materials_Create_Asset_Lib(Operator):
    bl_idname = "view3d.tm_createassetlib"
    bl_label = "create assets library"
    bl_description = "Create assets library, ignores previously created materials with the same name"
   
    def execute(self, context):
        if saveBlendFile():
            createAssetsLib()
        else:
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        makeReportPopup("Assets library created", ["Successfully created assets library"], "INFO")

        return {"FINISHED"}



def createAssetsLib() -> None:
    createAssetsCatalogFile()

    getOrCreateCatalog(getTmProps().LI_gameType)

    if isGameTypeTrackmania2020():
        generate2020Assets()
    elif isGameTypeManiaPlanet():
        generateMPAssets()

    # reload assets browser if it's on active screen
    for area in bpy.context.screen.areas:
        if area.type == "FILE_BROWSER":
            override_context = bpy.context.copy()
            override_context["area"] = area
            bpy.ops.asset.library_refresh(override_context)
   



def generate2020Assets() -> None:
    matList = getLinkedMaterials()

    for key in matList.keys():
        if key in MATERIALS_MAP_TM_2020:
            matNameNew = "TM_"+key+"_asset" 
            if matNameNew in bpy.data.materials:
                continue

            color = (0.0,0.319,0.855)
            if "Color" in MATERIALS_MAP_TM_2020[key]:
                color = hexToRGB(MATERIALS_MAP_TM_2020[key]["Color"])   
            mat = createMaterialAsset(matNameNew, key, color)

            if mat.use_nodes:
                if (
                    "IsSign" not in MATERIALS_MAP_TM_2020[key] and
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
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Decals")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif key.startswith("custom"):
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Custom")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif key.startswith("road"):
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Roads")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "platformtech" in key:
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Platform")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "specialfx" in key:
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/SpecialFXs")
                if uid:
                    mat.asset_data.catalog_id = uid
            elif "_sign" in key or "specialsign" in key:
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Signs")
                if uid:
                    mat.asset_data.catalog_id = uid
            else:
                uid = getOrCreateCatalog(getTmProps().LI_gameType+"/Rest")
                if uid:
                    mat.asset_data.catalog_id = uid



def generateMPAssets() -> None:
    catalogUUID = getOrCreateCatalog(getTmProps().LI_gameType+"/"+getTmProps().LI_materialCollection)

    matList = getLinkedMaterials()
    for matItem in matList:
        matNameNew = "MP_"+matItem.name+"_asset"
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

    MAT.gameType      = getTmProps().LI_gameType
    MAT.environment   = getTmProps().LI_materialCollection
    MAT.usePhysicsId  = False
    MAT.useGameplayId = False
    MAT.model         = "TDSN"
    MAT.link          = link
    MAT.baseTexture   = ""
    MAT.name          = name
    MAT.surfaceColor  = color
    
    createMaterialNodes(MAT)
    
    return MAT
        


def createAssetsCatalogFile() -> None:
    pathToAssets = os.path.join(Path(bpy.data.filepath).parent, "blender_assets.cats.txt")
    if not os.path.exists(pathToAssets):
        f = open(pathToAssets, "x")
        f.write("VERSION 1\n\n")
        f.close()



def getCatalogsList() -> dict:
    catList = {}
    with open(os.path.join(Path(bpy.data.filepath).parent, "blender_assets.cats.txt")) as f:
        for line in f.readlines():
            if line.startswith(("#", "VERSION", "\n")):
                continue
            
            parts = line.split(":")
            catList[parts[1]] = parts[0]

    return catList



# returns catalog UUID
def getOrCreateCatalog(name: str) -> str:
    catList = getCatalogsList()
    if name in catList:
        return catList[name]
    else:
        with open(os.path.join(Path(bpy.data.filepath).parent, "blender_assets.cats.txt"), "a") as f:
            uid = uuid.uuid4()
            f.write(f"{uid}:{name}:{name.replace('/', '-', -1)}\n")
            return f"{uid}"