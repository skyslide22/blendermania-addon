"""User defined UI layout (``layout.json``) - pure python, no ``bpy``.

``layout.json`` is the only file you need to edit to decide which fields the
simple "Particle" panel shows, in which order, under which headings.

    {
      "sections": [
        {
          "title": "Texture",                  # heading of the box
          "target": "CPlugParticleGpuModel",   # schema class the fields belong to
          "open": true,                        # optional, default true
          "fields": [
            "TextureAtlasDimX",                # plain key (see schema/base/<class>.json "key")
            {"key": "BitmapFile",              # or an object:
             "label": "Texture",               #   label override
             "widget": "texture"}              #   "texture" = file picker, default = schema widget
          ]
        }
      ]
    }

Sections are drawn for the node that is selected in the emitter list, so every
section only shows when the selected node is of its ``target`` class.
"""
import json
from pathlib import Path

LAYOUT_PATH = Path(__file__).resolve().parent / "layout.json"
_cache = {"mtime": None, "data": None, "error": ""}


def _norm_field(f):
    if isinstance(f, str):
        return {"key": f}
    return dict(f)


def load(force=False):
    """Return ``{"sections": [...], "error": str}``; re-reads the file when it changed."""
    try:
        mtime = LAYOUT_PATH.stat().st_mtime
    except OSError:
        return {"sections": [], "error": f"{LAYOUT_PATH.name} not found"}
    if not force and _cache["mtime"] == mtime and _cache["data"] is not None:
        return _cache["data"]
    try:
        with open(LAYOUT_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        sections = []
        for s in raw.get("sections", []):
            sections.append({
                "title": s.get("title", s.get("target", "")),
                "target": s["target"],
                "open": s.get("open", True),
                "fields": [_norm_field(f) for f in s.get("fields", [])],
            })
        data = {"sections": sections, "error": ""}
    except (ValueError, KeyError, TypeError) as e:
        data = {"sections": [], "error": f"layout.json: {e}"}
    _cache.update(mtime=mtime, data=data)
    return data


def targets(layout=None):
    layout = layout or load()
    return {s["target"] for s in layout["sections"]}
