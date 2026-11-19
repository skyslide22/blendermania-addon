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
    get_preview_object,
    import_image_file,
    is_reference_record,
    remove_asset_data,
    resolve_abs,
    spawn_preview_plane,
    sync_all_catalogs,
    sync_preview,
)
from ..properties.AssetProperties import ASSET_TYPES
from ..utils.AssetLibraryImporter import make_jobs, convert_assets_steps, convert_assets_steps_batched, apply_results, last_errors
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

        spawn_preview_plane(context, mat)

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
        obj = get_preview_object(mat)

        mat.name = self.new_name
        new = mat.name  # may differ if the name was taken

        # keep the default target path in sync, but don't touch custom paths
        if props.asset_type == "BITMAP" and props.relative_path == _default_bitmap_path(old):
            props.relative_path = _default_bitmap_path(new)

        # the image record is NOT renamed: it is shared and identified by its hash

        if obj:
            obj["gbx_preview_for"] = new
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
            img, created = import_image_file(self.filepath, copy=context.scene.tm_asset_copy_images)
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
            how = "Referenced" if is_reference_record(img) else "Imported"
            self.report({"INFO"}, f"{how if created else 'Reused existing'}: {rel}")
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
        assets = [a for a in assets if a is not None and a.library is None]  # linked assets belong to their library (e.g. default assets)
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
        jobs = yield from convert_assets_steps_batched(self._jobs)
        apply_results(jobs)

        for job in jobs:
            if job.convert_has_failed:
                last_errors.append((job.name, job.message))

        if last_errors:
            self.set_result("ERROR", f"{len(last_errors)} of {len(jobs)} asset(s) failed to export")
        else:
            self.set_result("INFO", f"Exported {len(jobs)} asset(s)")

    def task_finished(self, context):
        from ..utils.DefaultAssetsLibrary import DEFAULT_ASSETS_BLEND
        if Path(bpy.data.filepath).name != DEFAULT_ASSETS_BLEND:   # keeps its per-environment catalogs
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


DEFAULT_ASSETS_TASK_KEY = "tm.default_assets_job"


class _DefaultAssetsJob(ProgressTaskMixin):
    """runs one job of utils/DefaultAssetsLibrary in its thread and polls it: input stays free, the Cancel button stops it"""
    task_key = DEFAULT_ASSETS_TASK_KEY
    task_cancellable = False
    task_block_input = False
    task_wait_cursor = False
    task_timer_interval = 0.25
    task_status_hold = 10.0

    _job = None
    _sync = False

    @classmethod
    def poll(cls, context):
        from ..utils.DefaultAssetsLibrary import is_build_running
        return super().poll(context) and not is_build_running()

    def execute(self, context):
        if context.window is not None and not bpy.app.background:
            return ProgressTaskMixin.invoke(self, context, None)
        self._sync = True
        return ProgressTaskMixin.execute(self, context)

    def start_job(self, context):
        raise NotImplementedError

    def task_prepare(self, context):
        try:
            self._job = self.start_job(context)
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return False
        return True

    def task_steps(self, context):
        import time
        state = self._job
        while not state.done:
            with state.lock:
                progress, status = state.progress, state.status
            yield progress, status or "Starting..."
            if self._sync:
                time.sleep(0.2)
        if state.error:
            self.set_result("WARNING" if state.error == "Cancelled" else "ERROR", f"{self.task_title}: {state.error}")
            return
        from ..utils.DefaultAssetsLibrary import finish_build
        self.set_result("INFO", finish_build(state))
        _update_check_results.pop("default", None)

    def cancel(self, context):
        from ..utils.DefaultAssetsLibrary import cancel_build
        cancel_build()
        super().cancel(context)


class TM_OT_BuildDefaultAssets(_DefaultAssetsJob, Operator):
    bl_idname = "tm.build_default_assets"
    bl_label = "Build Default Assets"
    bl_description = ("Build the default asset library (all game bitmaps, images and tree texture sets) from the pak extract "
                      "into Items/_BlenderAssets/DefaultAssets and register it as asset library 'TM2020 Default Assets'")
    task_title = "Building default assets"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event, title="Build default assets?",
                                                     message="Takes about a minute and ~2.5 GB in Items/_BlenderAssets/DefaultAssets",
                                                     confirm_text="Build")

    def start_job(self, context):
        from ..utils.DefaultAssetsLibrary import start_build
        return start_build(context.scene.tm_props.ST_pakExtractPath)


class TM_OT_InstallDefaultAssets(_DefaultAssetsJob, Operator):
    bl_idname = "tm.install_default_assets"
    bl_label = "Install Default Assets"
    bl_description = "Download the newest default assets release and install it into Items/_BlenderAssets/DefaultAssets"
    task_title = "Installing default assets"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event, title="Install default assets?",
                                                     message="Downloads ~1.5 GB and replaces Items/_BlenderAssets/DefaultAssets",
                                                     confirm_text="Install")

    def start_job(self, context):
        from ..utils.DefaultAssetsLibrary import start_release_install
        return start_release_install()


class TM_OT_PackageDefaultAssets(_DefaultAssetsJob, Operator):
    bl_idname = "tm.package_default_assets"
    bl_label = "Package Default Assets for Release"
    bl_description = ("Write the built default assets as release files (zip + release.json) into a folder, "
                      "to upload them to the release repository")
    task_title = "Packaging default assets"

    directory: StringProperty(name="Output Folder", subtype="DIR_PATH")
    version: StringProperty(name="Version", default="1.0.0", description="Release version, the tag is default-assets-v<version>")

    def invoke(self, context, event):
        from ..utils.DefaultAssetsLibrary import get_default_assets_info
        info = get_default_assets_info() or {}
        if info.get("version") and not info["version"].startswith("local-"):
            self.version = info["version"]
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        self.layout.prop(self, "directory")
        self.layout.prop(self, "version")
        self.layout.label(text=f"Creates <folder>/default-assets-v{self.version}/ (upload all files of it)")

    def start_job(self, context):
        from ..utils.DefaultAssetsLibrary import start_package
        return start_package(self.directory, self.version)


class TM_OT_CancelDefaultAssets(Operator):
    bl_idname = "tm.cancel_default_assets"
    bl_label = "Cancel"
    bl_description = "Stop the running default assets job"

    def execute(self, context):
        from ..utils.DefaultAssetsLibrary import cancel_build
        cancel_build()
        return {"FINISHED"}


# results of TM_OT_CheckAssetUpdates for the panels: {"material": {...} | {"error": str}, "default": ...}
_update_check_results = {}


def get_update_check_result(key):
    return _update_check_results.get(key)


class TM_OT_CheckAssetUpdates(Operator):
    bl_idname = "tm.check_asset_updates"
    bl_label = "Check for Updates"
    bl_description = "Compare the installed asset libraries with their newest GitHub releases"

    library: EnumProperty(items=[("ALL", "All", ""), ("material", "Material library", ""), ("default", "Default assets", "")],
                          default="ALL", options={"SKIP_SAVE"})

    def execute(self, context):
        from ..utils import MaterialAssetsLibrary, DefaultAssetsLibrary
        checks = {"material": MaterialAssetsLibrary.check_for_update, "default": DefaultAssetsLibrary.check_for_update}
        for key, check in checks.items():
            if self.library not in ("ALL", key):
                continue
            try:
                _update_check_results[key] = check()
            except Exception as e:  # offline, rate limit, no repository configured
                _update_check_results[key] = {"error": str(e) or type(e).__name__}
        for area in context.screen.areas if context.screen else []:
            area.tag_redraw()
        return {"FINISHED"}


def draw_update_check(layout, key):
    """one status line under a library: newer version available / up to date / error"""
    result = get_update_check_result(key)
    if result is None:
        return
    if "error" in result:
        layout.label(text=f"Update check failed: {result['error']}", icon="ERROR")
    elif result.get("update"):
        layout.label(text=f"Update available: {result['latest']} (installed {result.get('installed') or '-'})", icon="IMPORT")
    elif result.get("latest"):
        layout.label(text=f"Up to date ({result['latest']})", icon="CHECKMARK")
    else:
        layout.label(text="No release found", icon="INFO")


from ..ui.widgets.asset_picker import TM_OT_PickAsset, TM_OT_AssignSelectedAsset

classes = (
    TM_OT_PickAsset,
    TM_OT_AssignSelectedAsset,
    TM_OT_BuildDefaultAssets,
    TM_OT_InstallDefaultAssets,
    TM_OT_PackageDefaultAssets,
    TM_OT_CancelDefaultAssets,
    TM_OT_CheckAssetUpdates,
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