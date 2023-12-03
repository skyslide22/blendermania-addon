import os
import json

from .. import bl_info

MIN_BLENDER_VERSION = bl_info["blender"]

DOTNET_COMMANDS = (
    PLACE_OBJECTS_ON_MAP             := "place-objects-on-map",
    CONVERT_ITEM_TO_OBJ              := "convert-item-to-obj",
    GET_MEDIATRACKER_CLIPS           := "get-mediatracker-clips",
    PLACE_MEDIATRACKER_CLIPS_ON_MAP  := "place-mediatracker-clips-on-map",
)



TODO_COMMANDS = (
    "crack-map-password",
    "change-map-thumbnail",
    "extract-map-thumbnail",
    "set-daytime-to-rotate-sun-with-mods", #dynamic daytime does not work with mods, not even static
    "get-user-online-login" # /documents/maniapanet/config/<username>.profile.gbx contains the online login (skyslide for me)
)

# path limit in windows 
EXCEED_260_PATH_LIMIT = "\\\\?\\" 

# For saving custom material properties as JSON string in the material (fbx)
MAT_PROPS_AS_JSON = "MAT_PROPS_AS_JSON"




# Panel related
UI_SPACER_FACTOR = 1.0
ICON_CHECKED            = "CHECKMARK"
ICON_UNCHECKED          = "CHECKBOX_DEHLT"
ICON_EXPORT             = "EXPORT"
ICON_IMPORT             = "IMPORT"
ICON_CONVERT            = "CON_FOLLOWPATH"
ICON_UV_MAPS            = "GROUP_UVS"
ICON_ORIGIN             = "PIVOT_CURSOR"
ICON_TRIGGER            = "GIZMO"
ICON_TRIGGER            = "SCREEN_BACK"
ICON_SOCKET             = "OBJECT_ORIGIN"
ICON_SOCKET             = "PIVOT_CURSOR"
ICON_LOD_0              = "MESH_CIRCLE"
ICON_LOD_0              = "THREE_DOTS"
ICON_LOD_0              = "LIGHTPROBE_GRID"
ICON_LOD_0              = "FILE_VOLUME"
ICON_LOD_1              = "MESH_ICOSPHERE"
ICON_LOD_1              = "DOT"
ICON_LOD_1              = "FILE_3D"
ICON_FLAT_SMOOTH        = "MOD_SMOOTH"
ICON_SMOOTH             = "SPHERECURVE"
ICON_FLAT               = "ROOTCURVE"
ICON_SELECTED           = "VIS_SEL_10"
ICON_SELECT             = "RESTRICT_SELECT_OFF"
ICON_VISIBLE            = "HIDE_OFF"
ICON_VIS_SEL            = "VIS_SEL_11"
ICON_HIDDEN             = "HIDE_ON"
ICON_ADD                = "ADD"
ICON_REMOVE             = "REMOVE"
ICON_UPDATE             = "FILE_REFRESH"
ICON_CANCEL             = "X"
ICON_QUESTION           = "QUESTION"
ICON_PARALLEL           = "SORTTIME"
ICON_PARALLEL           = "RECOVER_LAST"
ICON_INFO               = "INFO"
ICON_COLLECTION         = "OUTLINER_COLLECTION"
ICON_OBJECT             = "MESH_MONKEY"
ICON_OBJECT             = "OUTLINER_OB_MESH"
ICON_VIEWLAYER          = "RENDERLAYERS"
ICON_BLENDER            = "BLENDER"
ICON_ADDON              = "FILE_SCRIPT"
ICON_DEBUG              = "FILE_TEXT"
ICON_FOLDER             = "FILE_FOLDER"
ICON_GRID               = "MESH_GRID"
ICON_SNAP               = "SNAP_GRID"
ICON_TEXTURE            = "TEXTURE"
ICON_ASSETS             = "ASSET_MANAGER"
ICON_PERFORMANCE        = "SORTTIME"
ICON_MAP                = "WORLD_DATA"
ICON_BOUNDBOX           = "MESH_CUBE"
ICON_MATERIAL           = "MATERIAL"
ICON_SETTINGS           = "SETTINGS"
ICON_NINJARIPPER        = "GHOST_DISABLED"
ICON_RECURSIVE          = "OUTLINER"
ICON_AUTO               = "AUTO"
ICON_ERROR              = "ERROR"
ICON_SUCCESS            = "CHECKMARK"
ICON_NONE               = "NONE"
ICON_BLANK              = "BLANK1"
ICON_ICON               = "OUTLINER_OB_CAMERA"
ICON_CAMERA             = "VIEW_CAMERA"
ICON_EDIT               = "GREASEPENCIL"
ICON_IGNORE             = "GHOST_DISABLED"
ICON_LIGHT_SPOT         = "LIGHT_SPOT"
ICON_LIGHT_POINT        = "LIGHT_POINT"
ICON_LIGHT_POWER        = "OUTLINER_DATA_LIGHT"
ICON_LIGHT_RADIUS       = "PROP_OFF"
ICON_LIGHT_COLOR        = "KEYTYPE_KEYFRAME_VEC"
ICON_LIGHT_RADIUS_IN    = "PROP_ON"
ICON_LIGHT_RADIUS_OUT   = "PROP_CON"
ICON_DAYTIME            = "LIGHT_SUN"
ICON_AXIS_Z             = "AXIS_TOP"
ICON_AXIS_XY            = "AXIS_FRONT"
ICON_AXIS_X             = "AXIS_FRONT"
ICON_AXIS_Y             = "AXIS_SIDE"
ICON_MAP_PASSWORD_HACK  = "KEYINGSET"
ICON_MAP_EXPORT         = ICON_EXPORT
ICON_GHOSTMODE          = "GHOST_DISABLED"
ICON_AUTO_ROTATION      = "GIZMO"
ICON_ONE_AXIS_ROTATION  = "ORIENTATION_CURSOR"
ICON_SYNC               = "UV_SYNC_SELECT"
ICON_NOT_ON_ITEM        = "SNAP_OFF"
ICON_PIVOTS             = "PIVOT_ACTIVE"
ICON_SWITCH             = "UV_SYNC_SELECT"
ICON_LINKED             = "LINK_BLEND"
ICON_SEARCH             = "VIEWZOOM"
ICON_ENVIRONMENT        = "WORLD"
ICON_COMPRESS           = "FILE_BLEND"
ICON_SAVE               = "FILE_NEW"
ICON_CUBE               = "CUBE"
ICON_TEXT               = "FILE_TEXT"
ICON_MAGNET             = "SNAP_ON"
ICON_TRACKING           = "TRACKING"
ICON_MAP                = "IMAGE_BACKGROUND"
ICON_UGLYPACKAGE        = "UGLYPACKAGE"
ICON_WEBSITE            = "URL"
ICON_ZOOM_MIN           = "ZOOM_IN"
ICON_ZOOM_MAX           = "ZOOM_OUT"
ICON_ROTATION           = "DRIVER_ROTATIONAL_DIFFERENCE"
ICON_SCALE              = "ARROW_LEFTRIGHT"
ICON_LOCATION           = "OBJECT_ORIGIN"
ICON_LOCK               = "LOCKED"
ICON_OVERWRITE          = "CURRENT_FILE"
ICON_FILE               = "FILE_BLANK"
ICON_FILE_NEW           = "FILE_NEW"
ICON_IMAGE_DATA         = "IMAGE_DATA"


EDITORTRAILS_OBJECT_NAME = "_ignore_editortrails"

MAP_GRID_OBJECT_NAME    = "_ignore_map_grid_helper"
MAP_GRID_GEO_NODES_NAME = "Map Grid Geo Nodes"
MAP_VOLUME_OBJECT_NAME    = "_ignore_map_volume_helper"
MAP_VOLUME_GEO_NODES_NAME = "Map Volume Geo Nodes"
MAP_VOLUME_NODES_CUBE_NODE_NAME = "Volume Cube"
MAP_VOLUME_NODES_SETPOSITION_NODE_NAME = "Set Cube Position"

MAX_EMBED_SIZE_MANIAPLANET = 1024 # kB
MAX_EMBED_SIZE_TRACKMANIA2020 = 4096 # kB

# used for visibility/selection
ALL_OBJECTS             = "__ALL__"


# https://cloford.com/resources/charcodes/utf-8_arrows.htm
CHAR_VERTICAL   = "↕"
CHAR_HORIZONTAL = "↔"
CHAR_BOTTOM_RIGHT = "↘"
CHAR_BOTTOM_LEFT  = "↙"
CHAR_TOP          = "↑"

MSG_ERROR_ABSOLUTE_PATH_ONLY            = "Absolute path only!"
MSG_ERROR_NADEO_INI_FILE_NOT_SELECTED   = "Select the Nadeo.ini file first!"
MSG_ERROR_NADEO_INI_NOT_FOUND           = """Autofind failed, check "Help" """


# Path related
PATH_DESKTOP               = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "/"
PATH_HOME                  = os.path.expanduser("~").replace("\\", "/") + "/"
PATH_PROGRAM_DATA          = os.environ.get("ALLUSERSPROFILE").replace("\\", "/")   + "/"
PATH_PROGRAM_FILES         = os.environ.get("PROGRAMFILES").replace("\\", "/")      + "/"
PATH_PROGRAM_FILES_X86     = os.environ.get("PROGRAMFILES(X86)").replace("\\", "/") + "/"
PATH_CONVERT_REPORT        = PATH_HOME + "convert_report.html"
PATH_DEFAULT_SETTINGS_JSON = PATH_HOME + "blender_addon_for_tm2020_maniaplanet_settings.json"


# Links
URL_BLENDER_DOWNLOAD = "https://www.blender.org/download/"
URL_DOCUMENTATION    = "https://github.com/skyslide22/blendermania-addon/wiki/01.-Install-&-Configuration"
URL_BUG_REPORT       = "https://github.com/skyslide22/blendermania-addon"
URL_DISCORD          = "https://discord.com/channels/891279104794574948/921509901077975060"
URL_GITHUB           = "https://github.com/skyslide22/blendermania-addon"
URL_CHANGELOG        = "https://github.com/skyslide22/blendermania-addon/releases"
URL_RELEASES         = "https://api.github.com/repos/skyslide22/blendermania-addon/releases/latest"
URL_REGEX            = "https://regex101.com/"

URL_WORKAROUND_PHYSICID = "https://github.com/skyslide22/blendermania-addon/wiki/06.-Converting-Troubleshooting#physicid-workaround-for-customxxx-materials"

# dotnet addon name and version
BLENDERMANIA_DOTNET = "Blendermania_Dotnet_v0.0.7"

# Assets CDN Links
GITHUB_ASSETS_BASE_URL       = "https://github.com/skyslide22/blendermania-assets/releases/download/"
WEBSPACE_TEXTURES_MP_STADIUM = GITHUB_ASSETS_BASE_URL + "Textures_ManiaPlanet_Stadium/Textures_ManiaPlanet_Stadium.zip"
WEBSPACE_TEXTURES_MP_VALLEY  = GITHUB_ASSETS_BASE_URL + "Textures_ManiaPlanet_Valley/Textures_ManiaPlanet_Valley.zip"
WEBSPACE_TEXTURES_MP_STORM   = GITHUB_ASSETS_BASE_URL + "Textures_ManiaPlanet_Shootmania/Textures_ManiaPlanet_Shootmania.zip"
WEBSPACE_TEXTURES_MP_LAGOON  = GITHUB_ASSETS_BASE_URL + "Textures_ManiaPlanet_Lagoon/Textures_ManiaPlanet_Lagoon.zip"
WEBSPACE_TEXTURES_MP_CANYON  = GITHUB_ASSETS_BASE_URL + "Textures_ManiaPlanet_Canyon/Textures_ManiaPlanet_Canyon.zip"
WEBSPACE_TEXTURES_TM_STADIUM = GITHUB_ASSETS_BASE_URL + "Textures_TrackMania2020/Textures_TrackMania2020.zip"
WEBSPACE_NADEOIMPORTER_MP    = GITHUB_ASSETS_BASE_URL + "NadeoImporter_ManiaPlanet/NadeoImporter_ManiaPlanet.zip"
WEBSPACE_NADEOIMPORTER_TM    = GITHUB_ASSETS_BASE_URL + "NadeoImporter_TrackMania2020/NadeoImporter_TrackMania2020.zip"
WEBSPACE_ASSETS_TM_STADIUM   = GITHUB_ASSETS_BASE_URL + "Assets_Library_TrackMania2020/Assets_Library_TrackMania2020.zip"
WEBSPACE_ASSETS_MP           = GITHUB_ASSETS_BASE_URL + "Assets_Library_Maniaplanet/Assets_Library_Maniaplanet.zip"
WEBSPACE_DOTNET_EXECUTABLE   = GITHUB_ASSETS_BASE_URL + BLENDERMANIA_DOTNET+"/"+BLENDERMANIA_DOTNET+".zip"


# Used for collections in the outliner to define the waypoint type
COLLECTION_COLOR_TAG_NONE   = "NONE" # real icon name is OUTLINER_COLLECTION
COLLECTION_COLOR_TAG_RED    = "COLOR_01"
COLLECTION_COLOR_TAG_ORANGE = "COLOR_02"
COLLECTION_COLOR_TAG_YELLOW = "COLOR_03"
COLLECTION_COLOR_TAG_GREEN  = "COLOR_04"
COLLECTION_COLOR_TAG_BLUE   = "COLOR_05"
COLLECTION_COLOR_TAG_VIOLET = "COLOR_06"
COLLECTION_COLOR_TAG_PINK   = "COLOR_07"
COLLECTION_COLOR_TAG_BROWN  = "COLOR_08"


# Waypoints
class WaypointDict(dict):
    """ask for value, get key, ask for key, get value"""
    def __setitem__(self, key, value):
        parent = super(WaypointDict, self)
        parent.__setitem__(key, value)
        parent.__setitem__(value, key)

WAYPOINT_VALID_NAMES = (
    WAYPOINT_NAME_START         := "Start",
    WAYPOINT_NAME_CHECKPOINT    := "Checkpoint",
    WAYPOINT_NAME_STARTFINISH   := "StartFinish",
    WAYPOINT_NAME_FINISH        := "Finish",
)
WAYPOINT_NAME_NONE = "None"


WAYPOINTS = WaypointDict()
WAYPOINTS[WAYPOINT_NAME_NONE]        = COLLECTION_COLOR_TAG_NONE 
WAYPOINTS[WAYPOINT_NAME_START]       = COLLECTION_COLOR_TAG_GREEN 
WAYPOINTS[WAYPOINT_NAME_CHECKPOINT]  = COLLECTION_COLOR_TAG_BLUE 
WAYPOINTS[WAYPOINT_NAME_STARTFINISH] = COLLECTION_COLOR_TAG_YELLOW 
WAYPOINTS[WAYPOINT_NAME_FINISH]      = COLLECTION_COLOR_TAG_RED 


# For waypoint import and live manipulation
SPECIAL_NAME_PREFIXES = (
    SPECIAL_NAME_PREFIX_SOCKET        := "_socket_",
    SPECIAL_NAME_PREFIX_TRIGGER       := "_trigger_",
    SPECIAL_NAME_PREFIX_IGNORE        := "_ignore_",
    SPECIAL_NAME_PREFIX_ITEM          := "_item_",
    SPECIAL_NAME_PREFIX_GATE          := "_gate_",
    SPECIAL_NAME_PREFIX_NICE          := "_nice_",
    SPECIAL_NAME_PREFIX_ICON_ONLY     := "_icon_only_",
    SPECIAL_NAME_PREFIX_NOTVISIBLE    := "_notvisible_",
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE := "_notcollidable_",
    SPECIAL_NAME_PREFIX_MTTRIGGER     := "_mttrigger_"
)

SPECIAL_NAME_INFIXES = (
    SPECIAL_NAME_INFIX_ORIGIN         := "_origin_",
    SPECIAL_NAME_INFIX_PIVOT         := "_pivot_"
)

SPECIAL_NAME_SUFFIXES = (
    SPECIAL_NAME_SUFFIX_LOD0        := "_Lod0",
    SPECIAL_NAME_SUFFIX_LOD1        := "_Lod1",
    SPECIAL_NAME_SUFFIX_DOUBLESIDED := "_DoubleSided",
)

#Used by VisibilitySelection for dynamically drawing operators
SPECIAL_NAMES_TO_DRAW = {
    SPECIAL_NAME_PREFIX_IGNORE          :ICON_IGNORE,
    SPECIAL_NAME_PREFIX_ICON_ONLY       :ICON_IMAGE_DATA,
    SPECIAL_NAME_INFIX_ORIGIN           :ICON_ORIGIN,
    SPECIAL_NAME_INFIX_PIVOT            :ICON_PIVOTS,
    SPECIAL_NAME_PREFIX_TRIGGER         :ICON_TRIGGER,
    SPECIAL_NAME_PREFIX_SOCKET          :ICON_SOCKET,
    SPECIAL_NAME_SUFFIX_LOD0            :ICON_LOD_0,
    SPECIAL_NAME_SUFFIX_LOD1            :ICON_LOD_1,
    SPECIAL_NAME_PREFIX_NOTVISIBLE      :ICON_HIDDEN,
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE   :ICON_IGNORE,
}

GAMETYPE_NAMES = (
    GAMETYPE_TRACKMANIA2020 := "Trackmania2020",
    GAMETYPE_MANIAPLANET    := "ManiaPlanet",
)






# Not all physic ids are listed in the NadeoimporterMaterialLib.txt [Maniaplanet && TM2020]
MISSING_PHYSIC_IDS_IN_NADEOLIB = ["TechSuperMagnetic", "TechMagnetic", "TechMagneticAccel", "Offzone"]


# For better and faster selection in the dropdown menu
FAVORITE_PHYSIC_IDS = [
        "Concrete",         
        "NotCollidable",
        "Turbo",            
        "Turbo2",
        "Freewheeling",     
        "TechMagnetic",
        "TechSuperMagnetic",
        "Dirt",
        "Grass",            
        "Ice",
        "Wood",             
        "Metal"
    ]


# Not all physic ids are in the NadeoimporterMaterialLib.txt
# from https://doc.trackmania.com/nadeo-importer/04-how-to-create-the-meshparams-xml-file/
# from https://doc.maniaplanet.com/nadeo-importer/import-a-mesh
PHYSIC_IDS_TM2020 = [
    "Asphalt",          
    "Concrete",
    "Dirt",             
    "Grass",
    "Green",            
    "Ice",
    "Metal",            
    "MetalTrans",
    "NotCollidable",    
    "Pavement",
    "ResonantMetal",    
    "RoadIce",
    "RoadSynthetic",    
    "Rock",
    "Snow",             
    "Sand",
    "TechMagnetic",     
    "TechMagneticAccel",
    "TechSuperMagnetic",
    "Wood",
    "Rubber"
]



# Only for tm2020
# Gameplay ids are not defined in the NadeoimporterMaterialLib.txt
# Act like a secondary physic id, for example, Dirt & Freewheeling
# from https://doc.trackmania.com/nadeo-importer/04-how-to-create-the-meshparams-xml-file/
GAMEPLAY_IDS_TM2020 = [
    "Bumper",           
    "Bumper2",
    "Cruise",
    "ForceAcceleration",
    "Fragile",
    "FreeWheeling",
    "NoBrakes",     
    "NoGrip",
    "None",             
    "NoSteering",
    "ReactorBoost_Oriented",     
    "ReactorBoost2_Oriented",
    "Reset",            
    "SlowMotion",
    "Turbo",            
    "Turbo2",
]

# TODO
# from https://doc.trackmania.com/nadeo-importer/04-how-to-create-the-meshparams-xml-file/
LINKED_MATERIALS_COMPATIBLE_WITH_GAMEPLAY_ID = [
    "PlatformDirt_PlatformTech",
    "PlatformGrass_PlatformTech",
    "PlatformIce_PlatformTech",
    "PlatformTech",
    "RoadBump",
    "RoadDirt",
    "RoadIce",
    "RoadTech",
]

# # all customXXX are incompatible ...
# LINKED_MATERIALS_INCOMPATIBLE_WITH_PHYSICS_ID = [
#     "CustomBricks",
#     "CustomConcrete",
#     "CustomDirt",
#     "CustomGlass",
#     "CustomGrass",
#     "CustomIce",
#     "CustomMetal",
#     "CustomMetalPainted",
#     "CustomPlastic",
#     "CustomPlasticShiny",
#     "CustomRock",
#     "CustomRoughWood",
#     "CustomSand",
#     "CustomSnow",
# ]



# Blender has some issues with our usage of collections with those names
NOT_ALLOWED_COLLECTION_NAMES = ["master collection", "scene", "ignore"]


# Not used yet
NON_DEFAULT_UVLAYER_NAMES = ["Decal","NormalSpec","MulInside"]
DEFAULT_UVLAYER_NAMES     = ["BaseMaterial", "LightMap"]


# Properties which are shared in each panel class
PANEL_CLASS_COMMON_DEFAULT_PROPS = {
    "bl_category":       "Blendermania",
    "bl_space_type":     "VIEW_3D",
    "bl_region_type":    "UI",
    #"bl_context":        "objectmode",
    "bl_options":        {"DEFAULT_CLOSED"}
}

# Map export
MAP_OBJECT_TYPES = {
    MAP_OBJECT_BLOCK := "block",
    MAP_OBJECT_ITEM := "item",
}

MAP_OBJECT_TYPES_PROP = (
    #(MAP_OBJECT_BLOCK, "Block", ""), GBX.NET can't place free blocks yet, come back to it later
    (MAP_OBJECT_ITEM, "Item", ""),
)


# Custom properties of the materials for iterating & checking
MATERIAL_CUSTOM_PROPERTIES = [
        "name",
        "gameType",
        "baseTexture",
        "link",
        "physicsId",
        "usePhysicsId",
        "gameplayId",
        "useGameplayId",
        "model",
        "environment",
        "surfaceColor",
    ]



NADEO_IMPORTER_LATEST_VERSION_MANIAPLANET = "2019_10_09"
NADEO_IMPORTER_LATEST_VERSION_TM2020      = "2022_07_12"
NADEO_IMPORTER_ICON_OVERWRITE_VERSION     = "2022_07_12"



UV_LAYER_NAMES = (
    UV_LAYER_NAME_BASEMATERIAL := "BaseMaterial",
    UV_LAYER_NAME_LIGHTMAP     := "LightMap",
)

NADEO_MATLIB_DLIBRARYS = (
    NADEO_MATLIB_DLIBRARY_STORM   := "Storm",
    NADEO_MATLIB_DLIBRARY_STADIUM := "Stadium",
    NADEO_MATLIB_DLIBRARY_CANYON  := "Canyon",
    NADEO_MATLIB_DLIBRARY_VALLEY  := "Valley",
    NADEO_MATLIB_DLIBRARY_LAGOON  := "Lagoon",
)



ADDON_ICONS_PATH = os.path.join(os.path.dirname(__file__), os.pardir) + "/icons"


SETTINGS_JSON_KEYS = (
    SETTINGS_AUTHOR_NAME              := "author_name",
    SETTINGS_NADEO_INI_TRACKMANIA2020 := "nadeo_ini_path_tm",
    SETTINGS_NADEO_INI_MANIAPLANET    := "nadeo_ini_path_mp",
    SETTINGS_BLENDER_GRID_SIZE        := "blender_grid_size",
    SETTINGS_BLENDER_GRID_DIVISION    := "blender_grid_division",
    SETTINGS_ITEM_XML_TEMPLATES       := "itemxml_templates",
    SETTINGS_NEW_BLEND_PREFERRED_GAME := "new_blend_game",
)

ENVIRONMENT_NAMES = (
    ENVI_NAME_STADIUM    := "Stadium",
    ENVI_NAME_VALLEY     := "Valley",
    ENVI_NAME_CANYON     := "Canyon",
    ENVI_NAME_LAGOON     := "Lagoon",
    ENVI_NAME_SHOOTMANIA := "Shootmania",
)



# do not put this on top of file
# circular import
from .Functions import (
    get_addon_assets_path,
    get_addon_path,
    is_file_existing,

)

# custom items included in addon for import
ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM = get_addon_assets_path() + "/item_cars/CAR_Trackmania2020_StadiumCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_STADIUM    = get_addon_assets_path() + "/item_cars/CAR_Maniaplanet_StadiumCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_LAGOON     = get_addon_assets_path() + "/item_cars/CAR_Maniaplanet_LagoonCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_CANYON     = get_addon_assets_path() + "/item_cars/CAR_Maniaplanet_CanyonCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_VALLEY     = get_addon_assets_path() + "/item_cars/CAR_Maniaplanet_ValleyCar_Lowpoly.fbx"


# check if blender is opened by a dev (from vscode..?)
BLENDER_INSTANCE_IS_DEV = os.path.exists(get_addon_path() + ".git")

# imported templates
ADDON_ITEM_FILEPATH_TRIGGER_WALL_32x8  = get_addon_assets_path() + "/item_triggers/TRIGGER_WALL_32x8.fbx"
ADDON_ITEM_FILEPATH_MT_TRIGGER_10_66x8 = get_addon_assets_path() + "/item_mt_triggers/MT_TRIGGER_10_66x8.fbx"

# materials map for tm 2020 (someday nadeo gonna have corrent filenames for materials...)
MATERIAL_TEXTURE_MAP_FILEPATH_TM2020 = get_addon_assets_path()+"/materials/materials-map-trackmania2020.json"
MATERIALS_MAP_TM2020 = {}

if is_file_existing(MATERIAL_TEXTURE_MAP_FILEPATH_TM2020):
    with open(MATERIAL_TEXTURE_MAP_FILEPATH_TM2020, "r") as f:
        data = f.read()
        for item in json.loads(data):
            MATERIALS_MAP_TM2020[item["Name"]] = item






MODWORK_FOLDER_NAME     = "ModWork" 
MODWORK_OFF_FOLDER_NAME = "#-ModWork" 


NL = "\n"







