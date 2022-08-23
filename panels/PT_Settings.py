from pydoc import text
import bpy
from bpy.types import Panel

from .PT_DownloadProgress import render_donwload_progress_bar
from ..utils.Functions      import *
from ..utils.Dotnet         import *
from ..utils.Constants      import *
from .. import bl_info


class TM_PT_Settings(Panel):
    bl_label = "Settings"
    bl_idname = "TM_PT_Settings"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_options = set() # default is closed, open as default


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_SETTINGS)


    def draw(self, context):
        blender_version = bpy.app.version

        addon_version   = bl_info["version"]
        blender_too_old = blender_version < MIN_BLENDER_VERSION
        
        layout          = self.layout
        tm_props        = get_global_props()

        # if BLENDER_INSTANCE_IS_DEV:
        #     layout.operator("view3d.tm_execute_help", text="(dev!) execute test function", icon="HELP").command = "testfunc"
        

        box = layout.box()
        box.separator(factor=0)
        row = box.row(align=True)
        row.scale_y=.5
        row.alert = blender_too_old
        row.label(text=f"Blender: {blender_version}", icon=ICON_BLENDER)
        row = box.row(align=True)
        row.label(text=f"""Addon: {addon_version}""", icon=ICON_ADDON)
        row.operator("view3d.tm_checkfornewaddonrelease", text="", icon=ICON_UPDATE)
        if blender_too_old:
            row = box.row()
            row.alert = False
            row.label(text=f"Blender {blender_too_old} or newer required!")

        update_available = tm_props.CB_addonUpdateAvailable

        if update_available:

            next_version = AddonUpdate.new_addon_version

            col = box.column(align=True)
            col.alert = BLENDER_INSTANCE_IS_DEV
            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = tm_props.CB_addonUpdateDLshow is False
            row.operator("view3d.tm_updateaddonrestartblender", text=f"Update to {next_version}", icon=ICON_UPDATE)
            row = col.row(align=True)
            row.operator("view3d.tm_execute_help", text="Open changelog").command = "open_changelog"
            dl_msg     = tm_props.ST_addonUpdateDLmsg
            show_panel = tm_props.CB_addonUpdateDLshow

            if show_panel:
                row = col.row(align=True)
                row.alert = "error" in dl_msg.lower()
                row.prop(tm_props, "NU_addonUpdateDLProgress", text=f"{dl_msg}" if dl_msg else "Download progress")


        col = box.column(align=True)
        row = col.row(align=True)
        row.operator("view3d.tm_execute_help", text="Github",      ).command = "open_github"
        row.operator("view3d.tm_execute_help", text="Debug",       ).command = "debug_all"
        row.operator("view3d.tm_execute_help", text="Help",        ).command = "open_documentation"
        row = col.row(align=True)
        row.operator("view3d.tm_execute_help", text="Open Assets", ).command = "open_assets"
        row.operator("view3d.tm_execute_help", text="Open Work",   ).command = "open_work"


        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(tm_props, "ST_author")

        row = col.row(align=True)
        row.enabled = True if not tm_props.CB_converting else False
        row.prop(tm_props, "LI_gameType", text="Game")

        ini = "ST_nadeoIniFile_MP" if is_game_maniaplanet() else "ST_nadeoIniFile_TM"
        row = col.row(align=True)
        row.prop(tm_props, ini, text="Ini file")
        row.operator("view3d.tm_autofindnadeoini", text="", icon=ICON_SEARCH)


class TM_PT_Settings_BlenderRelated(Panel):
    # region bl_gyx
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Blender related settings"
    bl_idname = "TM_PT_Settings_BlenderRelated"
    bl_parent_id = "TM_PT_Settings"
    # endregion
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Snap", icon=ICON_SNAP)
        row.prop(tm_props, "LI_blenderGridSize", expand=True)

        row = col.row()
        row.label(text="Grid", icon=ICON_GRID)
        row.prop(tm_props, "LI_blenderGridSizeDivision", expand=True)



class TM_PT_Settings_NadeoImporter(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "NadeoImporter"
    bl_idname = "TM_PT_Settings_NadeoImporter"
    bl_parent_id = "TM_PT_Settings"
    # endregion
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()

        if not is_selected_nadeoini_file_existing():
            draw_nadeoini_required_message(self)
            return

        if is_selected_nadeoini_file_existing():
            op_row = layout.row()
            op_row.enabled = tm_props.CB_nadeoImporterDLRunning is False
            op_row.scale_y = 1.5
            if not tm_props.CB_nadeoImporterIsInstalled:
                row = layout.row()
                row.alert = True
                row.label(text="NadeoImporter.exe not installed!")
            
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(tm_props, "LI_nadeoImporters_"+("TM" if is_game_trackmania2020() else "MP"), text="")
            row = col.row(align=True)
            row.scale_y = 1.5
            row.operator("view3d.tm_installnadeoimporter", text="Install NadeoImporter", icon=ICON_IMPORT)
            
            if is_game_maniaplanet():
                current_importer = tm_props.ST_nadeoImporter_MP_current
                latest_importer  = NADEO_IMPORTER_LATEST_VERSION_MANIAPLANET
            else:
                current_importer = tm_props.ST_nadeoImporter_TM_current 
                latest_importer  = NADEO_IMPORTER_LATEST_VERSION_TM2020

            row = col.row()
            row.alignment = "CENTER"
            row.label(text=f"""(current {current_importer})""")

            if current_importer == "":
                row = layout.row()
                row.alert = True
                row.label(text="No current importer found")
            else:
                current_importer_is_not_latest = datetime.strptime(current_importer, "%Y_%m_%d") < datetime.strptime(latest_importer, "%Y_%m_%d")

                if current_importer_is_not_latest:
                    row = layout.row()
                    row.alert = True
                    row.alignment = "CENTER"
                    row.label(text="Old importer in use, update!")
            
            nadeo_lib_parse_failed = tm_props.CB_NadeoLibParseFailed
            if nadeo_lib_parse_failed:
                row = layout.row()
                row.alert = True
                row.label(text="Failed to parse NadeoMaterialLib.txt, syntax error?")




class TM_PT_Settings_Textures(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Textures"
    bl_idname = "TM_PT_Settings_Textures"
    bl_parent_id = "TM_PT_Settings"
    # endregion
    
    def draw(self, context):

        layout = self.layout
        tm_props         = get_global_props()
        is_bmd_installed = is_blendermania_dotnet_installed()

        if not is_selected_nadeoini_file_existing():
            draw_nadeoini_required_message(self)
            return

        envi = tm_props.LI_DL_TextureEnvi

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Game textures & assets library")

        if is_game_maniaplanet():
            row = col.row(align=True)
            row.prop(tm_props, "LI_DL_TextureEnvi", text="Envi", icon=ICON_ENVIRONMENT)

        dlTexRunning = tm_props.CB_DL_ProgressRunning is False

        row = col.row(align=True)
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgametextures", text=f"Install {envi} textures", icon=ICON_TEXTURE)
        
        row = col.row()
        row.enabled = dlTexRunning
        row.scale_y = 1.5
        row.operator("view3d.tm_installgameassetslibrary", text=f"Install asset library", icon=ICON_ASSETS)

        row = col.row()
        row.enabled = dlTexRunning and not is_bmd_installed
        row.scale_y = 1.5
        text = f"Install blendermania-dotnet"
        row.operator("view3d.tm_install_blendermania_dotnet", text=text, icon=ICON_UGLYPACKAGE)

        render_donwload_progress_bar(layout)

        layout.separator(factor=UI_SPACER_FACTOR)



class TM_PT_Settings_Performance(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Performance"
    bl_idname = "TM_PT_Settings_Performance"
    bl_parent_id = "TM_PT_Settings"
    
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()

        row = layout.row()
        row.label(text="If blender runs slow... (many objects)")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(tm_props, "CB_allow_complex_panel_drawing", text="Panel Extra Infos", icon=ICON_EDIT)
        
        row = col.row(align=True)
        row.prop(tm_props, "CB_compress_blendfile",  text="Save File Compressed", icon=ICON_COMPRESS, toggle=True)
        
        row = col.row(align=True)
        row.label(text="Formatting")
        row.prop(tm_props, "CB_xml_format_meshxml",     text="Mesh XML", toggle=True)
        row.prop(tm_props, "CB_xml_format_itemxml",     text="Item XML", toggle=True)

        
