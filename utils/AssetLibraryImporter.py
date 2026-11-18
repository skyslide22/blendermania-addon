import threading
from pathlib import Path

import bpy
from ..properties.AssetProperties import bitmap_to_config
from ..utils.Dotnet import run_convert_asset

from .AssetLibraryFunctions import gbx_rel_path, resolve_image_file


# (asset name, error message) of the last export run, shown in the panel
last_errors: list[tuple[str, str]] = []


class AssetConvert(threading.Thread):
    """Converts one asset material (tm_asset_properties) to gbx via the dotnet AssetConverter.
    All bpy data is read in __init__ (main thread); run() only touches plain python values.

    The dds is NOT copied here anymore: it already lives once in the library's image store
    (props.image.tm_image_asset.rel_path), shared by every asset that uses it."""

    def __init__(self, mat: bpy.types.Material, base_dir: Path) -> None:
        super().__init__()
        props = mat.tm_asset_properties

        self.mat = mat                                  # only touched on the main thread
        self.exported_path = ""
        self.name = mat.name
        self.asset_type = props.asset_type
        self.image_path = ""
        self.gbx_path = ""
        self.bitmap_config = None
        self._init_error = ""

        img = props.image
        if self.asset_type == "TEXTURESET":
            pass                                        # container only: nothing to resolve
        elif img is None or not img.tm_image_asset.is_managed:
            self._init_error = "no image assigned"
        else:
            try:
                self.image_path = str(resolve_image_file(img))
                rel = gbx_rel_path(mat)                 # "" for asset types without a gbx
                self.gbx_path = str((base_dir / rel).resolve()) if rel else ""
            except (RuntimeError, ValueError) as e:
                self._init_error = str(e)

        if self.asset_type == "BITMAP":
            self.bitmap_config = bitmap_to_config(props.bitmap)   # noqa: F821 (your import)

        self.convert_has_failed = False
        self.message = ""

    def validate(self) -> str:
        if self.asset_type == "TEXTURESET":
            return ""
        if self._init_error:
            return self._init_error
        if not Path(self.image_path).is_file():
            return f"image file missing: {self.image_path}"
        if self.asset_type == "BITMAP" and not self.gbx_path:
            return "missing target path"
        return ""

    def run(self) -> None:
        error = self.validate()
        if error:
            self.convert_has_failed = True
            self.message = error
            return

        if self.asset_type in ("IMAGE", "TEXTURESET"):
            # IMAGE: the dds is already in the store. TEXTURESET: pure reference container.
            if self.asset_type == "IMAGE":
                self.exported_path = self.image_path
            return

        try:
            Path(self.gbx_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.convert_has_failed = True
            self.message = f"could not create output folder: {e}"
            return

        if self.bitmap_config is not None:
            self.bitmap_config["ImageFile"] = self.image_path

        res = run_convert_asset(self.asset_type, self.gbx_path, self.bitmap_config) 
        self.convert_has_failed = not res.success
        if res.success:
            self.exported_path = self.gbx_path
        self.message = res.message


def apply_results(jobs: list[AssetConvert]) -> None:
    """Main thread: store the final output path on each asset (empty when it failed)."""
    for job in jobs:
        props = job.mat.tm_asset_properties
        props.exported_path = "" if job.convert_has_failed else job.exported_path


def make_jobs(materials: list[bpy.types.Material], base_dir: Path) -> list[AssetConvert]:
    """Snapshot the materials into jobs (main thread only)."""
    return [AssetConvert(m, base_dir) for m in materials]


def convert_assets_steps(jobs: list[AssetConvert]):
    """Generator for ProgressTaskMixin.task_steps: starts all jobs, yields progress until done.
    Returns the finished jobs."""
    for job in jobs:
        job.start()

    total = len(jobs)
    while True:
        running = [j for j in jobs if j.is_alive()]
        done = total - len(running)
        names = ", ".join(j.name for j in running[:3]) + ("..." if len(running) > 3 else "")
        yield done / total, f"{done}/{total} converted" + (f" - {names}" if running else "")
        if not running:
            return jobs
        running[0].join(0.02)