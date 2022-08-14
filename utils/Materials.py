import re
import bpy
import json

from .Functions import (
    debug,
    fixSlash,
    get_abs_path,
    get_path_filename,
    get_game_doc_path_items_assets_textures,
    get_game_doc_path,
    is_file_exist,
    isGameTypeTrackmania2020,
)

from .Constants import MAT_PROPS_AS_JSON, MATERIAL_CUSTOM_PROPERTIES, MATERIALS_MAP_TM2020

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
            bpy.ops.file.find_missing_files( directory=get_game_doc_path_items_assets_textures() )

        return True, texName
    
    else: 
        debug(f"failed to find file: {texName}")
        return False, texName

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
    create_material_nodes(mat)
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

    if is_file_exist( test_d_path_as_link ): tex_d_path = test_d_path_as_link
    if is_file_exist( test_i_path_as_link ): tex_i_path = test_i_path_as_link
    if is_file_exist( test_r_path_as_link ): tex_r_path = test_r_path_as_link
    if is_file_exist( test_n_path_as_link ): tex_n_path = test_n_path_as_link
    if is_file_exist( test_h_path_as_link ): tex_h_path = test_h_path_as_link

    print("ASDADSASD: ", tex_d_path)
    print("ASDADSASD: ", test_d_path_as_link)

    success, name = _load_dds_into_blender(tex_d_path)
    if success and name in imgs:
        tex_d.image = bpy.data.images[ name ]

    success, name = _load_dds_into_blender(tex_i_path)
    if success and name in imgs:
        tex_i.image = bpy.data.images[ name ]

    success, name = _load_dds_into_blender(tex_r_path)
    if success and name in imgs:
        tex_r.image = bpy.data.images[ name ]

    success, name = _load_dds_into_blender(tex_n_path)
    if success and name in imgs:
        tex_n.image = bpy.data.images[ name ]

    success, name = _load_dds_into_blender(tex_h_path)
    if success and name in imgs:
        tex_h.image = bpy.data.images[ name ]
            
        
    debug(matJSON, pp=True)
    del matJSON
    return True


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

    if isLinkedMat: tex = get_game_doc_path_items_assets_textures() + mat.environment + "/" + mat.link
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



def save_mat_props_json(mat) -> None:
    DICT = {}
    
    # material not created with this addon, no need to save it
    if mat is None or mat.name.startswith(("TM_", "MP_")) is False:
        return

    mat.surfaceColor = mat.diffuse_color[:3]
    if mat.use_nodes:
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