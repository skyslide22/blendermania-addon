"""Particle fx editor for Trackmania 2020 items (ItemConfig.ParticleFx).

Blender properties, UI and the json written to the item config are generated from the
schema in ``schema/base`` (produced from GBX.NET by ``tools/gen_schema.py``).

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
    from . import props, ops, ui, api, preview  # noqa: F401  (these need bpy)
    props.register()
    ops.register()
    ui.register()
    preview.register()
    _registered = True


def unregister():
    global _registered
    if not _registered:
        return
    from . import props, ops, ui, preview
    preview.unregister()
    ui.unregister()
    ops.unregister()
    props.unregister()
    _registered = False
