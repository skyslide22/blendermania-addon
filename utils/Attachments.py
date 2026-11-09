from __future__ import annotations

from typing import Callable

import bpy
from mathutils import Matrix, Quaternion, Vector

from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp
from ..properties.AttachmentProperties import get_attachment_option_dicts
from .FunctionsV2 import (
    get_item_attachment_collections,
    get_offset_from_item_origin,
    is_collection_instance,
)
from .ItemsExportV2Models import AttachmentConfig, Vec3


def _fresh_world_matrix(obj: bpy.types.Object) -> Matrix:
    """world matrix built from the current location/rotation/scale of the object and its parents (matrix_world can be stale)"""
    matrix = obj.matrix_basis.copy()
    if obj.parent is not None:
        matrix = _fresh_world_matrix(obj.parent) @ obj.matrix_parent_inverse @ matrix
    return matrix


# -----------------------------
# locator sources
# -----------------------------
# A locator source reads the attachment points of ONE attachment collection (own objects only) and returns their
# world matrices. Add further ways to define points (curves, vertices, ...) by registering another source.
LocatorSource = Callable[[bpy.types.Collection], list[Matrix]]
_LOCATOR_SOURCES: dict[str, LocatorSource] = {}

def register_locator_source(name: str, source: LocatorSource) -> None:
    _LOCATOR_SOURCES[name] = source

def unregister_locator_source(name: str) -> None:
    _LOCATOR_SOURCES.pop(name, None)


def _empties_source(col: bpy.types.Collection) -> list[Matrix]:
    """plain empties: position and rotation of the empty"""
    empties = [o for o in col.objects
               if o.type == 'EMPTY' and not is_collection_instance(o) and not getattr(o, ObjectProp.IGNORE, False)]
    return [_fresh_world_matrix(o) for o in sorted(empties, key=lambda o: o.name)]

register_locator_source("EMPTIES", _empties_source)


def get_attachment_locators(col: bpy.types.Collection) -> list[Matrix]:
    """world matrices of all attachment points defined in the collection"""
    matrices: list[Matrix] = []
    for name in _LOCATOR_SOURCES:
        matrices += _LOCATOR_SOURCES[name](col)
    return matrices


# -----------------------------
# config
# -----------------------------
def _iter_instance_occurrences(objs, stack: tuple = ()):
    """(instanced collection, matrix from the collection space to world) for every instance occurrence, nested instances included"""
    for inst in sorted((o for o in objs if is_collection_instance(o)), key=lambda o: o.name):
        yield from _walk_instance(inst, _fresh_world_matrix(inst), stack)

def _walk_instance(inst: bpy.types.Object, inst_world: Matrix, stack: tuple):
    col = inst.instance_collection
    if col.name in stack:   # instance cycle
        return
    to_world = inst_world @ Matrix.Translation(-Vector(col.instance_offset))
    yield col, to_world
    for o in col.all_objects:
        if is_collection_instance(o):
            yield from _walk_instance(o, to_world @ _fresh_world_matrix(o), stack + (col.name,))

def get_attachment_configs(item_collection: bpy.types.Collection, item_objects: list[bpy.types.Object]) -> list[AttachmentConfig]:
    """
    one AttachmentConfig per attachment collection (of the item and of the collections it instances), holding all its
    attachment points; an attachment collection inside an instanced collection adds its points once per instance.
    Positions/rotations are relative to the item origin (the same origin the fbx is exported with)
    """
    offset = get_offset_from_item_origin(item_objects) or [0.0, 0.0, 0.0]

    configs: dict[str, AttachmentConfig] = {}

    def add(col: bpy.types.Collection, to_world: Matrix) -> None:
        attachment = getattr(col, CollectionProp.ATTACHMENT, None)
        if attachment is None:
            return
        locators = get_attachment_locators(col)
        if not locators:
            return
        config = configs.get(col.name)
        if config is None:
            config = configs[col.name] = AttachmentConfig(
                Layout=int(attachment.layout),
                Options=get_attachment_option_dicts(attachment),
            )
        for world in locators:
            loc, rot, _scale = (to_world @ world).decompose()
            config.Positions.append(Vec3(loc.x - offset[0], loc.y - offset[1], loc.z - offset[2]))
            config.Rotations.append(Quaternion(rot))

    identity = Matrix.Identity(4)
    for col in get_item_attachment_collections(item_collection):
        add(col, identity)
    for inst_col, to_world in _iter_instance_occurrences(item_objects):
        for col in get_item_attachment_collections(inst_col):
            add(col, to_world)

    return list(configs.values())


# -----------------------------
# particles
# -----------------------------
def _particle_matrices(obj_eval: bpy.types.Object, psys) -> list[Matrix]:
    matrices: list[Matrix] = []
    if psys.settings.type == 'HAIR':
        mod = next((m for m in obj_eval.modifiers if m.type == 'PARTICLE_SYSTEM' and m.particle_system.name == psys.name), None)
        if mod is None:
            return matrices
        for p in psys.particles:
            if len(p.hair_keys) < 2:
                continue
            root = obj_eval.matrix_world @ p.hair_keys[0].co_object(obj_eval, mod, p)
            tip  = obj_eval.matrix_world @ p.hair_keys[1].co_object(obj_eval, mod, p)
            rot  = (tip - root).to_track_quat('Z', 'Y')
            matrices.append(Matrix.Translation(root) @ rot.to_matrix().to_4x4())
    else:
        for p in psys.particles:
            if p.alive_state != 'ALIVE':
                continue
            matrices.append(Matrix.Translation(p.location) @ p.rotation.to_matrix().to_4x4())
    return matrices

def _particles_source(col: bpy.types.Collection) -> list[Matrix]:
    """every particle of the particle systems of the objects in the collection (emitter: location/rotation,
    hair: root pointing along the hair), read at the current frame. No additional objects are needed."""
    objs = [o for o in col.objects if o.particle_systems and not getattr(o, ObjectProp.IGNORE, False)]
    if not objs:
        return []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    matrices: list[Matrix] = []
    for obj in sorted(objs, key=lambda o: o.name):
        obj_eval = obj.evaluated_get(depsgraph)
        for psys in obj_eval.particle_systems:
            matrices += _particle_matrices(obj_eval, psys)
    return matrices

register_locator_source("PARTICLES", _particles_source)
