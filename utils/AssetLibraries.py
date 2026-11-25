"""Blendermania asset libraries (custom ones the user creates + the original addon asset library).

- A .blend is declared an asset library by `Scene.tm_is_asset_library` (any scene). Only then the TM Asset tab
  is shown. The installed default assets blend counts as declared without the flag (releases predate it), and a
  file that already has own TM assets is declared once on load (files from before the flag existed).
- A declared, saved .blend inside Items/_BlenderAssets writes a marker file (MARKER_FILE) into its folder, so the
  Asset Library panel can list libraries without opening .blend files. Library = that folder (Blender asset
  libraries are folders), registered in the preferences with its folder name and import method Link.
- The original addon asset library (download "Install Complete Asset Library") lives in its own folder
  ADDON_ASSETS_LIB_FOLDER. Old installs unzipped it straight into _BlenderAssets (and registered the whole folder,
  so Blender also indexed the other libraries below it): `migrate_addon_assets_library` moves it.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

MARKER_FILE = "blendermania_asset_library.json"
MARKER_FORMAT = 1
ADDON_ASSETS_LIB_FOLDER = "AddonAssetsLibrary"
# folders below _BlenderAssets that are no custom libraries (own install boxes / plain texture stores)
MANAGED_FOLDERS = {"defaultassets", "materialassetslibrary", ADDON_ASSETS_LIB_FOLDER.lower(), "textures"}
SCAN_DEPTH = 2          # _BlenderAssets/<Name>/ and _BlenderAssets/<Group>/<Name>/
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _\-.]*$")


# -----------------------------
# paths
# -----------------------------
def _norm(path) -> str:
    return os.path.normcase(os.path.normpath(os.path.realpath(str(path))))


def assets_root() -> Path | None:
    """Items/_BlenderAssets (None if the game Items folder is unknown)"""
    from .Functions import get_game_doc_path_items_assets
    try:
        path = Path(get_game_doc_path_items_assets())
    except Exception:
        return None
    if not path.is_absolute() or not path.parent.is_dir():
        return None
    return path


def addon_assets_library_root() -> Path | None:
    root = assets_root()
    return root / ADDON_ASSETS_LIB_FOLDER if root else None


def is_inside_assets_root(filepath: str) -> bool:
    root = assets_root()
    if not root or not filepath:
        return False
    return _norm(filepath).startswith(_norm(root) + os.sep)


# -----------------------------
# declaration of the current file
# -----------------------------
def is_declared(context=None) -> bool:
    scenes = bpy.data.scenes
    if any(getattr(s, "tm_is_asset_library", False) for s in scenes):
        return True
    try:
        from .DefaultAssetsLibrary import DEFAULT_ASSETS_BLEND
        return Path(bpy.data.filepath).name.lower() == DEFAULT_ASSETS_BLEND.lower()
    except Exception:
        return False


def set_declared(value: bool) -> None:
    for scene in bpy.data.scenes:
        scene.tm_is_asset_library = value
    if bpy.data.filepath:
        write_marker(bpy.data.filepath, value)


def _has_local_assets() -> bool:
    # local texture sets / custom materials (Materials V2, not marked as Blender asset) don't make a library
    return any(m.library is None and m.tm_asset_properties.is_asset
               and (m.asset_data is not None or m.tm_asset_properties.asset_type not in ("TEXTURESET", "CUSTOMMATERIAL"))
               for m in bpy.data.materials)


# -----------------------------
# marker files + scan
# -----------------------------
def _read_marker(folder: Path) -> dict:
    try:
        data = json.loads((folder / MARKER_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_marker(filepath: str, declared: bool) -> None:
    """add/remove the blend in the marker of its folder (only inside _BlenderAssets, managed folders excluded)"""
    if not is_inside_assets_root(filepath):
        return
    folder = Path(filepath).parent
    if folder.name.lower() in MANAGED_FOLDERS:
        return
    data = _read_marker(folder)
    blends = [b for b in data.get("blends", []) if isinstance(b, str)]
    name = Path(filepath).name
    if declared and name not in blends:
        blends.append(name)
    elif not declared and name in blends:
        blends.remove(name)
    else:
        return
    marker = folder / MARKER_FILE
    try:
        if blends:
            marker.write_text(json.dumps({"format": MARKER_FORMAT, "blends": sorted(blends)}, indent=2), encoding="utf-8")
        elif marker.is_file():
            marker.unlink()
    except OSError as e:
        print(f"Blendermania: can't write {marker}: {e}")
    _scan_cache["time"] = 0.0


_scan_cache = {"time": 0.0, "root": None, "result": []}


def scan_libraries(force: bool = False) -> list[dict]:
    """declared libraries below _BlenderAssets: [{name, path, blends}] (cached 3 s, panels call this every redraw)"""
    root = assets_root()
    now = time.monotonic()
    if not force and _scan_cache["root"] == str(root) and now - _scan_cache["time"] < 3.0:
        return _scan_cache["result"]
    result = []
    if root and root.is_dir():
        def walk(folder: Path, depth: int):
            try:
                entries = sorted((e for e in os.scandir(folder) if e.is_dir()), key=lambda e: e.name.lower())
            except OSError:
                return
            for e in entries:
                if depth == 1 and e.name.lower() in MANAGED_FOLDERS:
                    continue
                sub = Path(e.path)
                blends = [b for b in _read_marker(sub).get("blends", []) if (sub / b).is_file()]
                if blends:
                    result.append({"name": sub.name, "path": str(sub), "blends": blends})
                elif depth < SCAN_DEPTH:
                    walk(sub, depth + 1)
        walk(root, 1)
    _scan_cache.update(time=now, root=str(root), result=result)
    return result


# -----------------------------
# preferences
# -----------------------------
def _libs():
    return bpy.context.preferences.filepaths.asset_libraries


def find_registered(folder) -> object | None:
    target = _norm(folder)
    for lib in _libs():
        if lib.path and _norm(bpy.path.abspath(lib.path)) == target:
            return lib
    return None


def register_library(folder, name: str | None = None, import_method: str = "LINK"):
    """add the folder to the preferences (Link: items keep pointing at the library, gbx paths stay valid)"""
    lib = find_registered(folder)
    if lib is None:
        taken = {l.name for l in _libs()}
        base = name or Path(folder).name
        unique, i = base, 2
        while unique in taken:
            unique, i = f"{base} {i}", i + 1
        lib = _libs().new(name=unique, directory=str(folder))
    try:
        lib.import_method = import_method
    except (AttributeError, TypeError):
        pass
    _save_userpref()
    return lib


def unregister_library(folder) -> bool:
    lib = find_registered(folder)
    if lib is None:
        return False
    _libs().remove(lib)
    _save_userpref()
    return True


def _save_userpref() -> None:
    """mark the preferences changed: auto-save on quit only writes dirty preferences (python edits don't set it),
    without auto-save Blender shows them as unsaved like any other preference change"""
    try:
        bpy.context.preferences.is_dirty = True
    except AttributeError:
        pass


# -----------------------------
# create a new custom library
# -----------------------------
def validate_new_name(name: str) -> str | None:
    """error text or None"""
    name = name.strip()
    root = assets_root()
    if root is None:
        return "Trackmania Items folder not found (check the Nadeo.ini setting)"
    if not name or not _NAME_RE.match(name):
        return "Use letters, digits, space, _ - . (starting with a letter or digit)"
    if name.lower() in MANAGED_FOLDERS:
        return f"'{name}' is reserved"
    if (root / name).exists():
        return f"_BlenderAssets/{name} already exists"
    return None


def new_library_blend_path(name: str) -> Path:
    name = name.strip()
    return assets_root() / name / f"{name}.blend"


def create_library(name: str) -> tuple[Path, object]:
    """new library WITHOUT touching the open file: an empty .blend written by a background Blender, declared by
    its marker (adopted as Scene.tm_is_asset_library when it is opened the first time), registered in the prefs"""
    blend = new_library_blend_path(name)
    blend.parent.mkdir(parents=True)
    expr = ("import bpy\n"
            "bpy.ops.wm.read_homefile(use_empty=True)\n"
            f"bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r}, compress=True)\n")
    try:
        out = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", "--python-expr", expr],
                             capture_output=True, text=True, timeout=120,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"Blender could not create {blend}: {e}")
    if not blend.is_file():
        raise RuntimeError(f"Blender could not create {blend}:\n{out.stdout[-1500:]}\n{out.stderr[-1500:]}")
    write_marker(str(blend), True)
    return blend, register_library(blend.parent)


def is_listed_in_marker(filepath: str) -> bool:
    return Path(filepath).name in _read_marker(Path(filepath).parent).get("blends", [])


# -----------------------------
# original addon asset library (own folder + migration of old installs)
# -----------------------------
def _old_library_files(root: Path) -> list[Path]:
    """files of an old install directly in _BlenderAssets (<GameType>_assets.blend + catalog + leftover zip)"""
    files = [p for p in root.glob("*_assets.blend")]
    if files:
        files += [p for p in (root / "blender_assets.cats.txt", root / "blender_assets.cats.txt~") if p.is_file()]
        files += [p for p in root.glob("*_assets.blend1")]
    return files


def fix_moved_library_images(blend: Path, levels_up: int = 1) -> bool:
    """the addon library images are '//Textures/...' relative to the old blend location -> '//../Textures/...'.
    Runs a background Blender (factory settings, the addon props are kept as plain id properties)."""
    prefix = "//" + "../" * levels_up
    expr = ("import bpy\n"
            "n = 0\n"
            "for i in bpy.data.images:\n"
            "    p = i.filepath.replace('\\\\', '/')\n"
            "    if p.lower().startswith('//textures/'):\n"
            f"        i.filepath = {prefix!r} + p[2:]; n += 1\n"
            "if n: bpy.ops.wm.save_mainfile(compress=True)\n"
            "print('TM_FIXED', n)\n")
    try:
        out = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", str(blend), "--python-expr", expr],
                             capture_output=True, text=True, timeout=300,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Blendermania: fixing image paths of {blend} failed: {e}")
        return False
    ok = "TM_FIXED" in out.stdout
    if not ok:
        print(f"Blendermania: fixing image paths of {blend} failed:\n{out.stdout[-2000:]}\n{out.stderr[-2000:]}")
    for leftover in blend.parent.glob(blend.name + "1"):     # .blend1 backup of the save
        try:
            leftover.unlink()
        except OSError:
            pass
    return ok


def move_old_install(root: Path, target: Path) -> list[Path]:
    """move the old files into the library folder, returns the moved .blend files"""
    target.mkdir(parents=True, exist_ok=True)
    moved = []
    for src in _old_library_files(root):
        dst = target / src.name
        try:
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
        except OSError as e:
            print(f"Blendermania: can't move {src} -> {dst}: {e}")
            continue
        if dst.suffix.lower() == ".blend":
            moved.append(dst)
    leftover = root / "assets.zip"           # the old download was never deleted
    if leftover.is_file():
        try:
            leftover.unlink()
        except OSError:
            pass
    return moved


def repoint_registered_root(root: Path, target: Path) -> None:
    """preference entry of the whole _BlenderAssets folder (old installs) -> library folder"""
    lib = find_registered(root)
    if lib is not None:
        lib.path = str(target)
        _save_userpref()


def needs_migration() -> bool:
    root = assets_root()
    return bool(root and root.is_dir() and (_old_library_files(root) or find_registered(root) is not None))


_migration = {"running": False}


def migrate_addon_assets_library(blocking: bool = False) -> None:
    """old install -> ADDON_ASSETS_LIB_FOLDER. Files are moved right away, the image path fix runs in a thread."""
    if _migration["running"] or not needs_migration():
        return
    root, target = assets_root(), addon_assets_library_root()
    moved = move_old_install(root, target)
    repoint_registered_root(root, target)
    if moved:
        print(f"Blendermania: moved the addon asset library into {target}")
    if not moved:
        return

    def work():
        try:
            for blend in moved:
                fix_moved_library_images(blend)
        finally:
            _migration["running"] = False

    _migration["running"] = True
    if blocking:
        work()
    else:
        import threading
        threading.Thread(target=work, daemon=True).start()


def is_migration_running() -> bool:
    return _migration["running"]


# -----------------------------
# handlers
# -----------------------------
@persistent
def _on_load_post(_dummy):
    # declare once (only if the flag was never set, so Undeclare sticks):
    # - libraries made by create_library (declared by their marker only)
    # - files with own TM assets from before the flag existed
    if bpy.data.filepath and not is_declared() and (is_listed_in_marker(bpy.data.filepath) or _has_local_assets()):
        scene = bpy.data.scenes[0] if bpy.data.scenes else None
        if scene is not None and not scene.is_property_set("tm_is_asset_library"):
            for s in bpy.data.scenes:
                s.tm_is_asset_library = True
    _scan_cache["time"] = 0.0


@persistent
def _on_save_post(_dummy):
    if bpy.data.filepath:
        write_marker(bpy.data.filepath, any(getattr(s, "tm_is_asset_library", False) for s in bpy.data.scenes))


def _deferred_migration():
    try:
        migrate_addon_assets_library()
    except Exception as e:
        print(f"Blendermania: migrating the addon asset library failed: {e}")
    return None


def register():
    bpy.types.Scene.tm_is_asset_library = bpy.props.BoolProperty(
        name="Asset Library", default=False,
        description="This .blend is a Blendermania asset library (shows the TM Asset tab)")
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)
    if _on_save_post not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(_on_save_post)
    if not bpy.app.background:
        bpy.app.timers.register(_deferred_migration, first_interval=2.0)


def unregister():
    if bpy.app.timers.is_registered(_deferred_migration):
        bpy.app.timers.unregister(_deferred_migration)
    for handlers, fn in ((bpy.app.handlers.load_post, _on_load_post), (bpy.app.handlers.save_post, _on_save_post)):
        if fn in handlers:
            handlers.remove(fn)
    del bpy.types.Scene.tm_is_asset_library
