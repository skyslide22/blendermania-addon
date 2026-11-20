"""Shared template storage for placement parameters, placement classes and particle fx.

Sources of a template kind:
    BUILTIN  shipped with the addon: assets/templates/<kind>/<name>.json (read-only; the file is the data itself)
    LOCAL    this machine: %APPDATA%/Blendermania/templates/<kind>/<name>.json
             ({"format", "kind", "name", "data"}; survives addon updates, can be shared as files)
    BLEND    embedded in the .blend - only for kinds that are assigned by name (placement parameters,
             handled in ItemsExportV2Models), so a shared file exports the same everywhere.

Insert-only kinds (placement class, particle fx) never go into the blend: inserting copies the values.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .Constants import PATH_SETTINGS_FOLDER
from .FunctionsV2 import get_addon_templates_path

SOURCE_BUILTIN = "BUILTIN"
SOURCE_LOCAL = "LOCAL"
SOURCE_BLEND = "BLEND"

SOURCE_LABELS = {SOURCE_BUILTIN: "Built-in", SOURCE_LOCAL: "Local", SOURCE_BLEND: "Blend file"}
SOURCE_ICONS = {SOURCE_BUILTIN: "PACKAGE", SOURCE_LOCAL: "HOME", SOURCE_BLEND: "BLENDER"}

KIND_PLACEMENT = "placement"
KIND_PLACEMENT_CLASS = "placement_class"
KIND_PARTICLE_FX = "particle_fx"

KIND_LABELS = {KIND_PLACEMENT: "Placement Parameters", KIND_PLACEMENT_CLASS: "Attachment (Placement Class)",
               KIND_PARTICLE_FX: "Particle FX"}

FILE_FORMAT = "blendermania-template/1"
_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class TemplateEntry:
    kind: str
    name: str
    source: str
    path: str = ""          # file of BUILTIN / LOCAL templates

    @property
    def id(self) -> str:
        """unique within a kind (used by pickers of insert-only kinds)"""
        return f"{self.source}|{self.name}"

    @property
    def label(self) -> str:
        return self.name.replace("_", " ") if self.source == SOURCE_BUILTIN else self.name


# ------------------------------------------------------------------ folders
def builtin_dir(kind: str) -> str:
    return os.path.join(get_addon_templates_path(), kind)


def local_root() -> str:
    return os.path.join(PATH_SETTINGS_FOLDER, "templates")


def local_dir(kind: str, create: bool = False) -> str:
    d = os.path.join(local_root(), kind)
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def file_name(name: str) -> str:
    """file name for a template name (names stay intact inside the file)"""
    stem = _INVALID.sub("_", name).strip().rstrip(".") or "template"
    return stem + ".json"


# ------------------------------------------------------------------ listing
def _scan(folder: str, kind: str, source: str) -> list[TemplateEntry]:
    out = []
    if not os.path.isdir(folder):
        return out
    for f in sorted(os.listdir(folder), key=str.lower):
        if not f.lower().endswith(".json"):
            continue
        path = os.path.join(folder, f)
        name = f[:-5]
        if source == SOURCE_LOCAL:
            try:
                with open(path, encoding="utf-8") as fh:
                    name = json.load(fh).get("name") or name
            except (OSError, ValueError, AttributeError):
                continue
        out.append(TemplateEntry(kind, name, source, path))
    return out


def builtin_entries(kind: str) -> list[TemplateEntry]:
    return _scan(builtin_dir(kind), kind, SOURCE_BUILTIN)


def local_entries(kind: str) -> list[TemplateEntry]:
    return _scan(local_dir(kind), kind, SOURCE_LOCAL)


def file_entries(kind: str) -> list[TemplateEntry]:
    """built-in then local templates"""
    return builtin_entries(kind) + local_entries(kind)


def find_entry(kind: str, entry_id: str) -> TemplateEntry | None:
    for e in file_entries(kind):
        if e.id == entry_id:
            return e
    return None


def find_local(kind: str, name: str) -> TemplateEntry | None:
    for e in local_entries(kind):
        if e.name == name:
            return e
    return None


# ------------------------------------------------------------------ read / write
def read(entry: TemplateEntry):
    """template data (built-in files are the data, local files wrap it)"""
    with open(entry.path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if entry.source == SOURCE_LOCAL and isinstance(doc, dict) and doc.get("format") == FILE_FORMAT:
        return doc.get("data")
    return doc


def _json_default(o):
    try:
        return list(o)  # mathutils Vector/Color/Euler, sets
    except TypeError:
        return str(o)


def save_local(kind: str, name: str, data) -> str:
    """write (or overwrite) local template ``name``; returns the file path"""
    name = name.strip()
    if not name:
        raise ValueError("template name is empty")
    old = find_local(kind, name)
    path = old.path if old else os.path.join(local_dir(kind, create=True), file_name(name))
    if old is None and os.path.exists(path):   # another name maps to the same file name
        stem, n = path[:-5], 2
        while os.path.exists(f"{stem}_{n}.json"):
            n += 1
        path = f"{stem}_{n}.json"
    text = json.dumps({"format": FILE_FORMAT, "kind": kind, "name": name, "data": data},
                      indent=2, default=_json_default)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:   # a failure must not truncate an existing template
        fh.write(text)
    os.replace(tmp, path)
    return path


def delete_local(kind: str, name: str) -> bool:
    e = find_local(kind, name)
    if e is None:
        return False
    os.remove(e.path)
    return True


def migrate_settings_json_placement(old_templates: list) -> int:
    """one-time move of the placement templates kept in settings.json into the local folder.
    Runs only while the folder does not exist yet; the settings.json entry stays as a backup."""
    if os.path.isdir(local_dir(KIND_PLACEMENT)):
        return 0
    local_dir(KIND_PLACEMENT, create=True)
    n = 0
    for t in old_templates or []:
        name = (t or {}).get("name")
        if name:
            save_local(KIND_PLACEMENT, name, t.get("config", {}))
            n += 1
    return n
