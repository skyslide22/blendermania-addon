
import re
import bpy

from .Constants import WAYPOINTS
from .Functions import *


def generate_item_XML(exported_fbx: ExportFBXModel) -> str:
    """generate item.xml"""
    tm_props        = get_global_props()
    tm_props_pivots = get_pivot_props()

    fbxfilepath = exported_fbx.filepath
    col         = exported_fbx.col

    xmlfilepath = fbxfilepath.replace(".fbx", ".Item.xml")
    overwrite   = tm_props.CB_xml_overwriteItemXML

    if not overwrite:
        if doesFileExist(filepath=xmlfilepath): return

    FILENAME_NO_EXT = re.sub(r"\..*$", "", fileNameOfPath(fbxfilepath), flags=re.IGNORECASE)

    use_simple_ui = tm_props.LI_xml_simpleOrAdvanced.upper() == "SIMPLE"

    AUTHOR              = tm_props.ST_author
    COLLECTION          = tm_props.LI_materialCollection if isGameTypeManiaPlanet() else "Stadium"
    GRID_H_STEP         = tm_props.NU_xml_gridX if not use_simple_ui else tm_props.LI_xml_simpleGridXY
    GRID_V_STEP         = tm_props.NU_xml_gridY if not use_simple_ui else tm_props.LI_xml_simpleGridZ
    GRID_H_OFFSET       = tm_props.NU_xml_gridXoffset
    GRID_V_OFFSET       = tm_props.NU_xml_gridYoffset
    LEVI_H_STEP         = tm_props.NU_xml_leviX if not use_simple_ui else tm_props.LI_xml_simpleGridXY
    LEVI_V_STEP         = tm_props.NU_xml_leviY if not use_simple_ui else tm_props.LI_xml_simpleGridZ
    LEVI_H_OFFSET       = tm_props.NU_xml_leviXoffset
    LEVI_V_OFFSET       = tm_props.NU_xml_leviXoffset
    AUTO_ROTATION       = tm_props.CB_xml_autoRot
    MANUAL_PIVOT_SWITCH = tm_props.CB_xml_pivotSwitch
    PIVOT_SNAP_DISTANCE = tm_props.NU_xml_pivotSnapDis
    NOT_ON_ITEM         = tm_props.CB_xml_notOnItem
    ONE_AXIS_ROTATION   = tm_props.CB_xml_oneAxisRot
    PIVOTS              = tm_props.CB_xml_pivots
    GHOST_MODE          = tm_props.CB_xml_ghostMode

    WAYPOINT_XML = ""
    WAYPOINT     = WAYPOINTS.get(col.color_tag, "")
    
    if WAYPOINT == "None":
        WAYPOINT = ""

    if WAYPOINT:
        WAYPOINT_XML = f"""<Waypoint Type="{ WAYPOINT }"/>\n"""
    
    MP_PHY_XML  = ""
    MP_VIS_XML  = ""
    TM_MESH_XML = ""
    PIVOTS_XML  = ""

    if PIVOTS:
        for pivot in tm_props_pivots:
            PIVOTS_XML += f"""%TAB%<Pivot Pos="{pivot.NU_pivotX} {pivot.NU_pivotZ} {pivot.NU_pivotY}" />\n"""

    if PIVOTS_XML:
        PIVOTS_XML = f"""<Pivots>\n{ PIVOTS_XML }\n</Pivots>"""


    filename    = get_path_filename( fbxfilepath )
    filename    = re.sub(r"\.(xml|fbx)", "", filename, flags=re.IGNORECASE)


    if isGameTypeManiaPlanet():
        SHAPE      = filename + ".Shape.gbx"
        MESH       = filename + ".Mesh.gbx"
        MP_VIS_XML += f"""%TAB%<Mesh      File="{ MESH }"/>\n"""
        MP_PHY_XML += f"""%TAB%<MoveShape File="{ SHAPE }" Type="Mesh"/>\n"""
        
        if WAYPOINT:
            MP_PHY_XML += f"""%TAB%<TriggerShape  Type="mesh" File="{ FILENAME_NO_EXT }Trigger.Shape.gbx"/>\n"""

    
    elif isGameTypeTrackmania2020():
        MESHPARAMS = filename + ".MeshParams.xml"
        TM_MESH_XML = f"""<MeshParamsLink File="{ MESHPARAMS }"/>"""
        
    fullXML = f"""
        <?xml version="1.0" ?>
        <Item AuthorName="{ AUTHOR }" Collection="{ COLLECTION }" Type="StaticObject">
            {WAYPOINT_XML}
            <Phy>
            {MP_PHY_XML}
            </Phy>
            <Vis>
            {MP_VIS_XML}
            </Vis>
            {TM_MESH_XML}
            <GridSnap   HOffset="{ GRID_H_OFFSET }" HStep="{ GRID_H_STEP }" VOffset="{ GRID_V_OFFSET }" VStep="{ GRID_V_STEP }"/>
            <Levitation HOffset="{ LEVI_H_OFFSET }" HStep="{ LEVI_H_STEP }" VOffset="{ LEVI_V_OFFSET }" VStep="{ LEVI_V_STEP }" GhostMode="{ GHOST_MODE}"/>
            <Options    AutoRotation="{ AUTO_ROTATION }" ManualPivotSwitch="{ MANUAL_PIVOT_SWITCH }" NotOnItem="{ NOT_ON_ITEM }" OneAxisRotation="{ ONE_AXIS_ROTATION }"/>
            <PivotSnap  Distance="{ PIVOT_SNAP_DISTANCE }"/>
            {PIVOTS_XML}
        </Item>
    """

    writeXMLFile(filepath=xmlfilepath, xmlstring=fullXML)







def generateMeshXML(exported_fbx: ExportFBXModel) -> str:
    """generate meshparams.xml"""
    tm_props  = get_global_props()
    overwrite = tm_props.CB_xml_overwriteMeshXML

    fbxfilepath = exported_fbx.filepath
    col         = exported_fbx.col
    scale       = exported_fbx.scale

    xmlfilepath = fbxfilepath.replace(".fbx", ".MeshParams.xml")

    if not overwrite:
        if doesFileExist(filepath=xmlfilepath): return

    
    GLOBAL_LIGHT_RADIUS= tm_props.NU_xml_lightGlobDistance  if tm_props.CB_xml_lightGlobDistance    else None
    GLOBAL_LIGHT_POWER = tm_props.NU_xml_lightPower         if tm_props.CB_xml_lightPower           else None
    GLOBAL_LIGHT_COLOR = tm_props.NU_xml_lightGlobColor     if tm_props.CB_xml_lightGlobColor       else None
    
    USE_GLOBAL_SCALE   = tm_props.CB_xml_scale is True
    GLOBAL_SCALE       = tm_props.NU_xml_scale
    
    SCALE = scale if USE_GLOBAL_SCALE is False else GLOBAL_SCALE 
    

    COLLECTION  = ""
    materials   = []
    materialsXML= ""
    lights      = []
    lightsXML   = ""

    
    for obj in col.objects:
        
        if obj.type == "MESH":
            for matSlot in obj.material_slots:
                materials.append( matSlot.material )
        
        if obj.type == "LIGHT":
            obj.name = safe_name(obj.name)
            lights.append( obj )


    for mat in materials:
        NAME            = mat.name
        GAME_IS_TM      = mat.gameType.lower() == "trackmania2020"
        GAME_IS_MP      = mat.gameType.lower() == "maniaplanet"
        PHYSICSID       = mat.physicsId
        USE_PHYSICSID   = mat.usePhysicsId and PHYSICSID # can be empty
        GAMEPLAYID      = mat.gameplayId
        USE_GAMEPLAYID  = mat.useGameplayId
        MODEL           = mat.model
        COLLECTION      = mat.environment
        LINK            = mat.link
        BASETEXTURE     = fixSlash(mat.baseTexture)
        BASETEXTURE     = re.sub(r"(?i)items/(?:_+|\-+)", r"Items/", BASETEXTURE)
        MAT_COLOR       = mat.diffuse_color     # extract diffuse collor by default
        if mat.use_nodes:                       # replace with BSDF color
            MAT_COLOR = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

        CUSTOM_COLOR    = rgbToHEX(MAT_COLOR, "", True) # convert to Hex with gamma correction
        USE_CUSTOM_COLOR= MAT_COLOR[3] > 0              # use custom color only if material color has Alpha > 0
        if BASETEXTURE:
            BASETEXTURE = fixSlash( BASETEXTURE )
            BASETEXTURE = re.sub(r".*/Items/|_?(D|N|S|I)\.dds", "", BASETEXTURE, flags=re.IGNORECASE)
            BASETEXTURE = "/Items/" + BASETEXTURE

        else: BASETEXTURE = LINK
            
        if GAME_IS_TM:
            GAMEPLAYID_XML  = f"""GameplayId="{ GAMEPLAYID }" """ if USE_GAMEPLAYID else ""
            PHYSICSID_XML   = f"""PhysicsId="{  PHYSICSID  }" """ if USE_PHYSICSID  else ""
            CUSTOM_COLOR_XML= f"""Color="{ CUSTOM_COLOR }" """    if USE_CUSTOM_COLOR and LINK.lower().startswith("custom") else ""
            materialsXML += f"""%TAB%<Material 
                                        Name="{ NAME }" 
                                        Link="{ LINK }" 
                                        { CUSTOM_COLOR_XML } 
                                        { PHYSICSID_XML } 
                                        { GAMEPLAYID_XML } 
                                    />\n"""
            
        elif GAME_IS_MP:
            materialsXML += f"""%TAB%<Material Name="{ NAME }" Model="{ MODEL }" BaseTexture="{ BASETEXTURE }" PhysicsId="{ PHYSICSID }" />\n"""


    for light in lights:
        is_spotlight = light.type == "SPOT"

        RADIUS      = light.data.shadow_soft_size if not GLOBAL_LIGHT_RADIUS else GLOBAL_LIGHT_RADIUS
        NAME        = light.name
        TYPE        = light.data.type    
        POWER       = light.data.energy if not GLOBAL_LIGHT_POWER else GLOBAL_LIGHT_POWER
        OUTER_ANGLE = 0 if not is_spotlight else (light.data.spot_size / math.pi) * 180
        INNER_ANGLE = 0 if not is_spotlight else OUTER_ANGLE * light.data.spot_blend
        NIGHT_ONLY  = "true" if light.data.night_only else "false"
        COLOR_R     = bpy.data.objects[light.name].data.color[0] 
        COLOR_G     = bpy.data.objects[light.name].data.color[1] 
        COLOR_B     = bpy.data.objects[light.name].data.color[2] 
        COLOR       = rgbToHEX([COLOR_R, COLOR_G, COLOR_B]) if not GLOBAL_LIGHT_COLOR else rgbToHEX(GLOBAL_LIGHT_COLOR)

        ANGLES_XML = f""" SpotInnerAngle="{ INNER_ANGLE }" SpotOuterAngle="{ OUTER_ANGLE }" """ if is_spotlight else ""

        lightsXML  += f"""%TAB%<Light 
                          %TAB%%TAB%Name="{ NAME }" 
                          %TAB%%TAB%Type="{ TYPE.title() }" 
                          %TAB%%TAB%sRGB="{ COLOR }" 
                          %TAB%%TAB%Intensity="{ POWER }" 
                          %TAB%%TAB%Distance="{ RADIUS }" 
                          %TAB%%TAB%NightOnly="{ NIGHT_ONLY }"
                          %TAB%%TAB%{ ANGLES_XML }  
                          %TAB%%TAB%PointEmissionRadius="0"
                          %TAB%%TAB%PointEmissionLength="0"
                          %TAB%/>\n"""

    fullXML = f"""
        <?xml version="1.0" ?>
        <MeshParams Scale="{ SCALE }" MeshType="Static" Collection="{ COLLECTION }" FbxFile="{ get_path_filename(fbxfilepath) }">
            <Materials>
            {materialsXML}
            </Materials>
            <Lights>
            {lightsXML}
            </Lights>
        </MeshParams>
    """
    
    writeXMLFile(filepath=xmlfilepath, xmlstring=fullXML)



def writeXMLFile(filepath, xmlstring) -> None:
    xmlstring = re.sub(r"^(\s|\t)+", "", xmlstring, flags=re.MULTILINE)
    xmlstring = xmlstring.replace("%TAB%", "\t")
    with open(filepath, "w", encoding="utf-8") as xml:
        xml.write(xmlstring)




def addOrRemovePivot(type: str) -> None:
    """add or remove a pivot for xml creation"""
    tm_props        = get_global_props()
    tm_props_pivots = get_pivot_props()
    
    pivotcount = len(tm_props_pivots)
    
    if type == "ADD":   tm_props_pivots.add()
    if type == "DEL":   tm_props_pivots.remove(pivotcount -1)
    
        
    



def extendObjectPropertiesPanel_LIGHT(self, context):
    layout = self.layout
    # return
    layout.split()
    row=layout.row()
    # row.alert = True
    row.prop(context.object.data, "night_only", text="Night & Sunset only")