# region imports
from sys import flags
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
        tm_props = context.scene.tm_props
        
        if not isNadeoIniValid():
            row = layout.row()
            row.alert = True
            row.label(text=errorMsg_NADEOINI)
            return

        mats        = bpy.data.materials
        action      = tm_props.LI_materialAction
        game        = tm_props.LI_gameType
        matname     = tm_props.ST_materialAddName
        matnameOld  = tm_props.LI_materials

        actionIsUpdate = str(action).lower() == "update"
        actionIsCreate = str(action).lower() == "create"

        layout.row().prop(tm_props, "LI_materialAction", expand=True)
        
        layout.row().prop(tm_props, "LI_materials") if actionIsUpdate else None
        layout.row().prop(tm_props, "ST_materialAddName")

        row = layout.row()
        row.enabled = True if not tm_props.CB_converting else False
        row.prop(tm_props, "LI_gameType", text="Game")

    
        use_physicsId   = tm_props.CB_materialUsePhysicsId
        use_gameplayId  = tm_props.CB_materialUseGameplayId



        if isGameTypeManiaPlanet():
            layout.row().prop(tm_props, "LI_materialCollection")

            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_physicsId else False
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon="HIDE_OFF")
            
            row = layout.row(align=True)
            row.prop(tm_props, "ST_materialBaseTexture")
            row.operator("view3d.tm_clearbasetexture", icon="X", text="")

            row = layout.row()
            row.enabled = tm_props.ST_materialBaseTexture != ""
            row.prop(tm_props, "LI_materialModel")
            
            row = layout.row()
            row.prop(tm_props, "LI_materialLink") 
            row.enabled = True if tm_props.ST_materialBaseTexture == "" else False




        elif isGameTypeTrackmania2020():
            layout.row().prop(tm_props, "LI_materialLink")
            
            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_physicsId else False
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon="HIDE_OFF")

            row = layout.row(align=True)
            col = row.column()
            col.enabled = True if use_gameplayId else False
            col.prop(tm_props, "LI_materialGameplayId", text="Gameplay")
            col = row.column()
            col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon="HIDE_OFF")

            linkIsCustom = str(tm_props.LI_materialLink).lower().startswith("custom")
            row = layout.row()
            row.enabled = linkIsCustom
            row.prop(tm_props, "NU_materialColor")
    



        row = layout.row()
        row.scale_y = 1.5

        if actionIsUpdate:
            row.operator("view3d.tm_updatematerial", text=f"{matnameOld}", icon="FILE_REFRESH")

        elif actionIsCreate:
            row.operator("view3d.tm_creatematerial", text=f"{matname}",    icon="ADD")



            
        






def createOrUpdateMaterial(action)->None:
    """create a export/convert ready material for TM and MP"""
    tm_props = bpy.context.scene.tm_props
    
    TM_PREFIX = "TM_"
    MP_PREFIX = "MP_"

    matName         = tm_props.LI_materials
    matNameNew      = fixName( tm_props.ST_materialAddName )
    matGameType     = tm_props.LI_gameType
    matCollection   = tm_props.LI_materialCollection
    matPhysicsId    = tm_props.LI_materialPhysicsId
    matUsePhysicsId = tm_props.CB_materialUsePhysicsId
    matGameplayId   = tm_props.LI_materialGameplayId
    matUseGameplayId= tm_props.CB_materialUseGameplayId
    matModel        = tm_props.LI_materialModel
    matLink         = tm_props.LI_materialLink
    matBaseTexture  = tm_props.ST_materialBaseTexture
    matColor        = tm_props.NU_materialColor
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
            MAT.gameType     = matGameType
            MAT.environment  = matCollection
            MAT.usePhysicsId = matUsePhysicsId
            MAT.physicsId    = matPhysicsId
            MAT.useGameplayId= matUseGameplayId
            MAT.gameplayId   = matGameplayId
            MAT.model        = matModel
            MAT.link         = matLink
            MAT.baseTexture  = matBaseTexture
            MAT.surfaceColor = matColor
            makeReportPopup(
                title=f"Material {matNameNew} successfully created!",
                icon ="CHECKMARK"
            )
            debug(f"Material {matNameNew} created")
    

    else: #UPDATE
        MAT = bpy.data.materials[matName]
        MAT.gameType     = matGameType
        MAT.environment  = matCollection
        MAT.usePhysicsId = matUsePhysicsId
        MAT.physicsId    = matPhysicsId
        MAT.useGameplayId= matUseGameplayId
        MAT.gameplayId   = matGameplayId
        MAT.model        = matModel
        MAT.link         = matLink
        MAT.baseTexture  = matBaseTexture if isGameTypeManiaPlanet() else ""
        MAT.surfaceColor = matColor
        MAT.name         = matNameNew
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
    mat.blend_method= "BLEND"
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
    
    debug(f"material link is : {mat.link}")
    debug(f"material is a link: {isLinkedMat}")

    if isLinkedMat: tex = getDocPathItemsAssetsTextures() + mat.environment + "/" + re.sub(r"_.*", "", mat.link, flags=re.IGNORECASE)
    else:           tex = re.sub(r"_?(i|d)\.dds$", "", mat.baseTexture, flags=re.IGNORECASE)

    debug(f"try to find file with suffix like _D.dds: {tex}")
    if      doesFileExist(tex + "D.dds"):   DTexture = tex + "D.dds"    ; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + "_D.dds"):  DTexture = tex + "_D.dds"   ; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + ".dds"):    DTexture = tex + ".dds"     ; debug(f"Texture to load: {DTexture}")
    if      doesFileExist(tex + "I.dds"):   ITexture = tex + "I.dds"    ; debug(f"Texture to load: {DTexture}")
    elif    doesFileExist(tex + "_I.dds"):  ITexture = tex + "_I.dds"   ; debug(f"Texture to load: {DTexture}")

    debug(f"_I texture is: {ITexture}")
    debug(f"_D texture is: {DTexture}")
    
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

    debug(f"try to load texture into blender: {texpath}")

    if doesFileExist(filepath=texpath):
    
        if texName not in imgs:
            imgs.load(texpath)
            debug(f"texture loaded: { getFilenameOfPath(texpath) }")
        return True, getFilenameOfPath(texpath)
    
    else: 
        debug(f"failed to find file: {texpath}")
        return False, getFilenameOfPath(texpath)






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