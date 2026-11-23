"""Asset Library panel operators: declare the current file, import/edit/remove listed libraries, create a new one."""

from pathlib import Path

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ..utils import AssetLibraries as AL


def _redraw(context) -> None:
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {"VIEW_3D", "FILE_BROWSER"}:
                area.tag_redraw()


class TM_OT_DeclareAssetLibrary(Operator):
    bl_idname = "tm.declare_asset_library"
    bl_label = "Declare Asset Library"
    bl_description = ("Declare this .blend an asset library (shows the TM Asset tab). Saved files are saved "
                      "right away so the declaration sticks")
    bl_options = {"REGISTER", "UNDO"}

    declare: BoolProperty(default=True, options={"HIDDEN"})

    def execute(self, context):
        AL.set_declared(self.declare)
        if bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
        _redraw(context)
        if self.declare:
            self.report({"INFO"}, "This file is an asset library now (TM Asset tab)")
        else:
            self.report({"INFO"}, "This file is no asset library anymore")
        return {"FINISHED"}


class TM_OT_ImportAssetLibrary(Operator):
    bl_idname = "tm.import_asset_library"
    bl_label = "Import"
    bl_description = "Add this library to the Blender preferences (Asset Browser), import method Link"

    folder: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        if not Path(self.folder).is_dir():
            self.report({"ERROR"}, f"Folder not found: {self.folder}")
            return {"CANCELLED"}
        lib = AL.register_library(self.folder)
        _redraw(context)
        self.report({"INFO"}, f"Asset library '{lib.name}' added")
        return {"FINISHED"}


class TM_OT_RemoveAssetLibrary(Operator):
    bl_idname = "tm.remove_asset_library"
    bl_label = "Remove"
    bl_description = "Remove this library from the Blender preferences (files stay on disk, Import adds it again)"

    folder: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        if not AL.unregister_library(self.folder):
            self.report({"WARNING"}, "Library is not registered")
            return {"CANCELLED"}
        _redraw(context)
        self.report({"INFO"}, f"Asset library removed from the preferences: {Path(self.folder).name}")
        return {"FINISHED"}


class TM_OT_EditAssetLibrary(Operator):
    bl_idname = "tm.edit_asset_library"
    bl_label = "Edit"
    bl_description = "Open the library .blend"

    filepath: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return context.window_manager.invoke_confirm(
                self, event, title="Open Asset Library",
                message="The current file has unsaved changes, they will be lost.", confirm_text="Open")
        return self.execute(context)

    def execute(self, context):
        if not Path(self.filepath).is_file():
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}
        bpy.ops.wm.open_mainfile(filepath=self.filepath)
        return {"FINISHED"}


class TM_OT_CreateAssetLibrary(Operator):
    bl_idname = "tm.create_asset_library"
    bl_label = "Create New Custom Asset Library"
    bl_description = ("New empty .blend in Items/_BlenderAssets/<Name>/<Name>.blend, declared as asset library "
                      "and added to the preferences. The current file stays open (use Edit to open the new one)")

    name: StringProperty(name="Name", default="", options={"SKIP_SAVE"})

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360, confirm_text="Create")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")
        error = AL.validate_new_name(self.name) if self.name else None
        col = layout.column(align=True)
        col.scale_y = 0.8
        if error:
            col.alert = True
            col.label(text=error, icon="ERROR")
        elif self.name:
            col.label(text=f"_BlenderAssets/{self.name.strip()}/{self.name.strip()}.blend", icon="FILE_BLEND")

    def execute(self, context):
        error = AL.validate_new_name(self.name)
        if error:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}
        context.window.cursor_set("WAIT") if context.window else None
        try:
            blend, lib = AL.create_library(self.name)
        except (RuntimeError, OSError) as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        finally:
            context.window.cursor_set("DEFAULT") if context.window else None
        AL.scan_libraries(force=True)
        _redraw(context)
        self.report({"INFO"}, f"Asset library '{lib.name}' created: {blend} (Edit opens it)")
        return {"FINISHED"}


def embed_items_hint_hidden() -> bool:
    """EmbedItems hint of the export panel switched off for this .blend (any scene)"""
    return any(getattr(s, "tm_hide_embed_items_hint", False) for s in bpy.data.scenes)


class TM_OT_ToggleEmbedItemsHint(Operator):
    bl_idname = "tm.toggle_embed_items_hint"
    bl_label = "EmbedItems Hint"
    bl_description = "Show or hide the EmbedItems hint in the export panel for this .blend file"
    bl_options = {"INTERNAL", "UNDO"}

    hide: BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        if properties.hide:
            return "Don't show the EmbedItems hint again in this .blend file (the info button brings it back)"
        return "Show the EmbedItems hint again in this .blend file"

    def execute(self, context):
        for scene in bpy.data.scenes:
            scene.tm_hide_embed_items_hint = self.hide
        _redraw(context)
        return {"FINISHED"}


class TM_OT_RefreshAssetLibraries(Operator):
    bl_idname = "tm.refresh_asset_libraries"
    bl_label = "Refresh"
    bl_description = "Search Items/_BlenderAssets again for asset libraries"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        AL.scan_libraries(force=True)
        _redraw(context)
        return {"FINISHED"}


classes = (
    TM_OT_DeclareAssetLibrary,
    TM_OT_ImportAssetLibrary,
    TM_OT_RemoveAssetLibrary,
    TM_OT_EditAssetLibrary,
    TM_OT_CreateAssetLibrary,
    TM_OT_RefreshAssetLibraries,
    TM_OT_ToggleEmbedItemsHint,
)


def register():
    bpy.types.Scene.tm_hide_embed_items_hint = BoolProperty(
        name="Hide EmbedItems Hint", default=False,
        description="Don't show the EmbedItems hint in the export panel for this .blend file")
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tm_hide_embed_items_hint
