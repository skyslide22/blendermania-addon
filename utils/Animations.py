import time

import bpy
from bpy.props import *
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector, Euler
import math

from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp
from ..utils.ItemsExportV2Models import AnimEase


def _in_out(f_in):
    """Derive Out and InOut from an In function."""
    f_out = lambda t: 1 - f_in(1 - t)
    f_io  = lambda t: f_in(2*t) / 2 if t < 0.5 else 1 - f_in(2*(1 - t)) / 2
    return f_out, f_io

def _bounce_out(t):
    n, d = 7.5625, 2.75
    if t < 1/d:     return n*t*t
    if t < 2/d:     t -= 1.5/d;   return n*t*t + 0.75
    if t < 2.5/d:   t -= 2.25/d;  return n*t*t + 0.9375
    t -= 2.625/d;                  return n*t*t + 0.984375

_C1 = 1.70158
_C2 = _C1 * 1.525
_C4 = 2*math.pi/3
_C5 = 2*math.pi/4.5

_IN = {
    "Quad":  lambda t: t**2,
    "Cubic": lambda t: t**3,
    "Quart": lambda t: t**4,
    "Quint": lambda t: t**5,
    "Sine":  lambda t: 1 - math.cos(t*math.pi/2),
    "Exp":   lambda t: 0.0 if t <= 0 else 2**(10*t - 10),
    "Circ":  lambda t: 1 - math.sqrt(max(0.0, 1 - t*t)),
    "Back":  lambda t: t*t*((_C1 + 1)*t - _C1),
    "Elastic": lambda t: 0.0 if t <= 0 else (1.0 if t >= 1 else
                -2**(10*t - 10) * math.sin((t*10 - 10.75) * _C4)),
    "Bounce": lambda t: 1 - _bounce_out(1 - t),
}

EASE = {"Constant": lambda t: 0.0, "Linear": lambda t: t}

for name, f_in in _IN.items():
    f_out, f_io = _in_out(f_in)
    EASE[name + "In"], EASE[name + "Out"], EASE[name + "InOut"] = f_in, f_out, f_io

# The generic InOut composition differs slightly from the canonical curves for these two:
EASE["BackInOut"] = lambda t: (
    ((2*t)**2 * ((_C2 + 1)*2*t - _C2)) / 2 if t < 0.5
    else ((2*t - 2)**2 * ((_C2 + 1)*(2*t - 2) + _C2) + 2) / 2)

def _elastic_io(t):
    if t <= 0: return 0.0
    if t >= 1: return 1.0
    s = math.sin((20*t - 11.125) * _C5)
    return -(2**(20*t - 10) * s) / 2 if t < 0.5 else (2**(-20*t + 10) * s) / 2 + 1
EASE["ElasticInOut"] = _elastic_io

# TODO: verify against the game, aliased for now
EASE["ElasticIn2"]    = EASE["ElasticIn"]
EASE["ElasticOut2"]   = EASE["ElasticOut"]
EASE["ElasticInOut2"] = EASE["ElasticInOut"]

def ease(u, kind):
    u = min(1.0, max(0.0, u))
    return EASE[kind](u)

# TM (Y-up) -> Blender (Z-up). Verify signs against the game once.
# Each entry: (blender axis index, sign)
AXIS_MAP = {"X": (0, 1.0), "Y": (1, 1.0), "Z": (2, 1.0)}

def read_defs(coll_prop):
    return [(d.duration, d.ease, d.reverse) for d in coll_prop]


def eval_channel(defs, t_ms, lo, hi):
    total = sum(d[0] for d in defs)
    if total <= 0:
        return lo
    t = t_ms % total
    cursor = 0.0
    for dur, easing, reverse in defs:
        if t < cursor + dur:
            a, b = (hi, lo) if reverse else (lo, hi)
            u = ease((t - cursor) / dur, easing)
            return a + (b - a) * u
        cursor += dur
    return lo

def rest_matrix(ob):
    f = ob.get("tm_rest")
    return Matrix([f[i*4:i*4+4] for i in range(4)]) if f else ob.matrix_world.copy()

def item_origin_object(col):
    origin = None
    for ob in col.all_objects:        # use the same iteration/order as your export
        if ob.type == 'MESH' and (origin is None or getattr(col, ObjectProp.ORIGIN)):
            origin = ob
    return origin

def pivot_object(col):
    """Object whose rest position is the rotation pivot."""
    return getattr(col, CollectionProp.MOVING_ANCHOR) or item_origin_object(col)

def local_matrix(col, t_ms, rot=True):
    g = lambda k: getattr(col, k)
    # translation
    loc = Vector()
    tdefs = read_defs(g(CollectionProp.KINEMATIC_TRANS_ANIMS))
    if tdefs:
        idx, sign = AXIS_MAP[g(CollectionProp.KINEMATIC_TRANS_AXIS)]
        loc[idx] = sign * eval_channel(tdefs, t_ms, g(CollectionProp.KINEMATIC_TRANS_MIN), g(CollectionProp.KINEMATIC_TRANS_MAX))
    # rotation about the anchor point = rest position of the anchor object (angles are already radians via subtype ANGLE)
    rdefs = read_defs(g(CollectionProp.KINEMATIC_ROT_ANIMS))
    R = Matrix.Identity(4)
    if rdefs and rot:
        idx, sign = AXIS_MAP[g(CollectionProp.KINEMATIC_ROT_AXIS)]
        ang = sign * eval_channel(rdefs, t_ms, g(CollectionProp.KINEMATIC_ROT_MIN), g(CollectionProp.KINEMATIC_ROT_MAX))
        axis = Vector(); axis[idx] = 1.0
        pv = pivot_object(col)
        p = rest_matrix(pv).translation if pv else Vector()
        R = Matrix.Translation(p) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p)
    return Matrix.Translation(loc) @ R   # order rotate-then-translate: verify in game

def total_matrix(col, t_ms, cache, stack=(), no_rot=False):
    if not no_rot and col.name in cache:
        return cache[col.name]
    if col.name in stack:
        return Matrix.Identity(4)
    m = local_matrix(col, t_ms, rot=not no_rot)
    parent = getattr(col, CollectionProp.RELATIVE_MOVING_GROUP)
    if parent and getattr(parent, CollectionProp.MOVING_GROUP):
        m = total_matrix(parent, t_ms, cache, stack + (col.name,)) @ m
    if not no_rot:
        cache[col.name] = m
    return m




# ---------- rest pose ----------
_written = {}      # ob.name -> (M applied, matrix_world read back after writing)
_busy = [False]
_t = [0.0]

def _moving_collections():
    return [c for c in bpy.data.collections if getattr(c, CollectionProp.MOVING_GROUP)]

def _objects_to_track(col):
    objs = set(col.all_objects)
    return objs

def _store_rest(ob, m):
    ob["tm_rest"] = [v for row in m for v in row]

def _same(a, b, eps=1e-4):
    # relative tolerance: float32 noise grows with coordinate magnitude
    for ra, rb in zip(a, b):
        for x, y in zip(ra, rb):
            if abs(x - y) > eps * (1.0 + abs(x)):
                return False
    return True

def commit_edits():
    edited, pivot_changed = set(), False
    for name, (M, written, cn) in list(_written.items()):
        ob = bpy.data.objects.get(name)
        if not ob or "tm_rest" not in ob:
            _written.pop(name, None)
            continue
        cur = ob.matrix_world.copy()
        if _same(cur, written):
            continue
        rest = M.inverted_safe() @ cur
        col = bpy.data.collections.get(cn)
        if col and pivot_object(col) == ob:
            Mt = total_matrix(col, _t[0], {}, no_rot=True)
            new_p = Mt.inverted_safe() @ cur.translation
            old_p = rest_matrix(ob).translation
            rest.translation = new_p
            if (new_p - old_p).length > 1e-3:
                pivot_changed = True
        _store_rest(ob, rest)
        edited.add(name)

    if not edited:
        return
    cache = {}                                   # built AFTER the new rests are stored
    for name, (M, written, cn) in list(_written.items()):
        ob = bpy.data.objects.get(name)
        col = bpy.data.collections.get(cn)
        if not ob or not col or "tm_rest" not in ob:
            continue
        M_new = total_matrix(col, _t[0], cache)
        if pivot_changed and name not in edited:
            # keep the geometry where it is displayed, relative to the new pivot
            _store_rest(ob, M_new.inverted_safe() @ ob.matrix_world)
        _written[name] = (M_new, ob.matrix_world.copy(), cn)

def capture_rest():
    for col in _moving_collections():
        for ob in _objects_to_track(col):
            if "tm_rest" not in ob:
                _store_rest(ob, ob.matrix_world)

def restore_rest():
    commit_edits()
    for ob in bpy.data.objects:
        if "tm_rest" in ob:
            f = ob["tm_rest"]
            ob.matrix_world = Matrix([f[i*4:i*4+4] for i in range(4)])
            del ob["tm_rest"]
    _written.clear()

# ---------- evaluation ----------
def current_time_ms(scene):
    if scene.tm_preview_use_timeline:
        fps = scene.render.fps / scene.render.fps_base
        return (scene.frame_current + scene.frame_subframe) / fps * 1000.0
    return scene.tm_preview_time

def apply_preview(scene):
    if not scene.tm_preview_enabled or _busy[0]:
        return
    _busy[0] = True
    try:
        commit_edits()
        t_ms = current_time_ms(scene)
        _t[0] = t_ms
        cache = {}
        for col in _moving_collections():
            M = total_matrix(col, t_ms, cache)
            for ob in _objects_to_track(col):
                if "tm_rest" not in ob:
                    # object added (e.g. new anchor) while preview is on: it is shown under M right now
                    _store_rest(ob, M.inverted_safe() @ ob.matrix_world)
                if ob.parent and ob.parent.name in col.all_objects:
                    continue
                ob.matrix_world = M @ rest_matrix(ob)
                _written[ob.name] = (M.copy(), ob.matrix_world.copy(), col.name)
    finally:
        _busy[0] = False

@persistent
def tm_preview_handler(scene, depsgraph=None):
    if scene.tm_preview_use_timeline:
        apply_preview(scene)

@persistent
def tm_detect_edits(scene, depsgraph):
    if _busy[0] or not scene.tm_preview_enabled:
        return
    if not depsgraph.id_type_updated('OBJECT'):
        return
    scr = bpy.context.screen
    if scr and scr.is_animation_playing:
        return                      # never commit during playback
    if abs(current_time_ms(scene) - _t[0]) > 1e-6:
        return                      # time moved: apply_preview will commit with the matching M
    _busy[0] = True
    try:
        commit_edits()
    finally:
        _busy[0] = False

@persistent
def tm_undo_redo(scene, depsgraph=None):
    _written.clear()                         # tm_rest and matrix_world are undone together
    apply_preview(bpy.context.scene)

# ---------- manual playback ----------
_last = [0.0]

def _tick():
    scene = bpy.context.scene
    if not (scene.tm_preview_enabled and scene.tm_preview_playing):
        return None
    now = time.perf_counter()
    dt, _last[0] = now - _last[0], now
    scene.tm_preview_time += dt * 1000.0 * scene.tm_preview_speed
    return 1 / 60

# ---------- update callbacks ----------
def _u_enabled(self, ctx):
    if self.tm_preview_enabled:
        capture_rest()
        apply_preview(self)
    else:
        self.tm_preview_playing = False
        restore_rest()

def _u_time(self, ctx):
    if not self.tm_preview_use_timeline:
        apply_preview(self)

def _u_mode(self, ctx):
    apply_preview(self)

def _u_playing(self, ctx):
    if self.tm_preview_playing and self.tm_preview_enabled and not self.tm_preview_use_timeline:
        _last[0] = time.perf_counter()
        bpy.app.timers.register(_tick)

def disable_animation_preview(scene=None):
    """turn the preview off and restore all objects to their rest transforms"""
    scene = scene or bpy.context.scene
    if getattr(scene, "tm_preview_enabled", False):
        scene.tm_preview_enabled = False   # update callback restores the rest matrices
    else:
        restore_rest()

_PROPS = ("enabled", "use_timeline", "time", "speed", "playing", "show_range")

def register_animation_preview():
    S = bpy.types.Scene
    S.tm_preview_enabled = BoolProperty(name="Preview", default=False, update=_u_enabled)
    S.tm_preview_use_timeline = BoolProperty(name="Use Timeline", default=False, update=_u_mode)
    S.tm_preview_time = FloatProperty(name="Time (ms)", default=0.0, min=0.0, step=1000, update=_u_time)
    S.tm_preview_speed = FloatProperty(name="Speed", default=1.0, min=0.0, soft_max=4.0)
    S.tm_preview_playing = BoolProperty(name="Play", default=False, update=_u_playing)
    S.tm_preview_show_range = BoolProperty(name="Show Range", default=False)
    H = bpy.app.handlers
    H.frame_change_post.append(tm_preview_handler)
    H.depsgraph_update_post.append(tm_detect_edits)
    H.undo_post.append(tm_undo_redo)
    H.redo_post.append(tm_undo_redo)

def unregister_animation_preview():
    H = bpy.app.handlers
    for lst, fn in ((H.frame_change_post, tm_preview_handler),
                    (H.depsgraph_update_post, tm_detect_edits),
                    (H.undo_post, tm_undo_redo),
                    (H.redo_post, tm_undo_redo)):
        if fn in lst:
            lst.remove(fn)
    restore_rest()
    for n in _PROPS:
        delattr(bpy.types.Scene, "tm_preview_" + n)
