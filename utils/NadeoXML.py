from __future__ import annotations

import re
import bpy
import math
import json


from .Models import ExportedItem
from .Constants import WAYPOINTS
from .Functions import (
    rgb_to_hex,
    fixSlash,
    safe_name,
    get_global_props,
    get_pivot_props,
    is_file_exist,
    get_path_filename,
    isGameTypeManiaPlanet,
    isGameTypeTrackmania2020,
    debug
)






class ItemXMLTemplate(bpy.types.PropertyGroup):
    name: str = "default_template_name",
    grid_xy: float = 32,
    grid_z: float = 8,
    grid_xy_offset: float = 0,
    grid_z_offset: float = 0,
    levitation_xy: float = 32,
    levitation_z: float = 8,
    levitation_xy_offset: float = 0,
    levitation_z_offset: float = 0,
    auto_rot: bool = False,
    one_axis_rot: bool = False,
    ghost_mode: bool = True,
    not_on_item: bool = False,
    pivots: list[list[float, float, float]] = [ [0, 0, 0] ],
    pivot_switch: bool = False,
    pivot_snap_distance: float = 0,
    
    def new(self,
        name: str = "default_template_name",
        grid_xy: float = 32,
        grid_z: float = 8,
        grid_xy_offset: float = 0,
        grid_z_offset: float = 0,
        levitation_xy: float = 32,
        levitation_z: float = 8,
        levitation_xy_offset: float = 0,
        levitation_z_offset: float = 0,
        auto_rot: bool = False,
        one_axis_rot: bool = False,
        ghost_mode: bool = True,
        not_on_item: bool = False,
        pivots: list[list[float, float, float]] = [ [0, 0, 0] ],
        pivot_switch: bool = False,
        pivot_snap_distance: float = 0,
    ):
        self.name = name 
        self.grid_xy = grid_xy
        self.grid_z = grid_z
        self.grid_xy_offset = grid_xy_offset
        self.grid_z_offset = grid_z_offset
        self.levitation_xy = levitation_xy
        self.levitation_z = levitation_z
        self.levitation_xy_offset = levitation_xy_offset
        self.levitation_z_offset = levitation_z_offset
        self.auto_rot = auto_rot
        self.one_axis_rot = one_axis_rot
        self.ghost_mode = ghost_mode
        self.not_on_item = not_on_item
        self.pivots = pivots
        self.pivot_switch = pivot_switch
        self.pivot_snap_distance = pivot_snap_distance

    def to_json(self):
        debug(self.__dict__)
        return json.dumps(self, default=lambda o: o.__dict__)

    def to_dict(self) -> dict:
        # return vars(self) # not working cut inherintance
        return {
            "name": self.name,
            "grid_xy": self.grid_xy,
            "grid_z": self.grid_z,
            "grid_xy_offset": self.grid_xy_offset,
            "grid_z_offset": self.grid_z_offset,
            "levitation_xy": self.levitation_xy,
            "levitation_z": self.levitation_z,
            "levitation_xy_offset": self.levitation_xy_offset,
            "levitation_z_offset": self.levitation_z_offset,
            "auto_rot": self.auto_rot,
            "one_axis_rot": self.one_axis_rot,
            "ghost_mode": self.ghost_mode,
            "not_on_item": self.not_on_item,
            "pivots": self.pivots,
            "pivot_switch": self.pivot_switch,
            "pivot_snap_distance": self.pivot_snap_distance,
        }

    @classmethod
    def from_dict(cls, dict_obj) -> ItemXMLTemplate:
        return cls(**dict_obj)

ítemxml_templates:list[ItemXMLTemplate] = list()
itemxml_templates_for_ui = []


# TODO fix every property is a tuple except "name"

def add_itemxml_template(existing_temp: dict = None) -> None:
    tm_props  = get_global_props()
    pivot_props = get_pivot_props()
    simple_ui = tm_props.LI_xml_simpleOrAdvanced == "simple"

    if existing_temp is None:
        template = bpy.context.scene.tm_props_itemxml_templates.add()
        template.name = tm_props.LI_xml_item_template_add_name
        
        sync_grid_levi = tm_props.CB_xml_syncGridLevi

        template.grid_xy = tm_props.NU_xml_gridX
        template.grid_z  = tm_props.NU_xml_gridY 
        if simple_ui: 
            template.grid_xy = tm_props.LI_xml_simpleGridXY
            template.grid_z  = tm_props.LI_xml_simpleGridZ 
        elif sync_grid_levi:
            template.grid_xy = tm_props.NU_xml_gridAndLeviX
            template.grid_z  = tm_props.NU_xml_gridAndLeviY 

        template.levitation_xy = tm_props.NU_xml_leviX
        template.levitation_z  = tm_props.NU_xml_leviY 
        if simple_ui: 
            template.levitation_xy = tm_props.LI_xml_simpleGridXY
            template.levitation_z  = tm_props.LI_xml_simpleGridZ 
        elif sync_grid_levi:
            template.levitation_xy = tm_props.NU_xml_gridAndLeviX
            template.levitation_z  = tm_props.NU_xml_gridAndLeviY 

        # TODO OFFSETS

        template.ghost_mode = tm_props.CB_xml_ghostMode
        template.auto_rot = tm_props.CB_xml_autoRot
        template.one_axis_rot = tm_props.CB_xml_oneAxisRot
        template.not_on_item = tm_props.CB_xml_notOnItem
        template.pivot_switch = tm_props.CB_xml_pivotSwitch
        template.pivot_snap_distance = tm_props.NU_xml_pivotSnapDis
        template.pivots = [
            [
                pivot.NU_pivotX,
                pivot.NU_pivotY,
                pivot.NU_pivotZ
            ] for pivot in pivot_props
        ]
        
    else:
        template = bpy.context.scene.tm_props_itemxml_templates.add()
        template.new(**existing_temp)



def remove_itemxml_template(template_name: str) -> None:
    templates = bpy.context.scene.tm_props_itemxml_templates

    for i, template in enumerate(templates):
        if template.name == template_name:
            templates.remove(i)




def generate_item_XML(item: ExportedItem) -> str:
    """generate item.xml"""
    tm_props        = get_global_props()
    tm_props_pivots = get_pivot_props()

    xmlfilepath = item.fbx_path.replace(".fbx", ".Item.xml")
    overwrite   = tm_props.CB_xml_overwriteItemXML

    if not overwrite:
        if is_file_exist(filepath=xmlfilepath): return

    FILENAME_NO_EXT = re.sub(r"\..*$", "", get_path_filename(item.fbx_path), flags=re.IGNORECASE)

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
    WAYPOINT     = WAYPOINTS.get(item.coll.color_tag, "")
    
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


    filename    = get_path_filename(item.fbx_path)
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

    write_XML_file(filepath=xmlfilepath, xmlstring=fullXML)

def generate_mesh_XML(item: ExportedItem) -> str:
    """generate meshparams.xml"""
    tm_props  = get_global_props()
    overwrite = tm_props.CB_xml_overwriteMeshXML

    xmlfilepath = item.fbx_path.replace(".fbx", ".MeshParams.xml")

    if not overwrite:
        if is_file_exist(filepath=xmlfilepath): return

    
    GLOBAL_LIGHT_RADIUS= tm_props.NU_xml_lightGlobDistance  if tm_props.CB_xml_lightGlobDistance    else None
    GLOBAL_LIGHT_POWER = tm_props.NU_xml_lightPower         if tm_props.CB_xml_lightPower           else None
    GLOBAL_LIGHT_COLOR = tm_props.NU_xml_lightGlobColor     if tm_props.CB_xml_lightGlobColor       else None
    
    USE_GLOBAL_SCALE   = tm_props.CB_xml_scale is True
    GLOBAL_SCALE       = tm_props.NU_xml_scale
    
    SCALE = item.scale if USE_GLOBAL_SCALE is False else GLOBAL_SCALE 
    

    COLLECTION  = ""
    materials   = []
    materialsXML= ""
    lights      = []
    lightsXML   = ""

    
    for obj in item.coll.objects:
        
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

        CUSTOM_COLOR    = rgb_to_hex(MAT_COLOR, "", True) # convert to Hex with gamma correction
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
        COLOR       = rgb_to_hex([COLOR_R, COLOR_G, COLOR_B]) if not GLOBAL_LIGHT_COLOR else rgb_to_hex(GLOBAL_LIGHT_COLOR)

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
        <MeshParams Scale="{ SCALE }" MeshType="Static" Collection="{ COLLECTION }" FbxFile="{ get_path_filename(item.fbx_path) }">
            <Materials>
            {materialsXML}
            </Materials>
            <Lights>
            {lightsXML}
            </Lights>
        </MeshParams>
    """
    
    write_XML_file(filepath=xmlfilepath, xmlstring=fullXML)



def write_XML_file(filepath, xmlstring) -> None:
    xmlstring = re.sub(r"^(\s|\t)+", "", xmlstring, flags=re.MULTILINE)
    xmlstring = xmlstring.replace("%TAB%", "\t")
    with open(filepath, "w", encoding="utf-8") as xml:
        xml.write(xmlstring)