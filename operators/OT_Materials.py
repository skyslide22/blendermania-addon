
import bpy
import re

from bpy.types import (Operator)
from ..utils.Functions  import *
from ..utils.Properties import *
from ..utils.Constants  import * 

class TM_OT_Materials_Create(Operator):
    bl_idname = "view3d.tm_creatematerial"
    bl_label = "create materials"
    bl_description = "create material"
   
    def execute(self, context):
        _create_or_ipdate_material("CREATE")
        context.region.tag_redraw()
        return {"FINISHED"}
    
class TM_OT_Materials_Update(Operator):
    bl_idname = "view3d.tm_updatematerial"
    bl_label = "update materials"
    bl_description = "update material"
   
    def execute(self, context):
        _create_or_ipdate_material("UPDATE")
        context.region.tag_redraw()
        return {"FINISHED"}

class TM_OT_Materials_ClearBaseMaterial(Operator):
    bl_idname = "view3d.tm_clearbasetexture"
    bl_label = "clear basematerial"
    bl_description = "clear basematerial"
   
    def execute(self, context):
        get_global_props()["ST_materialBaseTexture"] = ""
        context.region.tag_redraw()
        return {"FINISHED"}

class TM_OT_Materials_RevertCustomColor(Operator):
    bl_idname = "view3d.tm_revertcustomcolor"
    bl_label = "reset custom color"
    bl_description = "reset custom color"
   
    def execute(self, context):
        revertMaterialCustomColorLiveChanges()
        context.region.tag_redraw()
        return {"FINISHED"}

def _create_or_ipdate_material(action)->None:
    """create a export/convert ready material for TM and MP"""
    tm_props = get_global_props()
    
    TM_PREFIX = "TM_"
    MP_PREFIX = "MP_"

    matName          = tm_props.ST_selectedExistingMaterial
    matNameNew       = safe_name( tm_props.ST_materialAddName )
    matGameType      = tm_props.LI_gameType
    matCollection    = tm_props.LI_materialCollection
    matPhysicsId     = tm_props.LI_materialPhysicsId
    matUsePhysicsId  = tm_props.CB_materialUsePhysicsId
    matGameplayId    = tm_props.LI_materialGameplayId
    matUseGameplayId = tm_props.CB_materialUseGameplayId
    matModel         = tm_props.LI_materialModel
    matLink          = tm_props.ST_selectedLinkedMat
    matBaseTexture   = tm_props.ST_materialBaseTexture
    matColor         = tm_props.NU_materialCustomColor
    MAT              = None

    matTexSourceIsCustom = tm_props.LI_materialChooseSource == "CUSTOM"

    if isGameTypeTrackmania2020():
        if not matNameNew.startswith(TM_PREFIX):
            matNameNew = TM_PREFIX + matNameNew.replace(MP_PREFIX, "") 

    if isGameTypeManiaPlanet():
        if not matNameNew.startswith(MP_PREFIX):
            matNameNew = MP_PREFIX + matNameNew.replace(TM_PREFIX, "") 


    if action == "CREATE" and matNameNew in bpy.data.materials:
        show_report_popup(
            title="Material with this name already exists", 
            infos=["Creation failed"], 
            icon= "ERROR")
        debug(f"Material {matNameNew} creation failed")
        return

    if action == "CREATE":
        MAT = bpy.data.materials.new(name=matNameNew)
    else:
        MAT = bpy.data.materials[matName]

    MAT.gameType      = matGameType
    MAT.environment   = matCollection
    MAT.usePhysicsId  = matUsePhysicsId
    MAT.physicsId     = matPhysicsId
    MAT.useGameplayId = matUseGameplayId
    MAT.gameplayId    = matGameplayId
    MAT.model         = matModel
    MAT.link          = matLink
    MAT.baseTexture   = matBaseTexture if matTexSourceIsCustom          else ""
    MAT.name          = matNameNew
    MAT.surfaceColor  = matColor[:3]

    if action == "CREATE":
        show_report_popup(
            title=f"Material {matNameNew} successfully created!",
            icon ="CHECKMARK"
        )
        debug(f"Material {matNameNew} created")
    else: #UPDATE
        show_report_popup(
            title=f"Material {matName} sucessfully updated", 
            icon= "CHECKMARK"
        )
        debug(f"Material {matName} updated")

    create_material_nodes(MAT)
    applyMaterialLiveChanges()

def create_material_nodes(mat)->None:
    """create material nodes"""
    debug(f"start creating material nodes for {mat.name}")
    isCustomMat = mat.link.lower().startswith("custom")
    surfaceColor = mat.surfaceColor
    surfaceColor = (*surfaceColor, 1)

    mat.use_nodes = True
    mat.diffuse_color = surfaceColor
    mat.blend_method= "HASHED" #BLEND
    mat.show_transparent_back = False #backface culling
    mat.use_backface_culling  = False #backface culling

    links = mat.node_tree.links
    nodes = mat.node_tree.nodes
    
    _delete_material_nodes(mat=mat)

    xstep = 300
    ystep = 300
    x = lambda step:  (xstep * step)
    y = lambda step: -(ystep * step)

    # output
    NODE_output = nodes.new(type="ShaderNodeOutputMaterial")
    NODE_output.location = x(4), y(1)

    # big node with all stuff
    NODE_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    NODE_bsdf.subsurface_method = "BURLEY"
    NODE_bsdf.location = x(3), y(1)
    NODE_bsdf.inputs["Specular"].default_value = 0 #.specular
    NODE_bsdf.inputs["Emission Strength"].default_value = 3.0
    NODE_bsdf.inputs["Base Color"].default_value = surfaceColor

    # uvmap basematerial
    NODE_uvmap = nodes.new(type="ShaderNodeUVMap")
    NODE_uvmap.location = x(0), y(1)
    NODE_uvmap.uv_map = "BaseMaterial"

    # main texture, custom materials don't have it
    if not isCustomMat:
        NODE_tex_D = nodes.new(type="ShaderNodeTexImage")
        NODE_tex_D.location = x(1), y(1)
        NODE_tex_D.label = "Texture Diffuse _D.dds"
        NODE_tex_D.name  = "tex_D"

    # illumination(glow) texture
    normalModels = ["TDSN", "TDOSN", "TDOBSN", "TDSNI", "TDSNI_NIGHT"]

    NODE_tex_I = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_I.location = x(1), y(4)
    NODE_tex_I.label = "Texture Illum _I.dds"
    NODE_tex_I.name  = "tex_I"

    # rgb split
    NODE_rgbsplit = nodes.new(type="ShaderNodeSeparateRGB")
    NODE_rgbsplit.location = x(2), y(2)

    # Roughness
    NODE_tex_R = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_R.location = x(1), y(2)
    NODE_tex_R.label = "Texture Roughness _R.dds"
    NODE_tex_R.name  = "tex_R"

    # Normal
    NODE_tex_N = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_N.location = x(1), y(3)
    NODE_tex_N.label = "Texture Normal _N.dds"
    NODE_tex_N.name  = "tex_N"

    # normal map
    NODE_normal_map = nodes.new(type="ShaderNodeNormalMap")
    NODE_normal_map.location = x(2), y(3)

    # H
    NODE_tex_H = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_H.location = x(1), y(5)
    NODE_tex_H.label = "Texture H _H.dds"
    NODE_tex_H.name  = "tex_H"
    
    matMap2020 = None
    if isGameTypeTrackmania2020() and mat.link in MATERIALS_MAP_TM2020:
        matMap2020 = MATERIALS_MAP_TM2020[mat.link]

    NODE_mapping = None
    if matMap2020 and "Scale" in matMap2020 and matMap2020["Scale"] > 0:
        NODE_mapping = nodes.new(type="ShaderNodeMapping")
        NODE_mapping.location = x(0), y(2)
        NODE_mapping.inputs["Scale"].default_value = (matMap2020["Scale"], matMap2020["Scale"], 1)

    tex = ""
    DTexture = ""
    ITexture = ""
    RTexture = ""
    NTexture = ""
    HTexture = ""

    isLinkedMat = mat.baseTexture == ""
    
    debug(f"material link is :  {mat.link}")
    debug(f"material is a link: {isLinkedMat}")

    if isLinkedMat: tex = getGameDocPathItemsAssetsTextures() + mat.environment + "/" + mat.link
    else:           tex = re.sub(r"_?(i|d)\.dds$", "", mat.baseTexture, flags=re.IGNORECASE)

    if not isCustomMat:
        DTexture = _get_mat_dds(tex, "D")
    
    ITexture = _get_mat_dds(tex, "I")
    RTexture = _get_mat_dds(tex, "R")
    NTexture = _get_mat_dds(tex, "N")
    HTexture = _get_mat_dds(tex, "H")

    if not isCustomMat:
        DTexture = _load_dds_into_blender(texpath=DTexture)
    ITexture = _load_dds_into_blender(texpath=ITexture)
    RTexture = _load_dds_into_blender(texpath=RTexture)
    NTexture = _load_dds_into_blender(texpath=NTexture)
    HTexture = _load_dds_into_blender(texpath=HTexture)

    if not isCustomMat:
        DTextureSuccess = DTexture[0]
        DTextureName    = DTexture[1]
    ITextureSuccess = ITexture[0]
    ITextureName    = ITexture[1]
    RTextureSuccess = RTexture[0]
    RTextureName    = RTexture[1]
    NTextureSuccess = NTexture[0]
    NTextureName    = NTexture[1]
    HTextureSuccess = HTexture[0]
    HTextureName    = HTexture[1]

    if not isCustomMat and DTextureSuccess:
        _assign_texture_to_node(DTextureName, NODE_tex_D)

    if ITextureSuccess:
        _assign_texture_to_node(ITextureName, NODE_tex_I)

    if RTextureSuccess:
        _assign_texture_to_node(RTextureName, NODE_tex_R)

    if NTextureSuccess:
        _assign_texture_to_node(NTextureName, NODE_tex_N)
        NODE_tex_N.image.colorspace_settings.name = "Non-Color"

    if HTextureSuccess:
        _assign_texture_to_node(HTextureName, NODE_tex_H)

    if NODE_mapping:
        links.new(NODE_uvmap.outputs["UV"], NODE_mapping.inputs["Vector"])
        if not isCustomMat:
            links.new(NODE_mapping.outputs["Vector"], NODE_tex_D.inputs["Vector"])
        links.new(NODE_mapping.outputs["Vector"], NODE_tex_R.inputs["Vector"])
        links.new(NODE_mapping.outputs["Vector"], NODE_tex_N.inputs["Vector"])
        links.new(NODE_mapping.outputs["Vector"], NODE_tex_H.inputs["Vector"])
    else:
        if not isCustomMat:
            links.new(NODE_uvmap.outputs["UV"], NODE_tex_D.inputs["Vector"])
        links.new(NODE_uvmap.outputs["UV"], NODE_tex_R.inputs["Vector"])
        links.new(NODE_uvmap.outputs["UV"], NODE_tex_N.inputs["Vector"])
        links.new(NODE_uvmap.outputs["UV"], NODE_tex_H.inputs["Vector"])

    links.new(NODE_uvmap.outputs["UV"], NODE_tex_I.inputs["Vector"])

    if not isCustomMat:
        links.new(NODE_tex_D.outputs["Color"], NODE_bsdf.inputs["Base Color"]) #basecolor
        if not NODE_mapping:
            links.new(NODE_tex_D.outputs["Alpha"], NODE_bsdf.inputs["Alpha"]) if DTextureSuccess else None
    
    if RTextureSuccess:
        links.new(NODE_tex_R.outputs["Color"],  NODE_rgbsplit.inputs["Image"]) #RGB split
        links.new(NODE_rgbsplit.outputs["R"],  NODE_bsdf.inputs["Roughness"]) #roughness
        links.new(NODE_rgbsplit.outputs["G"],  NODE_bsdf.inputs["Metallic"]) #metallic

    if NTextureSuccess:
        links.new(NODE_tex_N.outputs["Color"],  NODE_normal_map.inputs["Color"]) #normal
        links.new(NODE_normal_map.outputs["Normal"],  NODE_bsdf.inputs["Normal"])
    
    links.new(NODE_tex_H.outputs["Color"],  NODE_bsdf.inputs["Emission Strength"]) if HTextureSuccess else None

    links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs["Emission"]) if ITextureSuccess else None
    
    links.new(NODE_bsdf.outputs["BSDF"],  NODE_output.inputs["Surface"])
    

    if mat.model.upper() == "TIADD":
        links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs["Alpha"])  #alpha
        links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs["Base Color"])   #basecolor
        NODE_bsdf.inputs["Emission Strength"].default_value = 100.0
        if not isCustomMat:
            nodes.remove(NODE_tex_D) #remove for solid view texture [0]

def _load_dds_into_blender(texpath: str) -> tuple:
    """load dds texture into blender, return tuple(bool(success), texNAME)"""
    imgs = bpy.data.images
    texpath = fixSlash(texpath)
    texName = get_path_filename(texpath)

    if not texpath: return False, "" 

    debug(f"try to load texture into blender: {texpath}")

    if is_file_exist(filepath=texpath):
    
        if texName not in imgs:
            imgs.load(texpath)
            debug(f"texture loaded: { texName }")
        
        else:
            debug(f"texture already loaded: { texName }")
            bpy.ops.file.find_missing_files( directory=getGameDocPathItemsAssetsTextures() )

        return True, texName
    
    else: 
        debug(f"failed to find file: {texName}")
        return False, texName

def _assign_texture_to_node(texname, node) -> bool:
    """assign blender already loaded texture (dds?) to given node of type ImageTexture"""
    imgs = bpy.data.images
    
    if texname in imgs:
        img = imgs[texname]
        node.image = img
        return True
    
    else:
        node.mute = True
        return False

def _get_mat_dds(tex: str, ddsType: str) -> str:
    Texture = ""
    basePath = "/".join(tex.split('/')[:-1]) + "/"
    matName = tex.split('/')[-1]

    matMap2020 = None
    if matName in MATERIALS_MAP_TM2020:
        matMap2020 = MATERIALS_MAP_TM2020[matName]

    debug(f"try to find:   {matName}_{ddsType}.dds")
    # if we have a map in 2020 dict -> use it, otherwise try default
    if (
        isGameTypeTrackmania2020() and
        matMap2020 and ddsType in matMap2020 and 
        len(matMap2020[ddsType]) > 0 and is_file_exist(basePath + matMap2020[ddsType])
    ): Texture = basePath + matMap2020[ddsType]
    elif is_file_exist(tex + "D.dds"): Texture = tex + ddsType+".dds"
    elif is_file_exist(tex + "_D.dds"): Texture = tex + "_"+ddsType+".dds"
    elif ddsType == "D" and is_file_exist(tex + ".dds"): Texture = tex + ".dds"
    debug(f"_{ddsType} found in: {Texture}") if Texture else debug(f"_{ddsType} texture not found")

    return Texture

def _delete_material_nodes(mat) -> None:
    """delete all nodes of material"""
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)