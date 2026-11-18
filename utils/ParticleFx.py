"""Validation of particle fx empties (see FX package, ItemConfig.ParticleFx)."""
from __future__ import annotations

from .FunctionsV2 import is_particle_fx_node


def get_particle_fx_issues(objs=()) -> list[str]:
    """errors of all particle fx empties among the exported objects of an item"""
    from ..FX import api as fx_api

    errors: list[str] = []
    for obj in sorted(objs, key=lambda o: o.name):
        if is_particle_fx_node(obj):
            errors += fx_api.get_fx_issues(obj)
    return list(dict.fromkeys(errors))
