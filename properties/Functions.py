from typing import Iterable
import bpy
import bpy.utils.previews
from bpy.props import *

from ..utils.ItemsIcon import generate_world_node
from ..utils.Functions import *
from ..utils.Constants import *

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

    def to_list(self) -> list:
        return self._list

    def remove(self, id: str) -> None:
        self._list = filter(lambda item: item[0] != id, self._list)

    def as_json(self) -> str:
        return json.dumps(self._list)

    def from_json(self, json_str: str) -> None:
        enum_props = json.loads(json_str)
        self._list = enum_props




ERROR_ENUM_ID    = "ERROR"
ERROR_ENUM_PROPS = EnumProps().add(id=ERROR_ENUM_ID, name ="Nothing found", desc=ERROR_ENUM_ID, icon="ERROR").to_list()
material_physics = ERROR_ENUM_PROPS
material_links   = ERROR_ENUM_PROPS


def is_convert_panel_active() -> bool:
    return get_global_props().CB_showConvertPanel


def errorEnumPropsIfNadeoINIisNotValid(func) -> callable:
    #func has to return tuple with tuples: ( (3x str or 4x str and unique index), )
    def wrapper(self, context):
        return func(self, context) if is_selected_nadeoini_file_name_ok() else ERROR_ENUM_PROPS        
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
            icon=ICON_UPDATE)

        isFirst = False
    
    return items.to_list()


def getNadeoImportersTrackmania2020() -> list:
    importers = ["2022_07_12.zip", "2021_10_15.zip", "2021_07_07.zip"]
    isFirst = True

    items = EnumProps()
    for imp in importers:
        name = " (latest)" if isFirst else ""

        items.add(
            id=imp,
            name=imp.lower().replace("nadeoimporter_","v. ").replace(".zip", "")+name,
            desc=imp,
            icon=ICON_UPDATE)

        isFirst = False

    return items.to_list()


def updateINI(prop) -> None:
    is_nadeoimporter_installed(prop)
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
        icon = get_addon_icon(GAMETYPE_MANIAPLANET)
    ).add(
        id   = GAMETYPE_TRACKMANIA2020,
        name = GAMETYPE_TRACKMANIA2020,
        desc = GAMETYPE_TRACKMANIA2020,
        icon = get_addon_icon(GAMETYPE_TRACKMANIA2020)
    ).to_list()
    


def gameTypeGotUpdated(self=None,context=None)->None:
    """reset important variables to fit new gameType environment"""
    is_nadeoimporter_installed()
    reset_nadeoini_settings()
    
    global material_links, material_physics, nadeoimporter_materiallib_materials
    material_links   = ERROR_ENUM_PROPS
    material_physics = ERROR_ENUM_PROPS
    parse_nadeoimporter_materiallibrary()

    tm_props     = get_global_props()
    colIsStadium = tm_props.LI_materialCollection.lower() == "stadium"

    if is_game_trackmania2020() and not colIsStadium:
        tm_props.LI_materialCollection = "Stadium"

    if is_game_trackmania2020():
        tm_props.LI_DL_TextureEnvi = "Stadium"
    
    update_installed_nadeoimporter_version_ui()

    redraw_all_panels()

    return None



def getGameTextureZipFileNames()->list:
    return EnumProps().add(
        id   = ENVI_NAME_STADIUM,
        name = ENVI_NAME_STADIUM,
        desc = ENVI_NAME_STADIUM,
        icon = get_addon_icon("ENVI_STADIUM")
    ).add(
        id   = ENVI_NAME_VALLEY,
        name = ENVI_NAME_VALLEY,
        desc = ENVI_NAME_VALLEY,
        icon = get_addon_icon("ENVI_VALLEY")
    ).add(
        id   = ENVI_NAME_CANYON,
        name = ENVI_NAME_CANYON,
        desc = ENVI_NAME_CANYON,
        icon = get_addon_icon("ENVI_CANYON")
    ).add(
        id   = ENVI_NAME_LAGOON,
        name = ENVI_NAME_LAGOON,
        desc = ENVI_NAME_LAGOON,
        icon = get_addon_icon("ENVI_LAGOON")
    ).add(
        id   = ENVI_NAME_SHOOTMANIA,
        name = ENVI_NAME_SHOOTMANIA,
        desc = ENVI_NAME_SHOOTMANIA,
        icon = get_addon_icon("ENVI_STORM")
    ).to_list()



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
    ).to_list()



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
    if is_game_maniaplanet():
        folders.add(
            id   = "Stadium",
            name = "Stadium",
            desc = "Stadium",
            icon = get_addon_icon("ENVI_STADIUM")
        ).add(
            id   = "Valley",
            name = "Valley",
            desc = "Valley",
            icon = get_addon_icon("ENVI_VALLEY")
        ).add(
            id   = "Canyon",
            name = "Canyon",
            desc = "Canyon",
            icon = get_addon_icon("ENVI_CANYON")
        ).add(
            id   = "Lagoon",
            name = "Lagoon",
            desc = "Lagoon",
            icon = get_addon_icon("ENVI_LAGOON")
        ).add(
            id   = "Shootmania",
            name = "Shootmania",
            desc = "Shootmania",
            icon = get_addon_icon("ENVI_STORM")
        )
    return folders.to_list()



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
    ).to_list()



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
    ).to_list()






def updateGridAndLevi(self, context) -> None:
    tm_props = get_global_props()
    place_xy = tm_props.NU_xml_gridAndLeviX
    place_z  = tm_props.NU_xml_gridAndLeviY
    tm_props.NU_xml_gridX = place_xy
    tm_props.NU_xml_gridY = place_z
    tm_props.NU_xml_leviX = place_xy
    tm_props.NU_xml_leviY = place_z
    
    offset_xy = tm_props.NU_xml_gridAndLeviOffsetX
    offset_z  = tm_props.NU_xml_gridAndLeviOffsetY
    tm_props.NU_xml_gridXoffset = offset_xy
    tm_props.NU_xml_gridYoffset = offset_z
    tm_props.NU_xml_leviXoffset = offset_xy
    tm_props.NU_xml_leviYoffset = offset_z


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
    ).to_list()

     

def onWaypointUpdate(self,context) -> None:
    redraw_panels(self,context)
    set_waypointtype_of_selected_collection()


def getItemXMLCollections() -> list:
    return EnumProps().add(
        id   = "Stadium",
        name = "Stadium",
        desc = "",
        icon = get_addon_icon("ENVI_STADIUM"),
    ).add(
        id   = "Canyon",
        name = "Canyon",
        desc = "",
        icon = get_addon_icon("ENVI_CANYON"),
    ).add(
        id   = "Valley",
        name = "Valley",
        desc = "",
        icon = get_addon_icon("ENVI_VALLEY"),
    ).add(
        id   = "Lagoon",
        name = "Lagoon",
        desc = "",
        icon = get_addon_icon("ENVI_LAGOON"),
    ).add(
        id   = "Storm",
        name = "Storm",
        desc = "",
        icon = get_addon_icon("ENVI_STORM"),
    ).add(
        id   = "Common",
        name = "Common",
        desc = "",
        icon = get_addon_icon("ENVI_COMMON"),
    ).add(
        id   = "SMCommon",
        name = "SMCommon",
        desc = "",
        icon = get_addon_icon("ENVI_COMMON"),
    ).to_list()


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
    ).to_list()



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
    ).to_list()




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
    ).to_list()






@errorEnumPropsIfNadeoINIisNotValid
def getWorkItemsRootFolderNames(s,c) -> list:
    """return all root folders of ../Work/Items/foldernames[]"""
    rootFolderNames = []
    
    for folder in os.listdir( get_game_doc_path_work_items() ):
        if os.path.isdir( get_game_doc_path_work_items() + folder ):
            rootFolderNames.append(3*(folder,))    
    
    return rootFolderNames








def getIconPerspectives() -> list:
    return EnumProps().add(
        id   = "CLASSIC_SE",
        name = "Classic_SE",
        desc = "Bird view SE",
        icon = "FILE_TEXT",
    ).add(
        id   = "CLASSIC_SW",
        name = "Classic_SW",
        desc = "Bird view SW",
        icon = "FILE_TEXT",
    ).add(
        id   = "CLASSIC_NW",
        name = "Classic_NW",
        desc = "Bird view NW",
        icon = "FILE_TEXT",
    ).add(
        id   = "CLASSIC_NE",
        name = "Classic_NE",
        desc = "Bird view NE",
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
    ).to_list()


def getIconWorlds() -> list:
    return EnumProps().add(
        id   = "STANDARD",
        name = "Standard",
        desc = "Standard world with colorable background",
        icon = "WORLD",
    ).add(
        id   = "TM2020-STADIUM",
        name = "Stadium",
        desc = "TM2020 stadium",
        icon = "IMAGE_DATA",
    ).to_list()


def getIconPXdimensions() -> list:
    return EnumProps().add(
        id   = "64",
        name = "64 px",
        desc = "Icon size in pixel",
        icon = "FILE_IMAGE",
    ).add(
        id   = "128",
        name = "128 px",
        desc = "Icon size in pixel",
        icon = "FILE_IMAGE",
    ).add(
        id   = "256",
        name = "256 px",
        desc = "Icon  size in pixel",
        icon = "FILE_IMAGE",
    ).to_list()


def updateWorldBG(s,c) -> None:
    tm_props    = c.scene.tm_props
    worlds      = bpy.data.worlds
    tm_world    = "tm_icon_world"
    color       = tm_props.NU_icon_bgColor

    if not tm_world in worlds: generate_world_node() 

    def changeColor(color):
        bpy.data.worlds[tm_world].node_tree.nodes["TM_BACKGROUND"].inputs[0].default_value = color

    try: changeColor(color)

    except KeyError: 
        generate_world_node()
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

    return material_prop_list.to_list()


def updateMaterialSettings(self, context):
    tm_props    = get_global_props()
    matToUpdate = get_global_props().ST_selectedExistingMaterial
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
    redraw_panels(self,context)


def setCurrentMatBackupColor() -> None:
    tm_props = get_global_props()
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
    tm_props = get_global_props()
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
    tm_props = get_global_props()
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
    tm_props = get_global_props()
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
        icon = get_addon_icon("MODEL_TDSN")
    ).add(
        id   = "TDOSN",
        name = "TDOSN",
        desc = "TDSN + 1bit transparency (100% or 0%)",
        icon = get_addon_icon("MODEL_TDOSN") 
    ).add(
        id   = "TDOBSN",
        name = "TDOBSN",
        desc = "TDSN + 256bit transparency (glass for example)",
        icon = get_addon_icon("MODEL_TDOBSN")
    ).add(
        id   = "TDSNI",
        name = "TDSNI",
        desc = "TDSN + glow, additional texture required: _I.dds",
        icon = get_addon_icon("MODEL_TDSNI")
    ).add(
        id   = "TDSNI_NIGHT",
        name = "TDSNI_NIGHT",
        desc = "TDSNI, but only in night and sunset mood",
        icon = get_addon_icon("MODEL_TDSNI_NIGHT")
    ).add(
        id   = "TIAdd",
        name = "TIAdd",
        desc = "Glowing 256bit transparency, only _I.dds is used",
        icon = get_addon_icon("MODEL_TIADD")
    ).to_list()



def getMaterialCollectionTypes()->list:
    return EnumProps().add(
        id   = "Stadium",
        name = "Stadium",
        desc = "",
        icon = get_addon_icon("ENVI_STADIUM"),
    ).add(
        id   = "Canyon",
        name = "Canyon",
        desc = "",
        icon = get_addon_icon("ENVI_CANYON"),
    ).add(
        id   = "Valley",
        name = "Valley",
        desc = "",
        icon = get_addon_icon("ENVI_VALLEY"),
    ).add(
        id   = "Lagoon",
        name = "Lagoon",
        desc = "",
        icon = get_addon_icon("ENVI_LAGOON"),
    ).add(
        id   = "Storm",
        name = "Storm",
        desc = "",
        icon = get_addon_icon("ENVI_STORM"),
    ).add(
        id   = "Common",
        name = "Common",
        desc = "",
        icon = get_addon_icon("ENVI_COMMON"),
    ).to_list()


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
    ).to_list()


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
    ).to_list()


@errorEnumPropsIfNadeoINIisNotValid
def getMaterialPhysicIds(self=None, context=None)->list:
    """get physics from nadeoLibParser() and return as list(tuples)"""
    global material_physics #create global variable to read libfile only once
    
    if len(material_physics) > 1:
        return material_physics
    
    #calling get_nadeo_importer_lib_path while addon is registering not allowed:
    #AttributeError: "_RestrictedContext" object has no attribute "scene"
    #return tuple "ERROR" the first few milliseconds to fix it
    #then assign list of physics to matPhysics, to read file only once
    try:    libfile =  get_nadeo_importer_lib_path()
    except  AttributeError:
        return material_physics
    
    if not libfile.endswith("Lib.txt"):
        return material_physics
    
    try:
        libmats = get_nadeoimporter_materiallibrary_materials()
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

    material_physics = physicsWithIcons.to_list()
    return material_physics


def getMaterialLinks(self, context)-> list:
    global material_links
    tm_props = get_global_props()

    if material_links is not ERROR_ENUM_PROPS:
        return material_links


    try:    libfile =  get_nadeo_importer_lib_path()
    except  AttributeError:
        return material_links

    if not libfile.endswith("Lib.txt"):
        return material_links
    
    materials    = []
    libmats      = get_nadeoimporter_materiallibrary_materials()
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
    return gameplay_id_props_list.to_list()


def get_car_names() -> list:
    return EnumProps().add(
        id   = ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM,
        name = "Car Stadium",
        desc = "Stadium",
        icon = get_addon_icon("TRACKMANIA2020")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_STADIUM,
        name = "Car Stadium",
        desc = "Stadium",
        icon = get_addon_icon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_CANYON,
        name = "Car Canyon",
        desc = "Canyon",
        icon = get_addon_icon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_VALLEY,
        name = "Car Valley",
        desc = "Valley",
        icon = get_addon_icon("MANIAPLANET")
    ).add(
        id   = ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_LAGOON,
        name = "Car Lagoon",
        desc = "Lagoon",
        icon = get_addon_icon("MANIAPLANET")
    ).to_list()


def getTriggerNames() -> list:
    return EnumProps().add(
        id   = ADDON_ITEM_FILEPATH_TRIGGER_WALL_32x8,
        name = "Wall 32x8",
        desc = "Wall 32x8",
        # icon = "SELECT_INTERSECT"
    ).to_list()



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
    
    return enums.to_list()


def get_itemxml_display_menu() -> list:
    return EnumProps().add(
        "simple",
        "Simple",
        "Minimal settings",
    ).add(
        "advanced",
        "Advanced",
        "Advanced settings"
    ).add(
        "template",
        "Templates",
        "Use & Configure Templates"
    ).to_list()


def getGridSizes() -> list:
    return EnumProps().add(
        "1",
        "1",
        "1x1 grid"
    ).add(
        "8",
        "8",
        "8x8 grid",
    ).add(
        "16",
        "16",
        "16x16 grid",
    ).add(
        "32",
        "32",
        "32x32 grid",
    ).add(
        "64",
        "64",
        "64x64 grid",
    ).to_list()


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
    ).to_list()


def getClipStartSizes() -> None:
    return EnumProps().add(
        "0.01",
        "Min",
    ).add(
        "4",
        "Normal",
    ).add(
        "64",
        "Max",
    ).to_list()

def getClipEndSizes() -> None:
    return EnumProps().add(
        "64",
        "Min",
    ).add(
        "1000",
        "Normal",
    ).add(
        "20000",
        "Max",
    ).to_list()


def getSimpleGridParams() -> list:
    # grids = [0, 0.5, 1, 2, 4, 8, 16, 32]
    # enums = EnumProps()
    # for grid in grids:
    #     enums.add(str(grid), str(grid))

    enums = EnumProps()
    enums.add("0",  "Sticky", icon=ICON_MAGNET)
    # enums.add("0.5","0.5",)
    enums.add("1",  "1",)
    enums.add("2",  "2",)
    enums.add("4",  "4",)
    enums.add("8",  "8",)
    enums.add("16", "16",)
    enums.add("32", "32",)
    # enums.add("64", "64",)
    return enums.to_list()


def get_itemxml_template_names_enum(self, context) -> list:
    templates = EnumProps()
    for template in context.scene.tm_props_itemxml_templates:
        templates.add(
            id=template.name,
            name=template.name,
        )
    return templates.to_list() or ERROR_ENUM_PROPS


class MediaTrackerClips:
    current_names:list[str] = []

def provide_current_map_mt_clip_names(self, context, edit_text) -> list:
    return MediaTrackerClips.current_names