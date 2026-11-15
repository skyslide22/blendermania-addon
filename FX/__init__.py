"""tm_fx - schema driven particle/VFX editor for Trackmania 2020 items.

Importing this package never imports ``bpy``; only ``register()`` does, so the
pure-Python modules (``expr``, ``schema``, ``codec``) can be used by tools and
tests outside Blender.
"""
from __future__ import annotations

__version__ = "0.1.0"

_registered = False


def register():
    global _registered
    if _registered:
        return
    from . import props, ops, ui, api, preview, naming  # noqa: F401  (these need bpy)
    props.register()
    naming.register()
    ops.register()
    ui.register()
    preview.register()
    _registered = True


def unregister():
    global _registered
    if not _registered:
        return
    from . import props, ops, ui, preview, naming
    naming.unregister()
    preview.unregister()
    ui.unregister()
    ops.unregister()
    props.unregister()
    _registered = False
