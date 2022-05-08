
import bpy
import bpy.utils.previews
from bpy.props import *
from bpy.types import (
    PropertyGroup
)

from .TM_Functions  import * 
from .TM_Items_Icon import generateWorldNode
from .TM_Descriptions import *



class EnumProps():
    """this needs to be returned by bpy.props.EnumProperty"""
    def __init__(self):
        self.index= 0
        self._list= []

    def add(self, id:str, name:str, desc:str="", icon:str="NONE"):
        self._list.append(
            (id, name, desc, icon, self.index)
        )
        self.index += 1
        return self

    def toList(self) -> list:
        return self._list





ERROR_ENUM_PROPS = EnumProps().add(id="ERROR", name ="Nothing found", desc="ERROR", icon="ERROR").toList()
material_physics = ERROR_ENUM_PROPS
material_links   = ERROR_ENUM_PROPS



def errorEnumPropsIfNadeoINIisNotValid(func) -> callable:
    #func has to return tuple with tuples: ( (3x str or 4x str and unique index), )
    def wrapper(self, context):
        return func(self, context) if isSelectedNadeoIniFilepathValid() else ERROR_ENUM_PROPS        
    return wrapper


def getNadeoImportersManiaplanet() -> list:
    # importers = ["NadeoImporter_2019_10_09.zip"]
    importers = ["2019_10_09.zip"]
    isFirst = True

    items = EnumProps()
    for imp in importers:
        name = " (latest)" if isFirst else ""

        items.add(
            id=imp,
            name=imp.lower().replace("nadeoimporter_","v. ").replace(".zip", "")+name,
            desc=imp,
            icon="FILE_REFRESH")

        isFirst = False
    
    return items.toList()


def getNadeoImportersTrackmania2020() -> list:
    # importers = ["NadeoImporter_2021_10_15.zip", "NadeoImporter_2021_07_07.zip"]
    importers = ["2021_10_15.zip", "2021_07_07.zip"]
    isFirst = True

    items = EnumProps()
    for imp in importers:
        name = " (latest)" if isFirst else ""

        items.add(
            id=imp,
            name=imp.lower().replace("nadeoimporter_","v. ").replace(".zip", "")+name,
            desc=imp,
            icon="FILE_REFRESH")

        isFirst = False

    return items.toList()


def updateINI(prop) -> None:
    isNadeoImporterInstalled(prop)
    global nadeo_ini_settings
    global nadeoimporter_materiallib_materials
    nadeo_ini_settings.clear() #reset when changed
    nadeoimporter_materiallib_materials.clear()
    try:
        gameTypeGotUpdated()
    except AttributeError:
        pass # debug("Error trying to change settings related to game type")



def defaultINI(prop) -> str:
    """return nadeo.ini path from envi variable, or empty string"""
    ini = ""
    if   prop.lower().endswith("TM"): ini = os.getenv("NADEO_INI_PATH_TM") or ""
    elif prop.lower().endswith("MP"): ini = os.getenv("NADEO_INI_PATH_MP") or ""
    
    return ini



def getGameTypes()->list:
    return EnumProps().add(
        id   = GAMETYPE_MANIAPLANET,
        name = GAMETYPE_MANIAPLANET,
        desc = GAMETYPE_MANIAPLANET,
        icon = getIcon(GAMETYPE_MANIAPLANET)
    ).add(
        id   = GAMETYPE_TRACKMANIA2020,
        name = GAMETYPE_TRACKMANIA2020,
        desc = GAMETYPE_TRACKMANIA2020,
        icon = getIcon(GAMETYPE_TRACKMANIA2020)
    ).toList()
    


def gameTypeGotUpdated(self=None,context=None)->None:
    """reset important variables to fit new gameType environment"""
    isNadeoImporterInstalled()
    resetNadeoIniSettings()
    
    global material_links, material_physics, nadeoimporter_materiallib_materials
    material_links   = ERROR_ENUM_PROPS
    material_physics = ERROR_ENUM_PROPS
    nadeoLibParser()

    tm_props     = getTmProps()
    colIsStadium = tm_props.LI_materialCollection.lower() == "stadium"

    if isGameTypeTrackmania2020() and not colIsStadium:
        tm_props.LI_materialCollection = "Stadium"

    if isGameTypeTrackmania2020():
        tm_props.LI_DL_TextureEnvi = "Stadium"
    
    refreshPanels()

    return None



def getGameTextureZipFileNames()->list:
    return EnumProps().add(
        id   = "Stadium",
        name = "Stadium",
        desc = "Stadium",
        icon = getIcon("ENVI_STADIUM")
    ).add(
        id   = "Valley",
        name = "Valley",
        desc = "Valley",
        icon = getIcon("ENVI_VALLEY")
    ).add(
        id   = "Canyon",
        name = "Canyon",
        desc = "Canyon",
        icon = getIcon("ENVI_CANYON")
    ).add(
        id   = "Lagoon",
        name = "Lagoon",
        desc = "Lagoon",
        icon = getIcon("ENVI_LAGOON")
    ).add(
        id   = "Shootmania",
        name = "Shootmania",
        desc = "Shootmania",
        icon = getIcon("ENVI_STORM")
    ).toList()



def getExportTypes()->list:
    return EnumProps().add(
        id   = "EXPORT",
        name = "Export only",
        desc = "Export only",
        icon = "EXPORT"
    ).add(
        id   = "EXPORT_CONVERT",
        name = "Export and Convert",
        desc = "Export fbx and convert to gbx",
        icon = "CON_FOLLOWPATH"
    ).toList()



def getExportFolderTypes(self,context)->list:
    folders = EnumProps().add(
        id   = "Base",
        name = "/",
        desc = "Base folder(Documents/Work/Items/)",
        icon = "HOME"
    ).add(
        id   = "Custom",
        name = "Custom Folder",
        desc = "Custom folder, needs to be in Documents/Work/Items/",
        icon = "HELP"
    )
    if isGameTypeManiaPlanet():
        folders.add(
            id   = "Stadium",
            name = "Stadium",
            desc = "Stadium",
            icon = getIcon("ENVI_STADIUM")
        ).add(
            id   = "Valley",
            name = "Valley",
            desc = "Valley",
            icon = getIcon("ENVI_VALLEY")
        ).add(
            id   = "Canyon",
            name = "Canyon",
            desc = "Canyon",
            icon = getIcon("ENVI_CANYON")
        ).add(
            id   = "Lagoon",
            name = "Lagoon",
            desc = "Lagoon",
            icon = getIcon("ENVI_LAGOON")
        ).add(
            id   = "Shootmania",
            name = "Shootmania",
            desc = "Shootmania",
            icon = getIcon("ENVI_STORM")
        )
    return folders.toList()



def getExportWhichObjects() -> list:
    return EnumProps().add(
        id   = "SELECTED",
        name = "Selected",
        desc = "Selected objects(their collection) only",
        icon = "RESTRICT_SELECT_OFF"
    ).add(
        id   = "VISIBLE",
        name = "Visible",
        desc = "Visible objects(their collection) only",
        icon = "HIDE_OFF"
    ).toList()



def getExportWhichObjTypes() -> list:
    return EnumProps().add(
        id   = "MESH_LIGHT_EMPTY",
        name = "All object types",
        desc = "Normal meshes, lights and empties",
        icon = "SCENE_DATA"
    ).add(
        id   = "MESH_LIGHT",
        name = "Mesh, Light",
        desc = "Normal meshes, lights, no empties",
        icon = "LIGHT_SUN"
    ).add(
        id   = "MESH_EMPTY",
        name = "Mesh, Empty",
        desc = "Normal meshes, empties(like _socket_START), no lights",
        icon = "EMPTY_ARROWS"
    ).toList()






def updateGridAndLevi(self, context) -> None:
    tm_props = getTmProps()
    syncX = tm_props.NU_xml_gridAndLeviX
    syncY = tm_props.NU_xml_gridAndLeviY
    tm_props.NU_xml_gridX = syncX
    tm_props.NU_xml_gridY = syncY
    tm_props.NU_xml_leviX = syncX
    tm_props.NU_xml_leviY = syncY


def getWayPointVariations() -> list:
    col = "COLLECTION_"
    return EnumProps().add(
        id   = "Start",
        name = "Start",
        desc = "Object will be a start",
        icon = col + COLLECTION_COLOR_TAG_GREEN
    ).add(
        id   = "Checkpoint",
        name = "Checkpoint",
        desc = "Object will be a checkpoint",
        icon = col + COLLECTION_COLOR_TAG_BLUE
    ).add(
        id   = "Finish",
        name = "Finish",
        desc = "Object will be a finish",
        icon = col + COLLECTION_COLOR_TAG_RED
    ).add(
        id   = "StartFinish",
        name = "Multilap (StartFinish)",
        desc = "Object will be a multilap, start and finish will be the same",
        icon = col + COLLECTION_COLOR_TAG_YELLOW
    ).add(
        id   = "None",
        name = "Default",
        desc = "Object will not be a waypoint",
        icon = "AUTO" 
    ).toList()

     

def onWaypointUpdate(self,context) -> None:
    redrawPanel(self,context)
    setWaypointTypeOfSelectedCollection()


def getItemXMLCollections() -> list:
    return EnumProps().add(
        id   = "Stadium",
        name = "Stadium",
        desc = "",
        icon = getIcon("ENVI_STADIUM"),
    ).add(
        id   = "Canyon",
        name = "Canyon",
        desc = "",
        icon = getIcon("ENVI_CANYON"),
    ).add(
        id   = "Valley",
        name = "Valley",
        desc = "",
        icon = getIcon("ENVI_VALLEY"),
    ).add(
        id   = "Lagoon",
        name = "Lagoon",
        desc = "",
        icon = getIcon("ENVI_LAGOON"),
    ).add(
        id   = "Storm",
        name = "Storm",
        desc = "",
        icon = getIcon("ENVI_STORM"),
    ).add(
        id   = "Common",
        name = "Common",
        desc = "",
        icon = getIcon("ENVI_COMMON"),
    ).add(
        id   = "SMCommon",
        name = "SMCommon",
        desc = "",
        icon = getIcon("ENVI_COMMON"),
    ).toList()


def getItemXMLType() -> list:
    return EnumProps().add(
        id   = "StaticObject",
        name = "StaticObject",
        desc = "Static Object",
        icon = "KEYFRAME",
    ).add(
        id   = "DynaObject",
        name = "DynaObject",
        desc = "Dynamic Object",
        icon = "KEYFRAME_HLT",
    ).toList()



def getMeshXMLType() -> list:
    return EnumProps().add(
        id   = "Static",
        name = "Static",
        desc = "Static",
        icon = "KEYFRAME",
    ).add(
        id   = "Dynamic",
        name = "Dynamic",
        desc = "Dynamic",
        icon = "KEYFRAME_HLT",
    ).toList()




def getImportTypes() -> list:
    return EnumProps().add(
        id   = "FILES",
        name = "Files",
        desc = "Files",
        icon = "FILE",
    ).add(
        id   = "FOLDER",
        name = "Folder",
        desc = "Folder",
        icon = "FILE_FOLDER",
    ).toList()






@errorEnumPropsIfNadeoINIisNotValid
def getWorkItemsRootFolderNames(s,c) -> list:
    """return all root folders of ../Work/Items/foldernames[]"""
    rootFolderNames = []
    
    for folder in os.listdir( getGameDocPathWorkItems() ):
        if os.path.isdir( getGameDocPathWorkItems() + folder ):
            rootFolderNames.append(3*(folder,))    
    
    return rootFolderNames








def getIconPerspectives() -> list:
    return EnumProps().add(
        id   = "CLASSIC",
        name = "Classic",
        desc = "Bird view",
        icon = "FILE_TEXT",
    ).add(
        id   = "TOP",
        name = "Top",
        desc = "From Top",
        icon = "ANCHOR_TOP",
    ).add(
        id   = "FRONT",
        name = "Front",
        desc = "From front",
        icon = "ANCHOR_CENTER",
    ).add(
        id   = "BACK",
        name = "Back",
        desc = "From back",
        icon = "ANCHOR_CENTER",
    ).add(
        id   = "LEFT",
        name = "Left",
        desc = "From left",
        icon = "ANCHOR_LEFT",
    ).add(
        id   = "RIGHT",
        name = "Right",
        desc = "From right",
        icon = "ANCHOR_RIGHT",
    ).add(
        id   = "BOTTOM",
        name = "Bottom",
        desc = "From bottom",
        icon = "ANCHOR_BOTTOM",
    ).toList()


def getIconPXdimensions() -> list:
    return EnumProps().add(
        id   = "128",
        name = "128 px",
        desc = "Icon size in pixel",
        icon = "FILE_IMAGE",
    ).add(
        id   = "256",
        name = "256 px",
        desc = "Icon  size in pixel",
        icon = "FILE_IMAGE",
    ).toList()


def updateWorldBG(s,c) -> None:
    tm_props    = c.scene.tm_props
    worlds      = bpy.data.worlds
    tm_world    = "tm_icon_world"
    color       = tm_props.NU_icon_bgColor

    if not tm_world in worlds: generateWorldNode() 

    def changeColor(color):
        bpy.data.worlds[tm_world].node_tree.nodes["TM_BACKGROUND"].inputs[0].default_value = color

    try: changeColor(color)

    except KeyError: 
        generateWorldNode()
        changeColor(color)





def getMaterials(self, context):
    material_prop_list = EnumProps()
    materials          = bpy.data.materials
    
    if len(materials) == 0: 
        return ERROR_ENUM_PROPS
    
    for mat in materials:
        material_prop_list.add(
            id   = mat.name,
            name = mat.name,
            desc = mat.name,
            icon = "MATERIAL"
        )

    return material_prop_list.toList()


def updateMaterialSettings(self, context):
    tm_props    = getTmProps()
    matToUpdate = getTmProps().ST_selectedExistingMaterial
    matToUpdate = bpy.data.materials.get(matToUpdate, None)

    if matToUpdate is None:
        debug("try to get selected material but failed")
        return

    currentColor = matToUpdate.diffuse_color
    if matToUpdate.use_nodes:
        currentColor = matToUpdate.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

    assignments = [
        ("tm_props.ST_materialAddName"      , "matToUpdate.name"),
        ("tm_props.LI_materialCollection"   , "matToUpdate.environment"),
        ("tm_props.LI_materialPhysicsId"    , "matToUpdate.physicsId"),
        ("tm_props.LI_materialModel"        , "matToUpdate.model"),
        ("tm_props.ST_selectedLinkedMat"    , "matToUpdate.link"),
        ("tm_props.ST_materialBaseTexture"  , "matToUpdate.baseTexture"),
        ("tm_props.NU_materialCustomColor"  , "currentColor"),
    ]

    for assignment in assignments:
        variable   = assignment[0]
        value      = assignment[1]
        assignment = f"{variable} = {value}" #"""tm_props.ST_materialAddName = matToUpdate.name"""
        try:
            exec(assignment)
        except TypeError:
            pass

    if matToUpdate.baseTexture != "":
        tm_props.LI_materialChooseSource = "CUSTOM"
    else:
        tm_props.LI_materialChooseSource = "LINK"

    
    setCurrentMatBackupColor()
    redrawPanel(self,context)


def setCurrentMatBackupColor() -> None:
    tm_props = getTmProps()
    method_is_update = tm_props.LI_materialAction == "UPDATE"

    if method_is_update is False:
        return
    
    mat = tm_props.ST_selectedExistingMaterial
    mat = bpy.data.materials.get(mat, None)
    
    tm_props.NU_materialCustomColorOld = mat.diffuse_color
    if mat.use_nodes:
        old_color = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
        tm_props.NU_materialCustomColorOld = old_color


def applyMaterialLiveChanges() -> None:
    tm_props = getTmProps()
    method_is_update = tm_props.LI_materialAction == "UPDATE"

    if method_is_update is False:
        return
    
    mat = tm_props.ST_selectedExistingMaterial
    mat = bpy.data.materials.get(mat, None)

    if mat is not None:
        color = tm_props.NU_materialCustomColor
        mat.diffuse_color = color
        if mat.use_nodes:
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
        
        tm_props.NU_materialCustomColorOld = color


def setMaterialCustomColorLiveChanges(self, context) -> None:
    tm_props = getTmProps()
    method_is_update = tm_props.LI_materialAction == "UPDATE"

    if method_is_update is False:
        return
    
    mat = tm_props.ST_selectedExistingMaterial
    mat = bpy.data.materials.get(mat, None)

    if mat is not None:
        color = tm_props.NU_materialCustomColor
        mat.diffuse_color = color
        if mat.use_nodes:
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color



def revertMaterialCustomColorLiveChanges() -> None:
    tm_props = getTmProps()
    method_is_update = tm_props.LI_materialAction == "UPDATE"

    if method_is_update is False:
        return
    
    mat = tm_props.ST_selectedExistingMaterial
    mat = bpy.data.materials.get(mat, None)

    if mat is not None:
        old_color = tm_props.NU_materialCustomColorOld
        mat.diffuse_color = old_color
        if mat.use_nodes:
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = old_color
        tm_props.NU_materialCustomColor = old_color




def getMaterialModelTypes()->list:
    return EnumProps().add(
        id   = "TDSN",
        name = "TDSN",
        desc = "Raw texture (_D.dds, _S.dds, _N.dds)",
        icon = getIcon("MODEL_TDSN")
    ).add(
        id   = "TDOSN",
        name = "TDOSN",
        desc = "TDSN + 1bit transparency (100% or 0%)",
        icon = getIcon("MODEL_TDOSN") 
    ).add(
        id   = "TDOBSN",
        name = "TDOBSN",
        desc = "TDSN + 256bit transparency (glass for example)",
        icon = getIcon("MODEL_TDOBSN")
    ).add(
        id   = "TDSNI",
        name = "TDSNI",
        desc = "TDSN + glow, additional texture required: _I.dds",
        icon = getIcon("MODEL_TDSNI")
    ).add(
        id   = "TDSNI_NIGHT",
        name = "TDSNI_NIGHT",
        desc = "TDSNI, but only in night and sunset mood",
        icon = getIcon("MODEL_TDSNI_NIGHT")
    ).add(
        id   = "TIAdd",
        name = "TIAdd",
        desc = "Glowing 256bit transparency, only _I.dds is used",
        icon = getIcon("MODEL_TIADD")
    ).toList()



def getMaterialCollectionTypes()->list:
    return EnumProps().add(
        id   = "Stadium",
        name = "Stadium",
        desc = "",
        icon = getIcon("ENVI_STADIUM"),
    ).add(
        id   = "Canyon",
        name = "Canyon",
        desc = "",
        icon = getIcon("ENVI_CANYON"),
    ).add(
        id   = "Valley",
        name = "Valley",
        desc = "",
        icon = getIcon("ENVI_VALLEY"),
    ).add(
        id   = "Lagoon",
        name = "Lagoon",
        desc = "",
        icon = getIcon("ENVI_LAGOON"),
    ).add(
        id   = "Storm",
        name = "Storm",
        desc = "",
        icon = getIcon("ENVI_STORM"),
    ).add(
        id   = "Common",
        name = "Common",
        desc = "",
        icon = getIcon("ENVI_COMMON"),
    ).toList()


def getMaterialActions()->list:
    return EnumProps().add(
        id   = "CREATE",
        name = "Create",
        desc = "Create",
        icon = "ADD",
    ).add(
        id   = "UPDATE",
        name = "Update",
        desc = "Update",
        icon = "FILE_REFRESH",
    ).toList()


def getMaterialTextureSourceOptions()->list:
    return EnumProps().add(
        id   = "LINK",
        name = "Link",
        desc = "Link",
        icon = "LINKED",
    ).add(
        id   = "CUSTOM",
        name = "Custom",
        desc = "Custom",
        icon = "FILE_IMAGE",
    ).toList()


@errorEnumPropsIfNadeoINIisNotValid
def getMaterialPhysicIds(self=None, context=None)->list:
    """get physics from nadeoLibParser() and return as list(tuples)"""
    global material_physics #create global variable to read libfile only once
    
    if len(material_physics) > 1:
        return material_physics
    
    #calling getNadeoImporterLIBPath while addon is registering not allowed:
    #AttributeError: "_RestrictedContext" object has no attribute "scene"
    #return tuple "ERROR" the first few milliseconds to fix it
    #then assign list of physics to matPhysics, to read file only once
    try:    libfile =  getNadeoImporterLIBPath()
    except  AttributeError:
        return material_physics
    
    if not libfile.endswith("Lib.txt"):
        return material_physics
    
    try:
        libmats = getNadeoLibMats()
    except AttributeError:
        return material_physics
    
    physics = []


    for envi in libmats:
        for mat in libmats[envi]:
            mat = libmats[envi][mat]
            phy = mat["PhysicsId"]
            if phy not in physics:
                physics.append(phy)
    
    #some physics are not used by nadeo but exist.
    for missingPhysic in MISSING_PHYSIC_IDS_IN_NADEOLIB: 
        if missingPhysic not in physics:
            physics.append(missingPhysic)
    
    physics.sort()
    physicsWithIcons = EnumProps()
    
    for phy in physics:
        icon = "FUND" if phy in FAVORITE_PHYSIC_IDS else "AUTO"
        physicsWithIcons.add(
            id   = phy,
            name = phy,
            desc = phy,
            icon = icon  
        )

    material_physics = physicsWithIcons.toList()
    return material_physics


def getMaterialLinks(self, context)-> list:
    global material_links
    tm_props = getTmProps()

    if material_links is not ERROR_ENUM_PROPS:
        return material_links


    try:    libfile =  getNadeoImporterLIBPath()
    except  AttributeError:
        return material_links

    if not libfile.endswith("Lib.txt"):
        return material_links
    
    materials    = []
    libmats      = getNadeoLibMats()
    selectedEnvi = str(tm_props.LI_materialCollection).lower()
    i = 0

    for envi in libmats:
        if envi.lower() == selectedEnvi:
            for mat in libmats[envi]:
                if mat not in materials:
                    materials.append((mat, mat, mat))
                    i += 1
            break
    
    materials.sort()
    material_links = materials
    return material_links


def getMaterialGameplayIds(self, context)->None:
    gameplay_id_props_list = EnumProps()

    for gameplay_id in GAMEPLAY_IDS_TM2020:
        gameplay_id_props_list.add(
            id   = gameplay_id,
            name = gameplay_id,
            desc = gameplay_id,
            icon = "AUTO"
        )
    return gameplay_id_props_list.toList()


def getCarNames() -> list:
    return EnumProps().add(
        id   = ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM,
        name = "Car Stadium",
        desc = "Stadium",
        icon = getIcon("TRACKMANIA2020")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_STADIUM,
        name = "Car Stadium",
        desc = "Stadium",
        icon = getIcon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_CANYON,
        name = "Car Canyon",
        desc = "Canyon",
        icon = getIcon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_VALLEY,
        name = "Car Valley",
        desc = "Valley",
        icon = getIcon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_LAGOON,
        name = "Car Lagoon",
        desc = "Lagoon",
        icon = getIcon("MANIAPLANET")
    ).toList()


def getTriggerNames() -> list:
    return EnumProps().add(
        id   = ADDON_ITEM_FILEPATH_TRIGGER_WALL_32x8,
        name = "Wall 32x8",
        desc = "Wall 32x8",
        # icon = "SELECT_INTERSECT"
    ).toList()



def getWorkspaceNames(self, context) -> list:
    workspaces = [w.name for w in bpy.data.workspaces]
    enums = EnumProps()
    
    # filter so a "UV" workspace is the default
    for wspace in workspaces:
        if "UV" in wspace:
            workspaces.remove(wspace)
            workspaces.insert(0, wspace) 
            break

    for wspace in workspaces:
        enums.add(wspace, "Workspace: "+wspace, wspace, "GREASEPENCIL")
    
    return enums.toList()


def getSimpleOrAdvancedXML() -> list:
    return EnumProps().add(
        "simple",
        "Simple",
        "Minimal settings",
    ).add(
        "advanced",
        "Advanced",
        "Advanced settings"
    ).toList()


def getGridSizes() -> list:
    return EnumProps().add(
        "1",
        "1m",
        "1x1 grid"
    ).add(
        "8",
        "8m",
        "8x8 grid",
    ).add(
        "16",
        "16m",
        "16x16 grid",
    ).add(
        "32",
        "32m",
        "32x32 grid",
    ).add(
        "64",
        "64m",
        "64x64 grid",
    ).toList()


def getGridDivisionSizes() -> None:
    return EnumProps().add(
        "1",
        "1",
    ).add(
        "8",
        "8",
    ).add(
        "16",
        "16",
    ).add(
        "32",
        "32",
    ).add(
        "64",
        "64",
    ).toList()


def getSimpleGridParams() -> list:
    grids = [0, 0.5, 1, 2, 4, 8, 16, 32]
    enums = EnumProps()
    for grid in grids:
        enums.add(str(grid), str(grid))
    return enums.toList()






#? CB = CheckBox => BoolProperty
#? LI = List     => EnumProperty
#? NU = Number   => IntProperty, FloatProperty
#? ST = String   => StringProperty

class TM_Properties_for_Panels(bpy.types.PropertyGroup):
    """general trackmania properties"""
    LI_gameType                 : EnumProperty(  name="Game",    items=getGameTypes(),   update=gameTypeGotUpdated)
    ST_nadeoIniFile_MP          : StringProperty(name="",        subtype="FILE_PATH",    update=lambda s, c: updateINI("ST_nadeoIniFile_MP"), default=defaultINI("ST_nadeoIniFile_MP"))
    ST_nadeoIniFile_TM          : StringProperty(name="",        subtype="FILE_PATH",    update=lambda s, c: updateINI("ST_nadeoIniFile_TM"), default=defaultINI("ST_nadeoIniFile_TM"))
    ST_author                   : StringProperty(name="Author",  default="")
    CB_nadeoImporterIsInstalled : BoolProperty(  name="NadeoImporter installed", default=False)
    NU_nadeoImporterDLProgress  : FloatProperty( min=0, max=100, default=0, subtype="PERCENTAGE", update=redrawPanel)
    CB_nadeoImporterDLRunning   : BoolProperty(  default=False,  update=redrawPanel)
    ST_nadeoImporterDLError     : StringProperty(name="Status",  default="", update=redrawPanel)
    CB_nadeoImporterDLshow      : BoolProperty(  default=False,  update=redrawPanel)
    LI_nadeoImporters_MP        : EnumProperty(items=getNadeoImportersManiaplanet(), name="Select NadeoImporter Version")
    ST_nadeoImporter_MP_current : StringProperty("None found")
    LI_nadeoImporters_TM        : EnumProperty(items=getNadeoImportersTrackmania2020(), name="Select NadeoImporter Version")
    ST_nadeoImporter_TM_current : StringProperty("None found")
    LI_blenderGridSize          : EnumProperty(items=getGridSizes(),         default=3, update=changeBlenderGridSize)
    LI_blenderGridSizeDivision  : EnumProperty(items=getGridDivisionSizes(), default=3, update=changeBlenderGridSize)

    CB_addonUpdateDLRunning   : BoolProperty(       default=False,  update=redrawPanel)
    NU_addonUpdateDLProgress  : FloatProperty(      min=0, max=100, default=0, subtype="PERCENTAGE", update=redrawPanel)
    ST_addonUpdateDLmsg       : StringProperty(     name="Status",  default="", update=redrawPanel)
    CB_addonUpdateDLshow      : BoolProperty(       default=False,  update=redrawPanel)
    CB_addonUpdateAvailable   : BoolProperty(       default=False,  update=redrawPanel)

    #object manipulation
    NU_objMplScaleFrom      : IntProperty(default=7, min=1, max=20)
    NU_objMplScaleTo        : IntProperty(default=4, min=1, max=20)
    NU_objMplScaleFactor    : IntProperty(default=4, min=1, max=20)
    CB_objMplScaleRecursive : BoolProperty(default=True, description="Affect child collections")

    #export
    LI_exportType               : EnumProperty(items=getExportTypes(),        name="Action", default=1)
    LI_exportFolderType         : EnumProperty(items=getExportFolderTypes,    name="Folder", default=0)
    ST_exportFolder_MP          : StringProperty(name="Folder", default="",   subtype="DIR_PATH") #update=lambda self, context: makeItemsPathRelative("ST_exportFolder")
    ST_exportFolder_TM          : StringProperty(name="Folder", default="",   subtype="DIR_PATH") #update=lambda self, context: makeItemsPathRelative("ST_exportFolder")
    LI_exportWhichObjs          : EnumProperty(items=getExportWhichObjects(), name="Export by?")
    LI_exportValidTypes         : EnumProperty(name="Export",      items=getExportWhichObjTypes())
    NU_exportObjScale           : FloatProperty(name="Scale", min=0, soft_max=16)
    NU_multiScaleExportFactor   : FloatProperty(name="Steps", min=0, soft_max=8, default=0.25)
    CB_useMultiScaleExport      : BoolProperty(default=True, name="Scale exports", description=DESC_MULTI_SCALE_EXPORT)
    CB_overwriteMultiScaleFactor: BoolProperty(default=False, name="Step factor" , description=DESC_MULTI_SCALE_EXPORT)
    
    #convert
    NU_convertCount              : IntProperty(min=0,               default=0, update=redrawPanel)
    NU_convertedRaw              : IntProperty(min=0,               default=0, update=redrawPanel)
    NU_converted                 : IntProperty(min=0, max=100,      default=0, subtype="PERCENTAGE", update=redrawPanel) 
    NU_convertedSuccess          : IntProperty(min=0,               default=0, update=redrawPanel)
    NU_convertedError            : IntProperty(min=0,               default=0, update=redrawPanel)
    ST_convertedErrorList        : StringProperty(default="",       update=redrawPanel)
    CB_showConvertPanel          : BoolProperty(default=False,      update=redrawPanel)
    CB_stopAllNextConverts       : BoolProperty(default=False,      update=redrawPanel, name="Stop all next converts")
    CB_converting                : BoolProperty(default=False,      update=redrawPanel)
    CB_convertMultiThreaded      : BoolProperty(default=False,      update=redrawPanel, description="Don't convert all at the same time (converts can be cancelled")
    CB_notifyPopupWhenDone       : BoolProperty(default=True,       name="Notify toast when done")
    NU_convertDurationSinceStart : IntProperty(min=-1,              default=-1,   update=redrawPanel)
    NU_convertStartedAt          : IntProperty(min=-1,              default=-1,   update=redrawPanel)
    NU_currentConvertDuration    : IntProperty(min=0,               default=0,    update=redrawPanel)
    NU_prevConvertDuration       : IntProperty(min=0,               default=0,    update=redrawPanel)
    CB_generateMeshAndShapeGBX   : BoolProperty(default=True,       update=redrawPanel, description="To import your item in meshmodeler, those 2 additional files are required")


    #import
    LI_importMatFailed        : StringProperty()
    LI_importType             : EnumProperty(items=getImportTypes())
    CB_importFolderRecursive  : BoolProperty(name="Recursive", default=False)

    #icons
    CB_icon_genIcons        : BoolProperty(name="Generate Icons",         default=True, update=redrawPanel)
    CB_icon_overwriteIcons  : BoolProperty(name="Overwrite Icons",        default=True, update=redrawPanel)
    LI_icon_perspective     : EnumProperty(items=getIconPerspectives(),   name="Perspective")
    LI_icon_pxDimension     : EnumProperty(items=getIconPXdimensions(),   name="Size")
    NU_icon_padding         : IntProperty(min=0, max=100,     default=80, subtype="PERCENTAGE", update=redrawPanel) 
    NU_icon_bgColor         : FloatVectorProperty(name='BG Color',        subtype='COLOR', min=0, max=1, size=4, default=(1,1,1,1), update=updateWorldBG)


    #uvmaps
    CB_uv_genLightMap               : BoolProperty(name="Generate LightMap",                        default=True,       update=redrawPanel)
    CB_uv_fixLightMap               : BoolProperty(name="Only if LM has overlaps",                  default=True,       update=redrawPanel)
    NU_uv_angleLimitLM              : FloatProperty(name="Angle Limit",                             default=r(89.0),    min=0, max=r(89.0), subtype="ANGLE")
    NU_uv_islandMarginLM            : FloatProperty(name="Island Margin",                           default=0.1,        min=0, max=1)
    NU_uv_areaWeightLM              : FloatProperty(name="Area Weight",                             default=0.0,        min=0, max=1)
    CB_uv_correctAspectLM           : BoolProperty(name="Correct Aspect",                           default=True,       update=redrawPanel)
    CB_uv_scaleToBoundsLM           : BoolProperty(name="Scale To Bounds",                          default=False,      update=redrawPanel)
    CB_uv_genBaseMaterialCubeMap    : BoolProperty(name="Generate BaseMaterial with Cube Project",  default=False,      update=redrawPanel)
    NU_uv_cubeProjectSize           : FloatProperty(name="Cube Project",                            default=0.2,        min=0, max=100)
    
    #workspaces
    LI_workspaces : EnumProperty(items=getWorkspaceNames, name="Workspace", default=3)

    #xml
    LI_xml_simpleOrAdvanced : EnumProperty(items=getSimpleOrAdvancedXML())
    LI_xml_simpleGridXY     : EnumProperty(items=getSimpleGridParams())
    LI_xml_simpleGridZ      : EnumProperty(items=getSimpleGridParams())
    CB_xml_syncGridLevi     : BoolProperty(name="Sync Grid & Levi steps",   default=True)
    CB_xml_overwriteMeshXML : BoolProperty(name="Overwrite Mesh XML",       default=True, update=redrawPanel)
    CB_xml_overwriteItemXML : BoolProperty(name="Overwrite Item XML",       default=True, update=redrawPanel)
    CB_xml_genItemXML       : BoolProperty(name="Generate Item XML",        default=True, update=redrawPanel)
    CB_xml_genMeshXML       : BoolProperty(name="Generate Mesh XML",        default=True, update=redrawPanel)
    LI_xml_meshtype         : EnumProperty( name="Type",                    items=getMeshXMLType())
    NU_xml_scale            : FloatProperty(name="Objscales",               default=1.0, min=0, max=256, step=100)
    CB_xml_scale            : BoolProperty( name="Obj Scale",               default=False)
    CB_xml_lightPower       : BoolProperty( name="Lightpower",              default=False)
    NU_xml_lightPower       : FloatProperty(name="Lightpower",              default=1.0, min=0, max=256, step=1)
    CB_xml_lightGlobColor   : BoolProperty(name="Lightcolor",               default=False)
    NU_xml_lightGlobColor   : FloatVectorProperty(name='Lightcolor',        subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855))
    CB_xml_lightGlobDistance: BoolProperty(name="Lightdistance",            default=False)
    NU_xml_lightGlobDistance: FloatProperty(name="Lightdistance",           default=32.0, min=0, max=256, step=1)
    LI_xml_itemtype         : EnumProperty( name="Type",            items=getItemXMLType())
    LI_xml_waypointtype     : EnumProperty( name="Waypoint",        items=getWayPointVariations(), update=onWaypointUpdate)
    LI_xml_enviType         : EnumProperty( name="Envi",            items=getItemXMLCollections())
    NU_xml_gridAndLeviX     : FloatProperty(name="Sync X",          default=8.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridAndLeviY     : FloatProperty(name="Synx Y",          default=8.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridX            : FloatProperty(name="X Grid",          default=8.0, min=0, max=256, step=100)
    NU_xml_gridXoffset      : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_gridY            : FloatProperty(name="Y Grid",          default=8.0,  min=0, max=256, step=100)
    NU_xml_gridYoffset      : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviX            : FloatProperty(name="X Levitation",    default=8.0,  min=0, max=256, step=100)
    NU_xml_leviXoffset      : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviY            : FloatProperty(name="Y Levitation",    default=8.0,  min=0, max=256, step=100)
    NU_xml_leviYoffset      : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    CB_xml_ghostMode        : BoolProperty(name="Ghostmode",        default=True)
    CB_xml_autoRot          : BoolProperty(name="Auto rotation",    default=False, description="Grid needs to be set to 0")
    CB_xml_oneAxisRot       : BoolProperty(name="OneAxisRot",       default=False)
    CB_xml_notOnItem        : BoolProperty(name="Not on Item",      default=True)
    CB_xml_pivots           : BoolProperty(name="Pivots (ingame Q Key)",default=False)
    CB_xml_pivotSwitch      : BoolProperty(name="Pivot switch",     default=False)
    NU_xml_pivotSnapDis     : FloatProperty(name="Pivot snap distance", default=0.0,  min=0, max=256, step=100)

    #materials          
    ST_selectedExistingMaterial : StringProperty(name="Material",                 update=updateMaterialSettings)
    #LI_materials                : EnumProperty(name="Material",                   items=getMaterials, update=updateMaterialSettings)
    LI_materialAction           : EnumProperty(name="Material Action",            default=0, items=getMaterialActions())
    ST_materialAddName          : StringProperty(name="Name",                     default="Matname...")
    LI_materialCollection       : EnumProperty(name="Collection",                 items=getMaterialCollectionTypes(), update=gameTypeGotUpdated)
    CB_materialUsePhysicsId     : BoolProperty(name="Use PhysicsId",              default=False)
    LI_materialPhysicsId        : EnumProperty(name="PhysicId",                   items=getMaterialPhysicIds)
    CB_materialUseGameplayId    : BoolProperty(name="Use GameplayId",             default=False)
    LI_materialGameplayId       : EnumProperty(name="GameplayId",                 items=getMaterialGameplayIds)
    LI_materialModel            : EnumProperty(name="Model",                      items=getMaterialModelTypes())
    #LI_materialLink             : EnumProperty(name="Link",                       items=getMaterialLinks)
    NU_materialCustomColorOld   : FloatVectorProperty(name='OldLightcolor',       subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855, 1.0), size=4,) # as backup, when BELOW changes(live preview)
    NU_materialCustomColor      : FloatVectorProperty(name='Lightcolor',          subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855, 1.0), size=4, update=setMaterialCustomColorLiveChanges)
    ST_materialBaseTexture      : StringProperty(name="BaseTexture",              default="", subtype="FILE_PATH", description="Custom texture located in Documents / Items / <Folders?> / <YouTexturename_D.dds>")
    LI_materialChooseSource     : EnumProperty(name="Custom Texture or Link",     items=getMaterialTextureSourceOptions())
    ST_selectedLinkedMat        : StringProperty(name="Linked mat", default="")

    #textures
    LI_DL_TextureEnvi      : EnumProperty(items=getGameTextureZipFileNames(), update=redrawPanel)
    CB_DL_TexturesRunning  : BoolProperty(name="Downloading...",              default=False, update=redrawPanel)
    NU_DL_Textures         : FloatProperty(min=0, max=100,                    default=0, subtype="PERCENTAGE", update=redrawPanel)
    ST_DL_TexturesErrors   : StringProperty(name="Status",                    default="")
    CB_DL_TexturesShow     : BoolProperty(default=False,                      update=redrawPanel)

    # cars
    LI_items_cars     : EnumProperty(name="Car",     items=getCarNames())
    LI_items_triggers : EnumProperty(name="Trigger", items=getTriggerNames())


class TM_Properties_LinkedMaterials(PropertyGroup):
    """for material creation panel, stores materials from the game's nadeoimportermateriallib.txt (linked)"""
    name : StringProperty(name="Linked mat name", default="")


class TM_Properties_Generated(PropertyGroup):
    """trackmania properties generated"""
    ST_matPhysicsId : StringProperty(name="PhysicsId",             default="Concrete")
    ST_matName      : StringProperty(name="Mat Name",              default="")
    ST_matModel     : StringProperty(name="Mat Model",             default="TDSN")
    ST_matBTex      : StringProperty(name="Mat BaseTexture",       default="StadiumPlatform")
    CB_matBool      : BoolProperty(name="mat name not set yet",    default=False)
    

class TM_Properties_Pivots(PropertyGroup):
    """trackmania properties generated for pivots (item xml)"""
    NU_pivotX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotZ   : FloatProperty(name="Z", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    

class TM_Properties_ConvertingItems(PropertyGroup):
    """trackmania properties generated for pivots (item xml)"""
    name              : StringProperty(name="ITEM NAME ... ", default="ITEM NAME ... ")
    name_raw          : StringProperty(name="COL NAME ... ",  default="COL NAME ... ")
    icon              : StringProperty(name="Icon name",      default="TIME")
    failed            : BoolProperty(name="Convert failed?",  default=False)
    converted         : BoolProperty(name="Item converted?",  default=False)
    convert_duration  : IntProperty(name="Convert duration",  default=0, min=0, max=10000)
    




    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
