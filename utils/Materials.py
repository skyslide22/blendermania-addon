import re
import bpy
import json

from .Functions import (
    debug,
    get_abs_path,
    get_game_doc_path_items_assets_textures,
    get_game_doc_path,
    get_global_props,
    is_file_existing,
    is_game_trackmania2020,
    load_image_into_blender,
)
from .MaterialsNodesGenerated import MATERIAL_NODES_CREATORS

from .Constants import MAT_PROPS_AS_JSON, MATERIAL_CUSTOM_PROPERTIES, MATERIALS_MAP_TM2020

x = lambda step:  (300 * step)
y = lambda step: -(300 * step)

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
    matName = tex.split('/')[-1]

    debug(f"try to find:   {matName}_{ddsType}.dds")
    if is_file_existing(tex + f"{ddsType}.dds"): Texture = tex + ddsType+".dds"
    elif is_file_existing(tex + f"_{ddsType}.dds"): Texture = tex + "_"+ddsType+".dds"
    elif ddsType == "D" and is_file_existing(tex + ".dds"): Texture = tex + ".dds"
    debug(f"_{ddsType} found in: {Texture}") if Texture else debug(f"_{ddsType} texture not found")

    return Texture

def _delete_material_nodes(mat) -> None:
    """delete all nodes of material"""
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

def _create_material_tex_node(mat: bpy.types.Material, location: tuple[int, int], label: str, name: str) -> bpy.types.ShaderNodeTexImage:
    node = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
    node.location = x(location[0]), y(location[1])
    node.label = label
    node.name  = name

    return node

def fix_material_names(obj) -> None:
    """MyMaterial.001 => MyMaterial, join materials."""
    slots = obj.material_slots
    mats  = bpy.data.materials
    regex = r"\.\d+$"
    
    for slot in slots:
        mat     = slot.material
        if mat is None: continue

        if re.search(regex, mat.name):
            
            try:
                matNameNoCountSuffix = re.sub(regex, "", mat.name)
                newmat = mats[matNameNoCountSuffix]
                slot.material = newmat 
            
            except KeyError: #mat.001 exists, mat not
                pass
            
        #delete now unused .001 mat
        if re.search(regex, mat.name):
            bpy.data.materials.remove(mat)

def create_material_shader(mat: bpy.types.Material) -> None:
    if is_game_trackmania2020() and mat.link in MATERIALS_MAP_TM2020:
        if _create_material_shader_specific(mat):
            return

    _create_default_material_nodes(mat)

def _create_material_shader_specific(mat: bpy.types.Material) -> bool:
    matData = MATERIALS_MAP_TM2020[mat.link]
    if matData and matData["Textures"] and len(matData["Textures"].keys()) > 0:
        shaderName = list(matData["Textures"].keys())[0]
        if shaderName in MATERIAL_NODES_CREATORS:
            mat.use_nodes = True
            mat.diffuse_color = (*mat.surfaceColor, 1)
            mat.blend_method= "BLEND"
            mat.show_transparent_back = False
            mat.use_backface_culling  = False
            _delete_material_nodes(mat=mat)

            MATERIAL_NODES_CREATORS[shaderName](mat)
            if "Principled BSDF" in mat.node_tree.nodes:
                mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0,0,0, 1)

            textures = matData["Textures"][shaderName]
            for texKey, texDDS in textures.items():
                texPath = get_game_doc_path_items_assets_textures() + mat.environment + "/" + texDDS
                custom_tex_source_folder = get_global_props().ST_TextureSource
                if custom_tex_source_folder != "":
                    texPath = custom_tex_source_folder + "/" + texDDS

                texData = load_image_into_blender(texPath)
                if texData[0] and f"tex{texKey}" in mat.node_tree.nodes:
                    if _assign_texture_to_node(texData[1], mat.node_tree.nodes[f"tex{texKey}"]):
                        if texKey == "_N":
                            mat.node_tree.nodes[f"tex{texKey}"].image.colorspace_settings.name = "Non-Color"
            
            if "cus_color" in mat.node_tree.nodes:
                surfaceColor = mat.surfaceColor
                surfaceColor = (*surfaceColor, 1)
                mat.node_tree.nodes["cus_color"].outputs[0].default_value = surfaceColor

            if "uv_scale" in mat.node_tree.nodes and "DefaultUVScale" in matData and matData["DefaultUVScale"] > 0:
                mat.node_tree.nodes["uv_scale"].inputs["Scale"].default_value = matData["DefaultUVScale"]

            if f"tex_D" in mat.node_tree.nodes and mat.node_tree.nodes["tex_D"].image:
                mat.node_tree.nodes.active = mat.node_tree.nodes["tex_D"]
            elif f"tex_I" in mat.node_tree.nodes and mat.node_tree.nodes["tex_I"].image:
                mat.node_tree.nodes.active = mat.node_tree.nodes["tex_I"]

            return True

    return False


def _create_default_material_nodes(mat: bpy.types.Material)->None:
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

    # output
    NODE_output = nodes.new(type="ShaderNodeOutputMaterial")
    NODE_output.location = x(4), y(1)

    # bsdf node input changes in blender 4.0 +
    blender_is_v4_or_newer = bpy.app.version[0] >= 4

    input_name_specular = "Specular IOR Level" if blender_is_v4_or_newer else "Specular"
    input_name_emission = "Emission Color" if blender_is_v4_or_newer else "Emission"

    # big node with all stuff
    NODE_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    NODE_bsdf.subsurface_method = "BURLEY"
    NODE_bsdf.location = x(3), y(1)
    NODE_bsdf.inputs[input_name_specular].default_value = 0 #.specular

    is_tiadd = mat.model.lower() == "tiadd"
    NODE_bsdf.inputs["Emission Strength"].default_value = 3.0 if is_tiadd else 0.0
    NODE_bsdf.inputs["Base Color"].default_value = surfaceColor

    # uvmap basematerial
    NODE_uvmap = nodes.new(type="ShaderNodeUVMap")
    NODE_uvmap.location = x(0), y(1)
    NODE_uvmap.from_instancer = True

    # main texture, custom materials don't have it
    if not isCustomMat:
        NODE_tex_D = _create_material_tex_node(mat, (1, 1), "Texture Diffuse _D.dds", "tex_D")

    NODE_tex_R = _create_material_tex_node(mat, (1, 2), "Texture Roughness _R.dds", "tex_R")
    NODE_tex_N = _create_material_tex_node(mat, (1, 3), "Texture Normal _N.dds", "tex_N")
    NODE_tex_I = _create_material_tex_node(mat, (1, 4), "Texture Illum _I.dds", "tex_I")
    NODE_tex_H = _create_material_tex_node(mat, (1, 5), "Texture Height _H.dds", "tex_H")

    # rgb split
    NODE_rgbsplit = nodes.new(type="ShaderNodeSeparateRGB")
    NODE_rgbsplit.location = x(2), y(2)

    # normal map
    NODE_normal_map = nodes.new(type="ShaderNodeNormalMap")
    NODE_normal_map.location = x(2), y(3)

    tex = ""
    DTexture = ""
    ITexture = ""
    RTexture = ""
    NTexture = ""
    HTexture = ""

    isLinkedMat = mat.baseTexture == ""
    
    debug(f"material link is :  {mat.link}")
    debug(f"material is a link: {isLinkedMat}")

    if isLinkedMat: 
        tex = get_game_doc_path_items_assets_textures() + mat.environment + "/" + mat.link
        
        tm_props = get_global_props()
        custom_tex_source_folder = tm_props.ST_TextureSource
        if custom_tex_source_folder != "":
            tex = custom_tex_source_folder + "/" + mat.link
    else:
        tex = re.sub(r"_?(i|d)\.dds$", "", mat.baseTexture, flags=re.IGNORECASE)

    if not isCustomMat:
        DTexture = _get_mat_dds(tex, "D")
    
    ITexture = _get_mat_dds(tex, "I")
    RTexture = _get_mat_dds(tex, "R")
    NTexture = _get_mat_dds(tex, "N")
    HTexture = _get_mat_dds(tex, "H")

    if not isCustomMat:
        DTexture = load_image_into_blender(texpath=DTexture)
    ITexture = load_image_into_blender(texpath=ITexture)
    RTexture = load_image_into_blender(texpath=RTexture)
    NTexture = load_image_into_blender(texpath=NTexture)
    HTexture = load_image_into_blender(texpath=HTexture)

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

    if not isCustomMat:
        links.new(NODE_uvmap.outputs["UV"], NODE_tex_D.inputs["Vector"])
    links.new(NODE_uvmap.outputs["UV"], NODE_tex_R.inputs["Vector"])
    links.new(NODE_uvmap.outputs["UV"], NODE_tex_N.inputs["Vector"])
    links.new(NODE_uvmap.outputs["UV"], NODE_tex_H.inputs["Vector"])

    links.new(NODE_uvmap.outputs["UV"], NODE_tex_I.inputs["Vector"])

    if not isCustomMat:
        links.new(NODE_tex_D.outputs["Color"], NODE_bsdf.inputs["Base Color"]) #basecolor
        links.new(NODE_tex_D.outputs["Alpha"], NODE_bsdf.inputs["Alpha"]) if DTextureSuccess else None
    
    if RTextureSuccess:
        links.new(NODE_tex_R.outputs["Color"],  NODE_rgbsplit.inputs["Image"]) #RGB split
        links.new(NODE_rgbsplit.outputs["R"],  NODE_bsdf.inputs["Roughness"]) #roughness
        links.new(NODE_rgbsplit.outputs["G"],  NODE_bsdf.inputs["Metallic"]) #metallic

    if NTextureSuccess:
        links.new(NODE_tex_N.outputs["Color"],  NODE_normal_map.inputs["Color"]) #normal
        links.new(NODE_normal_map.outputs["Normal"],  NODE_bsdf.inputs["Normal"])
    
    links.new(NODE_tex_H.outputs["Color"], NODE_bsdf.inputs["Emission Strength"]) if HTextureSuccess else None
    links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs[input_name_emission]) if ITextureSuccess else None
    links.new(NODE_bsdf.outputs["BSDF"],   NODE_output.inputs["Surface"])
    
    if mat.model.upper() == "TIADD":
        links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs["Alpha"])  #alpha
        links.new(NODE_tex_I.outputs["Color"], NODE_bsdf.inputs["Base Color"])   #basecolor
        NODE_bsdf.inputs["Emission Strength"].default_value = 100.0
        if not isCustomMat:
            nodes.remove(NODE_tex_D) #remove for solid view texture [0]



def is_material_exportable(mat) -> bool:
    valid = True

    # link or baseTexture needs to have a value
    # if not, material has not been modified with the addon
    if not mat.link and not mat.baseTexture:
        valid = False

    # if physicsid is enabled but has no value, material is invalid
    if mat.usePhysicsId and not mat.physicsId:
        valid = False

    return valid


def save_mat_props_json(mat) -> None:
    DICT = {}
    
    # material not created with this addon, no need to save it
    if mat is None or mat.name.startswith(("TM_", "MP_")) is False:
        return

    mat.surfaceColor = mat.diffuse_color[:3]
    if mat.use_nodes:
        if "cus_color" in mat.node_tree.nodes:
            mat.surfaceColor = mat.node_tree.nodes["cus_color"].outputs[0].default_value[:3]
        else:
            mat.surfaceColor = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]

    #tm_props
    for prop_name in MATERIAL_CUSTOM_PROPERTIES:
        prop = getattr(mat, prop_name, None)
        
        if prop is None: continue
        
        if prop.__class__.__name__ == "Color":
            prop = [prop[0], prop[1], prop[2]]

        if isinstance(prop, str):
            if prop.startswith("//"):
                prop = bpy.path.abspath(prop)
                prop = get_abs_path(prop)

        DICT[prop_name] = prop
    

    if mat.use_nodes:
        nodes = mat.node_tree.nodes
        tex_d = nodes["tex_D"].image if "tex_D" in nodes else None
        tex_i = nodes["tex_I"].image if "tex_I" in nodes else None
        tex_r = nodes["tex_R"].image if "tex_R" in nodes else None
        tex_n = nodes["tex_N"].image if "tex_N" in nodes else None
        tex_h = nodes["tex_H"].image if "tex_H" in nodes else None
            
        tex_d_path = tex_d.filepath if tex_d else ""
        tex_i_path = tex_i.filepath if tex_i else ""
        tex_r_path = tex_r.filepath if tex_r else ""
        tex_n_path = tex_n.filepath if tex_n else ""
        tex_h_path = tex_h.filepath if tex_h else ""
        
        DICT["tex_d_path"] = get_abs_path(tex_d_path)
        DICT["tex_i_path"] = get_abs_path(tex_i_path)
        DICT["tex_r_path"] = get_abs_path(tex_r_path)
        DICT["tex_n_path"] = get_abs_path(tex_n_path)
        DICT["tex_h_path"] = get_abs_path(tex_h_path)

    JSON = json.dumps(DICT)
    mat[ MAT_PROPS_AS_JSON ] = JSON


# custom properties of type int|bool|str can be saved in fbx.materials,
# so convert all custom props to JSON and save them as str prop
def assign_mat_json_to_mat(mat) -> bool:
    """used for mats of imported objs, take saved props in JSON and assign to the mat"""
    try:
        matJSON = mat.get( MAT_PROPS_AS_JSON )
        if matJSON == "": raise KeyError
    
    except KeyError: #empty or not found
        return False

    if matJSON is None: return False

    try:    DICT = json.loads(matJSON)
    except: return False
    
    mat.use_nodes = True

    #assign mat tm_props to mat
    for prop in DICT:
        if prop.startswith("tex_"): continue
        try:    setattr(mat, prop, DICT[prop])
        except: return False


    #assign textures
    _create_default_material_nodes(mat)
    imgs  = bpy.data.images
    nodes = mat.node_tree.nodes
    tex_d = getattr(nodes, "tex_D", "")
    tex_i = getattr(nodes, "tex_I", "")
    tex_r = getattr(nodes, "tex_R", "")
    tex_n = getattr(nodes, "tex_N", "")
    tex_h = getattr(nodes, "tex_H", "")

    btex  = getattr(DICT, "baseTexture", "")
    envi  = getattr(DICT, "environment", "")
    root  = get_game_doc_path_items_assets_textures()
    root  = root + envi + "/"

    tex_d_path = getattr(DICT, "tex_d_path", False) or get_game_doc_path() + btex + "_D.dds"
    tex_i_path = getattr(DICT, "tex_i_path", False) or get_game_doc_path() + btex + "_I.dds"
    tex_r_path = getattr(DICT, "tex_r_path", False) or get_game_doc_path() + btex + "_R.dds"
    tex_n_path = getattr(DICT, "tex_n_path", False) or get_game_doc_path() + btex + "_N.dds"
    tex_h_path = getattr(DICT, "tex_h_path", False) or get_game_doc_path() + btex + "_H.dds"

    test_d_path_as_link = root + tex_d_path.split("/")[-1]
    test_i_path_as_link = root + tex_i_path.split("/")[-1]
    test_r_path_as_link = root + tex_r_path.split("/")[-1]
    test_n_path_as_link = root + tex_n_path.split("/")[-1]
    test_h_path_as_link = root + tex_h_path.split("/")[-1]

    if is_file_existing( test_d_path_as_link ): tex_d_path = test_d_path_as_link
    if is_file_existing( test_i_path_as_link ): tex_i_path = test_i_path_as_link
    if is_file_existing( test_r_path_as_link ): tex_r_path = test_r_path_as_link
    if is_file_existing( test_n_path_as_link ): tex_n_path = test_n_path_as_link
    if is_file_existing( test_h_path_as_link ): tex_h_path = test_h_path_as_link

    success, name = load_image_into_blender(tex_d_path)
    if success and name in imgs:
        tex_d.image = bpy.data.images[ name ]

    success, name = load_image_into_blender(tex_i_path)
    if success and name in imgs:
        tex_i.image = bpy.data.images[ name ]

    success, name = load_image_into_blender(tex_r_path)
    if success and name in imgs:
        tex_r.image = bpy.data.images[ name ]

    success, name = load_image_into_blender(tex_n_path)
    if success and name in imgs:
        tex_n.image = bpy.data.images[ name ]

    success, name = load_image_into_blender(tex_h_path)
    if success and name in imgs:
        tex_h.image = bpy.data.images[ name ]
            
        
    debug(matJSON, pp=True)
    del matJSON
    return True