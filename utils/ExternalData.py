"""External files of a shared .blend (linked asset libraries, textures) on another machine.

Paths saved in a .blend belong to the machine that saved it: relative only if on the same drive, otherwise
absolute (e.g. Documents/Trackmania linked to another drive). On load, missing files are relinked to this
machine's install when possible:
    - anything inside the sender's Trackmania/Items      -> same path inside this machine's Items
    - TM2020_DefaultAssets.blend                        -> this machine's installed default assets
    - TM2020 Material Assets Library textures            -> this machine's installed edition/version
    - addon shader textures (_BlenderAssets)             -> by file name in the texture roots
Only missing files are touched. Whatever stays missing is reported in a popup.
"""

import os
import re
from pathlib import Path

import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator

_last_result: dict = {}


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _exists(path) -> bool:
    try:
        p = str(path)
        if os.name == "nt" and len(p) >= 240 and not p.startswith("\\\\?\\"):
            p = "\\\\?\\" + os.path.abspath(p)
        return os.path.exists(p)
    except (OSError, ValueError):
        return False


def _local_items() -> str | None:
    try:
        from .Functions import get_game_doc_path_items
        path = get_game_doc_path_items()
    except Exception:
        return None
    return _norm(path).rstrip("/") if path and os.path.isdir(path) else None


def rebase_on_local_items(path: str) -> str | None:
    """existing file at the same place inside this machine's Items folder (tries every '/Items/' of the path)"""
    items = _local_items()
    if not items:
        return None
    norm = _norm(path)
    for m in re.finditer(r"/items/", norm, flags=re.IGNORECASE):
        candidate = items + "/" + norm[m.end():]
        if _exists(candidate):
            return candidate
    return None


def _rebase_material_library(path: str) -> str | None:
    """texture of another edition/version of the material library -> installed one"""
    m = re.search(r"/MaterialAssetsLibrary/[^/]+/[^/]+/(.+)$", _norm(path), flags=re.IGNORECASE)
    if m is None:
        return None
    try:
        from .MaterialAssetsLibrary import get_installed_library_path
        lib = get_installed_library_path()
    except Exception:
        lib = None
    if lib is None:
        return None
    candidate = _norm(str(lib)).rstrip("/") + "/" + m.group(1)
    return candidate if _exists(candidate) else None


_texture_index: dict | None = None


def _addon_texture(filename: str) -> str | None:
    """addon shader texture by file name (texture roots: addon textures, material library textures)"""
    global _texture_index
    if _texture_index is None:
        _texture_index = {}
        try:
            from .Materials import get_texture_roots
            roots = get_texture_roots()
        except Exception:
            roots = []
        for root in roots:
            try:
                for env in os.scandir(root):
                    if env.is_dir():
                        for f in os.scandir(env.path):
                            _texture_index.setdefault(f.name.lower(), _norm(f.path))
            except OSError:
                pass
    return _texture_index.get(filename.lower())


def _default_assets_blend() -> str | None:
    try:
        from .DefaultAssetsLibrary import get_built_default_assets, DEFAULT_ASSETS_BLEND
        root = get_built_default_assets()
    except Exception:
        return None
    return _norm(str(root / DEFAULT_ASSETS_BLEND)) if root else None


def _abspath(id_block, path: str) -> str:
    return _norm(bpy.path.abspath(path, library=getattr(id_block, "library", None)))


def _find_library(lib) -> str | None:
    old = _abspath(lib, lib.filepath)
    from .DefaultAssetsLibrary import DEFAULT_ASSETS_BLEND
    if os.path.basename(old).lower() == DEFAULT_ASSETS_BLEND.lower():
        found = _default_assets_blend()
        if found:
            return found
    return rebase_on_local_items(old)


def _find_image(img) -> str | None:
    old = _abspath(img, img.filepath)
    found = _rebase_material_library(old) or rebase_on_local_items(old)
    if found is None and re.search(r"/(_BlenderAssets|MaterialAssetsLibrary)/", old, flags=re.IGNORECASE):
        found = _addon_texture(os.path.basename(old))
    return found


def _is_file_image(img) -> bool:
    return (img.source in {"FILE", "SEQUENCE", "TILED"} and not img.packed_file and img.library is None
            and bool(img.filepath))


def check_external_data(relink: bool = True) -> dict:
    """relink missing libraries/images where this machine has them, return what was relinked/still missing"""
    global _texture_index
    _texture_index = None
    result = {"relinked_libraries": [], "relinked_images": [], "missing_libraries": [], "missing_images": []}

    for name in [lib.name for lib in bpy.data.libraries]:   # reload() replaces the Library struct: go by name
        lib = bpy.data.libraries.get(name)
        if lib is None or _exists(_abspath(lib, lib.filepath)):
            continue
        found = _find_library(lib) if relink else None
        if found:
            lib.filepath = found
            try:
                lib.reload()
            except RuntimeError:
                pass
            result["relinked_libraries"].append(name)
        else:
            result["missing_libraries"].append(name)

    for img in bpy.data.images:
        if not _is_file_image(img) or _exists(_abspath(img, img.filepath)):
            continue
        found = _find_image(img) if relink else None
        if found:
            img.filepath = found
            try:
                img.reload()
            except RuntimeError:
                pass
            result["relinked_images"].append(img.name)
        else:
            result["missing_images"].append((img.name, _abspath(img, img.filepath)))

    _last_result.clear()
    _last_result.update(result)
    return result


def _hints(result: dict) -> list:
    """what to install; only for things that are not installed on this PC at all"""
    from .DefaultAssetsLibrary import DEFAULT_ASSETS_BLEND
    hints = []
    if any(DEFAULT_ASSETS_BLEND.lower() in n.lower() for n in result["missing_libraries"]) and not _default_assets_blend():
        hints.append("Default Assets: install them in Settings > Asset Libraries")
    paths = [p.lower() for _, p in result["missing_images"]]
    if any("/materialassetslibrary/" in p for p in paths):
        try:
            from .MaterialAssetsLibrary import get_installed_library_path
            installed = get_installed_library_path() is not None
        except Exception:
            installed = False
        if not installed:
            hints.append("Material Library textures: install it in Settings > Asset Libraries")
    items = _local_items()
    if any("/_blenderassets/textures/" in p for p in paths) and not (items and os.path.isdir(items + "/_BlenderAssets/Textures")):
        hints.append("Addon textures: Textures > Install & Update")
    return hints


def is_actionable(result: dict) -> bool:
    """worth a popup on load: relinked something, a library is missing, or something can be installed.
    Textures missing everywhere (e.g. a few files no library has) are only listed by the manual check."""
    return bool(result["relinked_libraries"] or result["relinked_images"] or result["missing_libraries"]
                or _hints(result))


def show_result_popup(result: dict, always: bool = False) -> None:
    missing = result["missing_libraries"] or result["missing_images"]
    relinked = result["relinked_libraries"] or result["relinked_images"]
    if bpy.app.background or not (missing or relinked or always):
        return

    def draw(self, context):
        lay = self.layout
        if relinked:
            lay.label(text=f"Relinked to this PC: {len(result['relinked_libraries'])} libraries, "
                           f"{len(result['relinked_images'])} images (save the file to keep it)", icon="LINKED")
        if not missing:
            lay.label(text="All external files found", icon="CHECKMARK")
            return
        for name in result["missing_libraries"][:8]:
            lay.label(text=f"Library missing: {name}", icon="LIBRARY_DATA_BROKEN")
        imgs = result["missing_images"]
        for name, _path in imgs[:8]:
            lay.label(text=f"Image missing: {name}", icon="IMAGE_DATA")
        if len(imgs) > 8:
            lay.label(text=f"... and {len(imgs) - 8} more images")
        for hint in _hints(result):
            lay.label(text=hint, icon="INFO")
        lay.label(text="Assets from missing libraries are skipped on export.", icon="ERROR")
        lay.label(text="Other files: File > External Data > Find Missing Files")
        lay.operator(TM_OT_CheckExternalData.bl_idname, text="Check again", icon="FILE_REFRESH")

    title = "Missing external files" if missing else "External files relinked"
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR" if missing else "INFO")


class TM_OT_CheckExternalData(Operator):
    bl_idname = "tm.check_external_data"
    bl_label = "Check Missing Files"
    bl_description = ("Relink missing asset libraries and textures of this .blend to this PC's Trackmania "
                      "install (Items folder, material library, default assets) and list what is still missing")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = check_external_data()
        show_result_popup(result, always=True)
        return {"FINISHED"}


@persistent
def _on_load_post(_dummy=None):
    if not bpy.data.filepath:
        return
    try:
        result = check_external_data()
    except Exception as e:  # never break file loading
        print(f"Blendermania: external data check failed: {e}")
        return
    if result["missing_images"]:
        print(f"Blendermania: {len(result['missing_images'])} missing image(s): "
              + ", ".join(n for n, _ in result["missing_images"][:20]))
    if is_actionable(result):
        bpy.app.timers.register(lambda: show_result_popup(result), first_interval=1.0)


def register():
    bpy.utils.register_class(TM_OT_CheckExternalData)
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
    bpy.utils.unregister_class(TM_OT_CheckExternalData)
