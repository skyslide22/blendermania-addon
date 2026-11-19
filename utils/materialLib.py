"""
NadeoImporterMaterialLib.txt parser for the NEW (TM2020 / V2) material system.

This module is fully isolated from the legacy material system:
it only reads ST_materialLibPath and never writes to any tm_props or legacy linked-material state.
"""
import re
import bpy
from ..properties.PropertyIdentifiers import ObjectProp

from ..utils.Functions import get_global_props, is_file_existing, debug, redraw_all_panels
from ..utils.Constants import LINKED_MATERIALS_WITH_TARGET_COLOR_LINKFULL


materiallib_materials: dict = {}

# V2 link search field: scene collection (items searched by prop_search) is filled for the selected collection
_link_search_collection_synced = ""
_link_search_sync_pending = False


def is_link_search_synced(collection_name: str) -> bool:
    scene = bpy.context.scene
    names = get_materiallibrary_material_names(collection_name)
    return bool(names) and _link_search_collection_synced == collection_name and len(scene.tm_props_linkedMaterialsLibrary) == len(names)


def sync_link_search_collection(collection_name: str) -> None:
    """fill scene.tm_props_linkedMaterialsLibrary with the materials of the collection (not allowed while drawing)"""
    global _link_search_collection_synced
    items = bpy.context.scene.tm_props_linkedMaterialsLibrary
    items.clear()
    for name in get_materiallibrary_material_names(collection_name):
        items.add().name = name
    _link_search_collection_synced = collection_name


def reset_materiallibrary_cache() -> None:
    """drop parsed materiallib and link search state, everything is rebuilt lazily from the current ST_materialLibPath"""
    global _link_search_collection_synced
    materiallib_materials.clear()
    _link_search_collection_synced = ""
    try:
        bpy.context.scene.tm_props_linkedMaterialsLibrary.clear()
    except AttributeError:
        pass


def request_link_search_sync() -> None:
    """drawing can't write properties, so the sync is done by a one-shot timer"""
    global _link_search_sync_pending
    if _link_search_sync_pending:
        return
    _link_search_sync_pending = True

    def _run():
        global _link_search_sync_pending
        _link_search_sync_pending = False
        try:
            sync_link_search_collection(str(get_global_props().LI_materialCollectionLibrary))
            redraw_all_panels()
        except Exception as e:
            debug(f"V2 link search sync failed: {e}")
        return None

    bpy.app.timers.register(_run, first_interval=0.0)

_REGEX_DLIBRARY   = re.compile(r"DLibrary\t*\(([\w-]+)")
_REGEX_DMATERIAL  = re.compile(r"DMaterial\t*\(([\w+-]+)\)")
_REGEX_DSURFACEID = re.compile(r"DSurfaceId(?:\t*|\s*)\(([\w-]+)\)")
_REGEX_DLINKFULL  = re.compile(r"DLinkFull\s*\(([^)]*)\)")
_REGEX_DTEXTURE   = re.compile(r"DTexture(?:\t*|\s*)\((?:\t*|\s*)([\w\-\.]+)\)")


def get_materiallibrary_collection_names() -> list:
    return sorted(get_materiallibrary_materials().keys())


def get_materiallibrary_material_names(collection_name: str) -> list:
    return sorted(get_materiallibrary_materials().get(collection_name, {}).keys())


def get_materiallibrary_materials() -> dict:
    if not materiallib_materials:
        parse_materiallibrary()
    return materiallib_materials


def material_supports_color(material_name: str, collection_name: str) -> bool:
    """
    True if the linked game material has the native TargetColor parameter (the converter writes colors as TargetColor).
    DColor0 is NOT the right indicator (it marks vertex color usage), "Custom*" by name is too broad (CustomMod* use color tables).
    """
    material = get_materiallibrary_materials().get(collection_name, {}).get(material_name)
    if material is not None and material.get("LinkFull"):
        return material["LinkFull"].lower() in LINKED_MATERIALS_WITH_TARGET_COLOR_LINKFULL
    # not in the selected materiallib: compare by name (aliases like Stadium_CustomConcrete are prefixed)
    name = material_name.lower()
    return any(name == n or name.endswith("_" + n) for n in _TARGET_COLOR_NAMES)


def _target_color_name(linkfull: str) -> str:
    """stadium/media/material_blockcustom/customice -> customice, .../modifier/platformice/decograss -> platformice_decograss"""
    parts = linkfull.split("\\")
    return "_".join(parts[3:]) if len(parts) > 3 and parts[2] == "modifier" else parts[-1]


_TARGET_COLOR_NAMES = {_target_color_name(full) for full in LINKED_MATERIALS_WITH_TARGET_COLOR_LINKFULL}

def has_material_with_gameplay_effect(obj: bpy.types.Object) -> str | None:
    """True if the object has any material with a gameplay effect."""
    if not obj or not obj.data or not hasattr(obj.data, "materials"):
        return None
    for mat in obj.data.materials:
        if mat and getattr(mat, "useGameplayId", False):
            return getattr(mat, "gameplayId", None)
    return None

def has_material_with_material_override(obj: bpy.types.Object) -> str | None:
    """True if the object has any material with a gameplay effect."""
    if not obj or not obj.data or not hasattr(obj.data, "materials"):
        return None
    if getattr(obj, ObjectProp.OVERRIDE_MATERIAL, False):
        return getattr(obj, ObjectProp.SURFACE_MATERIAL_TYPE, None)
    return None

def parse_materiallibrary() -> dict:
    """parse NadeoImporterMaterialLib.txt into materiallib_materials, no side effects on other state"""
    global materiallib_materials

    nadeolibfile = get_global_props().ST_materialLibPath
    if not nadeolibfile or not is_file_existing(nadeolibfile):
        return materiallib_materials

    lib = {}
    currentLib = ""
    currentLibRaw = ""
    currentMat = ""

    try:
        with open(nadeolibfile, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "DLibrary" in line:
                    m = _REGEX_DLIBRARY.search(line)
                    if m:
                        currentLib = m.group(1)
                        currentLibRaw = currentLib  # LinkFull keeps the real library (Stadium256)
                        if currentLib == "Stadium256":  # same as Stadium for addon needs
                            currentLib = "Stadium"
                        currentMat = ""
                        lib.setdefault(currentLib, {})

                if not currentLib:
                    continue

                if "DMaterial" in line:
                    m = _REGEX_DMATERIAL.search(line)
                    if m:
                        currentMat = m.group(1)
                        lib[currentLib][currentMat] = {
                            "MatName": currentMat,
                            "PhysicsId": "Concrete",
                            "Color": False,
                            "Model": "TDSN",
                            "Envi": currentLib,
                        }

                if not currentMat:
                    continue

                mat = lib[currentLib][currentMat]

                if "DLinkFull" in line:
                    m = _REGEX_DLINKFULL.search(line)
                    if m:
                        mat["LinkFull"] = currentLibRaw + "\\" + m.group(1).strip()

                if "DSurfaceId" in line:
                    m = _REGEX_DSURFACEID.search(line)
                    if m:
                        mat["PhysicsId"] = m.group(1)

                if "DColor0" in line:
                    mat["Color"] = True

                if "DTexture" in line:
                    m = _REGEX_DTEXTURE.search(line)
                    nadeoTex = m.group(1) if m else ""
                    for suffix in ("D", "S", "N", "I"):
                        key = f"NadeoTex{suffix}"
                        mat.setdefault(key, "")
                        if mat[key] == "" and nadeoTex.lower().endswith(f"{suffix.lower()}.dds"):
                            mat[key] = nadeoTex

        materiallib_materials = lib

    except OSError as e:
        debug("failed to parse nadeolib (V2)")
        debug(e)

    return materiallib_materials
