from datetime import datetime
from os.path import abspath, relpath
import string
import subprocess
import threading
import urllib.request
import urllib.error
import bpy
import os
import re
import math
import configparser
import json
import uuid
import pprint
import ctypes
from zipfile import ZipFile
from threading import Thread
from inspect import currentframe, getframeinfo
import bpy.utils.previews
from bpy.types import Key, UIList 




def getAddonPath() -> str:
    return os.path.dirname(__file__) + "/"

MSG_ERROR_ABSOLUTE_PATH = "Absolute path only!"
MSG_ERROR_NADEO_INI     = "Select the Nadeo.ini file first!"
UI_SPACER_FACTOR        = 1.0

URL_DOCUMENTATION       = "https://images.mania.exchange/com/skyslide/Blender-Addon-Tutorial/"
URL_BUG_REPORT          = "https://github.com/skyslide22/blender-addon-for-trackmania-and-maniaplanet"
URL_GITHUB              = "https://github.com/skyslide22/blender-addon-for-trackmania-and-maniaplanet"
URL_REGEX               = "https://regex101.com/"
PATH_DESKTOP            = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "/"
PATH_HOME               = os.path.expanduser("~")
PATH_DOCUMENTS          = os.path.expanduser("~/Documents/").replace("\\", "/")
PATH_PROGRAM_DATA       = os.environ.get("ALLUSERSPROFILE").replace("\\", "/")   + "/"
PATH_PROGRAM_FILES      = os.environ.get("PROGRAMFILES").replace("\\", "/")      + "/"
PATH_PROGRAM_FILES_X86  = os.environ.get("PROGRAMFILES(X86)").replace("\\", "/") + "/"
PATH_CONVERT_REPORT     = PATH_DESKTOP + "convert_report.html"

WEBSPACE_BASE_URL                 = "https://images.mania.exchange/com/skyslide/"
WEBSPACE_TEXTURES_MP_STADIUM     = WEBSPACE_BASE_URL + "_DTextures_ManiaPlanet_Stadium.zip"
WEBSPACE_TEXTURES_MP_VALLEY      = WEBSPACE_BASE_URL + "_DTextures_ManiaPlanet_Valley.zip"
WEBSPACE_TEXTURES_MP_STORM       = WEBSPACE_BASE_URL + "_DTextures_ManiaPlanet_Shootmania.zip"
WEBSPACE_TEXTURES_MP_LAGOON      = WEBSPACE_BASE_URL + "_DTextures_ManiaPlanet_Lagoon.zip"
WEBSPACE_TEXTURES_MP_CANYON      = WEBSPACE_BASE_URL + "_DTextures_ManiaPlanet_Canyon.zip"
WEBSPACE_TEXTURES_TM_STADIUM     = WEBSPACE_BASE_URL + "_DTextures_TrackMania2020.zip"
WEBSPACE_NADEOIMPORTER_MP        = WEBSPACE_BASE_URL + "NadeoImporter_ManiaPlanet.zip"
WEBSPACE_NADEOIMPORTER_TM        = WEBSPACE_BASE_URL + "NadeoImporter_TrackMania2020.zip"

MAT_PROPS_AS_JSON = "MAT_PROPS_AS_JSON"

COLOR_CHECKPOINT = "COLOR_05" 
COLOR_START      = "COLOR_04" 
COLOR_FINISH     = "COLOR_01" 
COLOR_STARTFINISH= "COLOR_03" 

missingPhysicsInLib = ["TechSuperMagnetic", "Offzone"]
favPhysicIds = [
        "Concrete",         "NotCollidable",
        "Turbo",            "Turbo2",
        "Freewheeling",     "TechMagnetic",
        "TechSuperMagnetic","Dirt",
        "Grass",            "Ice",
        "Wood",             "Metal"
    ]
tm2020PhysicIds = [
    "Asphalt",          "Concrete",
    "Dirt",             "Grass",
    "Green",            "Ice",
    "Metal",            "MetalTrans",
    "NotCollidable",    "Pavement",
    "ResonantMetal",    "RoadIce",
    "RoadSynthetic",    "Rock",
    "Snow",             "Sand",
    "TechMagnetic",     "TechMagneticAccel",
    "TechSuperMagnetic","Wood",
    "Rubber"
]
tm2020GameplayIds = [
    "Bumper",           "Bumper2",
    "ForceAcceleration","Fragile",
    "FreeWheeling",     "NoGrip",
    "ReactorBoost",     "ReactorBoost2",
    "Reset",            "SlowMotion",
    "Turbo",            "Turbo2",
    "None",             "NoSteering",
]

notAllowedColnames      = ["master collection", "scene", "ignore"]
notDefaultUVLayerNames  = ["Decal","NormalSpec","MulInside"]
defaultUVLayerNames     = ["BaseMaterial", "LightMap"]

panelClassDefaultProps = {
    "bl_category":       "TrackmaniaAddon",
    "bl_space_type":     "VIEW_3D",
    "bl_region_type":    "UI",
    "bl_context":        "objectmode",
}

mat_props = [
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
# -----

"""NADEO.INI DATA"""
nadeoIniSettings = {}


"""NadeoImporterMaterialLib.txt data"""
nadeoLibMaterials = {}


    

def getNadeoIniFilePath() -> str:
    if isGameTypeManiaPlanet():
        return fixSlash(bpy.context.scene.tm_props.ST_nadeoIniFile_MP)

    if isGameTypeTrackmania2020():
        return fixSlash(bpy.context.scene.tm_props.ST_nadeoIniFile_TM)
    
    else: return ""


def getTrackmaniaEXEPath() -> str:
    """get absolute path of C:/...ProgrammFiles/ManiaPlanet/ or Ubisoft/games/Trackmania etc..."""
    path = getNadeoIniFilePath()
    path = path.split("/")
    path.pop()
    path = "/".join(path)
    return path #just remove /Nadeo.ini ...


def resetNadeoIniSettings()->None:
    global nadeoIniSettings
    nadeoIniSettings = {}


def getNadeoIniData(setting: str) -> str:
    """return setting, if setting is not in dict nadeoIniSettings, read nadeo.ini and add it"""
    wantedSetting = setting
    # possibleSettings = ["WindowTitle", "Distro", "Language", "UserDir", "CommonDir"] #gg steam
    possibleSettings = ["WindowTitle", "Distro", "UserDir", "CommonDir"]
    
    try:
        setting = nadeoIniSettings[wantedSetting]
        if "{userdocs}"in setting.lower()\
        or "{userdir}" in setting.lower():
            debug(f"requested Ini key <{setting}> value has a variable in it, raise KEYERROR")
            raise KeyError

        else: 
            return setting
    
    except KeyError: #if setting does not exist, add.
        nadeoIniFilepath = getNadeoIniFilePath()
        iniData = configparser.ConfigParser()
        iniData.read(nadeoIniFilepath)
        category = "ManiaPlanet" if isGameTypeManiaPlanet() else "Trackmania"
        
        for setting in possibleSettings:
            if setting not in nadeoIniSettings.keys():
                nadeoIniSettings[setting] = iniData.get(category, setting) #ex: ManiaPlanet, UserDir
        
        for ini_key, ini_value in nadeoIniSettings.items():
            
            #maniaplanet.exe path
            if ini_value.startswith("{exe}"):
                nadeoIniSettings[ini_key] = fixSlash( ini_value.replace("{exe}", getNadeoIniFilePath().replace("Nadeo.ini", "")) + "/" )
                continue

            # /Documents/Trackmania is used by TMUF, 
            # if TMUF is installed, /Trackmania2020 is created and used by tm2020.exe
            docPathIsCustom = False
            if   "{userdocs}" in ini_value.lower():     docPathIsCustom = True #maniaplanet
            elif "{userdir}"  in ini_value.lower():     docPathIsCustom = True  #tm2020

            if docPathIsCustom:
                debug("UserDir has a variable, fix:")
                placeholders    = r"\{userdocs\}|\{userdir\}"
                newDocPath      = re.sub(placeholders, PATH_DOCUMENTS, ini_value, re.IGNORECASE) #placeholder to docpath
                tmufPath        = re.sub("trackmania", "TrackMania2020", newDocPath, flags=re.IGNORECASE)

                newDocPath = fixSlash(newDocPath)
                tmufPath   = fixSlash(tmufPath)
                
                debug(f"normal: {newDocPath}")
                debug(f"tmuf:   {tmufPath}")

                if doesFolderExist(tmufPath):
                    nadeoIniSettings[ini_key] = tmufPath
                
                elif doesFolderExist(newDocPath):
                    nadeoIniSettings[ini_key] = newDocPath

                else: makeReportPopup(
                    "Document path not found", 
                    [
                         "Could not find your documents path",
                         "Is your document folder in somehting like Outlook?",
                        f"If so, please put it back in {PATH_HOME}"
                         "Path which does not exist:",
                         newDocPath
                    ]); raise FileNotFoundError

                continue

            #cache
            if ini_value.startswith("{commondata}"):
                nadeoIniSettings[ini_key] = fixSlash( ini_value.replace("{commondata}", PATH_PROGRAM_DATA) )
                continue

        return nadeoIniSettings[wantedSetting]   



def createFolderIfNecessary(path) -> None:
    """create given folder if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)



def doesFileExist(filepath) -> bool:
    return os.path.isfile(filepath)

def doesFolderExist(folderpath) -> bool:
    return os.path.isdir(folderpath)



def rNone(*funcs):
    """call all functions and return None (for property lambdas"""
    for func in funcs:
        func()
    return None


def requireValidNadeoINI(self) -> bool:
    """adds a error row label to the panel, return bool isValid"""
    VALID = isNadeoIniValid()

    if not VALID:
        layout = self.layout
        row = layout.row()
        row.alert = True
        row.label(text=MSG_ERROR_NADEO_INI)

    return VALID


def isNadeoIniValid() -> bool:
    ini = ""

    if   isGameTypeManiaPlanet():
            ini = str(bpy.context.scene.tm_props.ST_nadeoIniFile_MP)

    elif isGameTypeTrackmania2020():
            ini = str(bpy.context.scene.tm_props.ST_nadeoIniFile_TM)
    
    return doesFileExist(ini) and ini.lower().endswith(".ini")



def chooseNadeoIniPathFirstMessage(row) -> object:
    return row.label(text="Select Nadeo.ini file first.", icon="ERROR")



def isNadeoImporterInstalled(prop="")->None:
    filePath = fixSlash( getTrackmaniaEXEPath() + "/NadeoImporter.exe" )
    exists   = os.path.isfile(filePath)
    tm_props = bpy.context.scene.tm_props
    tm_props.CB_nadeoImporter = exists

    if prop:
        path = tm_props[ prop ]
        if path.startswith("//"):
            tm_props[ prop ] = bpy.path.abspath( path ) # convert // to C:/...

    if exists:
        nadeoImporterInstalled_True()
    else:
        nadeoImporterInstalled_False()


def nadeoImporterInstalled_True()->None:
    bpy.context.scene.tm_props.CB_nadeoImporter     = True
    bpy.context.scene.tm_props.NU_nadeoImporterDL   = 0 #%
    

def nadeoImporterInstalled_False()->None:
    bpy.context.scene.tm_props.CB_nadeoImporter = False


def gameTexturesDownloading_False()->None:
    bpy.context.scene.tm_props.CB_DL_TexturesRunning = False
    bpy.context.scene.tm_props.NU_DL_Textures        = 0

def gameTexturesDownloading_True()->None:
    bpy.context.scene.tm_props.CB_DL_TexturesRunning = True
    bpy.context.scene.tm_props.NU_DL_Textures        = 0
    bpy.context.scene.tm_props.ST_DL_TexturesErrors  = ""


def isGameTypeManiaPlanet()->bool:
    return str(bpy.context.scene.tm_props.LI_gameType).lower() == "maniaplanet"


def isGameTypeTrackmania2020()->bool:
    return str(bpy.context.scene.tm_props.LI_gameType).lower() == "trackmania2020"


def unzipNadeoImporter()->None:
    """unzips the downloaded <exe>/NadeoImporter.zip file in <exe> dir"""
    nadeoImporterZip = fixSlash( getTrackmaniaEXEPath() + "/NadeoImporter.zip" )
    with ZipFile(nadeoImporterZip, 'r') as zipFile:
        zipFile.extractall(path=getTrackmaniaEXEPath())
    isNadeoImporterInstalled()


def installNadeoImporter()->None:
    filePath = fixSlash( getTrackmaniaEXEPath() + "/NadeoImporter.zip")
    update   = "NU_nadeoImporterDL"
    error    = "ST_nadeoImporterDLError"
    cbSuccess= [unzipNadeoImporter]
    cbError  = [nadeoImporterInstalled_False]


    #! no hardcode, GET from MX server (/latest) 
    if isGameTypeManiaPlanet():
        url = WEBSPACE_NADEOIMPORTER_MP

    else:
        url = WEBSPACE_NADEOIMPORTER_TM

    tm_props = bpy.context.scene.tm_props
    tm_props.ST_nadeoImporterDLError = ""
    tm_props.NU_nadeoImporterDL = 0

    try:
        download = DownloadTMFile(url, filePath, update, error, cbSuccess, cbError)
        download.start()
        
    
    except urllib.error.HTTPError as e: #http error (400,404,500 etc)
        tm_props.NU_nadeoImporterDL = 0
        tm_props.ST_nadeoImporterDLError = f"{e.code} {e.msg}"
        nadeoImporterInstalled_False()

    except urllib.error.URLError as e: #domain does not exist..
        tm_props.NU_nadeoImporterDL = 0
        tm_props.ST_nadeoImporterDLError = "URL ERROR"
        nadeoImporterInstalled_False()



def unzipGameTextures(filepath, extractTo)->None:
    """unzip downloaded game textures zip file in /items/_BA..."""
    with ZipFile(filepath, 'r') as zipFile:
        zipFile.extractall(path=extractTo)
    reloadAllMaterialTextures()



def reloadAllMaterialTextures() -> None:
    """reload all textures which ends with .dds"""
    for tex in bpy.data.images:
        if tex.name.lower().endswith(".dds"):
            tex.reload()


def installGameTextures()->None:
    """download and install game textures from MX to /Items/..."""
    tm_props    = bpy.context.scene.tm_props
    enviPrefix  = "TM_" if isGameTypeTrackmania2020() else "MP_"
    enviRaw     = tm_props.LI_DL_TextureEnvi
    envi        = str(enviPrefix + enviRaw).lower()
    url         = ""

    if      envi == "tm_stadium":   url = WEBSPACE_TEXTURES_TM_STADIUM
    elif    envi == "mp_canyon":    url = WEBSPACE_TEXTURES_MP_CANYON
    elif    envi == "mp_lagoon":    url = WEBSPACE_TEXTURES_MP_LAGOON
    elif    envi == "mp_shootmania":url = WEBSPACE_TEXTURES_MP_STORM
    elif    envi == "mp_stadium":   url = WEBSPACE_TEXTURES_MP_STADIUM
    elif    envi == "mp_valley":    url = WEBSPACE_TEXTURES_MP_VALLEY
    
    extractTo= fixSlash( getDocPathItemsAssetsTextures() + enviRaw) #ex C:/users/documents/maniaplanet/items/_BlenderAssets/Stadium
    filePath = f"""{extractTo}/{enviRaw}.zip"""
    update   = "NU_DL_Textures"
    error    = "ST_DL_TexturesErrors"
    cbSuccess= [gameTexturesDownloading_False, [unzipGameTextures, {"filepath": filePath, "extractTo": extractTo}]]
    cbError  = [gameTexturesDownloading_False]

    createFolderIfNecessary( extractTo )
    gameTexturesDownloading_True()

    try:
        download = DownloadTMFile(url, filePath, update, error, cbSuccess, cbError)
        download.start()
        
    except (urllib.error.HTTPError, urllib.error.URLError) as e: #domain does not exist..
        gameTexturesDownloading_False()
        err = f"{e.code} {e.msg}" if type(e) == "urllib.error.URLError" else str(e)
        tm_props[error] = err
        debug("DOWNLOAD FAIL: ", url)
        debug(err)
        return

    



class DownloadTMFile(Thread):
    """download file from URL, save file at SAVEFILEPATH, 
    update context.scene.tm_props. (errorProp=float(0-100%), updateProp=str),
    cbSuccess & cbError are arrays of callbacks, if callback is an array, [0] is callback, [1] is **kwargs (unpack dict)"""
    
    def __init__(self, url, saveFilePath, updateProp: str="", errorProp: str="", cbSuccess: list=[], cbError: list=[]):
        super(DownloadTMFile, self).__init__() #need to call init from Thread, otherwise error
        self.response       = urllib.request.urlopen(url)
        self.CHUNK          = 1024*512 # 512kb
        self.saveFilePath   = saveFilePath
        self.updateProp     = updateProp
        self.errorProp      = errorProp
        self.cbSuccess      = cbSuccess
        self.cbError        = cbError

    def updateTMProp(self, percentage):
        if self.updateProp != "":
            executeStr = f"bpy.context.scene.tm_props.{self.updateProp} = {percentage}"
            executeStr = executeStr #above causes syntax error, however, a=a fixes it...
            exec(executeStr)

        if self.response.code >=400 and self.errorProp != "":
            executeStr = f"bpy.context.scene.tm_props.{self.errorProp} = str({self.response.code})"
            executeStr = executeStr #above causes syntax error, however, a=a fixes it...
            exec(executeStr)
        

    def run(self):
        if self.response.code < 400:
            with open(self.saveFilePath, "wb+") as f:
                fileSize   = int(self.response.length)
                downloaded = 0

                while True:
                    downloaded = os.stat(self.saveFilePath).st_size #get filesize on disk
                    dataParts  = self.response.read(self.CHUNK) #get part of downloaded data, empty after each read() call

                    if not dataParts:
                        self.updateTMProp(downloaded/fileSize * 100)
                        break #if downloaded data is 0, download is complete

                    f.write(dataParts) #write part to disk
                    
                    try:
                        self.updateTMProp(downloaded/fileSize * 100) #update progressbar in UI
                    except ZeroDivisionError as e:
                        pass

                for callback in self.cbSuccess:
                    if callable(callback):
                        callback()
                    else:
                        kwargs   = callback[1]
                        callback = callback[0]
                        callback(**kwargs) 
        
        else:
            self.updateTMProp(0)
            for callback in self.cbError:
                if callable(callback):
                    callback()
                else:
                    kwargs   = callback[1]
                    callback = callback[0]
                    callback(**kwargs) 



def saveBlendFile() -> bool:
    """overwrite/save opened blend file, returns bool if saving was successfull"""
    if bpy.data.is_saved:
        bpy.ops.wm.save_as_mainfile()
        return True
    return False



def createExportOriginFixer(col, createAt=None)->object:
    """creates an empty, parent all objs in the collection to it"""
    ORIGIN_OBJ = None
    
    #check if user defined a origin already
    for obj in col.all_objects:
        if obj.name.lower().startswith("origin"):
            ORIGIN_OBJ = obj
            break

    #create if none is defined
    if ORIGIN_OBJ is None:

        if not createAt:
            createAt = col.objects[0].location
            for obj in col.objects:
                if obj.type == "MESH" and obj.name.startswith("_") is False:
                    createAt = obj.location
                    break

        bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=createAt)
        ORIGIN_OBJ = bpy.context.active_object
        ORIGIN_OBJ.name = "origin_delete"

        if ORIGIN_OBJ.name not in col.all_objects:
            col.objects.link(ORIGIN_OBJ)


    # parent all objects to the origins
    for obj in col.all_objects:

        #parent all objs to _Lod0
        if  obj is not ORIGIN_OBJ:
            deselectAll()
            selectObj(obj)
            selectObj(ORIGIN_OBJ)
            setActiveObj(ORIGIN_OBJ)
            try:    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            except: pass #RuntimeError: Error: Loop in parents
        

    
    return ORIGIN_OBJ


def unparentObjsAndKeepTransform(col)->None:
    """unparent all objects and keep transform"""
    for obj in col.all_objects:
        deselectAll()
        setActiveObj(obj)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')


def parentObjsToObj(col, obj):
    origin_obj = obj
    for obj in col.all_objects:
        if obj is not origin_obj:
            deselectAll()
            selectObj(obj)
            selectObj(origin_obj)
            setActiveObj(origin_obj)
            try:    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            except: pass #RuntimeError: Error: Loop in parents


def deleteExportOriginFixer(col)->None:
    """unparent all objects of a origin object"""
    for obj in col.all_objects:
        if not obj.name.lower().startswith("origin"):
            deselectAll()
            setActiveObj(obj)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    
    deselectAll()
    for obj in col.all_objects:
        if "delete" in str(obj.name).lower():
            setActiveObj(obj)
            deleteObj(obj)
            continue




def getDocPath() -> str:
    """return absolute path of maniaplanet documents folder"""
    return getNadeoIniData(setting="UserDir")



def getDocPathItems() -> str:
    """return absolute path of ../Items/"""
    return fixSlash(getDocPath() + "/Items/")



def getDocPathWorkItems() -> str:
    """return absolute path of ../Work/Items/"""
    return fixSlash(getDocPath() + "/Work/Items/")



def getDocPathItemsAssets() -> str:
    """return absolute path of ../_BlenderAssets/"""
    return fixSlash(getDocPathItems() + "/_BlenderAssets/")


def getDocPathItemsAssetsTextures() -> str:
    """return absolute path of ../_BlenderAssets/"""
    return fixSlash(getDocPathItemsAssets() + "/Textures/")



def getNadeoImporterPath() -> str:
    """return full file path of /xx/NadeoImporter.exe"""
    return fixSlash(getTrackmaniaEXEPath() + "/NadeoImporter.exe")



def getNadeoImporterLIBPath() -> str:
    """return full file path of /xx/NadeoImporterMaterialLib.txt"""
    return fixSlash(getTrackmaniaEXEPath() + "/NadeoImporterMaterialLib.txt")



def r(v,reverse=False) -> float:
    """return math.radians, example: some_blender_object.rotation_euler=(radian, radian, radian)"""
    return math.radians(v) if reverse is False else math.degrees(v)

def rList(*rads) -> list:
    """return math.radians as list"""
    return [r(rad) for rad in rads]



def fixUvLayerNamesOfObjects(col) -> None:
    """rename/create necessary uvlayer names of an object (eg: basematerial/Uvlayer1/sdkhgkjds => BaseMaterial)"""
    objs = col.all_objects

    for obj in objs:
        deselectAll()
        selectObj(obj) 
        
        if obj.type == "MESH"\
            and not "socket"  in obj.name.lower() \
            and not "trigger" in obj.name.lower() \
            and len(obj.material_slots.keys()) > 0:
            uvs = obj.data.uv_layers
            validUvLayerNames   = [uv.lower() for uv in notDefaultUVLayerNames + defaultUVLayerNames]
            normalUVLayerNames = [uv.lower() for uv in defaultUVLayerNames]

            # create uvlayer BaseMaterial & LightMap
            if len(uvs) == 0:
                uvs.new(name="BaseMaterial", do_init=True)
                uvs.new(name="LightMap",     do_init=True)

            elif len(uvs) == 1:
                if uvs[0].name.lower().startswith("light"):
                    uvs[0].name = "LightMap"

                elif not uvs[0].name.lower().startswith( ("light", "decal") )\
                    or  uvs[0].name.lower().startswith( "base" ):
                            uvs[0].name = "BaseMaterial"
                            uvs.new(name="LightMap",     do_init=True)

            elif len(uvs) == 2:
                if uvs[1].name.lower().startswith( ("light", "lm") ):
                    uvs[1].name = "LightMap"

                elif uvs[0].name.lower().startswith( ("base", "bm") ):
                    uvs[0].name = "BaseMaterial"




def getListOfFoldersInX(folderpath: str, prefix="") -> list:
    """return (only) names of folders which are in the folder given as argument"""
    folders = []
    for folder in os.listdir(folderpath):
        if os.path.isdir(folderpath + "/" + folder):
            if prefix != "":
                if folder.startswith(prefix):
                    folders.append(folder)
            else:
                folders.append(folder)
    
    return folders



def getFilenameOfPath(filepath)->str:
    return fixSlash( filepath ).split("/")[-1]


def isCollectionExcluded(col) -> bool:
    """check if collection is disabled in outliner (UI)"""
    hir = getCollectionHierachy(colname=col.name, hierachystart=[col.name])

    vl  = bpy.context.view_layer
    excluded = False
    currentCol = ""

    #loop over viewlayer (collection->children) <-recursive until obj col[0] found
    for hircol in hir: #hierachy collection
        
        if currentCol == "": #set first collection
            currentCol = vl.layer_collection.children[hircol]
        
        else:
            currentCol = currentCol.children[hircol]
            if currentCol.name == col.name: #last collection found
                excluded = currentCol.exclude
            
    return excluded

    

def createCollection(name) -> object:
    """return created or existing collection"""
    all_cols = bpy.data.collections
    new_col  = None

    if not name in all_cols:
        new_col = bpy.data.collections.new(name)
    else:
        new_col = bpy.data.collections[name]
    
    return new_col


def linkCollection(col, parentcol) -> None:
    """link collection to parentcollection"""
    all_cols = bpy.data.collections
    try:    parentcol.children.link(col)
    except: ...#RuntimeError: Collection 'col' already in collection 'parentcol'


def createUNDOstep(override) -> None:
    """create a step which can be used in script to go back(icons etc)"""
    bpy.ops.ed.undo_push(override)

def undo() -> None:
    """do not use in a bpy.ops.execute() (ex: UI operator button)"""
    bpy.ops.ed.undo()

def joinObjects() -> None:
    bpy.ops.object.join()

def duplicateObjects(linked=False) -> None:
    bpy.ops.object.duplicate(linked=linked)


def objectmode() -> None:
    bpy.ops.object.mode_set(mode='OBJECT')

def editmode() -> None:
    bpy.ops.object.mode_set(mode='EDIT')


def deleteObj(obj) -> None:
    unsetActiveObj()
    objname = str(obj.name)
    try:
        deselectAll()  
        setActiveObj(obj)
        bpy.ops.object.delete()
        debug(f"object <{objname}> deleted")
        
    except Exception as err:
        """reference error.. ignore."""
        debug("error while delete obj", objname, err)
        


def selectObj(obj)->bool:
    """selects object, no error during view_layer=scene.view_layers[0]"""
    if obj.name in bpy.context.view_layer.objects and obj.hide_get() is False:
        obj.select_set(True)
        return True
    
    return False



def deselectAll() -> None:
    """deselects all objects in the scene, works only for visible ones"""
    for obj in bpy.context.scene.objects:
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(False)



def selectAll() -> None:
    """selects all objects in the scene, works only for visible ones"""
    for obj in bpy.context.scene.objects:
        selectObj(obj)


def selectAllGeometry() -> None:
    bpy.ops.mesh.select_all(action='SELECT')

def deselectAllGeometry() -> None:
    bpy.ops.mesh.select_all(action='DESELECT')

def cursorToSelected() -> None:
    bpy.ops.view3d.snap_cursor_to_selected()

def getCursorLocation() -> list:
    return bpy.context.scene.cursor.location

def originToCenterOfMass() -> None:
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')




def hideAll() -> None:
    """hide all objects in scene (obj.hide_viewport, obj.hide_render)"""
    allObjs = bpy.context.scene.objects
    for obj in allObjs:
        obj.hide_render     = True
        obj.hide_viewport   = True



def unhideSelected(objs: list) -> None:
    """unhide objs in list, expect [ {"name":str, "render":bool, "viewport": bool} ]"""
    allObjs = bpy.context.scene.objects
    for obj in objs:
        allObjs[obj["name"]].hide_render    = obj["render"] 
        allObjs[obj["name"]].hide_viewport  = obj["viewport"]



def setActiveObj(obj) -> None:
    """set active object"""
    if obj.name in bpy.context.view_layer.objects:
        bpy.context.view_layer.objects.active = obj
        selectObj(obj)
    


def unsetActiveObj() -> None:
    """unset active object, deselect all"""
    bpy.context.view_layer.objects.active = None
    deselectAll()


def getMasterCollection()->object:
    return bpy.context.view_layer.layer_collection


def setMasterCollectionAsActive() -> None:
    bpy.context.view_layer.active_layer_collection = getMasterCollection()


def setActiveCollection(colname: str) -> None:
    """set active scene collection by name, used by item import"""
    vl = bpy.context.view_layer
    vl_col = vl.layer_collection.children[colname]
    vl.active_layer_collection = vl_col
    

def getActiveCollection() -> object:
    return bpy.context.view_layer.active_layer_collection.collection


def selectAllObjectsInACollection(col, exclude_infixes=None) -> None:
    """select all objects in a collection, you may use deselectAll() before"""
    objs = col.all_objects
    
    deselectAll()
    if exclude_infixes:
        infixes = exclude_infixes.replace(" ", "").split(",")
        for obj in objs:
            for infix in infixes:
                # debug(infix)
                if not infix.lower() in obj.name.lower():
                    selectObj(obj)
                
                else: debug(f"""infix <{infix}> is in obj name <{obj.name}>, obj ignored for export""")
        
        return

    for obj in objs: 
        selectObj(obj)
            
          
            
def getCollectionNamesFromVisibleObjs() -> list:
    """returns list of collection names of all visible objects in the scene"""
    objs = bpy.context.scene.objects
    return [col.name for col in (obj.users_collection for obj in objs)]



def getCollectionHierachyOfObj(objname: str, hierachystart: bool=False) -> list:
    """returns list of parent collection of the given object name"""
    cols    = bpy.context.scene.objects[objname].users_collection
    colname = cols[0].name
    
    if hierachystart is True:
        hierachystart = [colname]
    else:
        hierachystart = []
        
    return getCollectionHierachy(colname=cols[0].name, objname=objname, hierachystart=hierachystart)
    
    

def getCollectionHierachy(colname: str="", objname: str="No_Name", hierachystart: list=[]) -> list:
    """returns list of parent collection names from given collection name,"""
    hierachy = hierachystart
    sceneCols = bpy.data.collections
    
    def scanHierachy(colname):
        for currentCol in sceneCols:
            for childCol in currentCol.children:
                if childCol.name == colname:
                    hierachy.append(currentCol.name)
                    scanHierachy(colname=currentCol.name)
    
    scanHierachy(colname=colname)
    hierachy.reverse()
    # debug(f"hierachy is {hierachy}")
    return hierachy


def createCollectionHierachy(hierachy: list) -> object:
    """create collections hierachy from list and link root to the scene master collection"""
    cols        = bpy.data.collections
    currentCol  = bpy.context.scene.collection

    for colname in hierachy:
        newcol = cols.new(colname) if colname not in cols.keys() else cols[colname]
        if newcol.name not in currentCol.children:
            try:    currentCol.children.link(newcol)
            except: ...
        currentCol = newcol
    
    return cols[hierachy[-1]]


def checkMatValidity(matname: str) -> str("missing prop as str or True"):
    """check material for properties, retrurn True if all props are set, else return False"""
    mat = bpy.data.materials[matname]
    matprops = mat.keys()

    if "BaseTexture"  not in matprops: return False #"BaseTexture"  
    if "PhysicsId"    not in matprops: return False #"PhysicsId" 
    if "Model"        not in matprops: return False #"Model" 
    if "IsNadeoMat"   not in matprops: return False #"IsNadeoMat" 
    return True


def clearProperty(prop, value):
    bpy.context.scene.tm_props[prop] = value




def nadeoLibParser(refresh=False) -> dict:
    """read NadeoImporterMaterialLib.txt set global variable and return list of all materials as dict"""
    global nadeoLibMaterials #create global variable to read and parse liffile only once
    
    if nadeoLibMaterials != {} and not refresh:
        return nadeoLibMaterials
    
    nadeolibfile = getNadeoImporterLIBPath()
    
    lib = {}
    currentLib = ""
    currentMat = ""
    regex_DLibrary      = r"DLibrary\t*\((\w+)\)"           # group 1
    regex_DMaterial     = r"DMaterial\t*\((\w+)\)"          # group 1
    regex_DSurfaceId    = r"DSurfaceId(\t*|\s*)\((\w+)\)"   # group 2
    regex_DTexture      = r"DTexture(\t*|\s*)\((\t*|\s*)([0-9a-zA-Z_\.]+)\)"   # group 3
    
    if not doesFileExist(nadeolibfile):
        return nadeoLibMaterials

    with open(nadeolibfile, "r") as f:
        for line in f:
            
            if "DLibrary" in line:
                currentLib = re.search(regex_DLibrary, line).group(1) #libname (stadium, canyon, ...)
            
            if currentLib not in lib:
                lib[currentLib] = {} #first loop
                
            if "DMaterial" in line:
                currentMat = re.search(regex_DMaterial, line).group(1) #matname
                lib[currentLib][currentMat] = {
                        "MatName":currentMat,
                        "PhysicsId":"Concrete" #changed below, fallback if not
                    }
                    
            if "DSurfaceId" in line:
                currentPhy = re.search(regex_DSurfaceId, line).group(2) #pyhsicid
                lib[currentLib][currentMat]["PhysicsId"] = currentPhy
                
            if "DTexture" in line:
                mat      = lib[currentLib][currentMat]
                nadeoTex = re.search(regex_DTexture, line)
                nadeoTex = "" if nadeoTex is None else nadeoTex.group(3) #texture
                mat["NadeoTexD"] = "" if "NadeoTexD" not in mat.keys() else mat["NadeoTexD"]
                mat["NadeoTexS"] = "" if "NadeoTexS" not in mat.keys() else mat["NadeoTexS"]
                mat["NadeoTexN"] = "" if "NadeoTexN" not in mat.keys() else mat["NadeoTexN"]
                mat["NadeoTexI"] = "" if "NadeoTexI" not in mat.keys() else mat["NadeoTexI"]
                
                if mat["NadeoTexD"] == "":  mat["NadeoTexD"] = nadeoTex if nadeoTex.lower().endswith("d.dds")  else ""  
                if mat["NadeoTexS"] == "":  mat["NadeoTexS"] = nadeoTex if nadeoTex.lower().endswith("s.dds")  else ""  
                if mat["NadeoTexN"] == "":  mat["NadeoTexN"] = nadeoTex if nadeoTex.lower().endswith("n.dds")  else ""  
                if mat["NadeoTexI"] == "":  mat["NadeoTexI"] = nadeoTex if nadeoTex.lower().endswith("i.dds")  else ""  
            
            if currentLib != "":
                if currentMat !="":
                    if currentMat in lib[currentLib].keys():
                        lib[currentLib][currentMat]["Model"] = "TDSN" #can't read model from lib
                        lib[currentLib][currentMat]["Envi"]  = currentLib 
                    

    
    nadeoLibMaterials = lib
    return nadeoLibMaterials
    
    
    
def fixName(name: str) -> str:
    """return modified name\n
    replace chars which are not allowed with _ or #, fix ligatures: ä, ü, ö, ß, é. \n  
    allowed chars: abcdefghijklmnopqrstuvwxyz0123456789_-#"""

    allowedNameChars = list("abcdefghijklmnopqrstuvwxyz0123456789_-#")
    fixedName = str(name)
    
    for char in name:
        charOriginal = str(char)
        char = str(char).lower()
        if char not in allowedNameChars:
            fixedChar = "_"
            if    char == "ä": fixedChar = "ae"
            elif  char == "ö": fixedChar = "oe"
            elif  char == "ü": fixedChar = "ue"
            elif  char == "é": fixedChar = "e"
            elif  char == "ß": fixedChar = "ss"
            fixedName = fixedName.replace(charOriginal, fixedChar)
            
    return fixedName



def fixAllMatNames() -> None:
    """fixes not allowed chars for every material's name"""
    mats = bpy.data.materials
    for mat in mats:
        mat.name = fixName(name=mat.name)



def fixSlash(filepath) -> str:
    filepath = re.sub(r"\\+", "/", filepath)
    filepath = re.sub(r"\/+", "/", filepath)
    return filepath



def fixAllColNames() -> None:
    """fixes name for every collection in blender"""
    cols = bpy.data.collections
    for col in cols:
        try:    col.name = fixName(col.name)
        except: pass #mastercollection etc is readonly
    


def rgbToHEX(rgbList, hashtag: str="") -> str:
    """convert given rgbList=(0.0, 0.5, 0.93) to hexcode """
    r = int( rgbList[0] * 256) - 1 
    g = int( rgbList[1] * 256) - 1 
    b = int( rgbList[2] * 256) - 1 
    
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))

    hex = f"{hashtag}{r:02x}{g:02x}{b:02x}"
    return hex



def refreshPanels() -> None:
    """refresh panel in ui, they are not updating sometimes"""
    for region in bpy.context.area.regions:
        if region.type == "UI":
            region.tag_redraw()  


def getAbspath(path):
    return os.path.abspath(path) if path else ""


def roundInterval(num: float, interval: int) -> int:
    """round num to interval"""
    num = num + 1
    half   = interval / 2
    goesIn = max(num // interval, 1) #num 31=1, 33=1, 64=2
    
    intVal = interval * goesIn
    remains= intVal - num
    
    #make sure that atleast half interval space is left
    #num=1, interval=32 means return 32, num=17or31.999 means 64
    if remains <= half:
        return intVal
    
    return intVal - interval



def onlyMeshObjsOfCollection(col) -> list:
    return [obj for obj in col.all_objects if obj.type == "MESH"]


def getDimensionOfCollection(col: bpy.types.Collection)->list:
    """return dimension(x,y,z) of all mesh obj combined in collection"""
    deselectAll()
    selectAllObjectsInACollection(col=col)

    minx = 0
    miny = 0
    minz = 0
    
    maxx = 0
    maxy = 0
    maxz = 0

    c1=0
    
    for obj in bpy.context.selected_objects:
    
        if obj.type != "MESH":
            continue
    
        bounds = getobjectBounds(obj)
    
        oxmin = bounds[0][0]
        oxmax = bounds[1][0]

        oymin = bounds[0][1]
        oymax = bounds[1][1]
    
        ozmin = bounds[0][2]
        ozmax = bounds[1][2]

        if  c1 == 0:
            minx = oxmin
            miny = oymin
            minz = ozmin

            maxx = oxmax
            maxy = oymax
            maxz = ozmax

        #min
        if oxmin <= minx:   minx = oxmin
        if oymin <= miny:   miny = oymin
        if ozmin <= minz:   minz = ozmin

        #max
        if oxmax >= maxx:   maxx = oxmax
        if oymax >= maxy:   maxy = oymax
        if ozmax >= maxz:   maxz = ozmax

        c1+=1
    
    
    x = maxx - minx
    y = maxy - miny
    z = maxz - minz
    
    
    return (x, y, z)


def getobjectBounds(ob):
	
		obminx = ob.location.x
		obminy = ob.location.y
		obminz = ob.location.z
	
		obmaxx = ob.location.x
		obmaxy = ob.location.y
		obmaxz = ob.location.z
	
		for vertex in ob.bound_box[:]:
	
			x = ob.location.x + (ob.scale.x * vertex[0])
			y = ob.location.y + (ob.scale.y * vertex[1])
			z = ob.location.z + (ob.scale.z * vertex[2])
	
			if x <= obminx:
				obminx = x
			if y <= obminy:
				obminy = y
			if z <= obminz:
				obminz = z
	
			if x >= obmaxx:
				obmaxx = x
			if y >= obmaxy:
				obmaxy = y
			if z >= obmaxz:
				obmaxz = z
	
		boundsmin = [obminx,obminy,obminz]
		boundsmax = [obmaxx,obmaxy,obmaxz] 

		return [boundsmin,boundsmax]



def getFilesOfFolder(path, ext=None, recursive=False)->list:
    """return list of abspath files, can be nested, filtered by ext"""
    filepaths = []

    if recursive is False:
        items = os.listdir(path)
        for item in items:
            file = os.path.join(path, item)
            if os.path.isfile(file):
                if ext:
                    if file.lower().endswith(ext):
                        filepaths.append(file)
                    continue
                filepaths.append(file)

    else:
        for root, dirs, files in os.walk(path):
            for file in files:
                file = os.path.join(root, file)
                if ext: 
                    if file.lower().endswith(ext):
                        filepaths.append(file)
                    continue
                filepaths.append(file)

    return filepaths



def fileNameOfPath(path: str) -> str:
    """return <tex.dds> of C:/someFolder/anotherOne/tex.dds, path can contain \\ and /"""
    return fixSlash(filepath=path).split("/")[-1]



def getIconPathOfFBXpath(filepath) -> str:
    icon_path = getFilenameOfPath(filepath)
    icon_path = filepath.replace(icon_path, f"/Icon/{icon_path}")
    icon_path = re.sub("fbx", "tga", icon_path, re.IGNORECASE)
    return fixSlash(icon_path)



def getWaypointTypeOfFBXfile(filepath) -> str:
    filepath        = re.sub(r"fbx$", "Item.xml", filepath, re.IGNORECASE)
    waypoint_regex  = r"waypoint\s?type=\"(\w+)\""
    waypoint        = searchStringInFile(filepath, waypoint_regex, 1)
    return waypoint


def searchStringInFile(filepath, regex, group) -> list:
    try:
        with open(filepath, "r") as f:
            data  = f.read()
            result= re.search(regex, data, re.IGNORECASE)
            return result[group] if result is not None else None

    except (FileNotFoundError, IndexError):
        return None


debug_list = ""
def debug(*args, pp=False, add_to_list=False, save_list_to=None, clear_list=False, open_file=False) -> None:
    """better printer, adds line and filename as prefix"""
    global debug_list
    frameinfo = getframeinfo(currentframe().f_back)
    line = str(frameinfo.lineno)
    name = str(frameinfo.filename).split("\\")[-1]
    time = datetime.now().strftime("%H:%M:%S")
    
    line = line if int(line) > 10       else line + " " 
    line = line if int(line) > 100      else line + " " 
    line = line if int(line) > 1000     else line + " " 
    line = line if int(line) > 10000    else line + " " 
    # line = line if int(line) > 100000   else line + " " 

    base = f"{line}, {time}, {name}"
    baseLen = len(base)
    dashesToAdd = 40 - baseLen

    #make sure base is 40 chars long, better reading between different files
    if dashesToAdd > 0 :
        base += "-" * dashesToAdd
    
    print(base, end="")
    if add_to_list:
        debug_list += base

    if pp is True:
        for arg in args:
            pprint.pprint(arg)
            if add_to_list:
                debug_list += pprint.pformat(arg)
    else:
        for arg in args:
            
            text = " " + str(arg) 
            print(text, end="")
            if add_to_list:
                debug_list += text
    
    print()
    if add_to_list:
        debug_list += "\n"

    if save_list_to is not None:
        with open(save_list_to, "w") as f:
            f.write(debug_list)
        if open_file:
            p = subprocess.Popen(f"notepad {save_list_to}")

    if clear_list:
        debug_list = ""


def debugALL() -> None:
    """print all global and addon specific bpy variable values"""
    def separator(num):
        for _ in range(0, num): full_debug("--------")
    
    def full_debug(*args, **kwargs)->None:
        debug(*args, **kwargs, add_to_list=True)



    separator(5)
    full_debug("BEGIN FULL DEBUG")
    separator(2)

    full_debug("desktopPath:             ", PATH_DESKTOP)
    full_debug("documentsPath:           ", PATH_DOCUMENTS)
    full_debug("programDataPath:         ", PATH_PROGRAM_DATA)
    full_debug("programFilesPath:        ", PATH_PROGRAM_FILES)
    full_debug("programFilesX86Path:     ", PATH_PROGRAM_FILES_X86)
    full_debug("website_convertreport:   ", PATH_CONVERT_REPORT)
    separator(1)

    full_debug("tm_props:")
    tm_props        = bpy.context.scene.tm_props
    tm_prop_prefixes= ("li_", "cb_", "nu_", "st_") 
    tm_prop_names   = [name for name in dir(tm_props) if name.lower().startswith(tm_prop_prefixes)]
    max_chars       = 0

    for name in tm_prop_names:
        prop_len = len(name)
        if prop_len > max_chars: max_chars = prop_len

    for name in tm_prop_names:
        spaces   = " " * (max_chars - len(name))
        tm_prop  = tm_props.get(name)
        tm_prop_r= None

        if tm_prop is None: 
            # tm_props.property_unset(name)
            tm_prop  = tm_props.bl_rna.properties[ name ].default
        

        
        if name.lower().startswith("nu_"):
            if isinstance(tm_prop, float):
                tm_prop_r = r(tm_prop, reverse=True)
            if isinstance(tm_prop, bpy.types.bpy_prop_array):
                tm_prop = tuple(tm_prop)
        

        full_debug(f"{name}:{spaces}{tm_prop}")
        if tm_prop_r:
            full_debug(f"{name}:{spaces}{tm_prop_r} (radians => normal)")
        



    separator(5)
    full_debug("nadeoIniSettings:        ")
    full_debug(nadeoIniSettings, pp=True)

    separator(1)
    full_debug("nadeoLibMaterials:       ")
    full_debug(nadeoLibMaterials, pp=True)

    separator(3)
    full_debug("END DEBUG PRINT")
    separator(1)
    

    debug_file = PATH_DESKTOP + "/blender_debug_report.txt"
    debug(save_list_to=debug_file, clear_list=True, open_file=True)
    
    makeReportPopup(
            "Debug print finished", 
            [
                "For debugging..."
                "All addon related python variables have been written to:",
                "the console, and",
                debug_file,
            ])
    



#icons ...  
preview_collections = {}

iconsDir = os.path.join(os.path.dirname(__file__), "icons")
pcoll = bpy.utils.previews.new()

def getIcon(icon: str) -> object:
    """return icon for layout (row, col) parameter: 
        icon_value=getIcon('CAM_FRONT') / icon='ERROR'"""
    if icon not in pcoll.keys():
        pcoll.load(icon, os.path.join(iconsDir, icon + ".png"), "IMAGE")
    return pcoll[icon].icon_id
           



                
                
def generateUID() -> str:
    """generate unique id and return as string"""               
    return str(uuid.uuid4())



def redrawPanel(self, context):
    try:    context.area.tag_redraw()
    except  AttributeError: pass #works fine but spams console full of errors... yes



def newThread(func):
    """decorator, runs func in new thread, is its not blocking"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@newThread
def makeWindowsReportPopup(title: str, infos: list)->None:
    MessageBox = ctypes.windll.user32.MessageBoxW
    text = "\n".join(infos)
    MessageBox(None, text, title, 0)
    ##  Styles:
    ##  0 : OK
    ##  1 : OK | Cancel
    ##  2 : Abort | Retry | Ignore
    ##  3 : Yes | No | Cancel
    ##  4 : Yes | No
    ##  5 : Retry | No 
    ##  6 : Cancel | Try Again | Continue


def makeReportPopup(title= str("some error occured"), infos: list=[], icon: str='INFO', fileName: str="maniaplanet_report"):
    """create a small info(text) popup in blender, write infos to a file on desktop"""
    frameinfo   = getframeinfo(currentframe().f_back)
    line        = str(frameinfo.lineno)
    name        = str(frameinfo.filename).split("\\")[-1]
    pyinfos     = f"\n\nLINE: {line}\nFILE: {name}"

    def draw(self, context):
        # self.layout.label(text=f"This report is saved at: {desktopPath} as {fileName}.txt", icon="FILE_TEXT")
        for info in infos:
            self.layout.label(text=str(info))
        
              
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    
    # with open(desktopPath + fileName + ".txt", "w", encoding="utf-8") as reportFile:
    #     reportFile.write(title + "\n\n")
    #     for info in infos:
    #         reportFile.write(info + "\n")
    #     reportFile.write(pyinfos)



def stealUserLoginData() -> str:
    with open(getDocPath() + "/Config/User.Profile.Gbx", r) as f:
        data = f.read()
        if "username" and "password" in data:
            return "i probably should stop here...:)"