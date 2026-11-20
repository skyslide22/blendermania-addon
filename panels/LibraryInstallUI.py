"""Install/update UI of the two downloadable asset libraries, shared by Settings > Asset Libraries,
Textures > Install & Update and the TM Asset tab.

- TM2020 Material Assets Library: needed for (almost) every export, materials + shaders + MaterialLib.txt.
- TM2020 Default Assets: game bitmaps/images/tree texture sets, only needed for custom texture sets,
  vegetation and particle effects that should reuse game textures.
"""

import os

import bpy

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox
from ..ui.widgets.progress import draw_task_status, is_running
from ..utils.Constants import *


MATERIAL_LIBRARY_INFO = (
    "TM2020 Material Assets Library (community project by BigthirstyTM)",
    "",
    "WHAT: all 847 Nadeo game materials as Blender materials with game-like shaders,",
    "----> textures and the MaterialLib.txt (list of materials the converter knows)",
    "WHY: the export needs the MaterialLib.txt to link your materials to game materials,",
    "----> the material panel copies the library shader so the viewport looks like the game",
    "WHEN: install it once before your first export, update when a new version is out",
    "----> used EVERY time you create/update a material or export an item",
    "",
    "Where: <Trackmania>/Items/_BlenderAssets/MaterialAssetsLibrary",
    "-> registered in the Asset Browser as 'TM2020 Material Assets Library'",
    "-> the Material Lib setting is switched to its MaterialLib.txt",
    "Editions: 'materials-only' (~2.3 GB) or 'complete' (~3.3 GB, extra textures)",
    "Nothing of it is embedded in maps: items link the game materials",
)

DEFAULT_ASSETS_INFO = (
    "TM2020 Default Assets",
    "",
    "WHAT: game textures as linkable assets: Bitmaps (Texture.Gbx), Images (.dds)",
    "----> and Texture Sets (from the game's trees)",
    "WHY: reuse game textures for custom texture sets, vegetation (veget trees)",
    "----> and particle effects without extracting the game files yourself",
    "WHEN: RARELY needed, only if you want to use game textures in such features",
    "----> normal items with game materials do NOT need it",
    "",
    "Where: <Trackmania>/Items/_BlenderAssets/DefaultAssets",
    "-> registered in the Asset Browser as 'TM2020 Default Assets' (import method Link)",
    "After installing: open TM2020_DefaultAssets.blend once and run",
    "----> TM Asset > Export > Export All, this writes the Texture.Gbx files",
    "----> (releases ship no .gbx), without them the assets are not usable in game",
    "Referenced textures are copies under Items, they ARE embedded in maps (size!)",
    "",
    "Own (custom) assets: create them in a .blend that is saved INSIDE the",
    "Trackmania Items folder (e.g. Items/_BlenderAssets/MyAssets/MyAssets.blend),",
    "export them there and link them into your item files. Assets in a .blend",
    "outside the Items folder (or unsaved) can't be referenced by items.",
)


def draw_info_button(layout, title: str, lines) -> None:
    op = layout.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
    op.link = ""
    op.title = title
    op.infos = TM_OT_Settings_OpenMessageBox.get_text(*lines)


def _items_folder() -> str | None:
    from ..utils.Functions import get_game_doc_path_items
    try:
        path = get_game_doc_path_items()
    except Exception:
        return None
    return os.path.normcase(os.path.realpath(path)) if path and os.path.isdir(path) else None


def is_blend_in_items_folder(filepath: str | None = None) -> bool:
    """assets are referenced by gbx path, so only a saved .blend inside the game Items folder can provide them"""
    filepath = bpy.data.filepath if filepath is None else filepath
    items = _items_folder()
    if not filepath or not items:
        return False
    blend = os.path.normcase(os.path.realpath(filepath))
    return blend.startswith(items.rstrip("\\/") + os.sep)


def draw_custom_assets_location_warning(layout) -> None:
    """own assets are only usable from a saved .blend inside Trackmania/Items"""
    if is_blend_in_items_folder():
        return
    box = layout.box()
    col = box.column(align=True)
    col.alert = True
    if not bpy.data.filepath:
        col.label(text="This file is not saved", icon=ICON_ERROR)
    else:
        col.label(text="This file is not inside the Trackmania Items folder", icon=ICON_ERROR)
    col.label(text="Assets created here can't be used by items:")
    col.label(text="save the .blend inside Trackmania/Items first")
    col.label(text="(e.g. Items/_BlenderAssets/MyAssets/MyAssets.blend)")


def draw_material_library(layout, tm_props, compact: bool = False) -> None:
    """install / update box of the TM2020 Material Assets Library"""
    from ..utils.MaterialAssetsLibrary import get_installed_library_info
    from ..operators.OT_AssetLibrary import draw_update_check

    info = get_installed_library_info()
    box = layout.box()
    col = box.column(align=True)
    row = col.row(align=True)
    row.label(text="Material Library", icon=ICON_MATERIAL)
    row.operator("view3d.tm_open_url", text="", icon=ICON_WEBSITE).url = MATERIAL_ASSETS_LIB_URL
    draw_info_button(row, "Material Library", MATERIAL_LIBRARY_INFO)

    sub = col.column(align=True)
    sub.scale_y = 0.8
    sub.label(text="Game materials + shaders")
    sub.label(text="Needed for every export", icon=ICON_INFO)

    col.separator()
    if info:
        col.label(text=f"Installed: {info.get('edition', '?')} {info.get('version', '?')} "
                       f"({info.get('materials', '?')} materials)", icon=ICON_CHECKED)
        if not compact:
            row = col.row(align=True)
            row.operator("view3d.tm_open_folder", text="Open Folder", icon=ICON_FOLDER).folder = info["path"]
            row.operator("tm.check_asset_updates", text="Check for Updates", icon="FILE_REFRESH").library = "material"
            draw_update_check(col, "material")
    else:
        row = col.row()
        row.alert = True
        row.label(text="Not installed (needed!)", icon=ICON_ERROR)

    col.separator()
    row = col.row(align=True)
    row.prop(tm_props, "LI_DL_MaterialAssetsEdition", expand=True)
    row = col.row(align=True)
    row.scale_y = 1.4
    row.operator("view3d.tm_install_material_assets_library",
                 text="Update / Reinstall Material Library" if info else "Install Material Library", icon=ICON_ASSETS)

    key = "view3d.tm_install_material_assets_library"
    draw_task_status(col, key)
    if is_running(key):
        col.operator("view3d.tm_cancel_material_assets_library", icon="CANCEL")


def draw_default_assets(layout, scene, show_build: bool = False) -> None:
    """install / update box of the TM2020 Default Assets (+ build from a pak extract for maintainers)"""
    from pathlib import Path
    from ..utils.DefaultAssetsLibrary import (get_default_assets_info, is_release_repository_configured,
                                              DEFAULT_ASSETS_LIB_NAME, DEFAULT_ASSETS_BLEND)
    from ..operators.OT_AssetLibrary import DEFAULT_ASSETS_TASK_KEY, draw_update_check

    info = get_default_assets_info()
    box = layout.box()
    col = box.column(align=True)
    row = col.row(align=True)
    row.label(text="Default Assets (optional)", icon=ICON_TEXTURE)
    draw_info_button(row, "Default Assets", DEFAULT_ASSETS_INFO)

    sub = col.column(align=True)
    sub.scale_y = 0.8
    sub.label(text="Game textures as assets")
    sub.label(text="Rarely needed (trees, fx)", icon=ICON_INFO)

    col.separator()
    if info:
        game = f", game {info['game_source']}" if info.get("game_source") else ""
        col.label(text=f"Installed: {info.get('version', '?')}{game}", icon=ICON_CHECKED)
        col.label(text=f"{info.get('bitmaps', '?')} bitmaps, {info.get('images', '?')} images, "
                       f"{info.get('texture_sets', '?')} texture sets")
        blend = str(Path(info["path"]) / DEFAULT_ASSETS_BLEND)
        row = col.row(align=True)
        row.operator("wm.open_mainfile", text="Open Library .blend", icon="FILE_BLEND").filepath = blend
        row.operator("wm.path_open", text="", icon="FILE_FOLDER").filepath = info["path"]

        gbx = info.get("exported")
        bitmaps = info.get("bitmaps", 0) or 0
        if gbx is not None and bitmaps and gbx < bitmaps and not is_running(DEFAULT_ASSETS_TASK_KEY):
            warn = col.box().column(align=True)
            warn.alert = True
            if gbx == 0:
                warn.label(text="Not exported yet - not usable in game!", icon=ICON_ERROR)
            else:
                warn.label(text=f"Only {gbx}/{bitmaps} Texture.Gbx exported!", icon=ICON_ERROR)
            warn.label(text="Open the library .blend, then")
            warn.label(text="TM Asset > Export > Export All")
            if os.path.normcase(bpy.data.filepath) == os.path.normcase(blend):
                warn.label(text="(this is the library .blend)", icon=ICON_INFO)
    else:
        col.label(text="Not installed (optional)", icon=ICON_INFO)

    col.separator()
    row = col.row(align=True)
    row.scale_y = 1.2
    sub = row.row(align=True)
    sub.enabled = is_release_repository_configured()
    sub.operator("tm.install_default_assets",
                 text="Update Default Assets" if info else "Install Default Assets", icon="IMPORT")
    row.operator("tm.check_asset_updates", text="", icon="FILE_REFRESH").library = "default"
    if not is_release_repository_configured():
        col.label(text="No release repository set (utils/Constants.py)", icon=ICON_ERROR)
    draw_update_check(col, "default")

    draw_task_status(col, DEFAULT_ASSETS_TASK_KEY)
    if is_running(DEFAULT_ASSETS_TASK_KEY):
        col.operator("tm.cancel_default_assets", icon="CANCEL")

    if show_build:
        sub = box.box().column(align=True)
        sub.label(text="Build from game files")
        sub.prop(scene.tm_props, "ST_pakExtractPath", text="Pak Extract")
        row = sub.row(align=True)
        row.operator("tm.build_default_assets", text="Build", icon="ADD")
        row.operator("tm.package_default_assets", text="Package for Release", icon="PACKAGE")
