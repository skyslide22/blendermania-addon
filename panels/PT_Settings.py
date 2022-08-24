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


        box = layout.box()
        box.separator(factor=0)
        row = box.row(align=True)
        row.scale_y=.5
        row.alert = blender_too_old
        row.label(text=f"Blender: {blender_version}", icon=ICON_BLENDER)
        row = box.row(align=True)
        row.label(text=f"""Addon: {addon_version}""", icon=ICON_ADDON)
        row.operator("view3d.tm_checkfornewaddonrelease",   text="", icon=ICON_UPDATE)
        row.operator("view3d.tm_debug_all",                 text="", icon=ICON_DEBUG)
        
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
            # TODO change link
            row.operator("view3d.tm_open_url", text="Open changelog").url = URL_CHANGELOG
            dl_msg     = tm_props.ST_addonUpdateDLmsg
            show_panel = tm_props.CB_addonUpdateDLshow

            if show_panel:
                row = col.row(align=True)
                row.alert = "error" in dl_msg.lower()
                row.prop(tm_props, "NU_addonUpdateDLProgress", text=f"{dl_msg}" if dl_msg else "Download progress")


        col = box.column(align=True)
        row = col.row(align=True)
        row.operator("view3d.tm_open_url", text="Github", icon=ICON_WEBSITE).url = URL_GITHUB
        row.operator("view3d.tm_open_url", text="Help",   icon=ICON_WEBSITE).url = URL_DOCUMENTATION
        row = col.row(align=True)
        row.operator("view3d.tm_open_folder", text="Work",   icon=ICON_FOLDER).folder = get_game_doc_path_work_items()
        row.operator("view3d.tm_open_folder", text="Items",  icon=ICON_FOLDER).folder = get_game_doc_path_items()
        row = col.row(align=True)
        row.operator("view3d.tm_open_folder", text="Assets", icon=ICON_FOLDER).folder = get_game_doc_path_items_assets()
        row.operator("view3d.tm_open_folder", text="Maps",   icon=ICON_FOLDER).folder = get_game_doc_path_maps()


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

        nadeoini_invalid = draw_nadeoini_required_message(self)
        if nadeoini_invalid:
            return


class TM_PT_Settings_BlenderRelated(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Blender related settings"
    bl_idname = "TM_PT_Settings_BlenderRelated"
    bl_parent_id = "TM_PT_Settings"

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
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
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "NadeoImporter"
    bl_idname = "TM_PT_Settings_NadeoImporter"
    bl_parent_id = "TM_PT_Settings"
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()

    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()

        if not is_selected_nadeoini_file_name_ok():
            draw_nadeoini_required_message(self)
            return

        if is_selected_nadeoini_file_name_ok():
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








class TM_PT_Settings_Performance(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "Performance"
    bl_idname = "TM_PT_Settings_Performance"
    bl_parent_id = "TM_PT_Settings"
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()    
    
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

        
