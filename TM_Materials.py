# region imports#
from inspect import getargs
import json
import bpy
import re

from bpy.types import (
    Panel,
    Operator,
)
from .TM_Functions  import *
from .TM_Properties import *
# endregion imports

class TM_OT_Materials_Create(Operator):
    bl_idname = "view3d.tm_creatematerial"
    bl_label = "create materials"
    bl_description = "create material"
   
    def execute(self, context):
        createOrUpdateMaterial("CREATE")
        context.region.tag_redraw()
        return {"FINISHED"}
    
    
class TM_OT_Materials_Update(Operator):
    bl_idname = "view3d.tm_updatematerial"
    bl_label = "update materials"
    bl_description = "update material"
   
    def execute(self, context):
        createOrUpdateMaterial("UPDATE")
        context.region.tag_redraw()
        return {"FINISHED"}


class TM_OT_Materials_ClearBaseMaterial(Operator):
    bl_idname = "view3d.tm_clearbasetexture"
    bl_label = "clear basematerial"
    bl_description = "clear basematerial"
   
    def execute(self, context):
        getTmProps()["ST_materialBaseTexture"] = ""
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
    
   
class TM_PT_Materials(Panel):
    bl_label = "Material Creation/Update"
    bl_idname = "OBJECT_PT_TM_Materials"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="MATERIAL")
    

    def draw(self, context):

        layout   = self.layout
        tm_props = getTmProps()
        
        if requireValidNadeoINI(self) is False: return

        action      = tm_props.LI_materialAction
        mat_name     = tm_props.ST_materialAddName
        mat_name_old  = tm_props.ST_selectedExistingMaterial

        action_is_update = action == "UPDATE"
    
        use_physicsId   = tm_props.CB_materialUsePhysicsId
        use_gameplayId  = tm_props.CB_materialUseGameplayId

        #uncomment it during development if you need to generate new assets library file
        #box = layout.box()
        #row = box.row()
        #row.operator("view3d.tm_createassetlib", text=f"Create {tm_props.LI_gameType} Assets Library", icon="ADD")


        # choose action & mat name
        layout.row().prop(tm_props, "LI_materialAction", expand=True)

        if action_is_update:
            layout.row().prop_search(tm_props, "ST_selectedExistingMaterial", bpy.data, "materials") 
    
        layout.row().prop(tm_props, "ST_materialAddName")

        # row = layout.row()
        # row.enabled = True if not tm_props.CB_converting else False
        # row.prop(tm_props, "LI_gameType", text="Game")





        if isGameTypeManiaPlanet():
            row = layout.row()
            row.prop(tm_props, "LI_materialCollection", text="Collection")
            
            enable = True if use_physicsId else False
            icon   = ICON_TRUE if enable else ICON_FALSE

            row = layout.row(align=True)
            col = row.column()
            col.enabled = enable
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=icon)
            
            layout.separator(factor=UI_SPACER_FACTOR)

            # choose custom tex or linked mat
            row = layout.row(align=True)
            # col = row.column()
            # col.label(text="Source:")

            # col = row.column()
            # row = col.row()
            row.prop(tm_props, "LI_materialChooseSource", expand=True)
            
            using_custom_texture = tm_props.LI_materialChooseSource == "CUSTOM"

            # basetexture
            if using_custom_texture:
                row = layout.row(align=True)
                row.alert = True if "/Items/" not in fixSlash(tm_props.ST_materialBaseTexture) else False
                row.prop(tm_props, "ST_materialBaseTexture", text="Location")
                row.operator("view3d.tm_clearbasetexture", icon="X", text="")

                if row.alert:
                    row=layout.row()
                    row.alert = True
                    row.label(text=".dds file in Documents/Maniaplanet/Items/")

                # model
                row = layout.row()
                row.prop(tm_props, "LI_materialModel")
            

            # link
            else:
                row = layout.row()
                row.prop_search(
                    tm_props, "ST_selectedLinkedMat", # value of selection
                    context.scene, "tm_props_linkedMaterials", # list to search in 
                    icon="LINKED",
                    text="Link") 




        elif isGameTypeTrackmania2020():
            # physics id
            enable = True if use_physicsId else False
            icon   = ICON_TRUE if enable else ICON_FALSE

            row = layout.row(align=True)
            col = row.column()
            col.enabled = enable
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=icon)

            # gameplay id
            enable = True if use_gameplayId else False
            icon   = ICON_TRUE if enable else ICON_FALSE
            
            row = layout.row(align=True)
            col = row.column()
            col.enabled = enable
            col.prop(tm_props, "LI_materialGameplayId", text="Gameplay")
            col = row.column()
            col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon=icon)

            # custom color for materials starts with "custom"
            mat_uses_custom_color = tm_props.ST_selectedLinkedMat.lower().startswith("custom")

            row = layout.row(align=True)
            row.alert = mat_uses_custom_color
            col = row.column()
            col.scale_x = .55
            col.label(text="Color")
            col = row.column()
            col.prop(tm_props, "NU_materialCustomColor", text="")
            if action_is_update:
                row.operator("view3d.tm_revertcustomcolor", icon="FILE_REFRESH", text="")
            
            # Link
            row = layout.row()
            row.prop_search(
                tm_props, "ST_selectedLinkedMat", # value of selection
                context.scene, "tm_props_linkedMaterials", # list to search in 
                icon="LINKED",
                text="Link") 


        row = layout.row()
        row.scale_y = 1.5

        if action_is_update:
            row.operator("view3d.tm_updatematerial", text=f"Update {mat_name_old}", icon="FILE_REFRESH")

        else:
            row.operator("view3d.tm_creatematerial", text=f"Create {mat_name}",    icon="ADD")


        layout.separator(factor=UI_SPACER_FACTOR)


            
        






def createOrUpdateMaterial(action)->None:
    """create a export/convert ready material for TM and MP"""
    tm_props = getTmProps()
    
    TM_PREFIX = "TM_"
    MP_PREFIX = "MP_"

    matName          = tm_props.ST_selectedExistingMaterial
    matNameNew       = fixName( tm_props.ST_materialAddName )
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
        makeReportPopup(
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
        makeReportPopup(
            title=f"Material {matNameNew} successfully created!",
            icon ="CHECKMARK"
        )
        debug(f"Material {matNameNew} created")
    else: #UPDATE
        makeReportPopup(
            title=f"Material {matName} sucessfully updated", 
            icon= "CHECKMARK"
        )
        debug(f"Material {matName} updated")

    createMaterialNodes(MAT)
    applyMaterialLiveChanges()

   




def deleteMaterialNodes(mat) -> None:
    """delete all nodes of material"""
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)



        
def createMaterialNodes(mat)->None:
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
    
    deleteMaterialNodes(mat=mat)

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
        DTexture = getMatDDS(tex, "D")
    
    ITexture = getMatDDS(tex, "I")
    RTexture = getMatDDS(tex, "R")
    NTexture = getMatDDS(tex, "N")
    HTexture = getMatDDS(tex, "H")

    if not isCustomMat:
        DTexture = loadDDSTextureIntoBlender(texpath=DTexture)
    ITexture = loadDDSTextureIntoBlender(texpath=ITexture)
    RTexture = loadDDSTextureIntoBlender(texpath=RTexture)
    NTexture = loadDDSTextureIntoBlender(texpath=NTexture)
    HTexture = loadDDSTextureIntoBlender(texpath=HTexture)

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
        assignTextureToImageNode(DTextureName, NODE_tex_D)

    if ITextureSuccess:
        assignTextureToImageNode(ITextureName, NODE_tex_I)

    if RTextureSuccess:
        assignTextureToImageNode(RTextureName, NODE_tex_R)

    if NTextureSuccess:
        assignTextureToImageNode(NTextureName, NODE_tex_N)
        NODE_tex_N.image.colorspace_settings.name = "Non-Color"

    if HTextureSuccess:
        assignTextureToImageNode(HTextureName, NODE_tex_H)

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





def loadDDSTextureIntoBlender(texpath: str) -> tuple:
    """load dds texture into blender, return tuple(bool(success), texNAME)"""
    imgs = bpy.data.images
    texpath = fixSlash(texpath)
    texName = fileNameOfPath(texpath)

    if not texpath: return False, "" 

    debug(f"try to load texture into blender: {texpath}")

    if doesFileExist(filepath=texpath):
    
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







def assignTextureToImageNode(texname, node) -> bool:
    """assign blender already loaded texture (dds?) to given node of type ImageTexture"""
    imgs = bpy.data.images
    
    if texname in imgs:
        img = imgs[texname]
        node.image = img
        return True
    
    else:
        node.mute = True
        return False





# only type int|bool|str can be saved as custom prop in fbx,
# so save all props as JSON in a str prop



def saveMatPropsAsJSONinMat(mat) -> None:
    """save mat.prop, mat.prop123 as json string in mat["TM_PROPS_AS_JSON] for export"""
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
                prop = getAbspath(prop)

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
        
        DICT["tex_d_path"] = getAbspath(tex_d_path)
        DICT["tex_i_path"] = getAbspath(tex_i_path)
        DICT["tex_r_path"] = getAbspath(tex_r_path)
        DICT["tex_n_path"] = getAbspath(tex_n_path)
        DICT["tex_h_path"] = getAbspath(tex_h_path)

    JSON = json.dumps(DICT)
    mat[ MAT_PROPS_AS_JSON ] = JSON
    debug(f"saved json in material <{mat.name}>:")
    debug(DICT, pp=True)





# custom properties of type int|bool|str can be saved in fbx.materials,
# so convert all custom props to JSON and save them as str prop
def assignMatJSONpropsToMat(mat) -> bool:
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
    createMaterialNodes(mat)
    imgs  = bpy.data.images
    nodes = mat.node_tree.nodes
    tex_d = getattr(nodes, "tex_D", "")
    tex_i = getattr(nodes, "tex_I", "")
    tex_r = getattr(nodes, "tex_R", "")
    tex_n = getattr(nodes, "tex_N", "")
    tex_h = getattr(nodes, "tex_H", "")

    btex  = getattr(DICT, "baseTexture", "")
    envi  = getattr(DICT, "environment", "")
    root  = getGameDocPathItemsAssetsTextures()
    root  = root + envi + "/"

    tex_d_path = getattr(DICT, "tex_d_path", False) or getGameDocPath() + btex + "_D.dds"
    tex_i_path = getattr(DICT, "tex_i_path", False) or getGameDocPath() + btex + "_I.dds"
    tex_r_path = getattr(DICT, "tex_r_path", False) or getGameDocPath() + btex + "_R.dds"
    tex_n_path = getattr(DICT, "tex_n_path", False) or getGameDocPath() + btex + "_N.dds"
    tex_h_path = getattr(DICT, "tex_h_path", False) or getGameDocPath() + btex + "_H.dds"

    test_d_path_as_link = root + tex_d_path.split("/")[-1]
    test_i_path_as_link = root + tex_i_path.split("/")[-1]
    test_r_path_as_link = root + tex_r_path.split("/")[-1]
    test_n_path_as_link = root + tex_n_path.split("/")[-1]
    test_h_path_as_link = root + tex_h_path.split("/")[-1]

    if doesFileExist( test_d_path_as_link ): tex_d_path = test_d_path_as_link
    if doesFileExist( test_i_path_as_link ): tex_i_path = test_i_path_as_link
    if doesFileExist( test_r_path_as_link ): tex_r_path = test_r_path_as_link
    if doesFileExist( test_n_path_as_link ): tex_n_path = test_n_path_as_link
    if doesFileExist( test_h_path_as_link ): tex_h_path = test_h_path_as_link

    debug(tex_d_path)
    debug(test_d_path_as_link)

    success, name = loadDDSTextureIntoBlender(tex_d_path)
    if success and name in imgs:
        tex_d.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_i_path)
    if success and name in imgs:
        tex_i.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_r_path)
    if success and name in imgs:
        tex_r.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_n_path)
    if success and name in imgs:
        tex_n.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_h_path)
    if success and name in imgs:
        tex_h.image = bpy.data.images[ name ]
            
        
    debug(matJSON, pp=True)
    del matJSON
    return True





def fixMaterialNames(obj) -> None:
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



def getMatDDS(tex: str, ddsType: str) -> str:
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
        len(matMap2020[ddsType]) > 0 and doesFileExist(basePath + matMap2020[ddsType])
    ): Texture = basePath + matMap2020[ddsType]
    elif doesFileExist(tex + "D.dds"): Texture = tex + ddsType+".dds"
    elif doesFileExist(tex + "_D.dds"): Texture = tex + "_"+ddsType+".dds"
    elif ddsType == "D" and doesFileExist(tex + ".dds"): Texture = tex + ".dds"
    debug(f"_{ddsType} found in: {Texture}") if Texture else debug(f"_{ddsType} texture not found")

    return Texture



#! not in use
def importMaterialsFromJSON(filepath) -> None:
    """import materials from json file"""
    filepath  = filepath.replace("fbx", "json")
    mats_dict = None
    mats = bpy.data.materials

    with open(filepath, "r") as f:
        content = f.read()
        mats_dict = json.loads(content)
    
    for mat in mats_dict:
        mat = mats_dict[mat]
        
        if mat["name"] not in mats:
            newMat = bpy.data.materials.new(mat["name"])
            for prop in MATERIAL_CUSTOM_PROPERTIES:
                debug(prop)
                exec(f"""{newMat}.{prop}={mat[prop]}""")
    




#! not in use
def exportMaterialsAsJSON(col, filepath) -> None:
    """fbx export custom properties does not export material custom properties, create json..."""
    # filename = fileNameOfPath(filepath) 
    # filepath = filepath.replace( filename, f".{filename}" ) #dot does not hide files in windows...
    filepath = filepath.replace("json", "Materials.json")
    mats_dict = {}
    objs = col.objects

    for obj in objs:
        if obj.type != "MESH": continue

        for mat in obj.data.materials:
            
            # generate dict for each material
            try:
                if mat.name in mats_dict: continue

                debug(mat.name)

                mat_dict = {}
                for prop_name in MATERIAL_CUSTOM_PROPERTIES:
                    
                    prop = getattr(mat, prop_name)
                    if prop.__class__.__name__ == "Color":
                        prop = [prop.r, prop.g, prop.b]

                    mat_dict[prop_name] = prop
                
                mats_dict[mat.name] = mat_dict
            
            except KeyError: raise



    JSON = json.dumps(mats_dict, indent=4, sort_keys=True)

    debug(f"write material JSON file for {col.name}")
    debug(filepath)
    with open(filepath, "w") as f:
        f.write(JSON)


