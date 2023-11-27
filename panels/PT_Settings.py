from pydoc import text
import bpy
from bpy.types import Panel

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

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

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        
        if AddonUpdate.new_addon_available:
            col = row.column(align=True)
            box = col.box()
            # box.enabled = False
            box.alert = True
            box.label(text=" Update!")

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.title = "General Settings Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can see all the settings related to this addon.",
            "1. Select your Nadeo.ini file, which is located next to your (Maniaplanet/Trackmania2020).exe",
            "----> Please DO NOT use a relative path like ../../Nadeo.ini",
            "----> Use something like C:/Users/<YOU>/Program Files/Trackmania/Nadeo.ini",
            "2. To get started, install the Nadeoimporter for your game",
            "3. Set your author name, this name will be displayed on ItemExchange (IX)",
        )

    def draw(self, context):

        blender_version     = bpy.app.version
        addon_version       = bl_info["version"]
        
        layout          = self.layout
        tm_props        = get_global_props()

        box = layout.box()
        box.separator(factor=0)
        row = box.row(align=True)
        row.scale_y=.5
        row.label(text=f"Blender: {blender_version}", icon=ICON_BLENDER)

        row = box.row(align=True)
        row.label(text=f"""Addon: {addon_version}""", icon_value=get_addon_icon("BLENDERMANIA"))
        row.operator("view3d.tm_checkfornewaddonrelease",   text="", icon=ICON_UPDATE)
        row.operator("view3d.tm_debug_all",                 text="", icon=ICON_DEBUG)
        

        if AddonUpdate.new_addon_available:

            col = box.column(align=True)
            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = tm_props.CB_addonUpdateDLshow is False and not AddonUpdate.current_blender_too_old
            row.operator("view3d.tm_updateaddonrestartblender", text=f"Update to {AddonUpdate.new_addon_version}", icon=ICON_UPDATE)
            row = col.row(align=True)
            # TODO change link
            row.operator("view3d.tm_open_url", text="Open changelog").url = URL_CHANGELOG
            dl_msg     = tm_props.ST_addonUpdateDLmsg
            show_panel = tm_props.CB_addonUpdateDLshow

            if show_panel:
                row = col.row(align=True)
                row.alert = "error" in dl_msg.lower()
                row.prop(tm_props, "NU_addonUpdateDLProgress", text=f"{dl_msg}" if dl_msg else "Download progress")

            if AddonUpdate.current_blender_too_old:
                row = col.row()
                row.alert = True
                row.label(text="Your blender is too old!")
                row = col.row()
                row.scale_y = 1.5
                row.operator("view3d.tm_open_url", 
                             text=f"Download newer Blender",   
                             icon=ICON_ERROR
                ).url = URL_BLENDER_DOWNLOAD
                

        col = box.column(align=True)
        row = col.row(align=True)
        row.operator("view3d.tm_open_url", text="",icon_value=get_addon_icon("GITHUB")).url = URL_GITHUB
        row.operator("view3d.tm_open_url", text="",icon_value=get_addon_icon("DISCORD")).url = URL_DISCORD
        row.operator("view3d.tm_open_url", text="Open Wiki").url = URL_DOCUMENTATION
        
        col = box.column(align=True)
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
    bl_label = "Blender settings"
    bl_idname = "TM_PT_Settings_BlenderRelated"
    bl_parent_id = "TM_PT_Settings"

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()

        row_main  = layout.row(align=True)
        col_left  = row_main.column(align=True)
        col_left.scale_x = 2.5
        col_right = row_main.column(align=True)

        row = col_left.row()
        row.label(text="Snap", icon=ICON_SNAP)
        row = col_right.row()
        row.prop(tm_props, "LI_blenderGridSize", expand=True)
        row = col_left.row()
        row.label(text="Grid", icon=ICON_GRID)
        row = col_right.row()
        row.prop(tm_props, "LI_blenderGridSizeDivision", expand=True)

        row = col_left.row()
        row.label(text="Start", icon=ICON_VISIBLE)
        row = col_right.row()
        row.prop(tm_props, "LI_blenderClipStart", expand=True)
        row = col_left.row()
        row.label(text="End", icon=ICON_HIDDEN)
        row = col_right.row()
        row.prop(tm_props, "LI_blenderClipEnd", expand=True)

        row = layout.row()
        row.prop(tm_props, "CB_map_use_grid_helper", text="Map Grid Helper", icon=ICON_GRID)



class TM_PT_Settings_NadeoImporter(Panel):
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "NadeoImporter"
    bl_idname = "TM_PT_Settings_NadeoImporter"
    bl_parent_id = "TM_PT_Settings"
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "NadeoImporter Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Configure the NadeoImporter",
            "-> The NadeoImporter is a program by Nadeo which will convert",
            "-> the exported FBX files to the game format GBX, this addon only",
            "-> prepares the necessesary things for this program",
            "The latest version of the NadeoImporter might have some issues, if so, try older versions!",
        )

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
        tm_props = get_global_props()

        row = layout.row(align=True)
        row.prop(tm_props, "CB_allow_complex_panel_drawing", text="Show extra panel infos")
        
        row = layout.row(align=True)
        row.prop(tm_props, "CB_compress_blendfile",  text="Save file compressed")
        
        # row = col.row(align=True)
        # row.label(text="Formatting")
        # row.prop(tm_props, "CB_xml_format_meshxml",     text="Mesh XML", toggle=True)
        # row.prop(tm_props, "CB_xml_format_itemxml",     text="Item XML", toggle=True)

        
