
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
    
    show_report_popup(f"Modwork {enabled_text}", icon=icon)
