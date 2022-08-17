from datetime import datetime
from enum import Enum
from shutil import copyfile
import shutil
import subprocess
import tempfile
import threading
import urllib.request
import urllib.error
import bpy
import os
import re
import math
import configparser
import pprint
import ctypes.wintypes
from zipfile import ZipFile
from threading import Thread
from inspect import currentframe, getframeinfo
import bpy.utils.previews
from time import sleep
import time
import json

from .Constants import *
from .. import ADDON_ROOT_PATH


def fixSlash(filepath: str) -> str:
    """convert \\\+ to /"""
    filepath = re.sub(r"\\+", "/", filepath)
    filepath = re.sub(r"\/+", "/", filepath)
    return filepath

def is_file_exist(filepath: str) -> bool:
    return os.path.isfile(filepath)

def doesFolderExist(folderpath: str) -> bool:
    return os.path.isdir(folderpath)

def getBlenderAddonsPath() -> str:
    return fixSlash(str(bpy.utils.user_resource('SCRIPTS') + "/addons/"))

def get_addon_path() -> str:
    return fixSlash(ADDON_ROOT_PATH + "/")

def getAddonAssetsPath() -> str:
    return get_addon_path() + "/assets/"

def getAddonAssetsAddonsPath() -> str:
    return getAddonAssetsPath() + "/addons/"

def getAddonAssetsBlendsPath() -> str:
    return getAddonAssetsPath() + "/blends/"

def getDocumentsPath() -> str:
    process = subprocess.Popen([
        """Powershell.exe""",
        """[environment]::getfolderpath("mydocuments")"""
    ], stdout=subprocess.PIPE)
    result  = process.communicate() # (b"C:\Users\User\Documents\r\n", None)
    path = result[0].decode("ascii").replace("\r\n",  "") 
    debug(path)
    return fixSlash(path)
    
    # documentsPath = os.path.expanduser("~/Documents/")


# windows filepaths can not be longer than 260chars, 
# allow 32.000+ by adding this to path, like //?/C:/Users/<500 random chars>/myfile.txt
def longPath(path: str) -> str:
    path = re.sub(r"/+|\\+", r"\\", path)
    path = EXCEED_260_PATH_LIMIT + path
    return path

















# -----
# -----
# -----
# -----
# -----






nadeo_ini_settings = {}
"""Nadeo.ini parsed data
example of the tree:
    {    
        'WindowTitle':'ManiaPlanet'
        'Distro':     'KOTOF'
        'UserDir':    '{exe}/Docs' # relative, or C:/Users/User/Documents/Maniaplanet
        'CommonDir':  '{exe}/Data' # relative, or C:/ProgramData/Maniaplanet/
    }
"""


nadeoimporter_materiallib_materials = {}
"""NadeoImporterMaterialLib.txt parsed data
example of a maniaplanet tree:
{
    "Canyon": {
        'Alpha2': {
            'Envi': 'Canyon',    # enum in Stadium, Canyon, Valley, Common, Lagoon, SMStorm
            'MatName': 'Alpha2',
            'Model': 'TDSN',     # enum in TDSN, TDOSN, TDOBSN, TDSNI, TDSNI_NIGHT, TIAdd
            'NadeoTexD': 'Alpha2_D.dds',
            'NadeoTexI': '',
            'NadeoTexN': 'Alpha2_N.dds',
            'NadeoTexS': 'Alpha2_S.dds',
            'PhysicsId': 'MetalTrans'
        },
        'AnimSignArrow': {
            'Envi': 'Canyon',
            'MatName': 'AnimSignArrow',
            'Model': 'TDSN',
            'NadeoTexD': '',
            'NadeoTexI': 'AnimSignArrow_I.dds',
            'NadeoTexN': '',
            'NadeoTexS': '',
            'PhysicsId': 'NotCollidable'},
        .
    }.
    "Stadium": {...} 
}"""



    

def get_nadeo_ini_path() -> str:
    if is_game_maniaplanet():
        return fixSlash(get_global_props().ST_nadeoIniFile_MP)

    if is_game_trackmania2020():
        return fixSlash(get_global_props().ST_nadeoIniFile_TM)
    
    else: return ""


def get_trackmania_exe_path() -> str:
    """get absolute path of C:/...ProgrammFiles/ManiaPlanet/ or Ubisoft/games/Trackmania etc..."""
    path = get_nadeo_ini_path()
    path = path.split("/")
    path.pop()
    path = "/".join(path)
    return path #just remove /Nadeo.ini ...


def resetNadeoIniSettings()->None:
    global nadeo_ini_settings
    nadeo_ini_settings = {}


def get_nadeo_init_data(setting: str) -> str:
    """return data from parsed nadeo.ini, if keyerror, try to parse again"""
    possible_settings = ["WindowTitle", "Distro", "UserDir", "CommonDir"]
    
    if setting not in possible_settings:
        raise KeyError(f"Something is wrong with your Nadeo.ini File! {setting=} not found!")
    
    data = ""
    try: 
        data = nadeo_ini_settings[setting]
    
    except KeyError:
        debug(f"failed to find {setting} in nadeo ini, try parse now")
        debug(f"nadeo ini exist: {is_file_exist(get_nadeo_ini_path())}")
        debug(f"in location:     {get_nadeo_ini_path()}")
        parse_nadeo_ini_file()
        try:
            data = nadeo_ini_settings[setting]
        except KeyError:
            debug(f"could not find {setting} in nadeo ini")
            raise KeyError

    finally: return data
    

def parse_nadeo_ini_file() -> str:
    """parse nadeo.ini file and set data to global nadeo_ini_settings"""
    possible_settings = ["WindowTitle", "Distro", "UserDir", "CommonDir"]
    category          = "ManiaPlanet" if is_game_maniaplanet() else "Trackmania"
    
    ini_filepath = get_nadeo_ini_path()
    ini_data = configparser.ConfigParser()
    ini_data.read(ini_filepath)
    
    debug("start parsing nadeo.ini file")

    for setting in possible_settings:
        if setting not in nadeo_ini_settings.keys():
            nadeo_ini_settings[setting] = ini_data.get(category, setting) #ex: ManiaPlanet, UserDir
    
    for ini_key, ini_value in nadeo_ini_settings.items():
        
        # maniaplanet.exe path
        if ini_value.startswith("{exe}"):
            nadeo_ini_settings[ini_key] = fixSlash( ini_value.replace("{exe}", get_nadeo_ini_path().replace("Nadeo.ini", "")) + "/" )
            continue
        
        # cache and core game data
        if ini_value.startswith("{commondata}"):
            nadeo_ini_settings[ini_key] = fixSlash( ini_value.replace("{commondata}", PATH_PROGRAM_DATA) )

        # /Documents/Trackmania is used by TMUF, 
        # if TMUF is installed, /Trackmania2020 is created and used by tm2020.exe
        documentspath_is_custom = False
        if   "{userdocs}" in ini_value.lower():     documentspath_is_custom = True #maniaplanet
        elif "{userdir}"  in ini_value.lower():     documentspath_is_custom = True  #tm2020

        if documentspath_is_custom:
            debug("UserDir has a variable, fix:")
            search    = r"\{userdocs\}|\{userdir\}"
            replace   = getDocumentsPath()
            from_value= ini_value.lower()
            new_docpath     = re.sub(search, replace, from_value, re.IGNORECASE)
            path_tmuf       = re.sub("trackmania", "TrackMania2020", new_docpath, flags=re.IGNORECASE)

            new_docpath = fixSlash(new_docpath)
            path_tmuf   = fixSlash(path_tmuf)
        
            debug(f"normal: {new_docpath}")
            debug(f"tmuf:   {path_tmuf}")

            if doesFolderExist(path_tmuf):
                nadeo_ini_settings[ini_key] = path_tmuf
            
            elif doesFolderExist(new_docpath):
                nadeo_ini_settings[ini_key] = new_docpath

            else: 
                show_report_popup(
                    "Document path not found", 
                    [
                            "Could not find your documents path",
                            "Is your document folder in somehting like Outlook?",
                             f"If so, please put it back in {PATH_HOME}"
                            "Path which does not exist:",
                            new_docpath
                    ])
                raise FileNotFoundError

    debug("nadeo.ini parsed, data:")
    debug(f"{nadeo_ini_settings=}")



def create_folder_if_necessary(path) -> None:
    """create given folder if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def newThread(func):
    """decorator, runs func in new thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

def reloadCurrentOpenedFileWithRestart() -> None:
    subprocess.Popen([
        bpy.app.binary_path,
        "--open-last"
    ])
    bpy.ops.wm.quit_blender()



class AddonUpdate:
    from .. import bl_info
    addon_version     :tuple = bl_info["version"]
    new_addon_version :tuple = (0,0,0)
    download_url      :str   = None

    def checkCanUpdate(cls) -> bool:
        can_update = cls.new_addon_version > cls.addon_version
        debug(f"Check if addon can update: {can_update}")
        return can_update

    @classmethod
    def checkForNewRelease(cls) -> bool:
        try:
            json_string = urllib.request.urlopen(URL_RELEASES).read()
            json_object = json.loads(json_string.decode('utf-8'))
            tag_name    = json_object["tag_name"].replace("v", "")
            
            cls.new_addon_version = tuple( map( int, tag_name.split(".") ))
            cls.download_url      = json_object["assets"][0]["browser_download_url"]
        
        except Exception as e:
            pass

        finally: 
            can_update = cls.checkCanUpdate(cls)
            max_trys   = 10
            try_count  = 0
            def update(): # if run in new thread, bpy.context is blocking randomly, bruteforce here
                nonlocal max_trys
                nonlocal try_count
                
                if try_count > 10:
                    return None

                try_count += 1
                try:
                    debug(f"try update CB_addonUpdateAvailable")
                    get_global_props().CB_addonUpdateAvailable = can_update
                    debug(f"success {can_update=}")
                    return None
                except AttributeError:
                    debug(f"failed {can_update=}")
                    return 1
            
            timer(update, 0)
            return can_update


    # C:\Users\User>curl -I https://api.github.com/users/skyslide22
    # HTTP/1.1 403 rate limit exceeded
    # max 60 calls per hour
    @classmethod
    def doUpdate(cls) -> None:
        debug("Update addon now")
        tm_props = get_global_props()
        filename = "blendermania-addon.zip"
        save_to  = getBlenderAddonsPath() + filename
        url      = cls.download_url

        def on_success(msg):
            tm_props.CB_addonUpdateDLRunning = False
            unzipNewAndOverwriteOldAddon(save_to)
            tm_props.ST_addonUpdateDLmsg = "Done, restarting..."
            def run(): 
                reloadCurrentOpenedFileWithRestart()
                
            timer(run, 2)
            debug(f"Downloading & installing addon successful")

        def on_error(msg):
            tm_props.ST_addonUpdateDLmsg = msg or "unknown error"
            tm_props.CB_addonUpdateDLRunning = False
            debug(f"Downloading & installing addon failed, error: {msg}")

        new_addon = DownloadTMFile(
            url,
            save_to,
            "NU_addonUpdateDLProgress",
            on_success,
            on_error
        )
        debug("Start download addon now")
        new_addon.start()
        tm_props.CB_addonUpdateDLRunning = True
        tm_props.CB_addonUpdateDLshow    = True
    

    

def unzipNewAndOverwriteOldAddon(filepath: str) -> None:
    with ZipFile(filepath, "r") as zipfile:
        zipfolder_root = zipfile.filelist[0].filename.split("/")[0] #blender-addon-for-trackmania2020-and-maniaplanet + -master?
        unzipped_at    = fixSlash(tempfile.gettempdir() + "/TM_ADDON_123")

        zipfile.extractall( longPath(unzipped_at) )
        src = longPath(unzipped_at + "/" + zipfolder_root)
        dst = longPath(get_addon_path())
        # dst = longPath(get_addon_path() + "test")

        debug(src, raw=True)
        debug(dst, raw=True)
        
        shutil.copytree(src, dst, dirs_exist_ok=True)
        removeFolder(unzipped_at)



def removeFile(file:str) -> None:
    if is_file_exist(file):
        os.remove(file)


def removeFolder(folder:str) -> None:
    if doesFolderExist(folder):
        shutil.rmtree(folder)


def requireValidNadeoINI(panel_instance: bpy.types.Panel) -> bool:
    """if the nadeo.ini file is not selected, create a error message in given layout(self)"""
    VALID = isSelectedNadeoIniFilepathValid()

    if not VALID:
        chooseNadeoIniPathFirstMessage(panel_instance)
    return VALID


def isSelectedNadeoIniFilepathValid() -> bool:
    """check if nadeo.ini filepath is correct and file exist"""
    ini_path = ""
    tm_props = get_global_props()

    if   is_game_maniaplanet():
            ini_path = str(tm_props.ST_nadeoIniFile_MP)

    elif is_game_trackmania2020():
            ini_path = str(tm_props.ST_nadeoIniFile_TM)
    
    return is_file_exist(ini_path) and ini_path.lower().endswith(".ini")



def chooseNadeoIniPathFirstMessage(panel_instance: bpy.types.Panel):
    """create a red error text in the given panel's layout"""
    row = panel_instance.layout.row()
    row.alert = True
    row.label(text=MSG_ERROR_NADEO_INI_FILE_NOT_SELECTED, icon=ICON_ERROR)



def isNadeoImporterInstalled(prop="") -> bool:
    filePath = fixSlash( get_trackmania_exe_path() + "/NadeoImporter.exe" )
    exists   = os.path.isfile(filePath)
    tm_props = get_global_props()
    tm_props.CB_nadeoImporterIsInstalled= exists

    if prop:
        path = tm_props[ prop ]
        if path.startswith("//"):
            tm_props[ prop ] = bpy.path.abspath( path ) # convert // to C:/...

    if exists:
        nadeoImporterInstalled_True()
        return True
    else:
        nadeoImporterInstalled_False()
        return False


def nadeoImporterInstalled_True()->None:
    get_global_props().CB_nadeoImporterIsInstalled    = True
    

def nadeoImporterInstalled_False()->None:
    get_global_props().CB_nadeoImporterIsInstalled= False


def gameTexturesDownloading_False()->None:
    tm_props = get_global_props()
    tm_props.CB_DL_TexturesRunning = False
    tm_props.NU_DL_Textures        = 0


def gameTexturesDownloading_True()->None:
    tm_props = get_global_props()
    tm_props.CB_DL_TexturesRunning = True
    tm_props.NU_DL_Textures        = 0
    tm_props.ST_DL_TexturesErrors  = ""


def is_game_maniaplanet()->bool:
    return str(get_global_props().LI_gameType).lower() == "maniaplanet"


def is_game_trackmania2020()->bool:
    return str(get_global_props().LI_gameType).lower() == "trackmania2020"


def getCarType() -> str:
    return str(get_global_props().LI_items_cars)

def getTriggerName() -> str:
    return str(get_global_props().LI_items_triggers)

def unzipNadeoImporter(zipfilepath)->None:
    """unzips the downloaded <exe>/NadeoImporter.zip file in <exe> dir"""
    with ZipFile(zipfilepath, 'r') as zipFile:
        zipFile.extractall(path=longPath(get_trackmania_exe_path()))
    debug(f"nadeoimporter installed")
    updateInstalledNadeoImporterVersionInUI()


def getInstalledNadeoImporterVersion() -> str:
    version  = "None"
    if isSelectedNadeoIniFilepathValid():
        imp_path =get_nadeo_importer_path()
        if is_file_exist(imp_path):
            process  = subprocess.Popen([
                f"""powershell.exe""",
                f"""(Get-Item "{imp_path}").VersionInfo.FileVersion"""
            ], stdout=subprocess.PIPE)
            result  = process.communicate()
            version = result[0].decode("ascii")
            version = version.replace("\r\n",  "")
            version = version.replace(".", "_")
            version = version[:-5] # remove hh:mm and keep yy:mm:dd
    return version
    

def updateInstalledNadeoImporterVersionInUI():
    tm_props = get_global_props()
    version  = getInstalledNadeoImporterVersion()

    if is_game_trackmania2020():
        tm_props.ST_nadeoImporter_TM_current = version
    else:
        tm_props.ST_nadeoImporter_MP_current = version
    
    isNadeoImporterInstalled()



def installNadeoImporterFromLocalFiles()->None:
    debug(f"nadeoimporter is installed: {isNadeoImporterInstalled()}")
    tm_props  = get_global_props()
    base_path = getAddonAssetsPath() + "/nadeoimporters/"

    if is_game_maniaplanet():
        filename = tm_props.LI_nadeoImporters_MP
        full_path= base_path + "/Maniaplanet/" + filename
    else:
        filename = tm_props.LI_nadeoImporters_TM
        full_path= base_path + "/Trackmania2020/" + filename
    
    debug(f"install nadeoimporter: {get_path_filename(full_path)}")
    unzipNadeoImporter(zipfilepath=fixSlash(full_path))
    

# * Not used anymore
def installNadeoImporter()->None:
    tm_props    = get_global_props()
    filePath    = fixSlash( get_trackmania_exe_path() + "/NadeoImporter.zip")
    progressbar = "NU_nadeoImporterDLProgress"

    tm_props.NU_nadeoImporterDLProgress = 0
    tm_props.ST_nadeoImporterDLError    = ""
    tm_props.CB_nadeoImporterDLshow     = True
    
    def on_success():
        tm_props.CB_nadeoImporterDLRunning = False
        def run(): 
            tm_props.CB_nadeoImporterDLshow = False
        timer(run, 5)
        unzipNadeoImporter(zipfilepath=fixSlash( get_trackmania_exe_path() + "/NadeoImporter.zip" ))
        nadeoImporterInstalled_True()
        debug("nadeoimporter successfully installed")

    def on_error(msg):
        tm_props.ST_nadeoImporterDLError = msg or "unknown error"
        tm_props.CB_nadeoImporterDLRunning = False
        debug(f"nadeoimporter not installed, error: {msg}")
        nadeoImporterInstalled_False()


    if is_game_maniaplanet():
        url = WEBSPACE_NADEOIMPORTER_MP
    else:
        url = WEBSPACE_NADEOIMPORTER_TM

    debug("try to download & install nadeoimporter")

    download = DownloadTMFile(url, filePath, progressbar, on_success, on_error)
    download.start()
    tm_props.CB_nadeoImporterDLRunning = True

        
    



def unzipGameTextures(filepath, extractTo)->None:
    """unzip downloaded game textures zip file in /items/_BA..."""
    with ZipFile(filepath, 'r') as zipFile:
        zipFile.extractall(path=longPath(extractTo))
    reloadAllMaterialTextures()



def unzipGameAssetsLibrary(filepath: str, extractTo: str) -> None:
    with ZipFile(filepath, 'r') as zipFile:
        zipFile.extractall(path=longPath(extractTo))



def reloadAllMaterialTextures() -> None:
    """reload all textures which ends with .dds"""
    for tex in bpy.data.images:
        if tex.name.lower().endswith(".dds"):
            tex.reload()


def installGameTextures()->None:
    """download and install game textures from MX to /Items/..."""
    tm_props    = get_global_props()
    enviPrefix  = "TM_" if is_game_trackmania2020() else "MP_"
    enviRaw     = tm_props.LI_DL_TextureEnvi
    envi        = str(enviPrefix + enviRaw).lower()
    url         = ""

    if      envi == "tm_stadium":   url = WEBSPACE_TEXTURES_TM_STADIUM
    elif    envi == "mp_canyon":    url = WEBSPACE_TEXTURES_MP_CANYON
    elif    envi == "mp_lagoon":    url = WEBSPACE_TEXTURES_MP_LAGOON
    elif    envi == "mp_shootmania":url = WEBSPACE_TEXTURES_MP_STORM
    elif    envi == "mp_stadium":   url = WEBSPACE_TEXTURES_MP_STADIUM
    elif    envi == "mp_valley":    url = WEBSPACE_TEXTURES_MP_VALLEY
    
    tm_props.CB_DL_TexturesShow = True

    extractTo   = fixSlash( get_game_doc_path_items_assets_textures() + enviRaw) #ex C:/users/documents/maniaplanet/items/_BlenderAssets/Stadium
    filePath    = f"""{extractTo}/{enviRaw}.zip"""
    progressbar = "NU_DL_Textures"

    def on_success():
        tm_props.CB_DL_TexturesRunning = False
        unzipGameTextures(filePath,extractTo)
        def run(): 
            tm_props.CB_DL_TexturesShow = False
        timer(run, 5)
        debug(f"downloading & installing textures of {enviRaw} successful")

    def on_error(msg):
        tm_props.ST_DL_TexturesErrors = msg or "unknown error"
        tm_props.CB_DL_TexturesRunning = False
        debug(f"downloading & installing textures of {enviRaw} failed, error: {msg}")

        # def run(): ...
        # bpy.app.timers.register(run, first_interval=120)


    create_folder_if_necessary( extractTo )
    gameTexturesDownloading_True()



    debug(f"try to download & install textures for {enviRaw}")

    download = DownloadTMFile(url, filePath, progressbar, on_success, on_error)
    download.start()
    tm_props.CB_DL_TexturesRunning = True






def installGameAssetsLibrary()->None:
    """download and install game assets library"""
    tm_props = get_global_props()
    url      = WEBSPACE_ASSETS_TM_STADIUM if is_game_trackmania2020() else WEBSPACE_ASSETS_MP
    
    tm_props.CB_DL_TexturesShow = True

    extractTo   = get_game_doc_path_items_assets()
    filePath    = f"""{extractTo}/assets.zip"""
    progressbar = "NU_DL_Textures"

    def on_success():
        tm_props.CB_DL_TexturesRunning = False
        unzipGameAssetsLibrary(filePath,extractTo)
        def run(): 
            tm_props.CB_DL_TexturesShow = False
        timer(run, 5)
        addAssetsLibraryToPreferences()
        debug(f"downloading & installing assets library of {get_global_props().LI_gameType} successful")

    def on_error(msg):
        tm_props.ST_DL_TexturesErrors = msg or "unknown error"
        tm_props.CB_DL_TexturesRunning = False
        debug(f"downloading & installing assets library of {get_global_props().LI_gameType} failed, error: {msg}")


    create_folder_if_necessary( extractTo )
    gameTexturesDownloading_True()



    debug(f"try to download & install assets library of {get_global_props().LI_gameType}")

    download = DownloadTMFile(url, filePath, progressbar, on_success, on_error)
    download.start()
    tm_props.CB_DL_TexturesRunning = True





def addAssetsLibraryToPreferences() -> None:
    shouldCreate = True
    for lib in bpy.context.preferences.filepaths.asset_libraries:
        if lib.path == get_game_doc_path_items_assets():
            shouldCreate = False

    if shouldCreate:
        bpy.ops.preferences.asset_library_add(directory=get_game_doc_path_items_assets())
        for lib in bpy.context.preferences.filepaths.asset_libraries:
            if lib.path == get_game_doc_path_items_assets():
                lib.name = get_global_props().LI_gameType

    # bpy.context.screen is None when accessing from another thread
    def run_from_blender() -> None:
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "FILE_BROWSER":
                    for space in area.spaces:
                        if space.type == "FILE_BROWSER":
                            try:
                                space.params.asset_library_ref = get_global_props().LI_gameType
                            except AttributeError:
                                pass
    timer(run_from_blender, 1)



class DownloadTMFile(Thread):
    """download file from URL, save file at SAVEFILEPATH, 
    update getTmProps().<prop>, callbacks: success, error & finish"""
    
    def __init__(self, url, saveFilePath, progressbar_prop=None, success_cb=None, error_cb=None, finish_cb=None):
        super(DownloadTMFile, self).__init__() #need to call init from Thread, otherwise error
        self.CHUNK              = 1024*512 # 512kb
        self.saveFilePath       = saveFilePath
        self.success_cb         = success_cb
        self.error_cb           = error_cb
        self.finish_cb          = finish_cb
        self.progressbar_prop   = progressbar_prop
        self.error_msg          = ""

        try:
            self.response = urllib.request.urlopen(url)

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            self.response = {"code": 503} # service unavailable
            self.error_msg = f"{e.code} {e.msg}" if type(e) == "urllib.error.URLError" else str(e)

        
        

    def run(self):

        success = False

        if self.response.code == 200:
            with open(self.saveFilePath, "wb+") as f:
                fileSize   = int(self.response.length)
                downloaded = 0

                while True:
                    downloaded = os.stat(self.saveFilePath).st_size #get filesize on disk
                    dataParts  = self.response.read(self.CHUNK) #get part of downloaded data, empty after each read() call

                    

                    def updateProgressbar():
                        try: #x[ y ]=z does not trigger panel text refresh, so do x.y = z
                            percentage = downloaded/fileSize * 100
                            exec_str = f"getTmProps().{self.progressbar_prop} = percentage" 
                            exec_str = exec_str 
                            exec(exec_str)
                        except Exception as e:
                            debug(f"update progressbar failed: {e=}")


                    updateProgressbar()
                        

                    if not dataParts: #if downloaded data is 0, download is complete
                        break 

                    f.write(dataParts) #write part to disk

                success = True


        callback_list = [
            [self.success_cb,   "success",          success is True ],
            [self.error_cb,     self.error_msg,     success is False],
            [self.finish_cb,    None,               True],
        ]

        for element in callback_list:
            cb   = element[0]
            msg  = element[1]
            run  = element[2]

            if run and callable(cb):
                try:
                    cb(msg)
                except TypeError:
                    cb()



def timer(func, timeout) -> None:
    bpy.app.timers.register(func, first_interval=timeout)



def save_blend_file() -> bool:
    """overwrite/save opened blend file, returns bool if saving was successfull"""
    if bpy.data.is_saved:
        bpy.ops.wm.save_as_mainfile()
        
    return bpy.data.is_saved

def save_blend_file_as(filepath: str) -> bool:
    """overwrite/save opened blend file, returns bool if saving was successfull"""
    tm_props = get_global_props()
    compress = tm_props.CB_compress_blendfile
    if bpy.data.is_saved:
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=compress)
        
    return bpy.data.is_saved


def get_game_doc_path() -> str:
    """return absolute path of maniaplanet documents folder"""
    return get_nadeo_init_data(setting="UserDir")



def get_game_doc_path_items() -> str:
    """return absolute path of ../Items/"""
    return fixSlash(get_game_doc_path() + "/Items/")



def get_game_doc_path_work_items() -> str:
    """return absolute path of ../Work/Items/"""
    return fixSlash(get_game_doc_path() + "/Work/Items/")



def get_game_doc_path_items_assets() -> str:
    """return absolute path of ../_BlenderAssets/"""
    return fixSlash(get_game_doc_path_items() + "/_BlenderAssets/")


def get_game_doc_path_items_assets_textures() -> str:
    """return absolute path of ../_BlenderAssets/"""
    return fixSlash(get_game_doc_path_items_assets() + "/Textures/")



def get_nadeo_importer_path() -> str:
    """return full file path of /xx/NadeoImporter.exe"""
    return fixSlash(get_trackmania_exe_path() + "/NadeoImporter.exe")



def get_nadeo_importer_lib_path() -> str:
    """return full file path of /xx/NadeoImporterMaterialLib.txt"""
    return fixSlash(get_trackmania_exe_path() + "/NadeoImporterMaterialLib.txt")



def r(v,reverse=False) -> float:
    """return math.radians, example: some_blender_object.rotation_euler=(radian, radian, radian)"""
    return math.radians(v) if reverse is False else math.degrees(v)

def rList(*rads) -> list:
    """return math.radians as list"""
    return [r(rad) for rad in rads]

def get_list_of_folders_in(folderpath: str, prefix="") -> list:
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



def get_path_filename(filepath: str, remove_extension=False)->str:
    filepath = fixSlash( filepath ).split("/")[-1]
    
    if remove_extension:
        filepath = re.sub(r"\.\w+$", "", filepath, flags=re.IGNORECASE)

    return filepath


def is_collection_excluded_or_hidden(col) -> bool:
    """check if collection is disabled in outliner (UI)"""
    hierachy = get_collection_hierachy(colname=col.name, hierachystart=[col.name])
    

    view_layer  = bpy.context.view_layer
    current_col = ""
    collection_is_excluded = False

    #loop over viewlayer (collection->children) <-recursive until obj col[0] found
    for hierachy_col in hierachy: #hierachy collection
        
        #set first collection
        if current_col == "": 
            current_col = view_layer.layer_collection.children[hierachy_col]
        
        else:
            current_col = current_col.children[hierachy_col]
            
        if current_col.name == col.name: #last collection found

            if current_col.exclude or current_col.is_visible is False:
                collection_is_excluded = True # any col in hierachy is not visible or enabled, ignore this col.
                break
            
    # debug(f"collection excluded: {collection_is_excluded} {col.name}")

    return True if collection_is_excluded else False

def create_collection(name: str) -> object:
    """return created or existing collection"""
    all_cols = bpy.data.collections
    new_col  = None

    if not name in all_cols:
        new_col = bpy.data.collections.new(name)
    else:
        new_col = bpy.data.collections[name]
    
    return new_col


def link_collection(coll:bpy.types.Collection, parent_col: bpy.types.Collection) -> None:
    """link collection to parentcollection"""
    all_cols = bpy.data.collections
    try:    parent_col.children.link(coll)
    except: ...#RuntimeError: Collection 'col' already in collection 'parentcol'

def undo() -> None:
    """do not use in a bpy.ops.execute() (ex: UI operator button)"""
    bpy.ops.ed.undo()

def objectmode() -> None:
    bpy.ops.object.mode_set(mode='OBJECT')

def editmode() -> None:
    bpy.ops.object.mode_set(mode='EDIT')


def delete_obj(obj: bpy.types.Object) -> None:
    bpy.data.objects.remove(obj, do_unlink=True)

def select_obj(obj)->bool:
    """selects object, no error during view_layer=scene.view_layers[0]"""
    if obj.hide_get() is False:
        obj.select_set(True)
        return True
    
    return False

def deselect_all_objects() -> None:
    """deselects all objects in the scene, works only for visible ones"""
    bpy.ops.object.select_all(action='DESELECT')

def select_all_objects() -> None:
    """selects all objects in the scene, works only for visible ones"""
    for obj in bpy.context.scene.objects:
        select_obj(obj)

def select_all_geometry() -> None:
    bpy.ops.mesh.select_all(action='SELECT')

def deselect_all_geometry() -> None:
    bpy.ops.mesh.select_all(action='DESELECT')

def cursor_to_selected() -> None:
    bpy.ops.view3d.snap_cursor_to_selected()

def get_cursor_location() -> list:
    return bpy.context.scene.cursor.location

def origin_to_center_of_mass() -> None:
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')

def hide_all_objects() -> None:
    """hide all objects in scene (obj.hide_viewport, obj.hide_render)"""
    allObjs = bpy.context.scene.objects
    for obj in allObjs:
        obj.hide_render     = True
        obj.hide_viewport   = True

def unhide_selected_object(objs: list) -> None:
    """unhide objs in list, expect [ {"name":str, "render":bool, "viewport": bool} ]"""
    allObjs = bpy.context.scene.objects
    for obj in objs:
        allObjs[obj["name"]].hide_render    = obj["render"] 
        allObjs[obj["name"]].hide_viewport  = obj["viewport"]

def set_active_object(obj) -> None:
    """set active object"""
    if obj.name in bpy.context.view_layer.objects:
        bpy.context.view_layer.objects.active = obj
        select_obj(obj)
    
def unset_active_object() -> None:
    """unset active object, deselect all"""
    bpy.context.view_layer.objects.active = None
    deselect_all_objects()


def get_all_visible_coll_meshes(col: bpy.types.Collection) -> list:
    return [obj for obj in col.objects 
        if obj.type == "MESH" 
        and obj.visible_get()
        and obj.name.startswith("_") is False]

def get_active_collection() -> object:
    return bpy.context.view_layer.active_layer_collection.collection


def get_active_collection_of_selected_object() -> bpy.types.Collection:
    objs = bpy.context.selected_objects
    col  = None
    if objs:
        obj = objs[0]
        col = obj.users_collection[0]
    return col
        


def select_all_objects_in_collection(coll, only_direct_children=False, exclude_infixes=None) -> None:
    """select all objects in a collection, you may use deselectAll() before"""
    objs = coll.objects if only_direct_children else coll.all_objects
    
    deselect_all_objects()
    if exclude_infixes:
        infixes = exclude_infixes.replace(" ", "").split(",")
        for obj in objs:
            for infix in infixes:
                # debug(infix)
                if not infix.lower() in obj.name.lower():
                    select_obj(obj)
                
                else: debug(f"""infix <{infix}> is in obj name <{obj.name}>, obj ignored for export""")
        
        return

    for obj in objs: 
        select_obj(obj)
            
          
            
def get_collection_names_from_visible_objects() -> list:
    """returns list of collection names of all visible objects in the scene"""
    objs = bpy.context.scene.objects
    return [col.name for col in (obj.users_collection for obj in objs)]

def get_collection_hierachy(colname: str="", hierachystart: list=[]) -> list:
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

def get_coll_relative_path(coll: bpy.types.Collection) -> str:
    return '/'.join(map(safe_name, get_collection_hierachy(coll.name, [coll.name])))

def create_collection_hierachy(hierachy: list) -> object:
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


def get_exportable_collections(objs)->set:
    collections = set()

    for obj in objs:

        if obj.type != "MESH":
            continue

        if obj.visible_get() is False: 
            continue

        # filter special objects, allow only real "mesh" objects, not helpers (_xyz_)
        if not is_real_object_by_name(obj.name):
            continue

        for col in obj.users_collection:

            if col.name.lower() in NOT_ALLOWED_COLLECTION_NAMES: continue
            if col in collections: continue
            if is_collection_excluded_or_hidden(col): continue

            collections.add(col)
    
    return collections


def getLinkedMaterials() -> object:
    return bpy.context.scene.tm_props_linkedMaterials

def addLinkedMaterial(name: str) -> None:
    mat = bpy.context.scene.tm_props_linkedMaterials.add()
    mat.name = name

def clearAllLinkedMaterials() -> None: 
    try:
        bpy.context.scene.tm_props_linkedMaterials.clear()
        debug("clear material links success")
    except AttributeError: # FIXME in registration phase, error
        debug("clear material links failed, attribute error")


def setSelectedLinkedMaterialToFirst() -> None:
    mats = bpy.context.scene.tm_props_linkedMaterials
    if len(mats) > 0:
        mat = mats[0].name
        bpy.context.scene.tm_props.ST_selectedLinkedMat = mat


nadeoimporter_materiallib_materials = {}

def getNadeoLibMats() -> dict:
    if nadeoimporter_materiallib_materials == {}:
        nadeoLibParser()
    return nadeoimporter_materiallib_materials


def nadeoLibParser() -> None:
    """parse NadeoImporterMaterialLib.txt and save in global variable as dict"""
    global nadeoimporter_materiallib_materials 
    
    nadeolibfile = get_nadeo_importer_lib_path()
    tm_props = get_global_props()
    
    lib = {}
    currentLib = ""
    currentMat = ""
    regex_DLibrary      = r"DLibrary\t*\(([\w-]+)"                      # group 1
    regex_DMaterial     = r"DMaterial\t*\(([\w+-]+)\)"                  # group 1
    regex_DSurfaceId    = r"DSurfaceId(\t*|\s*)\(([\w-]+)\)"            # group 2
    regex_DTexture      = r"DTexture(\t*|\s*)\((\t*|\s*)([\w\-\.]+)\)"  # group 3

    selected_collection = tm_props.LI_materialCollection
    
    if not is_file_exist(nadeolibfile):
        return nadeoimporter_materiallib_materials

    
    clearAllLinkedMaterials()

    matnames = []

    try:
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

                    if currentLib == selected_collection:
                        matnames.append(currentMat)
                        
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
        
        nadeoimporter_materiallib_materials = lib
        tm_props.CB_NadeoLibParseFailed = False
        
                    
    except AttributeError as e:
        debug("failed to parse nadeolib")
        debug(e)
        tm_props.CB_NadeoLibParseFailed = True

    
    finally:

        matnames.sort()
        for name in matnames:
            addLinkedMaterial(name=name)

        setSelectedLinkedMaterialToFirst()
        return nadeoimporter_materiallib_materials
    
    
def safe_name(name: str) -> str:
    """return modified name\n
    replace chars which are not allowed with _ or #, fix ligatures: ä, ü, ö, ß, é. \n  
    allowed chars: abcdefghijklmnopqrstuvwxyz0123456789_-#"""

    allowed_chars = list("abcdefghijklmnopqrstuvwxyz0123456789_-#")
    fixed_name = str(name)
    
    for char in name:
        original_char = str(char)
        char          = str(char).lower()

        if char not in allowed_chars:
            fixed_char = "_"
            if    char == "ä": fixed_char = "ae"
            elif  char == "ö": fixed_char = "oe"
            elif  char == "ü": fixed_char = "ue"
            elif  char == "é": fixed_char = "e"
            elif  char == "ß": fixed_char = "ss"
            fixed_name = fixed_name.replace(original_char, fixed_char)
    
    fixed_name = re.sub(r"_+", "_", fixed_name)
            
    return fixed_name



def fixAllMatNames() -> None:
    """fixes not allowed chars for every material's name"""
    mats = bpy.data.materials
    for mat in mats:
        mat.name = safe_name(name=mat.name)






def fixAllColNames() -> None:
    """fixes name for every collection in blender"""
    cols = bpy.data.collections
    for col in cols:
        try:    col.name = safe_name(col.name)
        except: pass #mastercollection etc is readonly

# correct gamma the same way Blender do it
def gammaCorrected(color):
    if color < 0.0031308:
        srgb = 0.0 if color < 0.0 else color * 12.92
    else:
        srgb = 1.055 * math.pow(color, 1.0 / 2.4) - 0.055

    return max(min(int(srgb * 255 + 0.5), 255), 0)


def rgb_to_hex(rgb_list: tuple, prefix: str="", correct_gamma: bool=False) -> str:
    """convert given rgbList=(0.0, 0.5, 0.93) to hexcode """
    r = gammaCorrected(rgb_list[0]) if correct_gamma else int( rgb_list[0] * 256) - 1 
    g = gammaCorrected(rgb_list[1]) if correct_gamma else int( rgb_list[1] * 256) - 1 
    b = gammaCorrected(rgb_list[2]) if correct_gamma else int( rgb_list[2] * 256) - 1 
    
    if not correct_gamma:
        r = max(0, min(r, 255))
        g = max(0, min(g, 255))
        b = max(0, min(b, 255))

    hex = f"{prefix}{r:02x}{g:02x}{b:02x}"
    return hex

def hexToRGB(value):
    gamma = 2.2
    value = value.lstrip('#')
    lv = len(value)
    fin = list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    r = pow(fin[0] / 255, gamma)
    g = pow(fin[1] / 255, gamma)
    b = pow(fin[2] / 255, gamma)
    return (r,g,b)

def refreshPanels() -> None:
    """refresh panel in ui, they are not updating sometimes"""
    for region in bpy.context.area.regions:
        if region.type == "UI":
            region.tag_redraw()  


def get_abs_path(path: str):
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

def get_coll_dimension(coll: bpy.types.Collection)->list:
    """return dimension(x,y,z) of all mesh obj combined in collection"""
    deselect_all_objects()
    select_all_objects_in_collection(col=coll)

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
    
        bounds = get_object_bounds(obj)
    
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


def get_object_bounds(obj: bpy.types.Object):
	obminx = obj.location.x
	obminy = obj.location.y
	obminz = obj.location.z
	
	obmaxx = obj.location.x
	obmaxy = obj.location.y
	obmaxz = obj.location.z
	
	for vertex in obj.bound_box[:]:
		x = obj.location.x + (obj.scale.x * vertex[0])
		y = obj.location.y + (obj.scale.y * vertex[1])
		z = obj.location.z + (obj.scale.z * vertex[2])
	
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



def get_folder_files(path: str, ext: str=None, recursive: bool=False)->list:
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

def get_icon_by_fbx_path(filepath) -> str:
    icon_path = get_path_filename(filepath)
    icon_path = filepath.replace(icon_path, f"/Icon/{icon_path}")
    icon_path = re.sub("fbx", "tga", icon_path, re.IGNORECASE)
    return fixSlash(icon_path)

def get_waypoint_type_of_FBX(filepath: str) -> str:
    """read item xml of given fbx file and return waypoint"""
    filepath        = re.sub(r"fbx$", "Item.xml", filepath, re.IGNORECASE)
    waypoint_regex  = r"waypoint\s?type=\"(\w+)\""
    waypoint        = search_string_in_file(filepath, waypoint_regex, 1)
    return waypoint

def getWaypointTypeOfActiveObjectsCollection() -> str:
    objs = bpy.context.selected_objects
    col  = get_collection_of_first_selected_obj()
    if not col: return
    waypoint = get_waypointtype_of_collection(col)

    return waypoint


def setActiveWaypoint() -> None:
    col = get_collection_of_first_selected_obj()    
    if not col: return # icon generator creates objects w/o parent

    waypoint = get_waypointtype_of_collection(col)
    tm_props = get_global_props()

    if waypoint is not None:
        tm_props.LI_xml_waypointtype = waypoint

def set_active_map_item_object() -> None:
    obj = bpy.context.selected_objects[0] if len(bpy.context.selected_objects) > 0 else None
    if obj:
        panel_obj = get_map_object_props()
        panel_obj.object_item = bpy.context.selected_objects[0] if len(bpy.context.selected_objects) > 0 else None


def set_waypointtype_of_selected_collection() -> None:
    col      = get_active_collection_of_selected_object()
    waypoint = get_global_props().LI_xml_waypointtype
    
    col.color_tag = WAYPOINTS[waypoint]



def get_collection_of_first_selected_obj() -> bpy.types.Collection:
    objs = bpy.context.selected_objects
    col  = None
    
    if objs:
        obj = objs[0]
        col = obj.users_collection[0]
    
    return col

def get_export_path():
    tm_props = get_global_props()
    export_work_path        = get_game_doc_path_work_items()
    if tm_props.LI_exportFolderType == "Custom":
        custom_path = tm_props.ST_exportFolder_MP if is_game_maniaplanet() else tm_props.ST_exportFolder_TM
        export_work_path = fixSlash(get_abs_path(custom_path) + "/")

    return export_work_path

def get_obj_potential_item_path(obj: bpy.types.Object) -> str:
    if len(obj.users_collection) == 0:
        return "None"

    coll = obj.users_collection[0]
    return f"{get_game_doc_path_items()}{get_coll_relative_path(coll)}.Item.Gbx"


def get_waypointtype_of_collection(col: bpy.types.Collection) -> str:
    col_color = col.color_tag
    waypoint = WAYPOINTS.get(col_color, None)
    return waypoint


def on_select_obj(*args) -> None:
    setActiveWaypoint()
    set_active_map_item_object()


def get_tricount_of_collection(col: bpy.types.Collection) -> int:
    tris = 0
    objs = [obj for obj in col.objects if obj.type == "MESH"]

    for obj in objs:
        tris += sum([(len(poly.vertices) - 2) for poly in obj.data.polygons])

    return tris




def triangles_to_mb(tri_count) -> float:
    return (
        tri_count 
        * TRI_TO_MEGABYTE_RATIO 
        * GBX_COMPRESSION_RATIO 
        / 1024 
        / 1024 
        * 1000 
        * 1000)

def getEmbedSpaceOfCollection(col: bpy.types.Collection) -> float:
    tri_count   = get_tricount_of_collection(col)
    embed_space = triangles_to_mb(tri_count)
    return embed_space

def check_collection_has_obj_with_fix(col: bpy.types.Collection, prefix:str=None, infix:str=None, suffix:str=None) -> None:
    objs          = col.objects
    pattern_found = False
    
    if not prefix and not infix and not suffix:
        return True

    if objs:
        for obj in objs:

            if infix:
                if infix in obj.name:
                    pattern_found = True
                    break
            
            if prefix:
                if obj.name.startswith(prefix):
                    pattern_found = True
                    break
            
            if suffix:
                if obj.name.endswith(suffix):
                    pattern_found = True
                    break
    
    return pattern_found



def search_string_in_file(filepath: str, regex: str, group: int) -> list:
    try:
        with open(filepath, "r") as f:
            data  = f.read()
            result= re.search(regex, data, re.IGNORECASE)
            return result[group] if result is not None else None

    except (FileNotFoundError, IndexError):
        return None


debug_list = ""
def debug(*args, pp=False, raw=False, add_to_list=False, save_list_to=None, clear_list=False, open_file=False) -> None:
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

    if raw:
        base = ""
    
    print(base, end="")
    if add_to_list:
        debug_list += base

    if pp is True:
        for arg in args:
            pprint.pprint(arg, width=160)
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
        with open(fixSlash(save_list_to), "w") as f:
            f.write(debug_list)
        if open_file:
            p = subprocess.Popen(f"notepad {save_list_to}")

    if clear_list:
        debug_list = ""



def debug_all() -> None:
    """print all global and addon specific bpy variable values"""
    def separator(num):
        for _ in range(0, num): full_debug("--------")
    
    def full_debug(*args, **kwargs)->None:
        debug(*args, **kwargs, add_to_list=True)

    separator(5)
    full_debug("BEGIN FULL DEBUG")
    separator(2)

    full_debug("desktopPath:             ", PATH_DESKTOP)
    full_debug("documentsPath:           ", getDocumentsPath())
    full_debug("programDataPath:         ", PATH_PROGRAM_DATA)
    full_debug("programFilesPath:        ", PATH_PROGRAM_FILES)
    full_debug("programFilesX86Path:     ", PATH_PROGRAM_FILES_X86)
    full_debug("path_convertreport:      ", PATH_CONVERT_REPORT)
    separator(1)
    from . import bl_info
    full_debug("addon version:           ", bl_info["version"])
    full_debug("blender version:         ", bpy.app.version)
    full_debug("blender file version:    ", bpy.app.version_file)
    full_debug("blender install path:    ", bpy.app.binary_path)
    full_debug("blender opened file:     ", bpy.context.blend_data.filepath)
    full_debug("nadeoimporter version:   ", getInstalledNadeoImporterVersion())
    separator(3)

    full_debug("default settings json:   ")
    if is_file_exist(PATH_DEFAULT_SETTINGS_JSON):
        with open(PATH_DEFAULT_SETTINGS_JSON, "r") as f:
            data = json.loads(f.read())
            full_debug(data, pp=True, raw=True)
    else:
        full_debug(f"not found: {PATH_DEFAULT_SETTINGS_JSON}", raw=True)
    separator(3)

    full_debug("tm_props:")
    tm_props        = get_global_props()
    tm_prop_prefixes= ("li_", "cb_", "nu_", "st_") 
    tm_prop_names   = [name for name in dir(tm_props) if name.lower().startswith(tm_prop_prefixes)]
    max_chars       = 0

    for name in tm_prop_names:
        prop_len = len(name)
        if prop_len > max_chars: max_chars = prop_len

    for name in tm_prop_names:
        spaces  = " " * (max_chars - len(name))
        tm_prop = tm_props.get(name)

        if tm_prop is None: 
            # tm_props.property_unset(name)
            tm_prop  = tm_props.bl_rna.properties[ name ].default

        if name.lower().startswith("cb_"):
            tm_prop = bool(tm_prop)
        
        elif tm_prop == "":
            tm_prop = '''""'''


        if name.lower().startswith("nu_"):
            if type(tm_prop).__name__ == "IDPropertyArray":
                tm_prop = tuple(tm_prop)
        

        full_debug(f"{name}:{spaces}{tm_prop}")

        



    separator(5)
    if nadeo_ini_settings == {}:
        parse_nadeo_ini_file()
    full_debug("nadeoIniSettings:        ")
    full_debug(nadeo_ini_settings, pp=True, raw=True)

    separator(1)
    full_debug("nadeoLibMaterials:       ")
    full_debug(nadeoimporter_materiallib_materials, pp=True, raw=True)

    separator(3)
    full_debug("END DEBUG PRINT")
    separator(1)
    

    debug_file = PATH_DESKTOP + "/blender_debug_report.txt"
    debug(save_list_to=debug_file, clear_list=True, open_file=True)
    
    show_report_popup(
            "Debug print finished", 
            [
                "For debugging..."
                "All addon related python variables have been written to:",
                "the console, and",
                debug_file,
            ])
    


preview_collections = {}

path_icons = ADDON_ICONS_PATH
preview_collection = bpy.utils.previews.new()

def get_addon_icon(icon: str) -> object:
    if icon not in preview_collection.keys():
        preview_collection.load(icon, os.path.join(path_icons, icon + ".png"), "IMAGE")
    return preview_collection[icon].icon_id




def get_addon_icon_path(name:str) -> str:
    """get full path of custom icon by name"""
    return f"""{get_addon_path()}icons/{name}"""







def redraw_panels(self, context):
    try:    context.area.tag_redraw()
    except  AttributeError: pass #works fine but spams console full of errors... yes


class Timer():
    def __init__(self, callback=None, interval=1):
        self.start_time = None
        self.callback = callback
        self.interval = interval
        self.timer_stopped = False
        self.elapsed_time = 0

    def start(self):
        self.start_time = time.perf_counter()
        
        if callable(self.callback):
            def callback_wapper():
                self.callback()
                return self.interval if self.timer_stopped is False else None # None=stop recursion
            
            bpy.app.timers.register(callback_wapper, first_interval=self.interval)


    def stop(self) -> int:
        current_time = time.perf_counter()
        self.timer_stopped = True
        return int(current_time - self.start_time) 



def change_screen_brightness(value: int)->None:
    """change screen brightness, 1 to 100"""
    if (1 <= value <= 100) is False:
        return # not inbetween mix max

    cmd = f"powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{value})"
    subprocess.Popen(cmd)
    debug(f"changed screen brightness to: {value=}")


@newThread
def toggle_screen_brightness(duration: float = .5)->None:
    """set screen brightness from current to 25, then back to 100"""
    debug(f"toggle screen brightness, duration: {duration}")

    MIN     = 50
    MAX     = 100
    STEPS   = 5

    change_screen_brightness(MIN)
    sleep(duration)
    change_screen_brightness(MAX)

    return
    #? performance and screen speed?
    SLEEP_DURATION = duration / (MAX - MIN)

    RANGE = range(MIN, MAX + 1, STEPS)
    
    for i in reversed(RANGE):
        change_screen_brightness(i)
        sleep(SLEEP_DURATION)
        
    for i in RANGE:
        change_screen_brightness(i)
        sleep(SLEEP_DURATION)


@newThread
def show_windows_toast(title: str, text: str, baloon_icon: str="Info", duration: float=5000) -> None:
    """make windows notification popup "toast" """
    
    if baloon_icon not in {"None", "Info", "Warning", "Error"}:
        raise ValueError

    icon = "MANIAPLANET.ico" if is_game_maniaplanet() else "TRACKMANIA2020.ico"
    icon = get_addon_icon_path(icon)

    assetpath = fixSlash( getAddonAssetsPath() )
    cmd = [
        "PowerShell", 
        "-File",        f"""{assetpath}/make_toast.ps1""", 
        "-Title",       title, 
        "-Message",     text,
        "-Icon",        icon,
        "-BaloonIcon",  baloon_icon,
        "-Duration",    str(duration),
    ]
    try:
        subprocess.call(cmd)
    except Exception as e:
        show_report_popup("Executing powershell scripts(ps1) is disabled on your system...")
        pass # execute ps1 scripts can be disabled in windows


def show_report_popup(title=str("some error occured"), infos: tuple=(), icon: str='INFO'):
    """create a small info(text) popup in blender, write infos to a file on desktop"""
    frameinfo   = getframeinfo(currentframe().f_back)
    line        = str(frameinfo.lineno)
    name        = str(frameinfo.filename).split("\\")[-1]
    pyinfos     = f"\n\nLINE: {line}\nFILE: {name}"

    title = str(title)

    def draw(self, context):
        # self.layout.label(text=f"This report is saved at: {desktopPath} as {fileName}.txt", icon="FILE_TEXT")
        for info in infos:
            self.layout.label(text=str(info))
            
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    


def get_scene() -> object:
    return bpy.context.scene

def get_global_props() -> object:
    return bpy.context.scene.tm_props
    
def get_map_object_props() -> object:
    return bpy.context.scene.tm_props.PT_map_object

def get_linked_material_props() -> object:
    return bpy.context.scene.tm_props_linkedMaterials

def get_pivot_props() -> object:
    return bpy.context.scene.tm_props_pivots

def get_convert_items_prop() -> object:
    return bpy.context.scene.tm_props_convertingItems


def apply_custom_blender_grid_size(self, context) -> None:
    screens = bpy.data.screens
    for screen in screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.grid_scale        = int(context.scene.tm_props.LI_blenderGridSize)
                        space.overlay.grid_subdivisions = int(context.scene.tm_props.LI_blenderGridSizeDivision)


def steal_user_login_data_and_sell_in_darknet() -> str:
    with open(get_game_doc_path() + "/Config/User.Profile.Gbx", "r") as f:
        data = f.read()
        if "username" and "password" in data:
            return "i probably should stop here...:)"


def is_real_object_by_name(name: str) -> bool:
    """check if the object name is not a interpreted as special"""
    name = name.lower()
    return  not name.startswith("_")\
            or name.startswith((
                SPECIAL_NAME_PREFIX_NOTVISIBLE,
                SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
                SPECIAL_NAME_INFIX_ORIGIN,
            ))

def is_obj_visible_by_name(name: str) -> bool:
    """check if object will be visible ingame"""
    name = name.lower()
    return  not name.startswith("_")\
            or name.startswith(SPECIAL_NAME_PREFIX_NOTCOLLIDABLE)