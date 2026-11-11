from __future__ import annotations

import os
from typing import Callable

import bpy
from mathutils import Matrix, Quaternion, Vector

from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp
from ..properties.AttachmentProperties import (
    ATTACHMENT_KEY_TYPE,
    ATTACHMENT_KEY_SLOT,
    ATTACHMENT_KEY_PILOT_SLOT,
    get_attachment_option_dicts,
    get_podium_slots,
    format_attachment_slot,
    ATTACHMENT_PODIUM_REQUIRED_SLOTS,
)
from .FunctionsV2 import (
    get_item_attachment_collections,
    get_offset_from_item_origin,
    is_collection_instance,
)
from .ItemsExportV2Models import AttachmentConfig, Vec3
from .Constants import ADDON_ITEM_FILEPATH_LAMP, ADDON_ITEM_FILEPATH_SPECTATOR, ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM


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
def get_item_attachment_warnings(item_collection: bpy.types.Collection) -> list[str]:
    """a podium consists of separate attachments (Type=Podium + PilotSlot/Slot); the item needs at least PilotSlot and Slot 01, 02, 03"""
    pilot: set[int] = set()
    slot: set[int] = set()
    found = False
    for col in get_item_attachment_collections(item_collection):
        attachment = getattr(col, CollectionProp.ATTACHMENT, None)
        slots = get_podium_slots(attachment) if attachment is not None else None
        if slots is None:
            continue
        found = True
        pilot |= slots[0]
        slot |= slots[1]
    if not found:
        return []

    warnings: list[str] = []
    for key, used in (("PilotSlot", pilot), ("Slot", slot)):
        missing = [format_attachment_slot(s) for s in ATTACHMENT_PODIUM_REQUIRED_SLOTS if s not in used]
        if missing:
            warnings.append(f"Podium: {key} {', '.join(missing)} missing (01, 02, 03 required)")
    return warnings


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
    global _auto_placeholder
    _auto_placeholder = True
    try:
        for col in get_item_attachment_collections(item_collection):
            add(col, identity)
        for inst_col, to_world in _iter_instance_occurrences(item_objects):
            for col in get_item_attachment_collections(inst_col):
                add(col, to_world)
    finally:
        _auto_placeholder = False

    return list(configs.values())


# -----------------------------
# particles
# -----------------------------
PLACEHOLDER_OBJECT_PREFIX = "_ignore_placeholder_"
_auto_placeholder = False

# placeholder kind -> fbx file (None: not available yet). Add new placeholder models here.
PLACEHOLDER_FILES: dict[str, str | None] = {
    "Spectator":  ADDON_ITEM_FILEPATH_SPECTATOR,
    "StadiumCar": ADDON_ITEM_FILEPATH_CAR_TRACKMANIA2020_STADIUM,
    # boilerplate, set a file once a model exists:
    "Lamp":       ADDON_ITEM_FILEPATH_LAMP,
    "Tree":       ADDON_ITEM_FILEPATH_LAMP,
    "Rig":        ADDON_ITEM_FILEPATH_LAMP,
    "Show":       ADDON_ITEM_FILEPATH_LAMP,
    "Flag":       ADDON_ITEM_FILEPATH_LAMP,
    "Screen":     ADDON_ITEM_FILEPATH_LAMP,
}

# which placeholder an attachment shows: (option key, option value or None for any value, placeholder kind), first match wins
PLACEHOLDER_RULES: list[tuple[str, str | None, str]] = [
    (ATTACHMENT_KEY_PILOT_SLOT, None,        "Spectator"),
    (ATTACHMENT_KEY_SLOT,       None,        "StadiumCar"),
    (ATTACHMENT_KEY_TYPE,       "Spectator", "Spectator"),
    # boilerplate for the other types
    (ATTACHMENT_KEY_TYPE,       "Lamp",      "Lamp"),
    (ATTACHMENT_KEY_TYPE,       "Tree",      "Tree"),
    (ATTACHMENT_KEY_TYPE,       "Rig",       "Rig"),
    (ATTACHMENT_KEY_TYPE,       "Show",      "Show"),
    (ATTACHMENT_KEY_TYPE,       "Flag",      "Flag"),
    (ATTACHMENT_KEY_TYPE,       "Screen",    "Screen"),
]

def get_attachment_placeholder_kind(attachment) -> str | None:
    """placeholder kind of an attachment definition (see PLACEHOLDER_RULES), None if there is none (with a file)"""
    if attachment is None:
        return None
    for key, value, kind in PLACEHOLDER_RULES:
        if not PLACEHOLDER_FILES.get(kind):
            continue
        for option in attachment.options:
            for entry in option.entries:
                if entry.key.strip() != key:
                    continue
                if value is None or entry.value.strip().lower() == value.lower():
                    return kind
    return None

def get_placeholder_object(kind: str) -> bpy.types.Object | None:
    """the placeholder object of the kind if it was already created, never imports anything"""
    return bpy.data.objects.get(PLACEHOLDER_OBJECT_PREFIX + kind)

def get_particle_placeholder(kind: str = "Spectator") -> bpy.types.Object | None:
    """placeholder object of the kind (fbx of PLACEHOLDER_FILES), imported once"""
    obj = get_placeholder_object(kind)
    if obj is not None:
        return obj
    filepath = PLACEHOLDER_FILES.get(kind)
    if not filepath or not os.path.isfile(filepath):
        return None

    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=filepath)
    new_objs = [o for o in bpy.data.objects if o.name not in before]
    meshes = [o for o in new_objs if o.type == 'MESH']
    if not meshes:
        for o in new_objs:
            bpy.data.objects.remove(o)
        return None

    # one object, transforms applied so the instance matrices only hold the particle transform
    bpy.ops.object.select_all(action='DESELECT')
    for o in new_objs:
        if o not in meshes:
            bpy.data.objects.remove(o)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = PLACEHOLDER_OBJECT_PREFIX + kind

    # not linked to any collection: it stays out of the scene/outliner and is only used as particle render object
    obj.select_set(False)
    obj.use_fake_user = True   # unlinked objects are not saved otherwise
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    return obj

def apply_particle_placeholder(objs, kind: str | None) -> bool:
    """render the particle systems of the objects as the placeholder object of the kind, unless they already render objects/collections"""
    if kind is None:
        return False
    changed = False
    placeholder = None
    for obj in objs:
        for psys in obj.particle_systems:
            settings = psys.settings
            if settings.render_type == 'COLLECTION' or (settings.render_type == 'OBJECT' and settings.instance_object is not None):
                continue
            if placeholder is None:
                placeholder = get_particle_placeholder(kind)
                if placeholder is None:
                    return False
            settings.render_type = 'OBJECT'
            settings.instance_object = placeholder
            changed = True
    if changed:
        bpy.context.view_layer.update()
    return changed

def _particle_instance_matrices(obj_eval: bpy.types.Object, psys, depsgraph) -> list[Matrix] | None:
    """
    World matrices of the objects Blender instances for this particle system (render as Object/Collection). They include
    everything of the Rotation panel (global Z, randomize, phase, ...), which hair/emitter data does not expose.
    None if the system does not instance objects.
    """
    if psys.settings.render_type not in ('OBJECT', 'COLLECTION'):
        return None
    matrices = [inst.matrix_world.copy() for inst in depsgraph.object_instances
                if inst.is_instance
                and inst.parent is not None and inst.parent.name == obj_eval.name
                and getattr(inst.particle_system, "name", None) == psys.name]
    return matrices or None

def _particle_matrices(obj_eval: bpy.types.Object, psys, depsgraph) -> list[Matrix]:
    instanced = _particle_instance_matrices(obj_eval, psys, depsgraph)
    if instanced is not None:
        return instanced

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
            rot = p.rotation.normalized()   # particle quaternions are not guaranteed to be unit length
            matrices.append(Matrix.Translation(p.location) @ rot.to_matrix().to_4x4())
    return matrices

def _particles_source(col: bpy.types.Collection) -> list[Matrix]:
    """every particle of the particle systems of the objects in the collection (emitter: location/rotation,
    hair: root pointing along the hair), read at the current frame. No additional objects are needed."""
    objs = [o for o in col.objects if o.particle_systems and not getattr(o, ObjectProp.IGNORE, False)]
    if not objs:
        return []
    if _auto_placeholder:   # only while exporting; never while drawing (no data changes/imports allowed there)
        apply_particle_placeholder(objs, get_attachment_placeholder_kind(getattr(col, CollectionProp.ATTACHMENT, None)))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    matrices: list[Matrix] = []
    for obj in sorted(objs, key=lambda o: o.name):
        obj_eval = obj.evaluated_get(depsgraph)
        for psys in obj_eval.particle_systems:
            matrices += _particle_matrices(obj_eval, psys, depsgraph)
    return matrices

register_locator_source("PARTICLES", _particles_source)
