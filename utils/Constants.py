import os
import json

DOTNET_COMMANDS = (
    PLACE_OBJECTS_ON_MAP := "place-objects-on-map",
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
ICON_TRUE        = "CHECKMARK"
ICON_FALSE       = "CHECKBOX_DEHLT"
MSG_ERROR_ABSOLUTE_PATH_ONLY            = "Absolute path only!"
MSG_ERROR_NADEO_INI_FILE_NOT_SELECTED   = "Select the Nadeo.ini file first!"
MSG_ERROR_NADEO_INI_NOT_FOUND           = """Autofind failed, check "Help" """


# Path related
PATH_DESKTOP               = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "/"
PATH_HOME                  = os.path.expanduser("~").replace("\\", "/") + "/"
PATH_PROGRAM_DATA          = os.environ.get("ALLUSERSPROFILE").replace("\\", "/")   + "/"
PATH_PROGRAM_FILES         = os.environ.get("PROGRAMFILES").replace("\\", "/")      + "/"
PATH_PROGRAM_FILES_X86     = os.environ.get("PROGRAMFILES(X86)").replace("\\", "/") + "/"
PATH_CONVERT_REPORT        = PATH_DESKTOP + "convert_report.html"
PATH_DEFAULT_SETTINGS_JSON = PATH_HOME + "blender_addon_for_tm2020_maniaplanet_settings.json"


# Links
URL_DOCUMENTATION = "https://github.com/skyslide22/blendermania-addon/wiki/01.-Install-&-Configuration"
URL_BUG_REPORT    = "https://github.com/skyslide22/blendermania-addon"
URL_GITHUB        = "https://github.com/skyslide22/blendermania-addon"
URL_CHANGELOG     = "https://github.com/skyslide22/blendermania-addon/releases"
URL_RELEASES      = "https://api.github.com/repos/skyslide22/blendermania-addon/releases/latest"
URL_REGEX         = "https://regex101.com/"


# Assets CDN Links
GITHUB_ASSETS_BASE_URL       = "https://github.com/skyslide22/blendermania-addon-assets/releases/download/"
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

WAYPOINTS = WaypointDict()
WAYPOINTS["None"]        = COLLECTION_COLOR_TAG_NONE 
WAYPOINTS["Start"]       = COLLECTION_COLOR_TAG_GREEN 
WAYPOINTS["Checkpoint"]  = COLLECTION_COLOR_TAG_BLUE 
WAYPOINTS["StartFinish"] = COLLECTION_COLOR_TAG_YELLOW 
WAYPOINTS["Finish"]      = COLLECTION_COLOR_TAG_RED 


# For waypoint import and live manipulation
SPECIAL_NAME_PREFIXES = (
    SPECIAL_NAME_PREFIX_SOCKET        := "_socket_",
    SPECIAL_NAME_PREFIX_TRIGGER       := "_trigger_",
    SPECIAL_NAME_PREFIX_IGNORE        := "_ignore_",
    SPECIAL_NAME_PREFIX_NOTVISIBLE    := "_notvisible_",
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE := "_notcollidable_",
)

SPECIAL_NAME_SUFFIXES = (
    SPECIAL_NAME_SUFFIX_LOD0        := "_Lod0",
    SPECIAL_NAME_SUFFIX_LOD1        := "_Lod1",
    SPECIAL_NAME_SUFFIX_DOUBLESIDED := "_DoubleSided",
)

GAMETYPE_NAMES = (
    GAMETYPE_TRACKMANIA2020 := "Trackmania2020",
    GAMETYPE_MANIAPLANET    := "ManiaPlanet",
)






# Not all physic ids are listed in the NadeoimporterMaterialLib.txt [Maniaplanet && TM2020]
MISSING_PHYSIC_IDS_IN_NADEOLIB = ["TechSuperMagnetic", "Offzone"]


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
    "ReactorBoost",     
    "ReactorBoost2",
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



# Blender has some issues with our usage of collections with those names
NOT_ALLOWED_COLLECTION_NAMES = ["master collection", "scene", "ignore"]


# Not used yet
NON_DEFAULT_UVLAYER_NAMES = ["Decal","NormalSpec","MulInside"]
DEFAULT_UVLAYER_NAMES     = ["BaseMaterial", "LightMap"]


# Properties which are shared in each panel class
PANEL_CLASS_COMMON_DEFAULT_PROPS = {
    "bl_category":       "TrackmaniaAddon",
    "bl_space_type":     "VIEW_3D",
    "bl_region_type":    "UI",
    #"bl_context":        "objectmode",
    "bl_options":        {"DEFAULT_CLOSED"}
}


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
NADEO_IMPORTER_LATEST_VERSION_TM2020      = "2021_10_15"




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



# https://cdn.discordapp.com/attachments/905181250053107722/941599717182275594/unknown.png
GBX_COMPRESSION_RATIO = 0.666
TRI_TO_MEGABYTE_RATIO = 0.000066

ADDON_ICONS_PATH = os.path.join(os.path.dirname(__file__), os.pardir) + "/icons"





# do not put this on top of file
# circular import
from .Functions import (
    getAddonAssetsPath,
    getAddonPath,
    doesFileExist,

)

# custom items included in addon for import
ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM = getAddonAssetsPath() + "/item_cars/CAR_Trackmania2020_StadiumCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_STADIUM    = getAddonAssetsPath() + "/item_cars/CAR_Maniaplanet_StadiumCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_LAGOON     = getAddonAssetsPath() + "/item_cars/CAR_Maniaplanet_LagoonCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_CANYON     = getAddonAssetsPath() + "/item_cars/CAR_Maniaplanet_CanyonCar_Lowpoly.fbx"
ADDON_ITEM_FILEPATH_CAR_MANIAPLANET_VALLEY     = getAddonAssetsPath() + "/item_cars/CAR_Maniaplanet_ValleyCar_Lowpoly.fbx"


# check if blender is opened by a dev (from vscode..?)
BLENDER_INSTANCE_IS_DEV = os.path.exists(getAddonPath() + ".git")

# imported templates
ADDON_ITEM_FILEPATH_TRIGGER_WALL_32x8 = getAddonAssetsPath() + "/item_triggers/TRIGGER_WALL_32x8.fbx"

# materials map for tm 2020 (someday nadeo gonna have corrent filenames for materials...)
MATERIAL_TEXTURE_MAP_FILEPATH_TM2020 = getAddonAssetsPath()+"/materials/materials-map-trackmania2020.json"
MATERIALS_MAP_TM2020 = {}

if doesFileExist(MATERIAL_TEXTURE_MAP_FILEPATH_TM2020):
    with open(MATERIAL_TEXTURE_MAP_FILEPATH_TM2020, "r") as f:
        data = f.read()
        MATERIALS_MAP_TM2020 = json.loads(data)

















