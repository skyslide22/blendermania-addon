from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from ..utils.AssetLibraryFunctions import (
    DEFAULT_REL_BITMAP_DIR,
    GBX_EXT,
    active_asset,
    all_assets,
    assign_image,
    blend_dir,
    collect_export_data,
    gbx_rel_path,
    import_image_file,
    remove_asset_data,
    resolve_abs,
    spawn_preview_plane,
    sync_all_catalogs,
    sync_preview,
)
from ..properties.AssetProperties import ASSET_TYPES
from ..utils.AssetLibraryImporter import make_jobs, convert_assets_steps, last_errors
from ..ui.widgets.progress import ProgressTaskMixin
from ..properties.PropertyIdentifiers import AssetProp


def _default_bitmap_path(name):
    return f"{DEFAULT_REL_BITMAP_DIR}/{name}{GBX_EXT['BITMAP']}"


class TM_OT_CreateMaterialAsset(Operator):
    bl_idname = "tm.create_material_asset"
    bl_label = "Create Asset"
    bl_description = "Create a material for this asset type and spawn a preview plane"
    bl_options = {"REGISTER", "UNDO"}

    asset_name: StringProperty(name="Name", default="NewAsset")
    asset_type: EnumProperty(name="Type", items=ASSET_TYPES, default="BITMAP")
    mark_as_asset: BoolProperty(name="Mark as Blender Asset", default=True)

    def execute(self, context):
        mat = bpy.data.materials.new(self.asset_name)

        props = mat.tm_asset_properties
        props.is_asset = True
        props.asset_type = self.asset_type
        sync_preview(mat)       # after the type is set, so the preview matches it

        # type-dependent defaults -----------------------------------------
        if self.asset_type == "BITMAP":
            setattr(props, AssetProp.RELATIVE_PATH, _default_bitmap_path(mat.name))
        # IMAGE: no stored path. The dds location comes from the image record
        # (props.image.tm_image_asset.rel_path); an empty relative_path means "derived".
        # ---------------------------------------------------------------

        if self.mark_as_asset:
            mat.asset_mark()
            mat.asset_generate_preview()

        props.preview_object = spawn_preview_plane(context, mat)

        context.scene.tm_active_material = mat
        self.report({"INFO"}, f"Created {self.asset_type} asset '{mat.name}'")
        return {"FINISHED"}


class TM_OT_RenameMaterialAsset(Operator):
    bl_idname = "tm.rename_material_asset"
    bl_label = "Rename Asset"
    bl_options = {"REGISTER", "UNDO"}

    new_name: StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        mat = active_asset(context)
        return mat is not None and mat.library is None

    def invoke(self, context, event):
        self.new_name = active_asset(context).name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        mat = active_asset(context)
        props = mat.tm_asset_properties
        old = mat.name

        mat.name = self.new_name
        new = mat.name  # may differ if the name was taken

        # keep the default target path in sync, but don't touch custom paths
        if props.asset_type == "BITMAP" and props.relative_path == _default_bitmap_path(old):
            props.relative_path = _default_bitmap_path(new)

        # the image record is NOT renamed: it is shared and identified by its hash

        obj = props.preview_object
        if obj:
            obj.name = f"Preview_{new}"
            if obj.data:
                obj.data.name = f"{new}_mesh"
        return {"FINISHED"}


class TM_OT_RemoveMaterialAsset(Operator):
    bl_idname = "tm.remove_material_asset"
    bl_label = "Remove Asset"
    bl_options = {"REGISTER", "UNDO"}

    delete_files: BoolProperty(
        name="Also delete files",
        description="Delete this asset's gbx next to the .blend, and image files in the "
                    "store that no other asset uses anymore",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        mat = active_asset(context)
        return mat is not None and mat.library is None   # linked data can't be removed

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)   # confirm + option

    def execute(self, context):
        mat = active_asset(context)
        name = mat.name

        # resolve the gbx path BEFORE the material is gone
        gbx_file = None
        if self.delete_files and bpy.data.filepath:
            try:
                gbx_file = blend_dir(mat) / gbx_rel_path(mat)
            except (RuntimeError, ValueError):
                gbx_file = None

        context.scene.tm_active_material = None
        purged = remove_asset_data(mat, delete_files=self.delete_files)

        if gbx_file is not None and gbx_file.is_file():
            gbx_file.unlink()

        self.report({"INFO"}, f"Removed asset '{name}' ({purged} unused image(s) purged)")
        return {"FINISHED"}


class TM_OT_ImportImage(Operator, ImportHelper):
    bl_idname = "tm.import_image"
    bl_label = "Import Image"
    bl_description = ("Pick a .dds file for the active asset. It is copied into the library "
                      "store once (identical files are reused) and assigned")

    filename_ext = ".dds"
    filter_glob: StringProperty(default="*.dds", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        mat = active_asset(context)
        return mat is not None and mat.library is None

    def execute(self, context):
        mat = active_asset(context)
        props = mat.tm_asset_properties
        props.exported_path = ""
        try:
            img, created = import_image_file(self.filepath)
        except (RuntimeError, FileNotFoundError, OSError) as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        props.image = img           # update callback re-syncs the preview
        assign_image(mat, img)      # explicit, in case the value did not change

        if mat.asset_data:
            mat.asset_generate_preview()

        rel = img.tm_image_asset.rel_path
        if img.source == "GENERATED":
            self.report({"WARNING"}, f"Imported {rel}, but Blender could not load a preview of it")
        else:
            self.report({"INFO"}, f"{'Imported' if created else 'Reused existing'}: {rel}")
        props.exported_path = str(blend_dir() / rel)
        return {"FINISHED"}


class TM_OT_ExportAssetLibrary(ProgressTaskMixin, Operator):
    bl_idname = "tm.export_asset_library"
    bl_label = "Export Asset Library"
    bl_description = "Validate images, then run the exporter for the selected assets"

    task_title = "Exporting assets"
    task_cancellable = False   # dotnet processes can't be aborted safely

    only_active: BoolProperty(name="Only Active", default=False, options={"HIDDEN"})

    def task_prepare(self, context):
        last_errors.clear()
        if not bpy.data.filepath:
            self.report({"ERROR"}, "Save the .blend first (paths are relative to it)")
            return False

        base_dir = blend_dir()
        assets = [active_asset(context)] if self.only_active else all_assets()
        assets = [a for a in assets if a is not None]
        if not assets:
            self.report({"WARNING"}, "No assets to export")
            return False

        # validate images / output paths before anything runs
        # (verify=False skips re-hashing every dds; set True to detect external edits)
        problems = collect_export_data(assets, {}, verify=False)["problems"]
        if problems:
            last_errors.extend(("validation", p) for p in problems)
            self.report({"ERROR"}, f"{len(problems)} problem(s) found, nothing exported")
            return False

        # NOTE: make_jobs / convert_assets_steps (AssetLibraryImporter) must read the
        # image from props.image via resolve_image_file(), not from a source path.
        self._jobs = make_jobs(assets, base_dir)   # snapshot bpy data now
        return True

    def task_steps(self, context):
        jobs = yield from convert_assets_steps(self._jobs)

        for job in jobs:
            if job.convert_has_failed:
                last_errors.append((job.name, job.message))

        if last_errors:
            self.set_result("ERROR", f"{len(last_errors)} of {len(jobs)} asset(s) failed to export")
        else:
            self.set_result("INFO", f"Exported {len(jobs)} asset(s)")

    def task_finished(self, context):
        sync_all_catalogs(blend_dir())

class TM_OT_CopyAssetErrors(Operator):
    bl_idname = "tm.copy_asset_errors"
    bl_label = "Copy Errors"
    bl_description = "Copy the last asset export errors to the clipboard"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return bool(last_errors)

    def execute(self, context):
        context.window_manager.clipboard = "\n\n".join(f"[{n}]\n{m}" for n, m in last_errors)
        self.report({"INFO"}, "Errors copied to clipboard")
        return {"FINISHED"}


class TM_OT_OpenLibraryFolder(Operator):
    bl_idname = "tm.open_library_folder"
    bl_label = "Open Library Folder"
    bl_description = "Open the folder of the .blend that holds the active asset (or the current .blend)"

    def execute(self, context):
        try:
            folder = blend_dir(active_asset(context))   # linked assets resolve to their library .blend
        except RuntimeError:
            self.report({"ERROR"}, "Save the .blend first")
            return {"CANCELLED"}

        if not folder.is_dir():
            self.report({"ERROR"}, f"Folder does not exist: {folder}")
            return {"CANCELLED"}

        bpy.ops.wm.path_open(filepath=str(folder))
        return {"FINISHED"}


classes = (
    TM_OT_CreateMaterialAsset,
    TM_OT_RenameMaterialAsset,
    TM_OT_RemoveMaterialAsset,
    TM_OT_ImportImage,
    TM_OT_ExportAssetLibrary,
    TM_OT_CopyAssetErrors,
    TM_OT_OpenLibraryFolder,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)