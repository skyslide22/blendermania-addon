"""Blendermania tab > Asset Library: this file's declaration, libraries in Items/_BlenderAssets, create a new one,
and the install boxes of the downloadable libraries (moved here from Settings)."""

from pathlib import Path

import bpy
from bpy.types import Panel

from ..ui.widgets.panels import ViewPanelMixin
from ..utils.Constants import *
from ..utils.Functions import is_selected_nadeoini_file_name_ok, is_game_trackmania2020, get_global_props
from ..utils import AssetLibraries as AL


ASSET_LIBRARY_INFO = (
    "Asset libraries are .blend files with assets you link into your item files.",
    "",
    "This file",
    "-> 'Declare as Asset Library' shows the TM Asset tab (create/export Bitmap, Image",
    "----> and Texture Set assets). Save the file inside Items/_BlenderAssets/<Name>/",
    "----> so items can reference the exported files and it appears in the list below",
    "",
    "Libraries in _BlenderAssets",
    "-> all declared libraries found in Items/_BlenderAssets",
    "-> Import: adds it to the Blender preferences (Asset Browser), import method Link",
    "-> Remove: removes it from the preferences, the files stay",
    "-> Edit: opens its .blend",
    "",
    "Create New Custom Asset Library",
    "-> new empty .blend in Items/_BlenderAssets/<Name>/, declared and imported",
    "----> the current file stays open, use Edit to open the new library",
    "",
    "Downloads",
    "-> addon textures / asset library, Material Library, Default Assets",
)


class TM_PT_AssetLibraries(ViewPanelMixin, Panel):
    view_id = "asset_libraries"
    view_label = "Asset Library"

    locals().update(PANEL_CLASS_COMMON_DEFAULT_PROPS)
    bl_label = "Asset Library"
    bl_idname = "TM_PT_AssetLibraries"
    bl_order = 60

    @classmethod
    def view_poll(cls, context):
        return is_selected_nadeoini_file_name_ok()

    def draw_header(self, context):
        self.layout.label(icon=ICON_ASSETS)

    def draw_header_preset(self, context):
        from .LibraryInstallUI import draw_info_button
        draw_info_button(self.layout, "Asset Library", ASSET_LIBRARY_INFO)

    def draw(self, context):
        layout = self.layout
        self.draw_this_file(layout)
        layout.separator()
        self.draw_library_list(layout)
        layout.separator()
        self.draw_downloads(layout, context)

    # --- this file ------------------------------------------------------------------------------
    def draw_this_file(self, layout) -> None:
        box = layout.box()
        col = box.column(align=True)
        col.label(text="This File", icon="FILE_BLEND")
        declared = AL.is_declared()
        if declared:
            col.label(text="Asset library (TM Asset tab shown)", icon=ICON_CHECKED)
            if not bpy.data.filepath:
                warn = col.column(align=True)
                warn.alert = True
                warn.label(text="Not saved yet", icon=ICON_ERROR)
            elif not AL.is_inside_assets_root(bpy.data.filepath):
                warn = col.column(align=True)
                warn.alert = True
                warn.label(text="Not inside Items/_BlenderAssets", icon=ICON_ERROR)
                warn.label(text="-> items can't use its exported assets")
            col.separator()
            col.operator("tm.declare_asset_library", text="Undeclare", icon="X").declare = False
        else:
            row = col.row(align=True)
            row.scale_y = 1.3
            row.operator("tm.declare_asset_library", text="Declare as Asset Library", icon=ICON_ASSETS).declare = True

    # --- libraries in _BlenderAssets --------------------------------------------------------------
    def draw_library_list(self, layout) -> None:
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="Libraries in _BlenderAssets", icon="ASSET_MANAGER")
        row.operator("tm.refresh_asset_libraries", text="", icon="FILE_REFRESH")
        root = AL.assets_root()
        if root is not None:
            row.operator("view3d.tm_open_folder", text="", icon=ICON_FOLDER).folder = str(root)

        if AL.is_migration_running():
            col.label(text="Moving the addon asset library...", icon="SORTTIME")

        libraries = AL.scan_libraries()
        if not libraries:
            sub = col.column(align=True)
            sub.scale_y = 0.8
            sub.label(text="No asset libraries found", icon=ICON_INFO)
        current = AL._norm(bpy.data.filepath) if bpy.data.filepath else None
        for entry in libraries:
            lib_box = col.box()
            lib_col = lib_box.column(align=True)
            registered = AL.find_registered(entry["path"])
            row = lib_col.row(align=True)
            row.label(text=entry["name"], icon="ASSET_MANAGER")
            sub = row.row(align=True)
            sub.alignment = "RIGHT"
            sub.label(text="imported" if registered else "not imported", icon=ICON_CHECKED if registered else "BLANK1")
            row = lib_col.row(align=True)
            if registered:
                row.operator("tm.remove_asset_library", text="Remove", icon="REMOVE").folder = entry["path"]
            else:
                row.operator("tm.import_asset_library", text="Import", icon="IMPORT").folder = entry["path"]
            for blend in entry["blends"]:
                path = str(Path(entry["path"]) / blend)
                is_open = current == AL._norm(path)
                if len(entry["blends"]) == 1:
                    sub = row.row(align=True)
                else:
                    sub = lib_col.row(align=True)
                    sub.label(text=blend, icon="FILE_BLEND")
                sub.enabled = not is_open
                sub.operator("tm.edit_asset_library", text="Open" if is_open else "Edit",
                             icon="GREASEPENCIL").filepath = path

        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.3
        row.operator("tm.create_asset_library", text="Create New Custom Asset Library", icon="ADD")

    # --- downloads (moved from Settings > Asset Libraries) ---------------------------------------
    def draw_downloads(self, layout, context) -> None:
        from .LibraryInstallUI import draw_addon_textures, draw_material_library, draw_default_assets
        tm_props = get_global_props()
        col = layout.column(align=True)
        col.label(text="Downloads", icon="IMPORT")
        if is_game_trackmania2020():
            if PROMOTE_MATERIAL_ASSETS_LIBRARY:
                draw_material_library(layout, tm_props)
                draw_addon_textures(layout, tm_props)
            else:
                draw_addon_textures(layout, tm_props)
                draw_material_library(layout, tm_props)
            draw_default_assets(layout, context.scene, show_build=SHOW_DEFAULT_ASSETS_BUILD)
        else:
            draw_addon_textures(layout, tm_props)
        layout.separator()
        # shared .blend files: relink libraries/textures to this PC's install, list what is missing
        layout.operator("tm.check_external_data", icon="LIBRARY_DATA_BROKEN")
