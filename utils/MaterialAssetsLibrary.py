"""
TM2020 Material Assets Library (https://github.com/BigthirstyTM/TM2020-Material-Assets-Library) integration.

- install: download a release (release.json + N zip parts, sha256 checked), extract, register it as Blender asset library
  into Items/_BlenderAssets/MaterialAssetsLibrary/<edition>/<version> (same asset library name as the official
  Install-Library.ps1, which installs to %LOCALAPPDATA%; found by name, so either install works) and select its
  MaterialLib.txt (superset of the addon one: Stadium + other environments) as Material Lib.
- index: library material name <-> game material link, resolved via materials.json (native_link) + MaterialLib.txt.
- material instances: the V2 material panel copies the library shader for the chosen link instead of building the
  addon shader. Library materials themselves already carry the Blendermania props (link, gameType), so materials
  dragged in from the Asset Browser export without this module.
"""
import os
import re
import json
import shutil
import hashlib
import threading
import urllib.request
import urllib.error
import uuid
import zipfile
from pathlib import Path

import bpy

from .Constants import (
    MATERIAL_ASSETS_LIB_BLEND,
    MATERIAL_ASSETS_LIB_DOWNLOAD_BASE,
    MATERIAL_ASSETS_LIB_FALLBACK_VERSION,
    MATERIAL_ASSETS_LIB_NAME,
    MATERIAL_ASSETS_LIB_RELEASES_API,
)
from .Functions import debug, get_global_props


_HTTP_HEADERS = {"User-Agent": "blendermania-addon", "Accept": "application/vnd.github+json"}
_CHUNK = 1024 * 1024
_VALID_ARCHIVE = re.compile(r"^[A-Za-z0-9._-]+\.zip$")

LIBRARY_ASSET_PROP = "libraryAsset"           # Material prop: library material the shader was copied from
LIBRARY_DEFAULT_COLOR = "tm_library_default_color"  # custom prop: original cus_color of the library shader


# -----------------------------
# paths / installed state
# -----------------------------
def get_default_install_root() -> Path | None:
    """Items/_BlenderAssets/MaterialAssetsLibrary, next to the addon's other downloads (None if the game folder is unknown).
    Inside Items, so its textures can also be referenced by custom assets (bitmaps/texture sets) without copies."""
    from .Functions import get_game_doc_path_items_assets
    path = Path(get_game_doc_path_items_assets())
    if not path.is_absolute() or not path.parent.is_dir():  # Items folder must exist
        return None
    return path / "MaterialAssetsLibrary"


def _is_library_folder(path: Path) -> bool:
    return (path / MATERIAL_ASSETS_LIB_BLEND).is_file() and (path / "MaterialLib.txt").is_file()


def get_installed_library_path() -> Path | None:
    """folder of the registered library (asset library entry by name), None if not installed"""
    try:
        libs = bpy.context.preferences.filepaths.asset_libraries
    except AttributeError:
        return None
    for lib in libs:
        if lib.name == MATERIAL_ASSETS_LIB_NAME and lib.path:
            path = Path(bpy.path.abspath(lib.path))
            if _is_library_folder(path):
                return path
    return None


def get_installed_library_info() -> dict | None:
    """library.json of the installed library ({edition, version, materials, ...}) + "path" """
    path = get_installed_library_path()
    if path is None:
        return None
    info = {}
    try:
        info = json.loads((path / "library.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    info["path"] = str(path)
    return info


def register_asset_library(path: Path) -> None:
    """add/update the asset library entry (one entry, updated on reinstall like the official installer)"""
    libs = bpy.context.preferences.filepaths.asset_libraries
    lib = next((l for l in libs if l.name == MATERIAL_ASSETS_LIB_NAME), None)
    if lib is None:
        lib = libs.new(name=MATERIAL_ASSETS_LIB_NAME, directory=str(path))
    else:
        lib.path = str(path)
    try:
        lib.import_method = "APPEND_REUSE"  # editable copies, shared images/node groups are reused
    except (AttributeError, TypeError):
        pass


# -----------------------------
# index (library material <-> game material link)
# -----------------------------
_REGEX_DLIBRARY  = re.compile(r"DLibrary\s*\(([\w-]+)\)")
_REGEX_DMATERIAL = re.compile(r"DMaterial\s*\(([\w+-]+)\)")
_REGEX_DLINKFULL = re.compile(r"DLinkFull\s*\(([^)]*)\)")

_index_cache: dict = {"key": None, "index": None}


def _parse_linkfulls(materiallib: Path) -> dict:
    """{ "stadium\\media\\material\\roadtech": ["RoadTech", "Stadium_RoadTech"] } (file order)"""
    result = {}
    lib = mat = ""
    with open(materiallib, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _REGEX_DLIBRARY.search(line)
            if m:
                lib, mat = m.group(1), ""
                continue
            m = _REGEX_DMATERIAL.search(line)
            if m:
                mat = m.group(1)
                continue
            m = _REGEX_DLINKFULL.search(line)
            if m and lib and mat:
                result.setdefault(f"{lib}\\{m.group(1).strip()}".lower(), []).append(mat)
    return result


def _base_name(name: str) -> str:
    """TM_RoadTech_asset.001 -> TM_RoadTech_asset"""
    return re.sub(r"\.\d{3,}$", "", name)


def _name_to_link(name: str) -> str:
    """TM_RoadTech_asset -> RoadTech (matches the real link for ~98% of the library)"""
    return re.sub(r"(?i)^TM_|_asset$", "", _base_name(name))


def build_library_index(path: Path) -> dict:
    """
    by_name:     library material name -> {link, linkfull, physics, gameplay, catalog, preview_only}
    by_link:     link -> preferred library material name
    by_linkfull: lowercase DLibrary\\DLinkFull -> preferred library material name (covers aliases like Stadium_RoadTech)
    """
    linkfulls = _parse_linkfulls(path / "MaterialLib.txt")
    rows = json.loads((path / "materials.json").read_text(encoding="utf-8"))

    by_name, by_link, by_linkfull = {}, {}, {}
    for row in rows:
        name = row.get("name", "")
        native = (row.get("native_link") or "").lower()
        candidates = linkfulls.get(native, [])
        derived = _name_to_link(name)
        link = derived if derived in candidates else (candidates[0] if candidates else "")
        by_name[name] = {
            "link":         link,
            "linkfull":     native if candidates else "",
            "physics":      row.get("physics") or "",
            "gameplay":     row.get("gameplay") or "",
            "catalog":      row.get("catalog") or "",
            "preview_only": bool(row.get("preview_only")),
            "conditional":  bool(row.get("conditional")),  # ColorBlindness variants
        }

    def _better(new: str, old: str | None, link: str) -> bool:
        if old is None:
            return True
        rank = lambda n: (n != f"TM_{link}_asset", by_name[n]["conditional"], by_name[n]["preview_only"], n)
        return rank(new) < rank(old)

    for name, info in by_name.items():
        link = info["link"]
        if not link:
            continue
        if _better(name, by_link.get(link), link):
            by_link[link] = name
        if _better(name, by_linkfull.get(info["linkfull"]), link):
            by_linkfull[info["linkfull"]] = name

    return {"path": path, "by_name": by_name, "by_link": by_link, "by_linkfull": by_linkfull}


def get_library_index() -> dict | None:
    path = get_installed_library_path()
    if path is None:
        return None
    try:
        key = (str(path), os.path.getmtime(path / "materials.json"), os.path.getmtime(path / "MaterialLib.txt"))
    except OSError:
        return None
    if _index_cache["key"] != key:
        try:
            _index_cache["index"] = build_library_index(path)
        except (OSError, ValueError, KeyError) as e:
            debug(f"material assets library index failed: {e}")
            _index_cache["index"] = None
        _index_cache["key"] = key
    return _index_cache["index"]


def reset_library_index() -> None:
    _index_cache["key"] = None
    _index_cache["index"] = None


def find_library_material(link: str, collection: str = "") -> str | None:
    """library material name for a materiallib link (V2 panel: collection + material name)"""
    if not link:
        return None
    index = get_library_index()
    if index is None:
        return None
    from .materialLib import get_materiallibrary_materials
    entry = get_materiallibrary_materials().get(collection, {}).get(link)
    if entry and entry.get("LinkFull"):
        name = index["by_linkfull"].get(entry["LinkFull"].lower())
        if name:
            return name
    return index["by_link"].get(link)


# -----------------------------
# material instances
# -----------------------------
def _append_library_material(name: str) -> bpy.types.Material | None:
    """
    returns a NEW local copy of the library material (images and node groups are reused if already appended).
    The appended original is removed again, so the asset library material can be appended any number of times.
    """
    path = get_installed_library_path()
    if path is None:
        return None
    blend = str(path / MATERIAL_ASSETS_LIB_BLEND)

    before = set(bpy.data.materials)
    try:
        bpy.ops.wm.append(
            filepath=blend + "/Material/" + name,
            directory=blend + "/Material/",
            filename=name,
            link=False,
            do_reuse_local_id=True,
            set_fake=False,
            autoselect=False,
            active_collection=False,
            instance_collections=False,
            instance_object_data=False,
        )
    except RuntimeError as e:
        debug(f"append of library material {name} failed: {e}")
        return None

    appended = [m for m in bpy.data.materials if m not in before]
    template = appended[0] if appended else None
    if template is None:  # reused an already appended local copy
        template = next((m for m in bpy.data.materials
                         if m.library is None and _base_name(m.name) == name and "tm_asset_id" in m), None)
    if template is None:
        return None

    mat = template.copy()
    if appended:
        bpy.data.materials.remove(template)

    try:
        mat.asset_clear()
    except (AttributeError, RuntimeError):
        pass
    mat.use_fake_user = False
    if "MAT_PROPS_AS_JSON" in mat:  # stale snapshot of the library material (old name/link)
        del mat["MAT_PROPS_AS_JSON"]

    color_node = mat.node_tree.nodes.get("cus_color") if mat.node_tree else None
    if color_node is not None:
        mat[LIBRARY_DEFAULT_COLOR] = list(color_node.outputs[0].default_value)
    setattr(mat, LIBRARY_ASSET_PROP, name)
    return mat


def new_material_from_library(library_material: str, name: str) -> bpy.types.Material | None:
    mat = _append_library_material(library_material)
    if mat is not None:
        mat.name = name
    return mat


def replace_material_with_library(mat: bpy.types.Material, library_material: str) -> bpy.types.Material | None:
    """swap the shader of an existing material: all users are remapped to the new copy, which takes over the name"""
    new = _append_library_material(library_material)
    if new is None:
        return None
    name = mat.name
    mat.user_remap(new)
    bpy.data.materials.remove(mat)
    new.name = name
    return new


def is_library_shader_material(mat: bpy.types.Material) -> bool:
    return bool(mat is not None and getattr(mat, LIBRARY_ASSET_PROP, ""))


def apply_library_material_color(mat: bpy.types.Material, color, use_color: bool) -> None:
    """tint the library shader via its cus_color node (Custom* materials), restore the library color otherwise"""
    if mat is None or mat.node_tree is None:
        return
    node = mat.node_tree.nodes.get("cus_color")
    if node is None:
        return
    if use_color:
        rgba = list(color)[:4]
        node.outputs[0].default_value = rgba + [1.0] * (4 - len(rgba))
    elif LIBRARY_DEFAULT_COLOR in mat:
        node.outputs[0].default_value = list(mat[LIBRARY_DEFAULT_COLOR])


# -----------------------------
# install (worker thread + main thread poller)
# -----------------------------
class _InstallState:
    def __init__(self):
        self.lock     = threading.Lock()
        self.progress = 0.0
        self.status   = ""
        self.error    = ""
        self.done     = False
        self.result   = None   # installed folder
        self.cancel   = False


_state: _InstallState | None = None


def is_install_running() -> bool:
    return _state is not None and not _state.done


def cancel_install() -> None:
    if _state is not None:
        _state.cancel = True


class _Cancelled(Exception):
    pass


def _get_json(url: str):
    req = urllib.request.Request(url, headers=_HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _resolve_release(edition: str) -> tuple[str, str]:
    """(version, download base url) of the newest release of the edition, pinned version if the API fails"""
    version = MATERIAL_ASSETS_LIB_FALLBACK_VERSION
    try:
        pattern = re.compile(r"^v(.+)-" + re.escape(edition) + r"$")
        for release in _get_json(MATERIAL_ASSETS_LIB_RELEASES_API):
            m = pattern.match(release.get("tag_name", ""))
            if m and not release.get("draft") and not release.get("prerelease") \
                    and any(a.get("name") == "release.json" for a in release.get("assets", [])):
                version = m.group(1)
                break  # API lists newest first
    except (urllib.error.URLError, OSError, ValueError) as e:
        debug(f"material assets library: release lookup failed ({e}), using {version}")
    return version, f"{MATERIAL_ASSETS_LIB_DOWNLOAD_BASE}v{version}-{edition}/"


def _long(path: Path) -> str:
    """windows long path, texture paths of the library come close to MAX_PATH"""
    s = str(path)
    prefix = "\\\\?\\"
    if os.name == "nt" and not s.startswith(prefix):
        s = prefix + os.path.abspath(s)
    return s


def _sha256(path: Path, state: _InstallState) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            if state.cancel:
                raise _Cancelled()
            data = f.read(_CHUNK * 4)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def _install_worker(state: _InstallState, edition: str, root: Path) -> None:
    def status(text, progress=None):
        with state.lock:
            state.status = text
            if progress is not None:
                state.progress = progress
        debug(f"material assets library: {text}")

    staging = None
    try:
        status("Looking up release...", 0)
        version, base_url = _resolve_release(edition)
        manifest = _get_json(base_url + "release.json")
        if manifest.get("edition") != edition or manifest.get("version") != version:
            raise RuntimeError("release edition/version mismatch")

        dest  = root / edition / version
        cache = root / "Downloads" / f"{version}-{edition}"

        if _is_library_folder(dest):
            status(f"{edition} {version} already installed", 100)
            state.result = dest
            return
        if dest.exists():
            raise RuntimeError(f"folder exists but is no complete library, remove it: {dest}")

        archives = manifest.get("archives", [])
        for a in archives:
            if not _VALID_ARCHIVE.match(a.get("name", "")):
                raise RuntimeError("invalid archive name in release.json")

        # download (90%)
        cache.mkdir(parents=True, exist_ok=True)
        total = sum(int(a["bytes"]) for a in archives) or 1
        done_bytes = 0
        for i, a in enumerate(archives, 1):
            target = cache / a["name"]
            label  = f"part {i}/{len(archives)}"
            if target.is_file() and target.stat().st_size == int(a["bytes"]):
                status(f"Checking cached {label}...")
                if _sha256(target, state) == a["sha256"]:
                    done_bytes += int(a["bytes"])
                    continue
            tmp = target.with_name(target.name + ".part")
            h = hashlib.sha256()
            req = urllib.request.Request(base_url + a["name"], headers={"User-Agent": _HTTP_HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
                got = 0
                while True:
                    if state.cancel:
                        raise _Cancelled()
                    data = r.read(_CHUNK)
                    if not data:
                        break
                    f.write(data)
                    h.update(data)
                    got += len(data)
                    status(f"Downloading {label} ({(done_bytes + got) // 2**20} / {total // 2**20} MB)",
                           (done_bytes + got) / total * 90)
            if h.hexdigest() != a["sha256"]:
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"checksum mismatch: {a['name']}")
            tmp.replace(target)
            done_bytes += int(a["bytes"])

        # extract (10%) into a staging folder, moved to dest when complete
        staging = dest.with_name(dest.name + ".installing-" + uuid.uuid4().hex[:8])
        staging.mkdir(parents=True)
        staging_resolved = staging.resolve()
        entries = []
        for a in archives:
            with zipfile.ZipFile(cache / a["name"]) as z:
                entries.append(len([e for e in z.infolist() if not e.is_dir()]))
        count_total, count, seen = sum(entries) or 1, 0, set()
        for a in archives:
            with zipfile.ZipFile(cache / a["name"]) as z:
                for entry in z.infolist():
                    if entry.is_dir():
                        continue
                    if state.cancel:
                        raise _Cancelled()
                    rel = entry.filename.replace("\\", "/")
                    target = (staging / rel).resolve()
                    if staging_resolved not in target.parents:
                        raise RuntimeError(f"archive path escapes the installation folder: {rel}")
                    if rel.lower() in seen:
                        raise RuntimeError(f"duplicate archive entry: {rel}")
                    seen.add(rel.lower())
                    os.makedirs(_long(target.parent), exist_ok=True)
                    with z.open(entry) as src, open(_long(target), "wb") as dst:
                        shutil.copyfileobj(src, dst, _CHUNK)
                    count += 1
                    if count % 25 == 0:
                        status(f"Extracting ({count} / {count_total} files)", 90 + count / count_total * 10)

        expected = {k.replace("\\", "/").lower() for k in manifest.get("files", {})}
        missing = expected - seen
        if expected and missing:
            raise RuntimeError(f"{len(missing)} files missing, e.g. {sorted(missing)[0]}")
        if not _is_library_folder(staging):
            raise RuntimeError("extracted files are no library (blend or MaterialLib.txt missing)")

        staging.replace(dest)
        staging = None
        shutil.rmtree(cache, ignore_errors=True)  # the zips are as large as the library itself
        state.result = dest
        status(f"Installed {edition} {version}", 100)

    except _Cancelled:
        state.error = "Cancelled"
    except Exception as e:  # report every failure in the ui
        state.error = str(e) or type(e).__name__
        debug(f"material assets library install failed: {e!r}")
    finally:
        if staging is not None:
            shutil.rmtree(_long(staging), ignore_errors=True)
        state.done = True


def _finish_install(state: _InstallState) -> None:
    tm_props = get_global_props()
    path = state.result
    register_asset_library(path)
    reset_library_index()
    tm_props.ST_materialLibPath = str(path / "MaterialLib.txt")  # update callback resets the materiallib cache
    try:
        from ..operators.OT_Settings import saveDefaultSettingsJSON
        saveDefaultSettingsJSON()
    except Exception as e:
        debug(f"saving settings after library install failed: {e}")


def start_install(edition: str) -> _InstallState:
    """start the download/installation thread, poll the returned state (progress 0-100, status, done, error)"""
    global _state
    if is_install_running():
        raise RuntimeError("an installation is already running")
    root = get_default_install_root()
    if root is None:
        raise RuntimeError("Trackmania Items folder not found, check the Nadeo.ini setting")
    _state = _InstallState()
    threading.Thread(target=_install_worker, args=(_state, edition, root), daemon=True).start()
    return _state


def finish_install(state: _InstallState) -> str:
    """main thread, after the worker is done without error: register library + Material Lib, returns a message"""
    _finish_install(state)
    return f"{state.status}: {state.result}"
