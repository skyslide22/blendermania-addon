
import bpy
import re

from bpy.types import (Operator)

from ..utils.Functions      import *
from ..properties.Functions import *
from ..utils.Constants      import * 



class TM_OT_Textures_ToggleModwork(Operator):
    bl_idname = "view3d.tm_toggle_modwork"
    bl_description = "Toogle Modwork Folder Name (Enable/Disable)"
    bl_label = "Toggle Modwork"
        
    def execute(self, context):
        toggle_modwork_folder()
        return {"FINISHED"}




def is_selected_modwork_enabled() -> bool:
    tm_props = get_global_props()
    
    collection_folder = tm_props.LI_DL_TextureEnvi
    if is_game_trackmania2020():
        collection_folder = "Stadium"
        return tm_props.CB_modwork_tm_stadium_enabled   
    
    if is_game_maniaplanet():
        if collection_folder == ENVI_NAME_STADIUM:      return tm_props.CB_modwork_mp_stadium_enabled   
        if collection_folder == ENVI_NAME_CANYON:       return tm_props.CB_modwork_mp_canyon_enabled    
        if collection_folder == ENVI_NAME_VALLEY:       return tm_props.CB_modwork_mp_valley_enabled    
        if collection_folder == ENVI_NAME_LAGOON:       return tm_props.CB_modwork_mp_lagoon_enabled    
        if collection_folder == ENVI_NAME_SHOOTMANIA:   return tm_props.CB_modwork_mp_shootmania_enabled
    
    return False


# TODO works only with selcted game
def check_modwork_folders_enabled() -> bool:
    tm_props = get_global_props()
    modworks = [
        ("CB_modwork_tm_stadium_enabled",   fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_STADIUM)    + "/ModWork"),
        ("CB_modwork_mp_stadium_enabled",   fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_STADIUM)    + "/ModWork"),
        ("CB_modwork_mp_canyon_enabled",    fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_CANYON)     + "/ModWork"),
        ("CB_modwork_mp_valley_enabled",    fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_VALLEY)     + "/ModWork"),
        ("CB_modwork_mp_lagoon_enabled",    fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_LAGOON)     + "/ModWork"),
        ("CB_modwork_mp_shootmania_enabled",fix_slash(get_game_doc_path() + "/Skins/" + ENVI_NAME_SHOOTMANIA) + "/ModWork"),
    ]

    for modwork in modworks:
        prop, path = modwork
        modwork_enabled = is_folder_existing(path) 
        tm_props[prop] = modwork_enabled 
        debug(f"modwork enabled: {modwork_enabled} {path}")



def toggle_modwork_folder() -> None:

    tm_props = get_global_props()
    collection_folder = tm_props.LI_DL_TextureEnvi

    if is_game_trackmania2020():
        collection_folder = "Stadium"

    modwork_root     = get_game_doc_path() + "/Skins/" + collection_folder
    modwork_path     = modwork_root + "/" + MODWORK_FOLDER_NAME
    modwork_off_path = modwork_root + "/" + MODWORK_OFF_FOLDER_NAME
    
    modwork_exist     = is_folder_existing(fix_slash(modwork_path))
    modwork_off_exist = is_folder_existing(fix_slash(modwork_off_path))

    enabled_text = False

    if not modwork_exist and not modwork_off_exist:
        create_folder_if_necessary(modwork_path)
        modwork_exist = True

    if modwork_exist:
        if modwork_off_exist:
            rename_folder(modwork_off_path, modwork_off_path + "_old")
        rename_folder(modwork_path, modwork_off_path)
        enabled = False

    elif modwork_off_exist:
        if modwork_exist:
            rename_folder(modwork_path, modwork_path + "_old")
        rename_folder(modwork_off_path, modwork_path)
        enabled = True    

    icon         = ICON_SUCCESS if enabled else ICON_CANCEL
    enabled_text = "enabled"    if enabled else "disabled"

    if is_game_trackmania2020():
        tm_props.CB_modwork_tm_stadium_enabled = enabled
    if is_game_maniaplanet():
        if collection_folder == ENVI_NAME_STADIUM:      tm_props.CB_modwork_mp_stadium_enabled    = enabled
        if collection_folder == ENVI_NAME_CANYON:       tm_props.CB_modwork_mp_canyon_enabled     = enabled
        if collection_folder == ENVI_NAME_VALLEY:       tm_props.CB_modwork_mp_valley_enabled     = enabled
        if collection_folder == ENVI_NAME_LAGOON:       tm_props.CB_modwork_mp_lagoon_enabled     = enabled
        if collection_folder == ENVI_NAME_SHOOTMANIA:   tm_props.CB_modwork_mp_shootmania_enabled = enabled
    
    # show_report_popup(f"Modwork {enabled_text}", (f"Path: {modwork_path}",), icon=icon)
