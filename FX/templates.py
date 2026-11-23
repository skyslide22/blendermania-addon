"""Particle fx templates (built-in: assets/templates/particle_fx/*.json, local: utils/TemplateLibrary).

A template is a "tm-fx/1" document as written by bridge.export_document: bitmaps are bitmap asset names.
Built-in templates use the default asset library's names (BMP_FoggerSmoke, BMP_Sparkler_D, ...); missing
ones are linked from the installed default asset library when a template is used.
"""
import copy

import bpy

from . import bridge
from .codec import ROOT_CLASS


def _bitmap_names(node, out: set) -> set:
    if isinstance(node, dict):
        if node.get("$class") == "CPlugParticleGpuModel":
            name = (node.get("props") or {}).get("Bitmap")
            if isinstance(name, str) and name:
                out.add(name)
        for v in node.values():
            _bitmap_names(v, out)
    elif isinstance(node, list):
        for v in node:
            _bitmap_names(v, out)
    return out


def link_missing_bitmaps(names) -> list:
    """link bitmap assets that are not in this file from the default asset library; returns warnings"""
    missing = [n for n in sorted(names) if bpy.data.materials.get(n) is None]
    if not missing:
        return []
    from ..ui.widgets.asset_picker import _default_library_materials
    blend, available = _default_library_materials()
    if blend is None:
        return [f"default asset library not installed: bitmap(s) {', '.join(missing)} left empty "
                "(Blendermania > Asset Library)"]
    wanted = [n for n in missing if n in available]
    if wanted:
        with bpy.data.libraries.load(str(blend), link=True) as (_src, dst):
            dst.materials = wanted
    return [f"bitmap '{n}' is not in the default asset library, left empty" for n in missing if n not in available]


def _merge(current: dict, extra: dict) -> dict:
    """``current`` fx system + the effect nodes (emitters, variable updates, conditions) and variables of ``extra``"""
    out = copy.deepcopy(current)
    root = out["props"]["Root"]["props"]
    kids = list(root.get("Children") or [])
    kids += copy.deepcopy((extra["props"]["Root"]["props"].get("Children") or []))
    root["Children"] = kids
    known = {v["props"].get("Name") for v in (out["props"].get("Variables") or [])}
    variables = list(out["props"].get("Variables") or [])
    for v in extra["props"].get("Variables") or []:
        if v["props"].get("Name") not in known:
            variables.append(copy.deepcopy(v))
    out["props"]["Variables"] = variables
    # expressions of the added nodes may need the input context of the template (e.g. DecorationColorHSL)
    if out["props"].get("InputClassId") in (None, 4294967295):
        out["props"]["InputClassId"] = extra["props"].get("InputClassId", out["props"].get("InputClassId"))
    return out


def apply(settings, doc: dict, add: bool = False) -> list:
    """insert (replace the effect, it becomes the 'changed values' baseline) or add the template's emitters"""
    root = doc.get("vfx", doc)
    if root.get("$class") != ROOT_CLASS:
        return [f"template root is {root.get('$class')}, expected {ROOT_CLASS}: nothing changed"]
    warnings = link_missing_bitmaps(_bitmap_names(root, set()))
    if not add:
        return warnings + bridge.import_document(settings, {"vfx": root}, as_template=True)
    baseline = settings.template_json
    current = bridge.read_node(settings.vfx, ROOT_CLASS)
    warnings += bridge.import_document(settings, {"vfx": _merge(current, root)}, as_template=False)
    settings.template_json = baseline          # adding emitters keeps the previous baseline
    return warnings

