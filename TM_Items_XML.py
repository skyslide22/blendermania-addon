
from sys import flags
import bpy
import os.path
import re
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty
)
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .TM_Functions import *



    
    
class TM_OT_Items_ItemXML_RemovePivot(Operator):
    bl_idname = "view3d.tm_removepivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Remove a pivot"
        
    def execute(self, context):
        addOrRemovePivot("DEL")
        return {"FINISHED"}
    
    
class TM_OT_Items_ItemXML_AddPivot(Operator):
    bl_idname = "view3d.tm_addpivot"
    bl_description = "Execute Order 66"
    bl_icon = 'ADD'
    bl_label = "Add a pivot"
        
    def execute(self, context):
        addOrRemovePivot("ADD")
        return {"FINISHED"}


class TM_PT_Items_ItemXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Item XML file"
    bl_idname = "TM_PT_Items_Export_ItemXML"
    bl_parent_id = "TM_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    @classmethod
    def poll(cls, context):
        tm_props = getTmProps()
        show =  not tm_props.CB_showConvertPanel \
                and not tm_props.LI_exportType.lower() == "convert" \
                and isSelectedNadeoIniFilepathValid()
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = getTmProps()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_xml_genItemXML",         text="",    icon_only=True, icon="CHECKMARK",)
        row.prop(tm_props, "CB_xml_overwriteItemXML",   text="",            icon_only=True, icon="FILE_REFRESH")
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = getTmProps()
        tm_props_pivots = getTmPivotProps()
        
        if tm_props.CB_showConvertPanel:
            return
    
        if tm_props.CB_xml_genItemXML is True:
            
            if isGameTypeManiaPlanet():
                row = layout.row()
                row.prop(tm_props, "LI_materialCollection", text="Envi")
            
            layout.row().prop(tm_props, "CB_xml_syncGridLevi", icon="UV_SYNC_SELECT")
            sync = tm_props.CB_xml_syncGridLevi
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = True if sync else False
            boxRow.prop(tm_props, "NU_xml_gridAndLeviX")
            boxRow.prop(tm_props, "NU_xml_gridAndLeviY")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(tm_props, "NU_xml_gridX")
            boxRow.prop(tm_props, "NU_xml_gridY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "NU_xml_gridXoffset")
            boxRow.prop(tm_props, "NU_xml_gridYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(tm_props, "NU_xml_leviX")
            boxRow.prop(tm_props, "NU_xml_leviY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "NU_xml_leviXoffset")
            boxRow.prop(tm_props, "NU_xml_leviYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_ghostMode",   icon="GHOST_DISABLED")
            boxRow.prop(tm_props, "CB_xml_autoRot",     icon="GIZMO")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_oneAxisRot",  icon="NORMALS_FACE")
            boxRow.prop(tm_props, "CB_xml_notOnItem",   icon="SNAP_OFF")
            
            layout.separator(factor=UI_SPACER_FACTOR)
            
            layout.row().prop(tm_props, "CB_xml_pivots",        icon="EDITMODE_HLT")
            
            if tm_props.CB_xml_pivots is True:
                row = layout.row(align=True)
                row.prop(tm_props, "CB_xml_pivotSwitch",    text="Switch")
                row.prop(tm_props, "NU_xml_pivotSnapDis",   text="SnapDist")
                
                row = layout.row(align=True)
                row.operator("view3d.tm_addpivot",    text="Add",       icon="ADD")
                row.operator("view3d.tm_removepivot", text="Delete",    icon="REMOVE")
                # row.operator("view3d.removepivot", text="Del end",   icon="REMOVE")
                
                layout.separator(factor=UI_SPACER_FACTOR)
                
                for i, pivot in enumerate(tm_props_pivots):
                    boxRow = layout.row(align=True)
                    boxRow.prop(tm_props_pivots[i], "NU_pivotX", text="X" )
                    boxRow.prop(tm_props_pivots[i], "NU_pivotY", text="Y" )
                    boxRow.prop(tm_props_pivots[i], "NU_pivotZ", text="Z" )
                    
        layout.separator(factor=UI_SPACER_FACTOR)


class TM_PT_Items_MeshXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Mesh XML file"
    bl_idname = "TM_PT_Items_Export_MeshXML"
    bl_parent_id = "TM_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    @classmethod
    def poll(cls, context):
        tm_props = getTmProps()
        show =  not tm_props.CB_showConvertPanel \
                and not tm_props.LI_exportType.lower() == "convert" \
                and isSelectedNadeoIniFilepathValid()
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = getTmProps()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_xml_genMeshXML",         text="",            icon_only=True, icon="CHECKMARK")
        row.prop(tm_props, "CB_xml_overwriteMeshXML",   text="",            icon_only=True, icon="FILE_REFRESH")
        row=layout.row()

    
    def draw(self, context):
        layout = self.layout
        tm_props        = getTmProps()
        
        if tm_props.CB_showConvertPanel:
            return
    
        if tm_props.CB_xml_genItemXML is True:
            
            layout.row().label(text="Overwrite object settings:")



            #--- multi scales
            layout.separator(factor=UI_SPACER_FACTOR)
            layout.row().prop(tm_props, "CB_useMultiScaleExport", toggle=True, icon="SORTSIZE")
            
            row = layout.row(align=True)            
            col = row.column()
            col.prop(tm_props, "CB_overwriteMultiScaleFactor", toggle=True, icon="LINENUMBERS_ON")
            
            col = row.column()
            col.enabled = True if tm_props.CB_overwriteMultiScaleFactor else False
            col.prop(tm_props, "NU_multiScaleExportFactor", text="x =")
            
            
            layout.separator(factor=UI_SPACER_FACTOR)
            
            
            #--- object scale
            row = layout.row(align=True)
            
            col = row.column()
            col.enabled = True if tm_props.CB_useMultiScaleExport is False else False
            col.prop(tm_props, "CB_xml_scale", toggle=True, icon="OBJECT_ORIGIN")

            col = row.column()
            col.enabled = False if not tm_props.CB_xml_scale else True
            col.prop(tm_props, "NU_xml_scale", text="")

            
            #--- light power
            row = layout.row(align=True)

            col = row.column()
            col.enabled = True
            col.prop(tm_props, "CB_xml_lightPower",    text="Light Power", icon="OUTLINER_OB_LIGHT")
            
            col = row.column()
            col.enabled = False if not tm_props.CB_xml_lightPower else True
            col.prop(tm_props, "NU_xml_lightPower", text="")


            #--- light color
            row = layout.row(align=True)

            col = row.column()
            col.enabled = True
            col.prop(tm_props, "CB_xml_lightGlobColor", text="Light Color", icon="COLORSET_13_VEC")
            
            col = row.column()
            col.enabled = False if not tm_props.CB_xml_lightGlobColor else True
            col.prop(tm_props, "NU_xml_lightGlobColor", text="")
            
            
            #--- light distance
            row = layout.row(align=True)

            col = row.column()
            col.enabled = True
            col.prop(tm_props, "CB_xml_lightGlobDistance", text="Light Radius", icon="LIGHT_SUN")
            
            col = row.column()
            col.enabled = False if not tm_props.CB_xml_lightGlobDistance else True
            col.prop(tm_props, "NU_xml_lightGlobDistance", text="")
            
            

        layout.separator(factor=UI_SPACER_FACTOR)





def generateItemXML(exported_fbx: exportFBXModel) -> str:
    """generate item.xml"""
    tm_props        = getTmProps()
    tm_props_pivots = getTmPivotProps()

    fbxfilepath = exported_fbx.filepath
    col         = exported_fbx.col

    xmlfilepath = fbxfilepath.replace(".fbx", ".Item.xml")
    overwrite   = tm_props.CB_xml_overwriteItemXML

    if not overwrite:
        if doesFileExist(filepath=xmlfilepath): return

    FILENAME_NO_EXT = re.sub(r"\..*$", "", fileNameOfPath(fbxfilepath), flags=re.IGNORECASE)

    AUTHOR              = tm_props.ST_author
    COLLECTION          = tm_props.LI_materialCollection if isGameTypeManiaPlanet() else "Stadium"
    GRID_H_STEP         = tm_props.NU_xml_gridX
    GRID_V_STEP         = tm_props.NU_xml_gridY
    GRID_H_OFFSET       = tm_props.NU_xml_gridXoffset
    GRID_V_OFFSET       = tm_props.NU_xml_gridYoffset
    LEVI_H_STEP         = tm_props.NU_xml_leviX
    LEVI_V_STEP         = tm_props.NU_xml_leviY
    LEVI_H_OFFSET       = tm_props.NU_xml_leviXoffset
    LEVI_V_OFFSET       = tm_props.NU_xml_leviXoffset
    AUTO_ROTATION       = tm_props.CB_xml_autoRot
    MANUAL_PIVOT_SWITCH = tm_props.CB_xml_pivotSwitch
    PIVOT_SNAP_DISTANCE = tm_props.NU_xml_pivotSnapDis
    NOT_ON_ITEM         = tm_props.CB_xml_notOnItem
    ONE_AXIS_ROTATION   = tm_props.CB_xml_oneAxisRot
    PIVOTS              = tm_props.CB_xml_pivots
    GHOST_MODE          = tm_props.CB_xml_ghostMode

    WAYPOINT     = ""
    WAYPOINT_XML = ""

    if      col.color_tag == COLOR_CHECKPOINT:   WAYPOINT = "Checkpoint"
    elif    col.color_tag == COLOR_START:        WAYPOINT = "Start"
    elif    col.color_tag == COLOR_FINISH:       WAYPOINT = "Finish"
    elif    col.color_tag == COLOR_STARTFINISH:  WAYPOINT = "StartFinish"

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


    filename    = getFilenameOfPath( fbxfilepath )
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







def generateMeshXML(exported_fbx: exportFBXModel) -> str:
    """generate meshparams.xml"""
    tm_props  = getTmProps()
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
            obj.name = fixName(obj.name)
            lights.append( obj )


    for mat in materials:
        NAME            = mat.name
        GAME_IS_TM      = mat.gameType.lower() == "trackmania2020"
        GAME_IS_MP      = mat.gameType.lower() == "maniaplanet"
        PHYSICSID       = mat.physicsId
        USE_PHYSICSID   = mat.usePhysicsId
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
            materialsXML += f"""%TAB%<Material Name="{ NAME }" Link="{ LINK }" { CUSTOM_COLOR_XML } { PHYSICSID_XML } { GAMEPLAYID_XML } />\n"""
            
        elif GAME_IS_MP:
            materialsXML += f"""%TAB%<Material Name="{ NAME }" Model="{ MODEL }" BaseTexture="{ BASETEXTURE }" PhysicsId="{ PHYSICSID }" />\n"""


    for light in lights:
        RADIUS      = light.data.shadow_soft_size if not GLOBAL_LIGHT_RADIUS else GLOBAL_LIGHT_RADIUS
        NAME        = light.name
        TYPE        = light.data.type    
        POWER       = light.data.energy if not GLOBAL_LIGHT_POWER else GLOBAL_LIGHT_POWER
        NIGHT_ONLY  = "true" if light.data.night_only else "false"
        COLOR_R     = bpy.data.objects[light.name].data.color[0] 
        COLOR_G     = bpy.data.objects[light.name].data.color[1] 
        COLOR_B     = bpy.data.objects[light.name].data.color[2] 
        COLOR       = rgbToHEX([COLOR_R, COLOR_G, COLOR_B]) if not GLOBAL_LIGHT_COLOR else rgbToHEX(GLOBAL_LIGHT_COLOR)
        lightsXML  += f"""%TAB%<Light Name="{ NAME }" Type="{ TYPE }" sRGB="{ COLOR }" Intensity="{ POWER }" Distance="{ RADIUS }" NightOnly="{ NIGHT_ONLY }" />\n"""

    fullXML = f"""
        <?xml version="1.0" ?>
        <MeshParams Scale="{ SCALE }" MeshType="Static" Collection="{ COLLECTION }" FbxFile="{ getFilenameOfPath(fbxfilepath) }">
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
    tm_props        = getTmProps()
    tm_props_pivots = getTmPivotProps()
    
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









