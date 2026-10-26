"""
NadeoImporterMaterialLib.txt parser for the NEW (TM2020 / V2) material system.

This module is fully isolated from the legacy material system:
it only reads ST_materialLibPath and never writes to any tm_props or legacy linked-material state.
"""
import re
import bpy

from ..utils.Functions import get_global_props, is_file_existing, debug, redraw_all_panels


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
    """True if the material has a color entry (DColor0) in the material library."""
    can_use_custom_color = material_name.lower().startswith("custom")
    return can_use_custom_color
    material = get_materiallibrary_materials().get(collection_name, {}).get(material_name)
    if material is None:
        return False
    return material.get("Color", False) is True

def has_material_with_gameplay_effect(obj: bpy.types.Object) -> str | None:
    """True if the object has any material with a gameplay effect."""
    if not obj or not obj.data or not hasattr(obj.data, "materials"):
        return None
    for mat in obj.data.materials:
        if mat and getattr(mat, "useGameplayId", False):
            return getattr(mat, "gameplayId", None)
    return None

def parse_materiallibrary() -> dict:
    """parse NadeoImporterMaterialLib.txt into materiallib_materials, no side effects on other state"""
    global materiallib_materials

    nadeolibfile = get_global_props().ST_materialLibPath
    if not nadeolibfile or not is_file_existing(nadeolibfile):
        return materiallib_materials

    lib = {}
    currentLib = ""
    currentMat = ""

    try:
        with open(nadeolibfile, "r") as f:
            for line in f:
                if "DLibrary" in line:
                    m = _REGEX_DLIBRARY.search(line)
                    if m:
                        currentLib = m.group(1)
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
