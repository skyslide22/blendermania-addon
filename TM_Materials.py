# region imports#
from inspect import getargs
import json
import bpy
import os.path
import re
import xml.etree.ElementTree as ET
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    IntProperty
)
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .TM_Functions  import *
from .TM_Properties import *
# endregion imports




class TM_OT_Materials_Create(Operator):
    bl_idname = "view3d.tm_creatematerial"
    bl_label = "create materials"
    bl_desciption = "create material"
   
    def execute(self, context):
        createOrUpdateMaterial("CREATE")
        context.region.tag_redraw()
        return {"FINISHED"}
    
    
class TM_OT_Materials_Update(Operator):
    bl_idname = "view3d.tm_updatematerial"
    bl_label = "update materials"
    bl_desciption = "update material"
   
    def execute(self, context):
        createOrUpdateMaterial("UPDATE")
        context.region.tag_redraw()
        return {"FINISHED"}


class TM_OT_Materials_ClearBaseMaterial(Operator):
    bl_idname = "view3d.tm_clearbasetexture"
    bl_label = "clear basematerial"
    bl_desciption = "clear basematerial"
   
    def execute(self, context):
        clearProperty("ST_materialBaseTexture", "")
        context.region.tag_redraw()
        return {"FINISHED"}
    
   
class TM_PT_Materials(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label = "Material Creation/Update"
    bl_idname = "OBJECT_PT_TM_Materials"
    locals().update( panelClassDefaultProps )


    # endregion
    
    def draw(self, context):

        layout   = self.layout
        tm_props = getTmProps()
        
        if requireValidNadeoINI(self) is False: return

        action      = tm_props.LI_materialAction
        mat_name     = tm_props.ST_materialAddName
        mat_name_old  = tm_props.LI_materials

        action_is_update = action == "UPDATE"
    
        use_physicsId   = tm_props.CB_materialUsePhysicsId
        use_gameplayId  = tm_props.CB_materialUseGameplayId
        use_customColor = tm_props.CB_materialUseCustomColor
        mat_is_colorable = str(tm_props.LI_materialLink).lower().startswith("custom")




        # choose action & mat name
        layout.row().prop(tm_props, "LI_materialAction", expand=True)
        
        layout.row().prop(tm_props, "LI_materials") if action_is_update else None
        layout.row().prop(tm_props, "ST_materialAddName")

        row = layout.row()
        row.enabled = True if not tm_props.CB_converting else False
        row.prop(tm_props, "LI_gameType", text="Game")





        if isGameTypeManiaPlanet():
            row = layout.row()
            row.prop(tm_props, "LI_materialCollection", text="Collection")
            
            # physics id
            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_physicsId else False
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon="HIDE_OFF")
            
            layout.separator(factor=UI_SPACER_FACTOR)

            # choose custom tex or linked mat
            row = layout.row(align=True)
            col = row.column()
            col.label(text="Texture:")

            col = row.column()
            row = col.row()
            row.prop(tm_props, "LI_materialChooseSource", expand=True)
            
            using_custom_texture = tm_props.LI_materialChooseSource == "CUSTOM"

            # basetexture
            if using_custom_texture:
                row = layout.row(align=True)
                row.alert = True if "/Items/" not in fixSlash(tm_props.ST_materialBaseTexture) else False
                row.prop(tm_props, "ST_materialBaseTexture", text="Location")
                row.operator("view3d.tm_clearbasetexture", icon="X", text="")

                # model
                row = layout.row()
                row.prop(tm_props, "LI_materialModel")
            

            # link
            else:
                row = layout.row()
                row.prop(tm_props, "LI_materialLink", text="Link") 




        elif isGameTypeTrackmania2020():
            # Link
            row = layout.row()
            row.prop(tm_props, "LI_materialLink", text="Link")
            
            # physics id
            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_physicsId else False
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon="CHECKMARK")

            # gameplay id
            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_gameplayId else False
            col.prop(tm_props, "LI_materialGameplayId", text="Gameplay")
            col = row.column()
            col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon="CHECKMARK")

            
            # custom color
            if mat_is_colorable:
                row = layout.row(align=True)
                
                col = row.column()
                col.label(text="Color:")
                col.enabled = use_customColor

                col = row.column()
                col.enabled = use_customColor
                col.prop(tm_props, "NU_materialColor", text="")
                col = row.column()
                col.prop(tm_props, "CB_materialUseCustomColor", text="", toggle=True, icon="CHECKMARK")



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

    matName           = tm_props.LI_materials
    matNameNew        = fixName( tm_props.ST_materialAddName )
    matGameType       = tm_props.LI_gameType
    matCollection     = tm_props.LI_materialCollection
    matPhysicsId      = tm_props.LI_materialPhysicsId
    matUsePhysicsId   = tm_props.CB_materialUsePhysicsId
    matGameplayId     = tm_props.LI_materialGameplayId
    matUseGameplayId  = tm_props.CB_materialUseGameplayId
    matModel          = tm_props.LI_materialModel
    matLink           = tm_props.LI_materialLink
    matBaseTexture    = tm_props.ST_materialBaseTexture
    matColor          = tm_props.NU_materialColor
    matUseCustomColor = tm_props.CB_materialUseCustomColor
    MAT = None


    if isGameTypeTrackmania2020():
        if not matNameNew.startswith(TM_PREFIX):
            matNameNew = TM_PREFIX + matNameNew.replace(MP_PREFIX, "") 

    if isGameTypeManiaPlanet():
        if not matNameNew.startswith(MP_PREFIX):
            matNameNew = MP_PREFIX + matNameNew.replace(TM_PREFIX, "") 

    if action == "CREATE":
        if matNameNew in bpy.data.materials:
            makeReportPopup(
                title="Material with this name already exists", 
                infos=["Creation failed"], 
                icon= "ERROR")
            debug(f"Material {matNameNew} creation failed")
            return

        else:
            MAT = bpy.data.materials.new(name=matNameNew)
            MAT.gameType       = matGameType
            MAT.environment    = matCollection
            MAT.usePhysicsId   = matUsePhysicsId
            MAT.physicsId      = matPhysicsId
            MAT.useGameplayId  = matUseGameplayId
            MAT.gameplayId     = matGameplayId
            MAT.model          = matModel
            MAT.link           = matLink
            MAT.baseTexture    = matBaseTexture
            MAT.surfaceColor   = matColor
            MAT.useCustomColor = matUseCustomColor
            makeReportPopup(
                title=f"Material {matNameNew} successfully created!",
                icon ="CHECKMARK"
            )
            debug(f"Material {matNameNew} created")
    

    else: #UPDATE
        MAT = bpy.data.materials[matName]
        MAT.gameType       = matGameType
        MAT.environment    = matCollection
        MAT.usePhysicsId   = matUsePhysicsId
        MAT.physicsId      = matPhysicsId
        MAT.useGameplayId  = matUseGameplayId
        MAT.gameplayId     = matGameplayId
        MAT.model          = matModel
        MAT.link           = matLink
        MAT.baseTexture    = matBaseTexture if isGameTypeManiaPlanet() else ""
        MAT.surfaceColor   = matColor
        MAT.useCustomColor = matUseCustomColor
        MAT.name           = matNameNew
        makeReportPopup(
            title=f"Material {matName} sucessfully updated", 
            icon= "CHECKMARK"
        )
        debug(f"Material {matName} updated")

    createMaterialNodes(MAT)

   


def deleteMaterialNodes(mat) -> None:
    """delete all nodes of material"""
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)



        
def createMaterialNodes(mat)->None:
    """create material nodes"""
    debug(f"start creating material nodes for {mat.name}")
    usesColorOnly   = mat.link.lower().startswith("custom")
    mat.use_nodes   = not usesColorOnly
    mat.blend_method= "HASHED" #BLEND
    mat.show_transparent_back = False #backface culling
    mat.use_backface_culling  = False #backface culling

    if usesColorOnly:
        color = (*mat.surfaceColor, 1) #0,0,0,0 (make tuple size 4 instead of 3, (alpha necessary))
        mat.diffuse_color = color
        mat.specular_intensity = 0
        return #tm2020 customXYZ texture(link) uses no textures only color

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
    NODE_bsdf.location = x(3), y(1)
    NODE_bsdf.inputs[5 ].default_value = 0 #.specular
    NODE_bsdf.inputs[18].default_value = 3.0

    # uvmap basematerial
    NODE_uvmap = nodes.new(type="ShaderNodeUVMap")
    NODE_uvmap.location = x(0), y(1)
    NODE_uvmap.uv_map = "BaseMaterial"

    # main texture
    NODE_tex_D = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_D.location = x(1), y(1)
    NODE_tex_D.label = "Texture Diffuse _D.dds"
    NODE_tex_D.name  = "tex_D"

    # illumination(glow) texture
    normalModels = ["TDSN", "TDOSN", "TDOBSN", "TDSNI", "TDSNI_NIGHT"]

    NODE_tex_I = nodes.new(type="ShaderNodeTexImage")
    NODE_tex_I.location = x(1), y(2)
    NODE_tex_I.label = "Texture Illum _I.dds"
    NODE_tex_I.name  = "tex_I"
    
    tex = ""
    DTexture = ""
    ITexture = ""

    isLinkedMat = mat.baseTexture == ""
    
    debug(f"material link is :  {mat.link}")
    debug(f"material is a link: {isLinkedMat}")

    if isLinkedMat: tex = getDocPathItemsAssetsTextures() + mat.environment + "/" + re.sub(r"_.*", "", mat.link, flags=re.IGNORECASE)
    else:           tex = re.sub(r"_?(i|d)\.dds$", "", mat.baseTexture, flags=re.IGNORECASE)

    tex = bpy.path.abspath(tex)

    # D
    debug(f"try to find:   {tex.split('/')[-1]}_D.dds")
    if      doesFileExist(tex + "D.dds"):   DTexture = tex + "D.dds"    #; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + "_D.dds"):  DTexture = tex + "_D.dds"   #; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + ".dds"):    DTexture = tex + ".dds"     #; debug(f"Texture to load: {DTexture}")
    debug(f"_D found in: {DTexture}") if DTexture else debug("_D texture not found")
    
    # I
    debug(f"try to find:   {tex.split('/')[-1]}_I.dds")
    if      doesFileExist(tex + "I.dds"):   ITexture = tex + "I.dds"    #; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + "_I.dds"):  ITexture = tex + "_I.dds"   #; debug(f"Texture to load: {DTexture}")
    debug(f"_I found in: {ITexture}") if ITexture else debug("_I texture not found")

    
    DTexture = loadDDSTextureIntoBlender(texpath=DTexture)
    ITexture = loadDDSTextureIntoBlender(texpath=ITexture)

    DTextureSuccess = DTexture[0]
    DTextureName    = DTexture[1]
    ITextureSuccess = ITexture[0]
    ITextureName    = ITexture[1]

    if DTextureSuccess:
        assignTextureToImageNode(DTextureName, NODE_tex_D)

    if ITextureSuccess:
        assignTextureToImageNode(ITextureName, NODE_tex_I)


    links.new(NODE_uvmap.outputs[0], NODE_tex_D.inputs[0])
    links.new(NODE_uvmap.outputs[0], NODE_tex_I.inputs[0])
    links.new(NODE_tex_D.outputs[0], NODE_bsdf.inputs[0])                                #basecolor
    links.new(NODE_tex_D.outputs[1], NODE_bsdf.inputs[19]) if DTextureSuccess else None  #alpha
    links.new(NODE_tex_I.outputs[0], NODE_bsdf.inputs[17])                               #emission
    links.new(NODE_bsdf.outputs[0],  NODE_output.inputs[0])
    

    if mat.model.upper() == "TIADD":
        links.new(NODE_tex_I.outputs[0], NODE_bsdf.inputs[19])  #alpha
        links.new(NODE_tex_I.outputs[0], NODE_bsdf.inputs[0])   #basecolor
        NODE_bsdf.inputs[18].default_value = 100.0
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
            bpy.ops.file.find_missing_files( directory=getDocPathItemsAssetsTextures() )

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
    if mat.name.startswith(("TM_", "MP_")) is False:
        return

    #tm_props
    for prop_name in mat_props:
        prop = getattr(mat, prop_name, None)
        
        if prop is None: continue
        
        if prop.__class__.__name__ == "Color":
            prop = [prop[0], prop[1], prop[2]]

        if isinstance(prop, str):
            if prop.startswith("//"):
                prop = bpy.path.abspath(prop)
                prop = getAbspath(prop)

        DICT[prop_name] = prop
    

    # tm2020 mats like CustomBricks do not need nodes
    mat_has_nodes = mat.link.lower().startswith("custom") is False

    if mat_has_nodes:
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex_d = nodes["tex_D"].image
        tex_i = nodes["tex_I"].image
        
        tex_d_path = tex_d.filepath if tex_d else ""
        tex_i_path = tex_i.filepath if tex_i else ""
    
        DICT["tex_d_path"] = getAbspath(tex_d_path)
        DICT["tex_i_path"] = getAbspath(tex_i_path)

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
    
    link          = DICT.get("link", "")
    mat_has_nodes = False if link.lower().startswith("custom") else True

    mat.use_nodes = True if mat_has_nodes else False

    #assign mat tm_props to mat
    for prop in DICT:
        if prop.startswith("tex_"): continue
        try:    setattr(mat, prop, DICT[prop])
        except: return False
    

    #assign textures
    if mat_has_nodes:
        createMaterialNodes(mat)
        imgs  = bpy.data.images
        nodes = mat.node_tree.nodes
        tex_d = nodes["tex_D"]
        tex_i = nodes["tex_I"]

        link  = DICT["link"]
        btex  = DICT["baseTexture"]
        envi  = DICT["environment"]
        root  = getDocPathItemsAssetsTextures()
        root  = root + envi + "/"

        tex_d_path = DICT["tex_d_path"] or getDocPath() + btex + "_D.dds"
        tex_i_path = DICT["tex_i_path"] or getDocPath() + btex + "_I.dds"

        test_d_path_as_link = root + tex_d_path.split("/")[-1]
        test_i_path_as_link = root + tex_d_path.split("/")[-1]

        if doesFileExist( test_d_path_as_link ): tex_d_path = test_d_path_as_link
        if doesFileExist( test_i_path_as_link ): tex_d_path = test_i_path_as_link

        debug(tex_d_path)
        debug(test_d_path_as_link)

        success, name = loadDDSTextureIntoBlender(tex_d_path)
        if success and name in imgs:
            tex_d.image = bpy.data.images[ name ]

        success, name = loadDDSTextureIntoBlender(tex_i_path)
        if success and name in imgs:
            tex_i.image = bpy.data.images[ name ]
            
        
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
            for prop in mat_props:
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
                for prop_name in mat_props:
                    
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


