"""Public API used by the item exporter (utils/ItemConfigBuilder.py) and the panels.

    from ..FX import api as fx_api
    if fx_api.is_fx_node(obj):
        doc = fx_api.export_fx(obj, asset_ref)   # ItemConfig.ParticleFx[].Fx
"""
from . import bridge, codec
from .codec import ROOT_CLASS
from .props import OBJECT_ATTR, get_schema, is_fx_node  # noqa: F401  (re-exported)


def _settings(obj):
    return getattr(obj, OBJECT_ATTR)


def export_fx(obj, asset_ref=None):
    """``{"format", "vfx"}`` document. ``asset_ref(material) -> asset id`` registers the
    bitmap assets of the item (see ItemConfigBuilder._asset_ref); default: material name."""
    return bridge.export_document(_settings(obj), asset_ref)


def import_fx(obj, data, as_template=False) -> list:
    return bridge.import_document(_settings(obj), data, as_template)


def init_fx(obj) -> None:
    """Called when an object becomes a particle fx node."""
    if is_fx_node(obj):
        bridge.init_document(_settings(obj))


def get_fx_issues(obj) -> list:
    """Errors that make the converter fail (empty list = exportable)."""
    issues = []
    s = _settings(obj)
    try:
        doc = export_fx(obj)
    except Exception as e:   # never let validation break the export dialog
        return [f"<{obj.name}>: fx data can not be read ({e})"]
    root = doc["vfx"]["props"].get("Root") or {}
    if root.get("props", {}).get("Type", -1) < 0:
        issues.append(f"<{obj.name}>: root effect node has no type")
    for mat in bridge.used_assets(s.vfx, ROOT_CLASS):
        props = mat.tm_asset_properties
        if props.asset_type != "BITMAP":
            issues.append(f"<{obj.name}>: asset <{mat.name}> is not a bitmap asset")
    return list(dict.fromkeys(issues))


def validate_fx(obj) -> list:
    """Non-fatal findings of the schema validation (unknown enum values, unsorted curve keys, ...)."""
    try:
        return codec.validate(get_schema(), export_fx(obj)["vfx"], ROOT_CLASS)
    except Exception as e:
        return [str(e)]
