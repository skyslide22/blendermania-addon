"""Public API for your item exporter.

    from tm_fx import api
    doc = api.export_fx(obj)            # dict to embed in your item JSON, or None if obj is not an FX node
    warnings = api.import_fx(obj, doc)  # load FX from a dict (e.g. dumped from a working item)
"""
import bpy

from . import bridge, codec
from .props import OBJECT_ATTR, get_schema


def _settings(obj=None):
    return getattr(obj or bpy.context.object, OBJECT_ATTR)


def is_fx_node(obj):
    s = getattr(obj, OBJECT_ATTR, None)
    return bool(s and s.enabled)


def export_fx(obj=None):
    return bridge.export_document(_settings(obj))


def import_fx(obj, data, as_template=False):
    return bridge.import_document(_settings(obj), data, as_template)


def validate_fx(obj=None):
    doc = export_fx(obj)
    return codec.validate(get_schema(), doc["vfx"]) if doc else []
