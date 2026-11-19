import textwrap

import bpy
from bpy.types import Panel
from ..ui.drawers.bitmap import draw_bitmap
from ..properties.AssetProperties import ASSET_TYPES
from ..operators.OT_AssetLibrary import TM_OT_CreateMaterialAsset, TM_OT_ExportAssetLibrary, TM_OT_RemoveMaterialAsset, TM_OT_RenameMaterialAsset, TM_OT_ImportImage, TM_OT_CopyAssetErrors, TM_OT_OpenLibraryFolder

from ..utils.AssetLibraryFunctions import active_asset, all_assets, is_reference_record
from ..utils.AssetLibraryImporter import last_errors
from ..ui.widgets.progress import draw_task_status, get_state, is_running
from ..ui.widgets.asset_picker import draw_asset_field


def _wrapped_labels(layout, text, width=48):
    for line in text.splitlines() or [""]:
        for chunk in textwrap.wrap(line, width) or [""]:
            layout.label(text=chunk)


def draw_errors(layout, context):
    """Per-asset error list of the last export; hidden once the result is cleared or a run is active."""
    state = get_state(TM_OT_ExportAssetLibrary.bl_idname)
    if state.running or not state.message or not last_errors:
        return

    box = layout.box()
    row = box.row()
    row.label(text="Errors", icon="ERROR")
    row.operator(TM_OT_CopyAssetErrors.bl_idname, text="", icon="COPYDOWN")
    for name, message in last_errors:
        col = box.column(align=True)
        col.label(text=name, icon="MATERIAL")
        _wrapped_labels(col, message)

class GBXPanelBase:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TM Asset"



class TM_PT_AssetLibrary_Main(GBXPanelBase, Panel):
    bl_idname = "TM_PT_AssetLibrary_Main"
    bl_label = "TM Assets Library"

    def draw_default_assets(self, layout, scene):
        """all game bitmaps / images / tree texture sets as linkable assets: install a release or build from a pak extract"""
        from pathlib import Path
        from ..utils.DefaultAssetsLibrary import (get_default_assets_info, is_release_repository_configured,
                                                  DEFAULT_ASSETS_LIB_NAME, DEFAULT_ASSETS_BLEND)
        from ..operators.OT_AssetLibrary import DEFAULT_ASSETS_TASK_KEY, draw_update_check
        box = layout.box()
        box.label(text="Default Assets (game textures)")
        info = get_default_assets_info()
        col = box.column(align=True)
        if info:
            game = f", game {info['game_source']}" if info.get("game_source") else ""
            col.label(text=f"Version {info.get('version', '?')}{game}", icon="CHECKMARK")
            col.label(text=f"{info.get('bitmaps', '?')} bitmaps, {info.get('images', '?')} images, "
                           f"{info.get('texture_sets', '?')} texture sets in '{DEFAULT_ASSETS_LIB_NAME}'")
            row = col.row(align=True)
            row.operator("wm.open_mainfile", text="Open Library .blend", icon="FILE_BLEND").filepath =                 str(Path(info["path"]) / DEFAULT_ASSETS_BLEND)
            row.operator("wm.path_open", text="", icon="FILE_FOLDER").filepath = info["path"]
            gbx = info.get("exported")
            if gbx is not None and gbx < info.get("bitmaps", 0):
                col.label(text=f"{gbx}/{info.get('bitmaps')} Texture.Gbx exported: open the .blend, Export Asset Library",
                          icon="ERROR")
        else:
            col.label(text="Not installed", icon="INFO")

        row = box.row(align=True)
        row.scale_y = 1.3
        sub = row.row(align=True)
        sub.enabled = is_release_repository_configured()
        sub.operator("tm.install_default_assets", text="Update" if info else "Install", icon="IMPORT")
        row.operator("tm.check_asset_updates", text="", icon="FILE_REFRESH").library = "default"
        if not is_release_repository_configured():
            box.label(text="No release repository set (utils/Constants.py)", icon="ERROR")
        draw_update_check(box, "default")

        draw_task_status(box, DEFAULT_ASSETS_TASK_KEY)
        if is_running(DEFAULT_ASSETS_TASK_KEY):
            box.operator("tm.cancel_default_assets", icon="CANCEL")

        sub = box.box().column(align=True)
        sub.label(text="Build from game files")
        sub.prop(scene.tm_props, "ST_pakExtractPath", text="Pak Extract")
        row = sub.row(align=True)
        row.operator("tm.build_default_assets", text="Build", icon="ADD")
        row.operator("tm.package_default_assets", text="Package for Release", icon="PACKAGE")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator(TM_OT_OpenLibraryFolder.bl_idname, icon="FILE_FOLDER")

        box = layout.box()
        box.label(text="Settings")
        box.prop(scene, "tm_asset_copy_images")

        self.draw_default_assets(layout, scene)

        box = layout.box()
        box.label(text="Create")
        box.prop(scene, "tm_new_asset_name")
        # operator props are editable via the redo panel; expose type quickly:
        row = box.row(align=True)
        for ident, label, _ in ASSET_TYPES:
            o = row.operator(TM_OT_CreateMaterialAsset.bl_idname, text=label)
            o.asset_type = ident
            o.asset_name = scene.tm_new_asset_name

        layout.separator()
        layout.prop(scene, "tm_active_material", text="Active")

        row = layout.row()
        row.operator(TM_OT_RemoveMaterialAsset.bl_idname, text="Remove", icon="TRASH")


def draw_common(layout, mat):
    props = mat.tm_asset_properties
   

    row = layout.row(align=True)
    row.label(text=mat.name, icon="MATERIAL")
    row.operator(TM_OT_RenameMaterialAsset.bl_idname, text="", icon="GREASEPENCIL")

    if mat.library:
        layout.label(text="Linked (read-only)", icon="LINKED")
    col = layout.column()
    col.enabled = mat.library is None
    row = col.row(align=True)
    row.enabled = False
    img = getattr(props, "image", None)
    if img:
        if is_reference_record(img):  # shared original (e.g. _BlenderAssets), not a copy in this library
            row.label(text=f"{img.name} (shared, not copied)", icon="LINKED")
        else:
            row.label(text=img.name, icon="IMAGE_DATA")
    else:
        row.label(text="No image assigned", icon="ERROR")

    col.operator(TM_OT_ImportImage.bl_idname, icon="IMPORT")
    col.prop(props, "relative_path")
    #col.prop(props, "game_path")

class AssetLibrary_TypePanel(GBXPanelBase):
    asset_type = None
    
    @classmethod
    def poll(cls, context):
        mat = active_asset(context)
        return mat is not None and mat.tm_asset_properties.asset_type == cls.asset_type

    def draw(self, context):
        mat = active_asset(context)
        draw_common(self.layout, mat)
        self.draw_type(self.layout, mat.tm_asset_properties)

    def draw_type(self, layout, props):
        pass



class TM_PT_AssetLibrary_Bitmap(AssetLibrary_TypePanel, Panel):
    bl_idname = "TM_PT_AssetLibrary_Bitmap"
    bl_label = "Bitmap"
    asset_type = "BITMAP"

    def draw_type(self, layout, props):
        bmp = props.bitmap
        layout.label(text="Bitmap Settings")
        draw_bitmap(layout, bmp)

            

class TM_PT_AssetLibrary_Image(AssetLibrary_TypePanel, Panel):
    bl_idname = "TM_PT_AssetLibrary_Image"
    bl_label = "Image"
    asset_type = "IMAGE"

    def draw_type(self, layout, props):
        layout.label(text="Image Settings")
        #layout.prop(props, "img_note")



class TM_PT_AssetLibrary_TextureSet(AssetLibrary_TypePanel, Panel):
    bl_idname = "TM_PT_AssetLibrary_TextureSet"
    bl_label = "TextureSet"
    asset_type = "TEXTURESET"

    def draw(self, context):
        layout = self.layout
        mat = active_asset(context)
        row = layout.row(align=True)
        row.label(text=mat.name, icon="MATERIAL")
        row.operator(TM_OT_RenameMaterialAsset.bl_idname, text="", icon="GREASEPENCIL")
        if mat.library:
            layout.label(text="Linked (read-only)", icon="LINKED")
        col = layout.column()
        col.enabled = mat.library is None
        ts = mat.tm_asset_properties.texture_set
        row = col.row(align=True)
        row.prop(ts, "use_gameplay_effect", toggle=True)
        row = row.row(align=True)
        row.enabled = ts.use_gameplay_effect
        row.prop(ts, "gameplay_effect",text="")
        row = col.row(align=True)
        row.prop(ts, "use_surface_material", toggle=True)
        row = row.row(align=True)
        row.enabled = ts.use_surface_material
        row.prop(ts, "surface_material", text="")
        col.label(text="Images")
        for prop in ("color_image", "normal_image", "roughness_image"):
            draw_asset_field(col, ts, prop, "IMAGE", icon="IMAGE_DATA")
        col.label(text="Textures (optional)")
        for prop in ("color_texture", "normal_texture", "roughness_texture"):
            draw_asset_field(col, ts, prop, "BITMAP", icon="TEXTURE")


class TM_PT_AssetLibraryExport(GBXPanelBase, Panel):
    bl_idname = "TM_PT_AssetLibraryExport"
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"{len(all_assets())} asset(s) in this file")

        op = layout.operator(TM_OT_ExportAssetLibrary.bl_idname, text="Export Active", icon="EXPORT")
        op.only_active = True
        op = layout.operator(TM_OT_ExportAssetLibrary.bl_idname, text="Export All", icon="EXPORT")
        op.only_active = False

        draw_task_status(layout, TM_OT_ExportAssetLibrary.bl_idname)
        draw_errors(layout, context)





classes = (
    TM_PT_AssetLibrary_Main,
    TM_PT_AssetLibrary_Bitmap,
    TM_PT_AssetLibrary_Image,
    TM_PT_AssetLibrary_TextureSet,
    TM_PT_AssetLibraryExport,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)