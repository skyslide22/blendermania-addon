import threading
from pathlib import Path

import bpy
from ..properties.AssetProperties import CONTAINER_ASSET_TYPES, bitmap_to_config
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
        if self.asset_type in CONTAINER_ASSET_TYPES:
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
        if self.asset_type in CONTAINER_ASSET_TYPES:
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

        if self.asset_type == "IMAGE" or self.asset_type in CONTAINER_ASSET_TYPES:
            # IMAGE: the dds is already in the store. TEXTURESET/CUSTOMMATERIAL: pure reference containers.
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
    """Main thread: store the final output path on each asset (empty when it failed).
    Not in the default asset library: it is distributed, absolute paths of this machine don't belong into it
    (its paths are always derived from where the library is installed)."""
    from .DefaultAssetsLibrary import DEFAULT_ASSETS_BLEND
    keep = Path(bpy.data.filepath).name != DEFAULT_ASSETS_BLEND
    for job in jobs:
        props = job.mat.tm_asset_properties
        props.exported_path = job.exported_path if keep and not job.convert_has_failed else ""


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

# --------------------------------------------------------------------------
# batch conversion: one blendermania-dotnet process for many bitmaps (e.g. the default asset library, ~700 bitmaps)
# --------------------------------------------------------------------------
BATCH_MIN_BITMAPS = 4


def convert_assets_steps_batched(jobs: list[AssetConvert]):
    """Like convert_assets_steps, but all bitmaps go through one 'convert-assets' process instead of one process each."""
    import json
    import re
    import subprocess
    import tempfile
    from .Dotnet import ComplexEncoder
    from .Functions import get_blendermania_dotnet_path

    bitmaps = [j for j in jobs if j.asset_type == "BITMAP"]
    if len(bitmaps) < BATCH_MIN_BITMAPS:
        return (yield from convert_assets_steps(jobs))

    for job in jobs:
        if job.asset_type != "BITMAP":
            job.run()                                   # images / texture sets: nothing to convert

    payload, by_path = [], {}
    for job in bitmaps:
        error = job.validate()
        if error:
            job.convert_has_failed, job.message = True, error
            continue
        config = dict(job.bitmap_config or {})
        config["ImageFile"] = job.image_path
        payload.append({"AssetType": 0, "AssetPath": job.gbx_path, "BitmapPayload": config})
        by_path[str(Path(job.gbx_path)).lower()] = job

    if payload:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump({"Assets": payload}, tmp, cls=ComplexEncoder, ensure_ascii=False)
        proc = subprocess.Popen([str(get_blendermania_dotnet_path()), "convert-assets", tmp.name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        lines: list[str] = []
        reader = threading.Thread(target=lambda: lines.extend(l.rstrip() for l in proc.stdout), daemon=True)
        reader.start()
        total = len(payload)
        while reader.is_alive():
            done = next((int(m.group(1)) for l in reversed(lines) if (m := re.match(r"PROGRESS: (\d+)/", l))), 0)
            yield done / total, f"{done}/{total} bitmaps converted"
            reader.join(0.05)
        proc.wait()
        Path(tmp.name).unlink(missing_ok=True)

        failed = {}
        for line in lines:
            m = re.match(r"FAILED: (.+?\.Texture\.Gbx): (.*)", line, re.IGNORECASE)
            if m:
                failed[str(Path(m.group(1))).lower()] = m.group(2)
        crashed = proc.returncode != 0 and not failed     # e.g. invalid payload: everything failed
        for path, job in by_path.items():
            if crashed or path in failed:
                job.convert_has_failed = True
                job.message = failed.get(path) or "\n".join(lines[-10:])
            else:
                job.exported_path = job.gbx_path
    yield 1.0, f"{len(bitmaps)} bitmaps done"
    return jobs
