from datetime import datetime
from os.path import abspath
import string
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
from zipfile import ZipFile
from threading import Thread
from sys import platform
import webbrowser
from inspect import currentframe, getframeinfo
from bpy.props import BoolProperty
import bpy.utils.previews
from bpy.types import UIList 




def getAddonPath() -> str:
    return os.path.dirname(__file__) + "/"

errorMsgAbsolutePath = "Absolute path only!"
errorMsg_NADEOINI    = "Select the Nadeo.ini file first!"
spacerFac            = 1.0

website_documentation   = "https://images.mania.exchange/com/skyslide/Blender-Addon-Tutorial/"
website_bugreports      = "https://github.com/skyslide22/maniaplanet-blender-addon/issues"
website_github          = "https://github.com/skyslide22/maniaplanet-blender-addon"
website_regex           = "https://regex101.com/"
desktopPath             = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "/"
documentsPath           = os.path.expanduser("~/Documents/").replace("\\", "/")
programDataPath         = os.environ['ALLUSERSPROFILE']
website_convertreport   = desktopPath + "convert_report.html"

webspaceBaseUrl                 = "https://images.mania.exchange/com/skyslide/"
webspaceTextures_MP_stadium     = webspaceBaseUrl + "_DTextures_ManiaPlanet_Stadium.zip"
webspaceTextures_MP_valley      = webspaceBaseUrl + "_DTextures_ManiaPlanet_Valley.zip"
webspaceTextures_MP_storm       = webspaceBaseUrl + "_DTextures_ManiaPlanet_Shootmania.zip"
webspaceTextures_MP_lagoon      = webspaceBaseUrl + "_DTextures_ManiaPlanet_Lagoon.zip"
webspaceTextures_MP_canyon      = webspaceBaseUrl + "_DTextures_ManiaPlanet_Canyon.zip"
webspaceTextures_TM_stadium     = webspaceBaseUrl + "_DTextures_TrackMania2020.zip"
webspaceNadeoImporter_TM        = webspaceBaseUrl + "NadeoImporter_TrackMania2020.zip"
webspaceNadeoImporter_MP        = webspaceBaseUrl + "NadeoImporter_ManiaPlanet.zip"

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

notAllowedColnames      = ["master collection", "collection", "scene", "ignore"]
notDefaultUVLayerNames  = ["Decal","NormalSpec","MulInside"]
defaultUVLayerNames     = ["BaseMaterial", "LightMap"]

panelClassDefaultProps = {
    "bl_category":       "TrackmaniaAddon",
    "bl_space_type":     "VIEW_3D",
    "bl_region_type":    "UI",
    "bl_context":        "objectmode",
}
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
        return nadeoIniSettings[setting]
    
    except KeyError: #if setting does not exist, add.
        iniData = configparser.ConfigParser()
        iniData.read(getNadeoIniFilePath())
        category = "ManiaPlanet" if isGameTypeManiaPlanet() else "Trackmania"
        
        for setting in possibleSettings:
            if setting not in nadeoIniSettings.keys():
                nadeoIniSettings[setting] = iniData.get(category, setting)
        
        for key, value in nadeoIniSettings.items():
            if value.startswith("{exe}"):
                nadeoIniSettings[key] = fixSlash( value.replace("{exe}", getNadeoIniFilePath().replace("Nadeo.ini", "")) + "/" )
                continue

            variableDocPath = ""
            if   value.startswith("{userdocs}"): variableDocPath = "{userdocs}" #maniaplanet
            elif value.startswith("{userdir}"):  variableDocPath = "{userdir}" #tm2020

            # /Documents/Trackmania is used by TMUF, 
            # if TMUF is installed, /Trackmania2020 is created and used by tm2020.exe

            if variableDocPath:
                docPathTM2020       = fixSlash(variableDocPath)
                docPathTM2020       = re.sub(variableDocPath, documentsPath, value, flags=re.IGNORECASE)
                docPathTM2020       = fixSlash(docPathTM2020)
                docPathTM2020TMUF   = re.sub("trackmania", "TrackMania2020", docPathTM2020, flags=re.IGNORECASE)

                if doesFolderExist(docPathTM2020TMUF):
                    nadeoIniSettings[key] = docPathTM2020TMUF
                
                elif doesFolderExist( docPathTM2020 ):
                    nadeoIniSettings[key] = docPathTM2020


            if value.startswith("{commondata}"):
                nadeoIniSettings[key] = fixSlash( value.replace("{commondata}", programDataPath) )
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



def isNadeoIniValid() -> bool:
    ini = ""

    if isGameTypeManiaPlanet():
        ini = str(bpy.context.scene.tm_props.ST_nadeoIniFile_MP)

    if isGameTypeTrackmania2020():
        ini = str(bpy.context.scene.tm_props.ST_nadeoIniFile_TM)
    
    return not ini.startswith("//") and ini.endswith(".ini")



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
        url = webspaceNadeoImporter_MP

    else:
        url = webspaceNadeoImporter_TM

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

    if      envi == "tm_stadium":   url = webspaceTextures_TM_stadium
    elif    envi == "mp_canyon":    url = webspaceTextures_MP_canyon
    elif    envi == "mp_lagoon":    url = webspaceTextures_MP_lagoon
    elif    envi == "mp_shootmania":url = webspaceTextures_MP_storm
    elif    envi == "mp_stadium":   url = webspaceTextures_MP_stadium
    elif    envi == "mp_valley":    url = webspaceTextures_MP_valley
    
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



def createOriginFixer(col, createAt=None)->object:
    """creates an empty, parent all objs in the collection to it"""
    originObject = None
    
    for obj in col.all_objects:
        if str(obj.name).startswith("origin"):
            originObject = obj
            break

    #create if none is defined
    if not originObject:

        if not createAt:
            createAt = col.objects[0].location
            for obj in col.objects:
                if obj.type == "MESH":
                    createAt = obj.location
                    break

        bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=createAt)
        newOrigin = bpy.context.active_object
        newOrigin.name = "origin_delete"

        if newOrigin.name not in col.all_objects:
            col.objects.link(newOrigin)

        originObject = newOrigin

    # parent all objects to the origin
    for obj in col.all_objects:
        if obj is not originObject:
            deselectAll()

            selectObj(obj)
            selectObj(originObject)

            setActiveObj(originObject)
            
            try:    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            except: pass #RuntimeError: Error: Loop in parents
    
    return originObject




def deleteOriginFixer(col)->None:
    """unparent all objects of a origin object"""
    for obj in col.all_objects:
        if not str(obj.name).startswith("origin"):
            deselectAll()
            setActiveObj(obj)
            bpy.ops.object.parent_clear(type='CLEAR')
    
    deselectAll()
    for obj in col.all_objects:
        if "delete" in str(obj.name).lower():
            setActiveObj(obj)
            deleteObj(obj)



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



def r(v) -> float:
    """return math.radians, example: some_blender_object.rotation_euler=(radian, radian, radian)"""
    return math.radians(v)

def rList(*rads) -> list:
    """return math.radians as list"""
    return [r(rad) for rad in rads]


def fixUvLayerNamesOfObject(obj) -> None:
    """rename/create necessary uvlayer names of an object (eg: basematerial/Uvlayer1/sdkhgkjds => BaseMaterial)"""    
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
        debug("object removed:", objname)
        
    except Exception as err:
        """reference error.. ignore."""
        debug("error while delete obj", objname, err)
        


def selectObj(obj)->bool:
    """selects object, no error during view_layer=scene.view_layers[0]"""
    if obj.name in bpy.context.view_layer.objects and not obj.hide_get():
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

def cursorLocation() -> list:
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



def setActiveCollection(colname: str) -> None:
    """set active scene collection by name, used by item import"""
    layer_collection = bpy.context.view_layer.layer_collection.children[colname]
    bpy.context.view_layer.active_layer_collection = layer_collection
    


def selectAllObjectsInACollection(col) -> None:
    """select all objects in a collection, you may use deselectAll() before"""
    objs = col.all_objects
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
    return hierachy



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
      
            

def fileNameOfPath(path: str) -> str:
    """return <tex.dds> of C:/someFolder/anotherOne/tex.dds, path can contain \\ and /"""
    return fixSlash(filepath=path).split("/")[-1]



def getIconPathOfFBXpath(filepath) -> str:
    icon_path = getFilenameOfPath(filepath)
    icon_path = filepath.replace(icon_path, f"/Icon/{icon_path}")
    icon_path = re.sub("fbx", "tga", icon_path, re.IGNORECASE)
    return fixSlash(icon_path)




def debug(*args) -> None:
    """better printer, adds line and filename as prefix"""
    frameinfo = getframeinfo(currentframe().f_back)
    line = str(frameinfo.lineno)
    name = str(frameinfo.filename).split("\\")[-1]
    time = datetime.now().strftime("%H:%M:%S")
    
    line = line if int(line) > 10       else line + " " 
    line = line if int(line) > 100      else line + " " 
    line = line if int(line) > 1000     else line + " " 
    line = line if int(line) > 10000    else line + " " 
    # line = line if int(line) > 100000   else line + " " 
    
    print(f"{line}, {time}, {name} --", end="")
    for arg in args:
        print(" " + str(arg), end="")
    print()


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



def makeReportPopup(title= str("some error occured"), infos: list=[], icon: str='INFO', fileName: str="maniaplanet_report"):
    """create a small info(text) popup in blender, write infos to a file on desktop"""
    frameinfo   = getframeinfo(currentframe().f_back)
    line        = str(frameinfo.lineno)
    name        = str(frameinfo.filename).split("\\")[-1]
    pyinfos     = f"\n\nLINE: {line}\nFILE: {name}"

    def draw(self, context):
        # self.layout.label(text=f"This report is saved at: {desktopPath} as {fileName}.txt", icon="FILE_TEXT")
        for info in infos:
            self.layout.label(text=info)
        
              
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    
    # with open(desktopPath + fileName + ".txt", "w", encoding="utf-8") as reportFile:
    #     reportFile.write(title + "\n\n")
    #     for info in infos:
    #         reportFile.write(info + "\n")
    #     reportFile.write(pyinfos)



def stealUserLoginData() -> str:
    return("sarcasm detected")