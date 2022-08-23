from __future__ import annotations

import re
import bpy
import math
import json

import xml.etree.ElementTree as ET

from ..properties.PivotsProperties import PivotsProperties

from .Models import ExportedItem
from .Constants import WAYPOINTS
from .Functions import (
    rgb_to_hex,
    fix_slash,
    safe_name,
    get_global_props,
    get_pivot_props,
    is_file_existing,
    get_path_filename,
    is_game_maniaplanet,
    is_game_trackmania2020,
    debug
)






class ItemXMLTemplate(bpy.types.PropertyGroup):
    name: str = "default_template_name",
    grid_xy: bpy.props.FloatProperty(32)
    grid_z: bpy.props.FloatProperty(8)
    grid_xy_offset: bpy.props.FloatProperty(0)
    grid_z_offset: bpy.props.FloatProperty(0)
    levitation_xy: bpy.props.FloatProperty(32)
    levitation_z: bpy.props.FloatProperty(8)
    levitation_xy_offset: bpy.props.FloatProperty(0)
    levitation_z_offset: bpy.props.FloatProperty(0)
    auto_rot: bpy.props.BoolProperty(False)
    one_axis_rot: bpy.props.BoolProperty(False)
    ghost_mode: bpy.props.BoolProperty(True)
    not_on_item: bpy.props.BoolProperty(False)
    pivots: bpy.props.CollectionProperty(type=PivotsProperties)
    pivot_switch: bpy.props.BoolProperty(False)
    pivot_snap_distance: bpy.props.FloatProperty(0)
    
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
        pivots: list[list[float]] = [[0,0,0]],
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
        self.pivot_switch = pivot_switch
        self.pivot_snap_distance = pivot_snap_distance
        for pivot in pivots:
            new_pivot = self.pivots.add()
            new_pivot.NU_pivotX = pivot[0]
            new_pivot.NU_pivotY = pivot[1]
            new_pivot.NU_pivotZ = pivot[2]

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
            "pivots": [(p.NU_pivotX, p.NU_pivotY, p.NU_pivotZ) for p in self.pivots],
            "pivot_switch": self.pivot_switch,
            "pivot_snap_distance": self.pivot_snap_distance,
        }

    @classmethod
    def from_dict(cls, dict_obj) -> ItemXMLTemplate:
        return cls(**dict_obj)




def get_itemxml_template(name: str) -> ItemXMLTemplate | None:
    templates = bpy.context.scene.tm_props_itemxml_templates
    for template in templates:
        if template.name == name:
            return template
    else:
        return None


def add_itemxml_template(existing_template: dict = None) -> None:
    tm_props  = get_global_props()
    pivot_props = get_pivot_props()
    simple_ui = tm_props.LI_xml_simpleOrAdvanced == "simple"

    if existing_template is None:
        template = bpy.context.scene.tm_props_itemxml_templates.add()
        template.name = tm_props.ST_xml_item_template_add_name
        
        sync_grid_levi = tm_props.CB_xml_syncGridLevi

        template.grid_xy = tm_props.NU_xml_gridX
        template.grid_z  = tm_props.NU_xml_gridY 
        if simple_ui: 
            template.grid_xy = float(tm_props.LI_xml_simpleGridXY)
            template.grid_z  = float(tm_props.LI_xml_simpleGridZ) 
        elif sync_grid_levi:
            template.grid_xy = tm_props.NU_xml_gridAndLeviX
            template.grid_z  = tm_props.NU_xml_gridAndLeviY 

        template.levitation_xy = tm_props.NU_xml_leviX
        template.levitation_z  = tm_props.NU_xml_leviY 
        if simple_ui: 
            template.levitation_xy = float(tm_props.LI_xml_simpleGridXY)
            template.levitation_z  = float(tm_props.LI_xml_simpleGridZ) 
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

        for pivot in pivot_props:
            new_pivot = template.pivots.add()
            new_pivot.NU_pivotX = pivot.NU_pivotX
            new_pivot.NU_pivotY = pivot.NU_pivotY
            new_pivot.NU_pivotZ = pivot.NU_pivotZ

        
    else:
        template = bpy.context.scene.tm_props_itemxml_templates.add()
        template.new(**existing_template)



def remove_itemxml_template(template_name: str) -> None:
    templates = bpy.context.scene.tm_props_itemxml_templates

    for i, template in enumerate(templates):
        if template.name == template_name:
            templates.remove(i)
            break



# TODO implement usage of collection itemxml template here 
def generate_item_XML(item: ExportedItem) -> str:
    """generate item.xml"""
    tm_props        = get_global_props()
    tm_props_pivots = get_pivot_props()

    xml_filepath = item.fbx_path.replace(".fbx", ".Item.xml")
    overwrite   = tm_props.CB_xml_overwriteItemXML

    if not overwrite:
        if is_file_existing(filepath=xml_filepath): return

    filename_no_extension = re.sub(r"\..*$", "", get_path_filename(item.fbx_path), flags=re.IGNORECASE)

    use_simple_ui       = tm_props.LI_xml_simpleOrAdvanced.upper() == "SIMPLE"
    use_advanced_ui     = tm_props.LI_xml_simpleOrAdvanced.upper() == "ADVANCED"
    use_template_ui     = tm_props.LI_xml_simpleOrAdvanced.upper() == "TEMPLATE"
    overwrite_template  = tm_props.CB_xml_ignore_assigned_templates

    author                  = tm_props.ST_author
    envi_collection         = tm_props.LI_materialCollection if is_game_maniaplanet() else "Stadium"
    grid_h_step             = tm_props.NU_xml_gridX if not use_simple_ui else tm_props.LI_xml_simpleGridXY
    grid_v_step             = tm_props.NU_xml_gridY if not use_simple_ui else tm_props.LI_xml_simpleGridZ
    grid_h_offset           = tm_props.NU_xml_gridXoffset
    grid_v_offset           = tm_props.NU_xml_gridYoffset
    levitation_h_step       = tm_props.NU_xml_leviX if not use_simple_ui else tm_props.LI_xml_simpleGridXY
    levitation_v_step       = tm_props.NU_xml_leviY if not use_simple_ui else tm_props.LI_xml_simpleGridZ
    levitation_h_offset     = tm_props.NU_xml_leviXoffset
    levitation_v_offset     = tm_props.NU_xml_leviXoffset
    pivot_snap_distance     = tm_props.NU_xml_pivotSnapDis
    use_manual_pivot_switch = tm_props.CB_xml_pivotSwitch
    use_auto_rotation       = tm_props.CB_xml_autoRot
    use_not_on_item         = tm_props.CB_xml_notOnItem
    use_one_axis_rotation   = tm_props.CB_xml_oneAxisRot
    use_pivots              = tm_props.CB_xml_pivots
    use_ghost_mode          = tm_props.CB_xml_ghostMode
    

    template = get_itemxml_template(item.coll.tm_itemxml_template)
    
    if use_template_ui:
        selected_template = bpy.context.scene.tm_props.LI_xml_item_template_globally
        selected_template = get_itemxml_template(selected_template)

        if (selected_template is not None and template is None) \
        or (selected_template is not None and overwrite_template):
            template = selected_template 

    if template:
        grid_h_step                 = template.grid_xy
        grid_v_step                 = template.grid_z
        grid_h_offset               = template.grid_xy_offset
        grid_v_offset               = template.grid_z_offset
        levitation_h_step           = template.levitation_xy
        levitation_v_step           = template.levitation_z
        levitation_h_offset         = template.levitation_xy_offset
        levitation_v_offset         = template.levitation_z_offset
        pivot_snap_distance         = template.pivot_snap_distance
        use_manual_pivot_switch     = template.pivot_switch
        use_auto_rotation           = template.auto_rot
        use_not_on_item             = template.not_on_item
        use_one_axis_rotation       = template.one_axis_rot
        use_pivots                  = len(template.pivots) > 0
        use_ghost_mode              = template.ghost_mode


    xml_waypoint = ""
    waypoint     = WAYPOINTS.get(item.coll.color_tag, "")
    
    if waypoint == "None":
        waypoint = ""

    if waypoint:
        xml_waypoint = f"""<Waypoint Type="{ waypoint }"/>"""
    
    xml_phy_maniaplanet  = ""
    xml_vis_maniaplanet  = ""
    xml_mesh_tm2020      = ""
    xml_pivots           = ""
    
    def gen_pivot_xml(x,y,z) -> str:
        return f"""<Pivot Pos="{x} {z} {y}" />"""

    if use_pivots:
        if template:
            pivots = template.pivots
        else:
            pivots = tm_props_pivots

        for pivot in pivots:
            xml_pivots += gen_pivot_xml(pivot.NU_pivotX, pivot.NU_pivotY, pivot.NU_pivotZ)

    if xml_pivots:
        xml_pivots = f"""<Pivots>{ xml_pivots }</Pivots>"""


    filename    = get_path_filename(item.fbx_path)
    filename    = re.sub(r"\.(xml|fbx)", "", filename, flags=re.IGNORECASE)


    if is_game_maniaplanet():
        shape_filename      = filename + ".Shape.gbx"
        mesh_filename       = filename + ".Mesh.gbx"
        xml_vis_maniaplanet += f"""<Mesh      File="{ mesh_filename }"/>"""
        xml_phy_maniaplanet += f"""<MoveShape File="{ shape_filename }" Type="Mesh"/>"""
        
        if waypoint:
            xml_phy_maniaplanet += f"""
                <TriggerShape  
                    Type="mesh" 
                    File="{ filename_no_extension }Trigger.Shape.gbx"
                />"""

    
    elif is_game_trackmania2020():
        meshparams_filename = filename + ".MeshParams.xml"
        xml_mesh_tm2020 = f"""<MeshParamsLink File="{ meshparams_filename }"/>"""
        
    fullXML = f"""
        <?xml version="1.0" ?>
        <Item AuthorName="{ author }" Collection="{ envi_collection }" Type="StaticObject">
            <AddonItemXmlTemplate Name="{template.name if template else ''}" />
            {xml_waypoint}
            {xml_mesh_tm2020}
            <Phy>
                {xml_phy_maniaplanet}
            </Phy>
            <Vis>
                {xml_vis_maniaplanet}
            </Vis>
            <GridSnap   
                HStep="{ grid_h_step }" 
                VStep="{ grid_v_step }"
                HOffset="{ grid_h_offset }" 
                VOffset="{ grid_v_offset }" 
            />
            <Levitation 
                HStep="{ levitation_h_step }" 
                VStep="{ levitation_v_step }" 
                HOffset="{ levitation_h_offset }" 
                VOffset="{ levitation_v_offset }" 
                GhostMode="{ use_ghost_mode}"
            />
            <Options    
                AutoRotation="{ use_auto_rotation }" 
                ManualPivotSwitch="{ use_manual_pivot_switch }" 
                NotOnItem="{ use_not_on_item }" 
                OneAxisRotation="{ use_one_axis_rotation }"
            />
            <PivotSnap  
                Distance="{ pivot_snap_distance }"
            />
            {xml_pivots}
        </Item>
    """

    write_XML_file(filepath=xml_filepath, xmlstring=fullXML, pretty=tm_props.CB_xml_format_itemxml)



def generate_mesh_XML(item: ExportedItem) -> str:
    """generate meshparams.xml"""
    tm_props  = get_global_props()
    overwrite = tm_props.CB_xml_overwriteMeshXML

    xmlfilepath = item.fbx_path.replace(".fbx", ".MeshParams.xml")

    if not overwrite:
        if is_file_existing(filepath=xmlfilepath): return

    
    global_light_radius= tm_props.NU_xml_lightGlobDistance  if tm_props.CB_xml_lightGlobDistance    else None
    global_light_power = tm_props.NU_xml_lightPower         if tm_props.CB_xml_lightPower           else None
    global_light_color = tm_props.NU_xml_lightGlobColor     if tm_props.CB_xml_lightGlobColor       else None
    
    use_global_scale   = tm_props.CB_xml_scale is True
    global_scale       = tm_props.NU_xml_scale
    
    scale = item.scale if use_global_scale is False else global_scale 
    

    mat_envi_collection  = ""
    materials   = []
    xml_materials= ""
    lights      = []
    lightsXML   = ""

    
    for obj in item.coll.objects:
        
        if obj.type == "MESH":
            for mat_slot in obj.material_slots:
                materials.append( mat_slot.material )
        
        if obj.type == "LIGHT":
            obj.name = safe_name(obj.name)
            lights.append( obj )


    for mat in materials:
        mat_name                = mat.name
        mat_game_is_tm2020      = mat.gameType.lower() == "trackmania2020"
        mat_game_is_maniaplanet = mat.gameType.lower() == "maniaplanet"
        mat_physic_id           = mat.physicsId
        mat_use_physicid        = mat.usePhysicsId and mat_physic_id # can be empty
        mat_gameplay_id         = mat.gameplayId
        mat_use_gameplay_id     = mat.useGameplayId
        mat_model               = mat.model
        mat_envi_collection     = mat.environment
        mat_link                = mat.link
        mat_basetexture         = fix_slash(mat.baseTexture)
        mat_basetexture         = re.sub(r"(?i)items/(?:_+|\-+)", r"Items/", mat_basetexture)
        mat_color               = mat.diffuse_color     # extract diffuse collor by default
        
        if mat.use_nodes: # replace with BSDF color
            mat_color = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

        mat_custom_color     = rgb_to_hex(mat_color, "", True) # convert to Hex with gamma correction
        mat_use_custom_color = mat_color[3] > 0                # use custom color only if material color has Alpha > 0
        
        # maniaplanet relateed (external texture in Maniaplanet/Items/blabla_D.dds)
        if mat_basetexture:
            mat_basetexture = fix_slash( mat_basetexture )
            mat_basetexture = re.sub(r".*/Items/|_?(D|N|S|I)\.dds", "", mat_basetexture, flags=re.IGNORECASE)
            mat_basetexture = "/Items/" + mat_basetexture
        else: 
            mat_basetexture = mat_link
            
        if mat_game_is_tm2020:
            # TODO refactor this line, can color be always present?
            use_custom_color_attr = mat_use_custom_color and mat_link.lower().startswith("custom")
            xml_materials += f"""
                <Material 
                    Name="{ mat_name }" 
                    Link="{ mat_link }" 
                    {f'Color="{mat_custom_color}"'     if use_custom_color_attr else ''} 
                    {f'PhysicsId="{mat_physic_id}"'    if mat_use_physicid      else ''} 
                    {f'GameplayId="{mat_gameplay_id}"' if mat_use_gameplay_id   else ''} 
                />"""
            
        elif mat_game_is_maniaplanet:
            xml_materials += f"""
                <Material 
                    Name="{ mat_name }" 
                    Model="{ mat_model }" 
                    BaseTexture="{ mat_basetexture }" 
                    PhysicsId="{ mat_physic_id }" 
                />"""


    for light in lights:
        light_is_spotlight = light.type == "SPOT"

        light_radius      = light.data.shadow_soft_size if not global_light_radius else global_light_radius
        light_name        = light.name
        light_type        = light.data.type    
        light_power       = light.data.energy if not global_light_power else global_light_power
        light_outer_angle = 0 if not light_is_spotlight else (light.data.spot_size / math.pi) * 180
        light_inner_angle = 0 if not light_is_spotlight else light_outer_angle * light.data.spot_blend
        light_night_only  = "true" if light.data.night_only else "false"
        light_color_r     = bpy.data.objects[light.name].data.color[0] 
        light_color_g     = bpy.data.objects[light.name].data.color[1] 
        light_color_b     = bpy.data.objects[light.name].data.color[2] 
        light_color_hex   = rgb_to_hex([light_color_r, light_color_g, light_color_b]) if not global_light_color else rgb_to_hex(global_light_color)


        lightsXML  += f"""
            <Light 
                Name="{ light_name }" 
                Type="{ light_type.title() }" 
                sRGB="{ light_color_hex }" 
                Intensity="{ light_power }" 
                Distance="{ light_radius }" 
                NightOnly="{ light_night_only }"
                PointEmissionRadius="0"
                PointEmissionLength="0"
                {f'SpotInnerAngle="{light_inner_angle}"' if light_is_spotlight else '' }  
                {f'SpotOuterAngle="{light_outer_angle}"' if light_is_spotlight else '' }  
            />"""

    xml_completed = f"""
        <?xml version="1.0" ?>
        <MeshParams 
            Scale="{scale}" 
            MeshType="Static" 
            Collection="{ mat_envi_collection }" 
            FbxFile="{ get_path_filename(item.fbx_path) }">
                <Materials>
                    {xml_materials}
                </Materials>
                <Lights>
                    {lightsXML}
                </Lights>
        </MeshParams>
    """
    
    write_XML_file(filepath=xmlfilepath, xmlstring=xml_completed, pretty=tm_props.CB_xml_format_meshxml)



def write_XML_file(filepath, xmlstring, pretty:bool=False) -> None:
    
    xmlstring = re.sub(r"^(\s|\t)+", "", xmlstring, flags=re.MULTILINE)
    
    if pretty:
        xml = ET.XML(xmlstring)
        ET.indent(xml, space="    ")
        xmlstring = ET.tostring(xml, encoding="unicode")
    
    with open(filepath, "w", encoding="utf-8") as xml:
        xml.write(xmlstring)