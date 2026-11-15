"""Keeps the object name and the "Particle effect node" flag in sync.

The converter finds particle nodes in the fbx by the ``_particleFX_`` infix in the object name:
    toggle on   -> infix added to the name
    toggle off  -> infix removed from the name
    rename      -> infix present = node enabled, infix gone = node disabled
"""
import bpy
from bpy.app.handlers import persistent

from ..utils.Constants import SPECIAL_NAME_INFIX_PARTICLEFX as INFIX
from .props import OBJECT_ATTR

_busy = False
_owner = object()


def _settings(obj):
    return getattr(obj, OBJECT_ATTR, None)


def name_with_infix(name: str) -> str:
    return name if INFIX in name else name + INFIX


def name_without_infix(name: str) -> str:
    stripped = name.replace(INFIX, "")
    return stripped or "Empty"


def apply_enabled(obj) -> None:
    """enabled flag changed (UI): rename the object to match"""
    global _busy
    s = _settings(obj)
    if s is None or _busy:
        return
    _busy = True
    try:
        new = name_with_infix(obj.name) if s.enabled else name_without_infix(obj.name)
        if new != obj.name:
            obj.name = new
    finally:
        _busy = False


def sync_from_names(*_args) -> None:
    """object renamed: enable/disable the node to match the infix in the name"""
    global _busy
    if _busy:
        return
    _busy = True
    try:
        for obj in bpy.data.objects:
            s = _settings(obj)
            if s is None:
                continue
            has_infix = INFIX in obj.name
            if has_infix != bool(s.enabled):
                s.enabled = has_infix
    finally:
        _busy = False


def _subscribe() -> None:
    bpy.msgbus.clear_by_owner(_owner)
    bpy.msgbus.subscribe_rna(key=(bpy.types.Object, "name"), owner=_owner, args=(),
                             notify=sync_from_names)


@persistent
def _on_load(*_args) -> None:
    _subscribe()
    sync_from_names()


def register() -> None:
    _subscribe()
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)


def unregister() -> None:
    bpy.msgbus.clear_by_owner(_owner)
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
