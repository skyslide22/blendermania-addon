import textwrap

import bpy
from bpy.types import Panel
from ..ui.drawers.bitmap import draw_bitmap
from ..properties.AssetProperties import ASSET_TYPES
from ..operators.OT_AssetLibrary import TM_OT_CreateMaterialAsset, TM_OT_ExportAssetLibrary, TM_OT_RemoveMaterialAsset, TM_OT_RenameMaterialAsset, TM_OT_ImportImage, TM_OT_CopyAssetErrors, TM_OT_OpenLibraryFolder

from ..utils.AssetLibraryFunctions import active_asset, all_assets, is_reference_record, gbx_rel_path
from ..utils.AssetLibraryImporter import last_errors
from ..ui.widgets.progress import draw_task_status, get_state, is_running
from ..ui.widgets.asset_picker import draw_asset_field
from ..ui.drawers.custom_material import draw_custom_material, draw_texture_set


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

    @classmethod
    def poll(cls, context):
        # the whole tab only exists in files declared as asset library (Blendermania > Asset Library)
        from ..utils.AssetLibraries import is_declared
        return is_declared()



class TM_PT_AssetLibrary_Main(GBXPanelBase, Panel):
    bl_idname = "TM_PT_AssetLibrary_Main"
    bl_label = "TM Assets Library"

    def draw_header_preset(self, context):
        from .LibraryInstallUI import draw_info_button
        draw_info_button(self.layout, "TM Assets Library", (
            "Create and export your own Bitmap / Image / Texture Set assets",
            "",
            "IMPORTANT: assets are referenced by items via their exported files,",
            "-> the .blend with your assets must be saved INSIDE the Trackmania Items folder",
            "----> e.g. Items/_BlenderAssets/MyAssets/MyAssets.blend",
            "-> export them (Export > Export All) before exporting items that use them",
            "-> link (don't append) them into your item .blend files via the Asset Browser",
            "-> maps using such items need EmbedItems (github.com/AchimBunke/EmbedItems),",
            "----> the editor embeds only the item, not the textures it uses",
            "",
            "Default Assets: game textures ready to link (optional, rarely needed),",
            "-> installed in Blendermania > Asset Library",
            "",
            "This tab is shown because the file is declared as asset library",
            "-> Blendermania > Asset Library > This File",
        ))

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator(TM_OT_OpenLibraryFolder.bl_idname, icon="FILE_FOLDER")

        box = layout.box()
        box.label(text="Settings")
        box.prop(scene, "tm_asset_copy_images")


class TM_PT_AssetLibrary_Create(GBXPanelBase, Panel):
    """own assets of this .blend: create, pick the active one, remove"""
    bl_idname = "TM_PT_AssetLibrary_Create"
    bl_label = "Create Asset"

    def draw_header(self, context):
        self.layout.label(icon="ADD")

    def draw(self, context):
        from .LibraryInstallUI import draw_custom_assets_location_warning
        layout = self.layout
        scene = context.scene

        draw_custom_assets_location_warning(layout)

        col = layout.column(align=True)
        col.prop(scene, "tm_new_asset_name", text="Name")
        # operator props are editable via the redo panel; expose type quickly:
        grid = col.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        grid.scale_y = 1.3
        for ident, label, _ in ASSET_TYPES:
            o = grid.operator(TM_OT_CreateMaterialAsset.bl_idname, text=label)
            o.asset_type = ident
            o.asset_name = scene.tm_new_asset_name

        layout.separator()
        row = layout.row(align=True)
        row.prop(scene, "tm_active_material", text="Active")
        row.operator(TM_OT_RemoveMaterialAsset.bl_idname, text="", icon="TRASH")


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
    draw_target(col, mat)
    #col.prop(props, "game_path")


def asset_target(mat) -> str:
    """library-relative file the asset stands for: the written gbx (bitmap) or the image file (image)"""
    props = mat.tm_asset_properties
    if props.asset_type == "IMAGE":
        img = props.image
        if img is None:
            return ""
        rel = img.tm_image_asset.rel_path
        return rel or bpy.path.abspath(img.filepath, library=img.library)
    try:
        return gbx_rel_path(mat)
    except ValueError as e:
        return str(e)


def draw_target(layout, mat) -> None:
    """read-only for now (renaming the asset updates a derived bitmap target)"""
    row = layout.row(align=True)
    split = row.split(factor=0.25, align=True)
    split.label(text="Target")
    target = asset_target(mat)
    sub = split.row(align=True)
    sub.enabled = False
    sub.label(text=target or "-", icon="FILE")
    if mat.tm_asset_properties.exported_path:
        row.label(text="", icon="CHECKMARK")

class AssetLibrary_TypePanel(GBXPanelBase):
    asset_type = None
    
    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
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
        from ..utils.ItemConfigBuilder import image_game_path
        mat = props.id_data
        if props.game_path or mat.library is None:
            layout.prop(props, "game_path")
        derived = image_game_path(mat)
        if derived and not props.game_path:
            row = layout.row()
            row.enabled = False
            row.label(text=f"Game path: {derived}", icon="WORLD")
        if derived:
            layout.label(text="Custom materials use the game texture (not shipped)", icon="INFO")



def _draw_container_header(layout, mat):
    """name + rename of a container asset (texture set / custom material); returns the editable column"""
    row = layout.row(align=True)
    row.label(text=mat.name, icon="MATERIAL")
    row.operator(TM_OT_RenameMaterialAsset.bl_idname, text="", icon="GREASEPENCIL")
    if mat.library:
        layout.label(text="Linked (read-only)", icon="LINKED")
    col = layout.column()
    col.enabled = mat.library is None
    return col


class TM_PT_AssetLibrary_TextureSet(AssetLibrary_TypePanel, Panel):
    bl_idname = "TM_PT_AssetLibrary_TextureSet"
    bl_label = "TextureSet"
    asset_type = "TEXTURESET"

    def draw(self, context):
        mat = active_asset(context)
        draw_texture_set(_draw_container_header(self.layout, mat), mat.tm_asset_properties.texture_set)


class TM_PT_AssetLibrary_CustomMaterial(AssetLibrary_TypePanel, Panel):
    bl_idname = "TM_PT_AssetLibrary_CustomMaterial"
    bl_label = "Custom Material"
    asset_type = "CUSTOMMATERIAL"

    def draw(self, context):
        mat = active_asset(context)
        draw_custom_material(_draw_container_header(self.layout, mat), mat.tm_asset_properties.custom_material)


class TM_PT_AssetLibraryExport(GBXPanelBase, Panel):
    bl_idname = "TM_PT_AssetLibraryExport"
    bl_label = "Export"

    def draw(self, context):
        from .LibraryInstallUI import draw_custom_assets_location_warning
        layout = self.layout
        draw_custom_assets_location_warning(layout)
        layout.label(text=f"{len(all_assets())} asset(s) in this file")

        op = layout.operator(TM_OT_ExportAssetLibrary.bl_idname, text="Export Active", icon="EXPORT")
        op.only_active = True
        op = layout.operator(TM_OT_ExportAssetLibrary.bl_idname, text="Export All", icon="EXPORT")
        op.only_active = False

        draw_task_status(layout, TM_OT_ExportAssetLibrary.bl_idname)
        draw_errors(layout, context)





classes = (
    TM_PT_AssetLibrary_Main,
    TM_PT_AssetLibrary_Create,
    TM_PT_AssetLibrary_Bitmap,
    TM_PT_AssetLibrary_Image,
    TM_PT_AssetLibrary_TextureSet,
    TM_PT_AssetLibrary_CustomMaterial,
    TM_PT_AssetLibraryExport,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)