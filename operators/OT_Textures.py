
import bpy
import re

from bpy.types import (Operator)

from ..utils.Functions      import *
from ..properties.Functions import *
from ..utils.Constants      import * 



class TM_OT_Textures_UpdateTextureSource(Operator):
    bl_idname = "view3d.tm_update_texture_source"
    bl_description = "Update Texture Source Folder"
    bl_label = "Update Texture Sources"
        
    def execute(self, context):
        update_texture_folder()
        return {"FINISHED"}
    

    
def get_raw_filename(path: str) -> str:
    return path.replace("/", "\\").split("\\")[-1].split(".")[0]

def update_texture_folder(tex_src:str = ""):
    tm_props = get_global_props()
    
    tex_src_new = tex_src # DEFAULT
    tex_src_type= tm_props.LI_TextureSources

    if tex_src_type == "CUSTOM":
        tex_src_new = tm_props.ST_TextureSource
        if tex_src_new == "": 
            show_report_popup("No path specified", ["Custom path is empty, select a folder with dds files!"])
            return

    elif tex_src_type == "MODWORK":
        tex_src_new, _ = get_modwork_paths()
        tex_src_new += "/Image"
        if not is_folder_existing(tex_src_new):
            show_report_popup("ModWork diabled", ["ModWork folder is disabled, please enable it before you update the texture sources"])
            return

    elif tex_src_type == "DEFAULT":
        envi = tm_props.LI_materialCollection
        root = get_game_doc_path_items_assets_textures()
        tex_src_new = root + envi + "/"
    
    else:
        raise ValueError(f"Type {tex_src_type} not supported")
    
    
    pref_format = tm_props.LI_TextureSourcePreferKind

    images = bpy.data.images

    filepaths = get_folder_files(tex_src_new)
    filenames = []

    for file in filepaths:
        filename = get_raw_filename(file) # raw name no ext/path
        filenames.append(filename.lower())
    
    found_images = []
    for image in images:
        if image.name.split(".")[0].lower() in filenames:
            found_images.append(image)

    for image in found_images:
        image_name = image.name.split(".")[0]

        new_path = tex_src_new + "\\" + image_name + "." + pref_format.lower()
        if not is_file_existing(new_path):
            new_path = new_path.split(".")[0] + ".dds"
            if not is_file_existing(new_path):
                continue 
        
        image.filepath = new_path
        image.reload()
    





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



def get_modwork_paths() -> tuple[str]:
    tm_props = get_global_props()
    collection_folder = tm_props.LI_DL_TextureEnvi

    if is_game_trackmania2020():
        collection_folder = "Stadium"

    modwork_root     = get_game_doc_path() + "/Skins/" + collection_folder
    modwork_path     = fix_slash(modwork_root + "/" + MODWORK_FOLDER_NAME)
    modwork_off_path = fix_slash(modwork_root + "/" + MODWORK_OFF_FOLDER_NAME)

    return (modwork_path, modwork_off_path)


def toggle_modwork_folder() -> None:

    tm_props = get_global_props()
    collection_folder = tm_props.LI_DL_TextureEnvi

    if is_game_trackmania2020():
        collection_folder = "Stadium"

    modwork_path, modwork_off_path = get_modwork_paths()
    
    modwork_exist     = is_folder_existing(fix_slash(modwork_path))
    modwork_off_exist = is_folder_existing(fix_slash(modwork_off_path))

    enabled_text = False

    if not modwork_exist and not modwork_off_exist:
        create_folder_if_necessary(modwork_path + "/Image")
        modwork_exist = True

    try:
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
    except PermissionError as err:
        show_report_popup(
            "Rename failed", [
                "Rename of the folder ModWork failed", 
                "Try closing all windows explorer instances!", 
                "Error:", err])
        return

    # icon         = ICON_SUCCESS if enabled else ICON_CANCEL
    # enabled_text = "enabled"    if enabled else "disabled"

    if is_game_trackmania2020():
        tm_props.CB_modwork_tm_stadium_enabled = enabled
    if is_game_maniaplanet():
        if   collection_folder == ENVI_NAME_STADIUM:      tm_props.CB_modwork_mp_stadium_enabled    = enabled
        elif collection_folder == ENVI_NAME_CANYON:       tm_props.CB_modwork_mp_canyon_enabled     = enabled
        elif collection_folder == ENVI_NAME_VALLEY:       tm_props.CB_modwork_mp_valley_enabled     = enabled
        elif collection_folder == ENVI_NAME_LAGOON:       tm_props.CB_modwork_mp_lagoon_enabled     = enabled
        elif collection_folder == ENVI_NAME_SHOOTMANIA:   tm_props.CB_modwork_mp_shootmania_enabled = enabled
    
    # show_report_popup(f"Modwork {enabled_text}", (f"Path: {modwork_path}",), icon=icon)
