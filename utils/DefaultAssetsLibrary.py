"""
Default asset library: Image / Bitmap / TextureSet assets for the game's own textures, built from a pak extract.

Layout (inside the game Items folder, so exported items can reference the files):
    Items/_BlenderAssets/DefaultAssets/
        TM2020_DefaultAssets.blend      the assets (registered as asset library "TM2020 Default Assets", LINK)
        blender_assets.cats.txt         Default Assets/<Environment>/Bitmaps|Images|TextureSets
        <Env>/Media/Texture/...         re-exported Texture.Gbx (mirrors the game path) + copied images

Self-contained (independent of the TM2020 Material Assets Library): every image is copied into the folder, all
paths are relative inside it, so a packaged release just gets extracted. Game files can't be referenced directly
(tested in game: items referencing pack files are not placeable).

Build steps (job thread of the operator):
    1. blendermania-dotnet read-pak-assets   -> bitmap settings + image refs, tree model refs (json)
    2. background Blender: build()           -> blend, catalogs, copied images, convert payload (json)
    3. blendermania-dotnet convert-assets    -> Texture.Gbx files
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from collections import defaultdict
from pathlib import Path

import bpy

from .Constants import (
    DEFAULT_ASSETS_DOWNLOAD_BASE, DEFAULT_ASSETS_RELEASE_REPOSITORY, DEFAULT_ASSETS_RELEASE_TAG_PREFIX,
    DEFAULT_ASSETS_RELEASES_API,
)
from .ReleaseInstaller import (
    Cancelled, download_and_extract, get_json, latest_version, long_path, version_key, write_release,
)

DEFAULT_ASSETS_LIB_NAME = "TM2020 Default Assets"
DEFAULT_ASSETS_BLEND = "TM2020_DefaultAssets.blend"
DEFAULT_ASSETS_FOLDER = "DefaultAssets"
CATALOG_ROOT = "Default Assets"
BITMAP_EXT = ".Texture.Gbx"
IMAGE_EXTENSIONS = (".dds", ".tga", ".png", ".jpg", ".webp")
LIBRARY_FORMAT = 1                              # bump when the package layout changes
RELEASE_EDITION = "default-assets"


# -----------------------------
# paths / registration (main Blender)
# -----------------------------
def get_default_assets_root() -> Path | None:
    from .Functions import get_game_doc_path_items_assets
    path = Path(get_game_doc_path_items_assets())
    if not path.is_absolute() or not path.parent.is_dir():  # Items folder must exist
        return None
    return path / DEFAULT_ASSETS_FOLDER


def get_built_default_assets() -> Path | None:
    """folder of the registered default asset library, None if not built"""
    try:
        libs = bpy.context.preferences.filepaths.asset_libraries
    except AttributeError:
        return None
    for lib in libs:
        if lib.name == DEFAULT_ASSETS_LIB_NAME and lib.path:
            path = Path(bpy.path.abspath(lib.path))
            if (path / DEFAULT_ASSETS_BLEND).is_file():
                return path
    return None


def register_default_assets_library(path: Path) -> None:
    libs = bpy.context.preferences.filepaths.asset_libraries
    lib = next((l for l in libs if l.name == DEFAULT_ASSETS_LIB_NAME), None)
    if lib is None:
        lib = libs.new(name=DEFAULT_ASSETS_LIB_NAME, directory=str(path))
    else:
        lib.path = str(path)
    try:
        # LINK: the assets keep pointing at the library (gbx/image paths resolve against it, nothing is duplicated)
        lib.import_method = "LINK"
    except (AttributeError, TypeError):
        pass


# -----------------------------
# build (background Blender)
# -----------------------------
def _progress(fraction: float, text: str) -> None:
    print(f"PROGRESS: {fraction:.4f} {text}", flush=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _env(game_path: str) -> str:
    return game_path.split("/", 1)[0]


class _Names:
    """unique material names: plain name first, environment prefix on collision"""
    def __init__(self):
        self.used = set(m.name for m in bpy.data.materials)

    def get(self, name: str, env: str) -> str:
        """the type prefix (BMP_, IMG_, TS_) stays in front: BMP_GreenCoast_Land_D"""
        prefix, sep, rest = name.partition("_")
        if not sep or f"{prefix}_" not in TYPE_PREFIX.values():
            prefix, rest = "", name
        else:
            prefix += "_"
        for cand in (name, f"{prefix}{env}_{rest}"):
            if cand not in self.used:
                self.used.add(cand)
                return cand
        i = 2
        while f"{prefix}{env}_{rest}_{i}" in self.used:
            i += 1
        self.used.add(f"{prefix}{env}_{rest}_{i}")
        return f"{prefix}{env}_{rest}_{i}"


# type identification in the Asset Browser and in pointer field dropdowns: name prefix, tag, thumbnail bar color
TYPE_PREFIX = {"BITMAP": "BMP_", "IMAGE": "IMG_", "TEXTURESET": "TS_", "CUSTOMMATERIAL": "CM_"}
TYPE_LABEL = {"BITMAP": "Bitmap", "IMAGE": "Image", "TEXTURESET": "TextureSet", "CUSTOMMATERIAL": "Custom Material"}
TYPE_COLOR = {"BITMAP": (0.15, 0.45, 1.0), "IMAGE": (0.2, 0.8, 0.3), "TEXTURESET": (1.0, 0.55, 0.1),
              "CUSTOMMATERIAL": (0.75, 0.3, 0.9)}
PREVIEW_SIZE = 128


def _new_asset(name: str, asset_type: str, catalog: str, env: str, game_path: str, image=None) -> bpy.types.Material:
    from .AssetLibraryFunctions import catalog_uuid, sync_preview
    mat = bpy.data.materials.new(name)
    props = mat.tm_asset_properties
    props.is_asset = True
    props.asset_type = asset_type
    if image is not None:
        props.image = image
    if asset_type == "IMAGE":
        props.game_path = game_path      # custom materials reference the game's own file (nothing shipped)
    sync_preview(mat)
    mat.asset_mark()
    data = mat.asset_data
    data.catalog_id = catalog_uuid(catalog)
    for tag in (TYPE_LABEL[asset_type], env, "Default Asset"):
        data.tags.new(tag, skip_if_exists=True)
    data.description = f"{TYPE_LABEL[asset_type]} (default game asset): {game_path}"
    return mat


def _set_type_preview(mat, image, asset_type: str) -> None:
    """asset thumbnail: the texture scaled down + a bar in the type color (also when the image can't be decoded)"""
    import numpy as np
    s = PREVIEW_SIZE
    px = np.full((s, s, 4), 0.25, dtype=np.float32)
    if image is not None:
        try:
            tmp = image.copy()
            tmp.scale(s, s)
            buf = np.empty(s * s * 4, dtype=np.float32)
            tmp.pixels.foreach_get(buf)
            bpy.data.images.remove(tmp)
            px = buf.reshape(s, s, 4)
        except (RuntimeError, ValueError):
            pass
    px[..., 3] = 1.0
    px[: s // 10, :, :3] = TYPE_COLOR[asset_type]     # bottom bar
    mat.preview_ensure()
    mat.preview.image_size = (s, s)
    mat.preview.image_pixels_float.foreach_set(px.ravel())


def _apply_bitmap_config(bmp, cfg: dict) -> None:
    from ..properties.AssetProperties import usage_from_config
    def color(v, n):
        v = list(v or [])[:n]
        return v + [0.0] * (n - len(v))
    bmp.usage = usage_from_config(cfg.get("Usage", "Color"))
    bmp.render_size_mul = max(1, int(cfg.get("RenderSizeMul", 1)))
    bmp.render_size_div = max(1, int(cfg.get("RenderSizeDiv", 1)))
    bmp.pixel_update = int(cfg.get("PixelUpdate", 0))
    bmp.border_rgb = color(cfg.get("BorderRGB"), 3)
    bmp.clear_color = color(cfg.get("ClearColor"), 4)
    bmp.default_render_clear_color = color(cfg.get("DefaultRenderClearColor"), 4)
    bmp.bump_scale_factor = cfg.get("BumpScaleFactor", 1.0)
    bmp.bump_scale_mip_level = cfg.get("BumpScaleMipLevel", 0.5)
    bmp.height_in_meters = cfg.get("HeightInMeters", 1.0)
    bmp.mip_lod_bias_default = cfg.get("MipMapLodBiasDefault", 0.0)
    bmp.mip_lower_alpha = cfg.get("MipMapLowerAlpha", 0.0)
    bmp.mip_fade_alphas.clear()
    for v in cfg.get("MipMapFadeAlphas") or []:
        bmp.mip_fade_alphas.add().value = v
    bmp.default_uv.rotate = cfg.get("DefaultTexCoordRotate", 0.0)
    bmp.default_uv.scale = cfg.get("DefaultTexCoordScale", [1.0, 1.0])
    bmp.default_uv.trans = cfg.get("DefaultTexCoordTrans", [0.0, 0.0])
    bmp.grass_id = cfg.get("GrassId", "") or ""
    bmp.grass_uv.rotate = cfg.get("GrassIdTexCoordRotate ", cfg.get("GrassIdTexCoordRotate", 0.0))  # C# key has a trailing space
    bmp.grass_uv.scale = cfg.get("GrassIdTexCoordScale", [1.0, 1.0])
    bmp.grass_uv.trans = cfg.get("GrassIdTexCoordTrans", [0.0, 0.0])


# TextureSet slot (read-pak-assets) -> texture_set property
TEXTURE_SET_SLOTS = {
    "ColorImage": "color_image", "NormalImage": "normal_image", "RoughnessImage": "roughness_image",
    "DiffuseBitmap": "color_texture", "NormalBitmap": "normal_texture", "RoughnessBitmap": "roughness_texture",
}
_LEGACY_SLOT = {"D": "ColorImage", "N": "NormalImage", "R": "RoughnessImage",
                "D_bitmap": "DiffuseBitmap", "N_bitmap": "NormalBitmap", "R_bitmap": "RoughnessBitmap"}


def _texture_set_slots(refs: list[str]) -> list[dict]:
    """fallback for an old read-pak-assets without TextureSets: groups the flat ref list by file stem
    (wrong for sets that mix stems, e.g. ItemFallTreeBranch_D + ItemSpringTreeBranch_N)"""
    sets = defaultdict(dict)
    for ref in refs:
        base = ref.rsplit("/", 1)[-1]
        m = re.match(r"(?i)(.+?)_(D|N|R)\.(dds|tga|texture\.gbx)$", base)
        if m:
            key = m.group(2).upper() + ("_bitmap" if m.group(3).lower() == "texture.gbx" else "")
            sets[m.group(1)].setdefault(_LEGACY_SLOT[key], ref)
    return list(sets.values())


def _tree_texture_sets(tree: dict) -> list[dict]:
    """the tree model's texture sets as {slot: game path} (slots of TEXTURE_SET_SLOTS, plus "Name")"""
    if tree.get("TextureSets") is None:
        return _texture_set_slots(tree.get("Refs") or [])
    return [{k: v for k, v in ts.items() if v and (k in TEXTURE_SET_SLOTS or k == "Name")}
            for ts in tree["TextureSets"]]


def _stem(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    base = re.sub(r"(?i)\.(texture\.gbx|dds|tga|png|jpg|webp)$", "", base)
    return re.sub(r"(?i)_(D|N|R)$", "", base)


def build(pak_root: Path, out_root: Path, data_json: Path, payload_out: Path) -> dict:
    from .AssetLibraryFunctions import catalog_uuid, HEADER, _make_record, _blender_path

    data = json.loads(data_json.read_text(encoding="utf-8"))
    out_root.mkdir(parents=True, exist_ok=True)
    blend = out_root / DEFAULT_ASSETS_BLEND

    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):                     # factory startup scene (cube, camera, light)
            coll.remove(block)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))   # '//' paths need a saved file

    # images used by bitmaps and tree models -----------------------------------------------------
    bitmaps = [b for b in data["Bitmaps"] if not b.get("Error") and b.get("Image") and b.get("Config")]
    tree_sets = {}     # (env, slot tuple) -> slots; identical sets of several tree models only once
    for tree in data["Trees"]:
        for slots in _tree_texture_sets(tree):
            files = tuple(sorted((k, v) for k, v in slots.items() if k in TEXTURE_SET_SLOTS))
            if any(k in ("ColorImage", "DiffuseBitmap") for k, _ in files):
                tree_sets.setdefault((_env(tree["Path"]), files), slots)
    needed = {b["Image"] for b in bitmaps}
    for slots in tree_sets.values():
        needed.update(v for k, v in slots.items() if k.endswith("Image"))
    needed = sorted(p for p in needed if p.lower().endswith(IMAGE_EXTENSIONS) and (pak_root / p).is_file())

    names = _Names()
    images = {}        # game path -> image record
    image_assets = {}  # game path -> IMAGE asset material
    stats = {"images": 0, "bitmaps": 0, "texture_sets": 0}
    for i, game_path in enumerate(needed):
        if i % 20 == 0:
            _progress(i / len(needed) * 0.6, f"Images {i}/{len(needed)}")
        src = pak_root / game_path
        sha = _sha256(src)
        dst = out_root / game_path
        rel = game_path
        if not dst.is_file() or dst.stat().st_size != src.stat().st_size:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        img = _make_record(dst, rel, sha, src.name)
        img.filepath = _blender_path(rel)
        images[game_path] = img
        env = _env(game_path)
        image_assets[game_path] = mat = _new_asset(names.get(TYPE_PREFIX["IMAGE"] + src.stem, env), "IMAGE",
                                                   f"{CATALOG_ROOT}/{env}/Images", env, game_path, img)
        _set_type_preview(mat, img, "IMAGE")
        stats["images"] += 1

    # bitmaps -------------------------------------------------------------------------------------
    bitmap_assets = {}  # game path (lowercase) -> BITMAP asset material
    for i, b in enumerate(bitmaps):
        if i % 20 == 0:
            _progress(0.6 + i / max(1, len(bitmaps)) * 0.3, f"Bitmaps {i}/{len(bitmaps)}")
        img = images.get(b["Image"])
        if img is None:
            continue
        game_path = re.sub(r"(?i)\.texture\.gbx$", BITMAP_EXT, b["Path"])
        env = _env(game_path)
        stem = re.sub(r"(?i)\.texture\.gbx$", "", game_path.rsplit("/", 1)[-1])
        mat = _new_asset(names.get(TYPE_PREFIX["BITMAP"] + stem, env), "BITMAP", f"{CATALOG_ROOT}/{env}/Bitmaps",
                         env, game_path, img)
        _set_type_preview(mat, img, "BITMAP")
        props = mat.tm_asset_properties
        props.relative_path = game_path                     # gbx mirrors the game path
        _apply_bitmap_config(props.bitmap, b["Config"])
        from ..properties.AssetProperties import USAGE_ITEMS
        mat.asset_data.tags.new(next(label for ident, label, _ in USAGE_ITEMS if ident == props.bitmap.usage),
                                skip_if_exists=True)
        from .AssetLibraryFunctions import sync_preview
        sync_preview(mat)                                    # usage decides the preview shading
        bitmap_assets[b["Path"].lower()] = mat
        stats["bitmaps"] += 1

    # texture sets (as used by the game's tree models) -----------------------------------------
    used_ts = {}       # (env, name) -> files: a different set with the same color stem gets its texture name
    for (env, files), slots in sorted(tree_sets.items()):
        color = slots.get("ColorImage") or slots.get("DiffuseBitmap")
        stem = _stem(color)
        if used_ts.setdefault((env, stem), files) != files and slots.get("Name"):
            stem = f"{stem}_{slots['Name']}"
        mat = _new_asset(names.get(TYPE_PREFIX["TEXTURESET"] + stem, env), "TEXTURESET",
                         f"{CATALOG_ROOT}/{env}/TextureSets", env,
                         f"{env} tree texture set {slots.get('Name') or stem}")
        ts = mat.tm_asset_properties.texture_set
        for key, ref in files:
            target = bitmap_assets.get(ref.lower()) if key.endswith("Bitmap") else image_assets.get(ref)
            if target is not None:
                setattr(ts, TEXTURE_SET_SLOTS[key], target)
        color = ts.color_image or ts.color_texture
        _set_type_preview(mat, color.tm_asset_properties.image if color else None, "TEXTURESET")
        from .AssetLibraryFunctions import sync_preview
        sync_preview(mat)
        stats["texture_sets"] += 1

    # catalogs ------------------------------------------------------------------------------------
    paths = sorted({f"{CATALOG_ROOT}/{_env(p)}/{kind}" for p in needed for kind in ("Images", "Bitmaps", "TextureSets")}
                   | {CATALOG_ROOT})
    lines = [HEADER.rstrip("\n")]
    for path in paths:
        parts = path.split("/")
        for depth in range(1, len(parts)):                 # parents first, so the tree is complete
            parent = "/".join(parts[:depth])
            line = f"{catalog_uuid(parent)}:{parent}:{parent.replace('/', '-')}"
            if line not in lines:
                lines.append(line)
        lines.append(f"{catalog_uuid(path)}:{path}:{path.replace('/', '-')}")
    (out_root / "blender_assets.cats.txt").write_text("\n".join(dict.fromkeys(lines)) + "\n", encoding="utf-8")

    _progress(0.95, "Saving")
    _write_convert_payload(out_root, payload_out)
    bpy.ops.wm.save_mainfile(compress=True)
    info = dict(stats, format=LIBRARY_FORMAT, version="local-" + _today(), edition=RELEASE_EDITION,
                game_source=_pak_date(pak_root))
    (out_root / "library.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("BUILD_RESULT: " + json.dumps(stats), flush=True)
    return stats


def _write_convert_payload(out_root: Path, payload_out: Path) -> int:
    """convert-assets payload for every bitmap asset of the open default library blend"""
    from ..properties.AssetProperties import bitmap_to_config
    from .Dotnet import ComplexEncoder
    payload = []
    for mat in bpy.data.materials:
        props = mat.tm_asset_properties
        if mat.library is None and props.is_asset and props.asset_type == "BITMAP" and props.image:
            config = bitmap_to_config(props.bitmap)
            config["ImageFile"] = str((out_root / props.image.tm_image_asset.rel_path).resolve())
            payload.append({"AssetType": 0, "AssetPath": str(out_root / props.relative_path), "BitmapPayload": config})
    payload_out.write_text(json.dumps({"Assets": payload}, cls=ComplexEncoder), encoding="utf-8")
    return len(payload)


def _today() -> str:
    import datetime
    return datetime.date.today().strftime("%Y.%m.%d")


def _pak_date(pak_root: Path) -> str:
    """newest file date of the pak extract (pak.index.json MTimeTicks: .NET ticks), identifies the game version used"""
    import datetime
    try:
        index = json.loads((pak_root.parent / "pak.index.json").read_text(encoding="utf-8-sig"))
        ticks = max(e.get("MTimeTicks", 0) for e in index.get("Entries", []))
        return (datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=ticks // 10)).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return ""


def strip_machine_paths(blend: Path, out: Path) -> None:
    """background Blender: save a copy of the library blend without exported_path (absolute paths of this machine)"""
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False)
    cleared = 0
    for mat in bpy.data.materials:
        props = mat.tm_asset_properties
        if mat.library is None and props.exported_path:
            props.exported_path = ""
            cleared += 1
    bpy.ops.wm.save_as_mainfile(filepath=str(out), copy=True, relative_remap=False, compress=True)
    print(f"STRIP_RESULT: {json.dumps({'cleared': cleared})}", flush=True)


def build_from_argv() -> None:
    """entry for the background Blender: ... -- build <pak_root> <out_root> <data_json> <payload_out>
                                         or ... -- strip <blend> <out_blend>"""
    args = sys.argv[sys.argv.index("--") + 1:]
    if args[0] == "strip":
        strip_machine_paths(Path(args[1]), Path(args[2]))
        return
    pak_root, out_root, data_json, payload_out = args[1:5]
    build(Path(pak_root), Path(out_root), Path(data_json), Path(payload_out))


# -----------------------------
# jobs (main Blender, worker thread with subprocesses): build from a pak extract, install a release, package a release
# -----------------------------
class _BuildState:
    def __init__(self, kind: str):
        self.kind = kind       # "build" | "install" | "package"
        self.lock = threading.Lock()
        self.progress = 0.0    # 0..1
        self.status = ""
        self.error = ""
        self.done = False
        self.stats = None
        self.result = None     # install: version, package: release.json path
        self.cancel = False
        self.process = None

    def report(self, text, fraction=None):
        with self.lock:
            self.status = text
            if fraction is not None:
                self.progress = fraction


_build: _BuildState | None = None


def is_build_running() -> bool:
    return _build is not None and not _build.done


def cancel_build() -> None:
    if _build is not None:
        _build.cancel = True
        proc = _build.process
        if proc is not None and proc.poll() is None:
            proc.kill()


def _run_stage(state: _BuildState, args: list, base: float, span: float, label: str) -> list[str]:
    """run a subprocess, map its PROGRESS lines into [base, base + span], return all output lines"""
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    state.process = proc
    lines = []
    for line in proc.stdout:
        line = line.rstrip()
        lines.append(line)
        m = re.match(r"PROGRESS: (\d+)/(\d+)", line)          # dotnet: i/n
        f = re.match(r"PROGRESS: ([\d.]+) (.*)", line)        # blender: fraction text
        if m:
            state.report(f"{label} {m.group(1)}/{m.group(2)}", base + span * int(m.group(1)) / max(1, int(m.group(2))))
        elif f:
            state.report(f"{label}: {f.group(2)}", base + span * float(f.group(1)))
    proc.wait()
    state.process = None
    if state.cancel:
        raise InterruptedError()
    if proc.returncode != 0:
        tail = "\n".join(l for l in lines if l and not l.startswith("PROGRESS"))[-600:]
        raise RuntimeError(f"{label} failed (exit {proc.returncode}): {tail}")
    return lines


def _blender_args(*args) -> list:
    """background Blender running build_from_argv(args) with this addon registered"""
    package = __package__.split(".")[0]
    addon_parent = str(Path(__file__).resolve().parents[2])
    code = ("import sys, importlib; sys.path.insert(0, {!r}); importlib.import_module({!r}).register(); "
            "importlib.import_module({!r}).build_from_argv()").format(addon_parent, package, package + ".utils.DefaultAssetsLibrary")
    return [bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1",
            "--python-expr", code, "--", *[str(a) for a in args]]


def _result_line(lines: list, key: str) -> dict:
    line = next((l for l in lines if l.startswith(key + ": ")), None)
    if line is None:
        raise RuntimeError(f"no {key} reported")
    return json.loads(line[len(key) + 2:])


def _job(state: _BuildState, work: Path, body) -> None:
    try:
        work.mkdir(parents=True, exist_ok=True)
        body(work)
        state.report("Done", 1.0)
    except (InterruptedError, Cancelled):
        state.error = "Cancelled"
    except Exception as e:  # shown in the ui
        state.error = str(e) or type(e).__name__
    finally:
        shutil.rmtree(long_path(work), ignore_errors=True)
        state.done = True


def _start(kind: str, target, *args) -> _BuildState:
    global _build
    if is_build_running():
        raise RuntimeError("another default assets job is running")
    _build = _BuildState(kind)
    threading.Thread(target=target, args=(_build, *args), daemon=True).start()
    return _build


def _out_root() -> Path:
    out_root = get_default_assets_root()
    if out_root is None:
        raise RuntimeError("Trackmania Items folder not found, check the Nadeo.ini setting")
    return out_root


def _dotnet() -> str:
    from .Functions import get_blendermania_dotnet_path
    dotnet = get_blendermania_dotnet_path()
    if not dotnet or not os.path.isfile(str(dotnet)):
        raise RuntimeError("blendermania-dotnet not installed")
    return str(dotnet)


# --- build from a pak extract -----------------------------------------------------------------
def start_build(pak_extract: str) -> _BuildState:
    """pak_extract: folder with GameData/ (or GameData itself)"""
    root = Path(bpy.path.abspath(pak_extract or ""))
    if (root / "GameData").is_dir():
        root = root / "GameData"
    if not pak_extract or not root.is_dir():
        raise RuntimeError("Pak extract folder not found")
    out_root, dotnet = _out_root(), _dotnet()

    def body(work):
        data_json, payload_json = work / "pak_assets.json", work / "convert_payload.json"
        _run_stage(_build, [dotnet, "read-pak-assets", json.dumps({"Root": str(root), "OutputPath": str(data_json)})],
                   0.0, 0.1, "Reading game assets")
        lines = _run_stage(_build, _blender_args("build", root, out_root, data_json, payload_json),
                           0.1, 0.75, "Building library")
        _build.stats = _result_line(lines, "BUILD_RESULT")
        _run_stage(_build, [dotnet, "convert-assets", str(payload_json)], 0.85, 0.15, "Writing Texture.Gbx")

    return _start("build", lambda state: _job(state, out_root.parent / (out_root.name + ".build"), body))


# --- install / update from the release repository ----------------------------------------------
def is_release_repository_configured() -> bool:
    return "YOUR-" not in DEFAULT_ASSETS_RELEASE_REPOSITORY


def _latest_release() -> str | None:
    return latest_version(DEFAULT_ASSETS_RELEASES_API, re.compile("^" + re.escape(DEFAULT_ASSETS_RELEASE_TAG_PREFIX) + r"(.+)$"))


def start_release_install() -> _BuildState:
    if not is_release_repository_configured():
        raise RuntimeError("no release repository set (DEFAULT_ASSETS_RELEASE_REPOSITORY in utils/Constants.py)")
    out_root = _out_root()

    def body(work):
        _build.report("Looking up release...", 0.0)
        version = _latest_release()
        if not version:
            raise RuntimeError(f"no release '{DEFAULT_ASSETS_RELEASE_TAG_PREFIX}<version>' in {DEFAULT_ASSETS_RELEASE_REPOSITORY}")
        base_url = f"{DEFAULT_ASSETS_DOWNLOAD_BASE}{DEFAULT_ASSETS_RELEASE_TAG_PREFIX}{version}/"
        install_from_manifest(_build, base_url, get_json(base_url + "release.json"), out_root, work)

    return _start("install", lambda state: _job(state, out_root.parent / (out_root.name + ".download"), body))


def install_from_manifest(state: _BuildState, base_url: str, manifest: dict, out_root: Path, work: Path) -> None:
    """download + extract into a staging folder (all paths are relative inside the package), swap into out_root"""
    if manifest.get("edition") != RELEASE_EDITION or int(manifest.get("format", 0)) > LIBRARY_FORMAT:
        raise RuntimeError("release is no default assets package of a supported format (update the addon)")
    staging = out_root.with_name(out_root.name + ".installing")
    shutil.rmtree(long_path(staging), ignore_errors=True)
    try:
        download_and_extract(base_url, manifest, work / "zips", staging, report=state.report,
                             cancelled=lambda: state.cancel, span=(0.0, 0.8, 0.98))
        if not (staging / DEFAULT_ASSETS_BLEND).is_file():
            raise RuntimeError(f"release contains no {DEFAULT_ASSETS_BLEND}")
        old = out_root.with_name(out_root.name + ".old")
        shutil.rmtree(long_path(old), ignore_errors=True)
        if out_root.exists():
            out_root.replace(old)
        staging.replace(out_root)
        staging = None
        shutil.rmtree(long_path(old), ignore_errors=True)
        state.result = manifest.get("version")
        state.stats = json.loads((out_root / "library.json").read_text(encoding="utf-8"))
    finally:
        if staging is not None:
            shutil.rmtree(long_path(staging), ignore_errors=True)


# --- package for a release -------------------------------------------------------------------------
def start_package(dest_dir: str, version: str) -> _BuildState:
    out_root = get_built_default_assets() or get_default_assets_root()
    if out_root is None or not (out_root / DEFAULT_ASSETS_BLEND).is_file():
        raise RuntimeError("build the default assets first")
    version = (version or "").strip()
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.\-]*", version):
        raise RuntimeError("version must be like 1.0.0")
    dest = Path(bpy.path.abspath(dest_dir or "")) if dest_dir else None
    if dest is None:
        raise RuntimeError("choose an output folder")

    def body(work):
        info = json.loads((out_root / "library.json").read_text(encoding="utf-8"))
        info["version"] = version
        (out_root / "library.json").write_text(json.dumps(info, indent=2), encoding="utf-8")  # installed copy carries it
        files = []
        for f in out_root.rglob("*"):
            rel = f.relative_to(out_root).as_posix()
            # Texture.Gbx are not shipped: the user creates them with "Export Asset Library" in the library blend
            if f.is_file() and not rel.endswith(".blend1") and not rel.lower().endswith(".texture.gbx"):
                files.append(rel)
        manifest = {k: info.get(k) for k in ("version", "edition", "format", "game_source", "bitmaps", "images", "texture_sets")}
        manifest["edition"] = RELEASE_EDITION
        clean_blend = work / DEFAULT_ASSETS_BLEND             # copy without machine specific absolute paths
        _run_stage(_build, _blender_args("strip", out_root / DEFAULT_ASSETS_BLEND, clean_blend), 0.0, 0.05, "Cleaning blend")
        _build.result = write_release(files, out_root, dest / f"{DEFAULT_ASSETS_RELEASE_TAG_PREFIX}{version}",
                                      f"TM2020-DefaultAssets-{version}", manifest,
                                      report=_build.report, cancelled=lambda: _build.cancel,
                                      overrides={DEFAULT_ASSETS_BLEND: clean_blend})
        _build.stats = info

    return _start("package", lambda state: _job(state, out_root.parent / (out_root.name + ".package"), body))


# --- results / status ----------------------------------------------------------------------------
def finish_build(state: _BuildState) -> str:
    """main thread after a successful job"""
    s = state.stats or {}
    if state.kind == "package":
        return f"Release files written: {Path(state.result).parent} (upload all files to tag {Path(state.result).parent.name})"
    register_default_assets_library(get_default_assets_root())
    if state.kind == "install":
        return (f"Default assets {state.result} installed. Open the library blend and run Export Asset Library "
                f"to create the {s.get('bitmaps', 0)} Texture.Gbx")
    return (f"Default assets built: {s.get('bitmaps', 0)} bitmaps, {s.get('images', 0)} images, "
            f"{s.get('texture_sets', 0)} texture sets")


def get_default_assets_info() -> dict | None:
    path = get_built_default_assets()
    if path is None:
        return None
    try:
        info = json.loads((path / "library.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        info = {}
    info["path"] = str(path)
    info["exported"] = _count_exported(path)
    return info


_exported_cache = {"key": None, "time": 0.0, "count": 0}


def _count_exported(path: Path) -> int:
    """number of Texture.Gbx in the library folder (panel hint), rescanned at most every 5 s"""
    import time
    now = time.monotonic()
    if _exported_cache["key"] != str(path) or now - _exported_cache["time"] > 5.0:
        _exported_cache.update(key=str(path), time=now,
                               count=sum(1 for _ in path.rglob("*" + BITMAP_EXT)) if not is_build_running() else 0)
    return _exported_cache["count"]


def check_for_update() -> dict:
    """{"installed", "latest", "update"}; raises when GitHub can't be asked or no repository is set"""
    if not is_release_repository_configured():
        raise RuntimeError("no release repository set")
    installed = (get_default_assets_info() or {}).get("version")
    latest = _latest_release()
    newer = bool(latest and (not installed or installed.startswith("local-") or version_key(latest) > version_key(installed)))
    return {"installed": installed, "latest": latest, "update": newer}
