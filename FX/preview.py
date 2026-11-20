"""Approximate particle preview, drawn as a viewport overlay.

NOT the game: only fields with a clear meaning are used. Nothing is added to the
scene (no objects, collections, meshes or materials), so nothing can be exported by
accident. Particles are simulated from the timeline time (deterministic, scrubbing
works) and drawn as camera facing sprites with the GPU model's bitmap asset.

Taken from every GPU model of the effect:
    LifeMax, LifeVar01              lifetime and its randomness (s)
    SizeMax, SizeVar01              start size and its randomness
    SizeEndScale                    size at the end of life (linear over life)
    Weight x gravity scale          vertical acceleration in m/s² (sign tested in game: < 0 falls, magnitude a guess)
    Viscosity                       linear air drag (1/s; 0 keeps the speed, 10 stops at once, tested in game)
    Intensity                       brightness of the sprite
    IntensityFadeIn/Out, IntensityPower, IntensityVariation
                                    fade in/out as fraction of the life, power-shaped fade out (power 0 = no fade),
                                    per particle brightness (can be switched off)
    EffectNode U09 (DOVExpr)        particles travel along -DOV (tested in game: default float3(0,0,-1) emits
                                    towards TM +Z = Blender -Y of the empty)
    EffectNode U02 / U03            local offset (rotates with the empty) / world offset (float3 constants only)
    EffectNode U12                  DOVAndUpAreLocalSpace: 0 = direction and shape in world axes
    Bitmap, TextureAtlasDimX/Y      texture; atlas cells first / over life / random (how the game picks is unknown)
GPU spawn (in-game tests, option "From GPU spawn"): U04 rate, U11 speed, U12 speed variation, U13 cone half angle,
U10 vertical speed, U15 shape: 1 point (+ U17 axial spread), 2 ring (U20 radius, U21 width, U25 arc, U22/U23
axial start/end, U26 swirl / U27 outward speed are guesses), 3 box (U28 centre + size, TM axes).
U08 max particles (no new particle while the pool is full), U01 rate mode 0 (approximated: keeps the pool full).
GPU model look: rotation (c002_U13 on/off, Rotation + RotationVariation turns/s), additive glow (c002_U10/U11),
distortion (c002_U04, drawn faint), hue (UseEmitterHue + UseHueShift with node LinearHue01 / HueLightness,
UseHueShift alone: Hue), UseEnergyOverLife (white -> red), reverse direction (c000_U04), loop period
(c000_U02, short stop at the end of each period, guess).
Expressions ("Use expressions", FX/fxexpr.py): per particle birth the system's variable updates and the
emitter's conditions are evaluated, then its rate multiplier (U05), local/world offset (U02/U03), direction
(U09), hue (U14), lightness (U15) and ambient light (U07, 0 dark .. 3 bright). Unknown inputs are 0.
Preview only (never exported): shape, size, spread, rate and speed when "From GPU spawn" is off.

Veget tree propagation (falling leaves of TreeModel collections, ``VegetTreeProperties``):
    propagation_emission_positions  emitters, relative to the tree model (its first mesh, location + rotation)
    propagation_emission_spawn_radius  random spawn disc (horizontal, at the position's height) around each position
    propagation_leaf_per_second     leaves per second (all positions together) x preview rate factor
    propagation_cone_half_angle     fall direction cone around straight down
    propagation_leaf_size           leaf size
    propagation_base_color, _atlas_grid  texture, one random atlas cell per leaf
Preview only: rate factor, fall speed, spin and leaf life; leaves die after the life, or at the tree
mesh's height when they started above it.
Not used: ground gen point count (meaning unknown), normal bitmap.
"""
import colorsys
import heapq
import math
import re
import struct

import bpy
import gpu
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from . import bridge, fxexpr
from .props import OBJECT_ATTR, is_fx_node, settings_of

PREVIEW_ATTR = "tm_fx_preview"
GPU_MODEL = "CPlugParticleGpuModel"
LEGACY_NAMES = ("_ignore_TMFX_Preview", "TMFX_Preview")   # scene data of the old particle system preview

SHAPES = [("POINT", "Point", "Spawn at the empty"),
          ("SPHERE", "Sphere", "Spawn inside a sphere around the empty"),
          ("BOX", "Box", "Spawn inside a cube around the empty")]
ATLAS = [("LIFE", "Over life", "Step through the atlas cells over the particle life"),
         ("RANDOM", "Random", "One random atlas cell per particle"),
         ("FIRST", "First cell", "Always the first (top left) cell")]
SCOPES = [("ACTIVE", "Active", "Only the active particle fx empty"),
          ("ALL", "All", "Every visible particle fx empty of the scene")]


def _redraw(self=None, context=None):
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _toggled(self=None, context=None):
    """keep the shared preview clock (Blendermania > Preview) running when an overlay is switched on"""
    from ..utils.Animations import on_preview_toggled
    on_preview_toggled(bpy.context.scene)
    _redraw()


def preview_time_s(scene) -> float:
    """shared preview clock (own clock or timeline, see utils.Animations.current_time_ms) in seconds"""
    from ..utils.Animations import current_time_ms
    return current_time_ms(scene) / 1000.0


class FXPreview(bpy.types.PropertyGroup):
    show: BoolProperty(name="Particles", default=False, update=_toggled,
                       description="Draw an approximate particle preview in the viewport (overlay, adds nothing to the scene)")
    scope: EnumProperty(name="Show", items=SCOPES, default="ACTIVE", update=_redraw)
    shape: EnumProperty(name="Shape", items=SHAPES, default="POINT", update=_redraw)
    radius: FloatProperty(name="Spawn size", default=0.5, min=0.0, update=_redraw, description="Preview only")
    use_spawn: BoolProperty(name="From GPU spawn", default=True, update=_redraw,
                            description="Shape, cone, rate and speeds from the GPU spawn fields found in game tests "
                                        "(the manual shape, size, rate, speed and spread below are ignored)")
    use_expressions: BoolProperty(name="Use expressions", default=True, update=_redraw,
                                  description="Evaluate the effect node expressions per particle birth: Time, "
                                              "variables, conditions, rate multiplier, offsets, direction, hue, ambient "
                                              "light. Off: only constant values (faster)")
    rate: FloatProperty(name="Rate /s", default=20.0, min=0.1, soft_max=500.0, update=_redraw, description="Preview only")
    speed: FloatProperty(name="Speed", default=0.5, min=0.0, update=_redraw,
                         description="Preview only: start speed along the emission direction (-DOV of the effect node, "
                                     "default TM +Z = Blender -Y of the empty; sphere/box: outwards)")
    spread: FloatProperty(name="Spread", default=0.2, min=0.0, max=1.0, subtype="FACTOR", update=_redraw,
                          description="Preview only: random direction added to the start speed")
    gravity: FloatProperty(name="Gravity scale", default=1.0, soft_min=0.0, soft_max=2.0, update=_redraw,
                           description="Vertical acceleration = Weight x this in m/s² (Weight < 0 falls, > 0 rises, "
                                       "tested in game; the magnitude is a guess)")
    atlas: EnumProperty(name="Atlas", items=ATLAS, default="LIFE", update=_redraw)
    fade: BoolProperty(name="Fade (guess)", default=True, update=_redraw,
                       description="Fade in over IntensityFadeIn, fade out from IntensityFadeOut (fractions of the life) "
                                   "with IntensityPower as curve exponent; IntensityVariation varies the brightness")
    max_particles: IntProperty(name="Max particles", default=2000, min=10, soft_max=10000, update=_redraw,
                               description="Per GPU model / tree model, keeps the viewport responsive")
    # veget tree propagation
    show_trees: BoolProperty(name="Tree Leaves", default=False, update=_toggled,
                             description="Draw the falling leaves of every visible tree model with Leaf Animation enabled (overlay)")
    leaf_fall_speed: FloatProperty(name="Fall speed", default=1.0, min=0.01, soft_max=5.0, unit="VELOCITY",
                                   update=_redraw, description="Preview only: how fast leaves fall")
    leaf_rate: FloatProperty(name="Rate factor", default=0.1, min=0.0, soft_max=1.0, subtype="FACTOR", update=_redraw,
                             description="Preview only: multiplies Leaves Per Second. The game shows fewer leaves than the "
                                         "setting suggests; 0.1 matched the game in a test")
    leaf_life: FloatProperty(name="Leaf life", default=8.0, min=0.1, soft_max=10.0, unit="TIME_ABSOLUTE", update=_redraw,
                             description="Preview only: leaves disappear after this time or when they reach the ground. "
                                         "No tree setting is known for it; 8 s matched the game in a test")
    leaf_spin: FloatProperty(name="Spin", default=1.0, min=0.0, soft_max=5.0, update=_redraw,
                             description="Preview only: leaf rotation speed (turns per second, randomised)")


# ------------------------------------------------------------------ simulation (pure)
def _rnd(i: int, k: int, seed: int) -> float:
    """Deterministic hash -> [0, 1): particle ``i``, channel ``k``."""
    x = (i * 73856093 ^ k * 19349663 ^ seed * 83492791) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5BD1E995) & 0xFFFFFFFF
    x ^= x >> 15
    return x / 4294967296.0


def _rnd_dir(i, k, seed):
    z = 2.0 * _rnd(i, k, seed) - 1.0
    a = 2.0 * math.pi * _rnd(i, k + 1, seed)
    r = math.sqrt(max(0.0, 1.0 - z * z))
    return Vector((r * math.cos(a), r * math.sin(a), z))


TM_FORWARD = (0.0, 0.0, -1.0)   # default emitter forward axis (EffectNode expression), Trackmania space


def tm_to_blender(v) -> Vector:
    """Trackmania (Y up, -Z forward) -> Blender (Z up, +Y forward) axes: (x, y, z) -> (x, -z, y)."""
    return Vector((v[0], -v[2], v[1]))


def parse_float3(expr):
    """``float3(a,b,c)`` / ``float3(a)`` -> (a, b, c); None for anything else (variables, functions)."""
    import re
    m = re.fullmatch(r"\s*float3\(([^()]*)\)\s*", expr or "")
    if not m:
        return None
    try:
        parts = [float(x) for x in m.group(1).split(",")]
    except ValueError:
        return None
    if len(parts) == 1:
        parts = parts * 3
    return tuple(parts) if len(parts) == 3 else None


def simulate(m: dict, p: dict, t: float, seed: int = 0) -> list:
    """Particles alive at time ``t`` (s) for GPU model values ``m`` and preview settings ``p``.

    Returns dicts with ``pos`` (local start offset), ``vel`` (local), ``age``, ``life``,
    ``size`` and ``r`` (per particle random). Particle ``i`` is born at ``i / rate``.
    """
    if m.get("inactive"):
        return []
    spawn = m.get("spawn") if p.get("use_spawn") else None
    life_max = max(0.01, m["LifeMax"])
    pool = int(spawn["max"]) if spawn and spawn.get("max", 0) >= 1 else 0
    if spawn and spawn.get("rate_mode", 1) == 0 and pool:
        rate = pool / life_max            # rate ignored (in-game: far more particles): keep the pool full (guess)
    else:
        rate = spawn["rate"] if spawn else p["rate"]
    rate = max(0.1, rate)
    if pool and pool >= rate * life_max:
        pool = 0                           # the pool never fills up: no effect
    history = life_max * (3.0 if pool else 1.0)   # the pool needs earlier particles to know what is alive
    first = max(0, math.floor((t - history) * rate))
    last = math.floor(t * rate)
    limit = p["max_particles"] * (20 if pool else 1)
    if last - first > limit:
        first = last - limit
    prog = m.get("program")
    period = m.get("loop_period", 0.0)
    alive_until = []                       # death times of accepted particles (pool)
    cache = {}
    out = []
    for i in range(first, last + 1):
        birth = i / rate
        life = life_max * (1.0 - min(0.99, max(0.0, m["LifeVar01"])) * _rnd(i, 0, seed))
        if period > 0.0 and (birth / period) % 1.0 > 0.95:
            continue                       # loop period: short stop at the end of each period (guess)
        vals = None
        if prog is not None:
            if prog.get("random", True):
                k = [20]
                def rnd(i=i, k=k):
                    k[0] += 1
                    return _rnd(i, k[0], seed)
                vals = evaluate_program(prog, birth * 1000.0, rnd)
            else:                          # Time only: evaluated once per 1/120 s
                step = math.floor(birth * 120.0)
                if step not in cache:
                    cache[step] = evaluate_program(prog, step / 0.12, None)
                vals = cache[step]
            if vals is None:
                continue                   # a condition above the emitter is false
        rate_mul = vals.get("rate", m.get("rate_mul", 1.0)) if vals else m.get("rate_mul", 1.0)
        if _rnd(i, 13, seed) >= rate_mul:  # SpawnFreqModifier: <= 0 stops, 0.5 halves (> 1 not shown)
            continue
        if pool:
            while alive_until and alive_until[0] <= birth:
                heapq.heappop(alive_until)
            if len(alive_until) >= pool:
                continue                   # pool full: no new particle until one dies
            heapq.heappush(alive_until, birth + life)
        age = t - birth
        if age < 0.0 or age >= life:
            continue
        node = _apply_node_values({}, vals, m) if vals else {}
        forward = node.get("forward", m.get("forward", Vector((0.0, -1.0, 0.0))))
        if spawn:
            pos, vel = _spawn_particle(spawn, forward, i, seed)
        else:
            shape, radius = p["shape"], p["radius"]
            if shape == "SPHERE":
                d = _rnd_dir(i, 1, seed)
                pos = d * (radius * _rnd(i, 3, seed) ** (1.0 / 3.0))
                base = d
            elif shape == "BOX":
                pos = Vector([(2.0 * _rnd(i, 4 + a, seed) - 1.0) * radius for a in range(3)])
                base = pos.normalized() if pos.length > 1e-6 else forward
            else:
                pos = Vector((0.0, 0.0, 0.0))
                base = forward
            vel = (base + _rnd_dir(i, 7, seed) * p["spread"]).normalized() * p["speed"]
        size = m["SizeMax"] * (1.0 - min(1.0, max(0.0, m["SizeVar01"])) * _rnd(i, 9, seed))
        q = {"pos": pos, "vel": vel, "age": age, "life": life,
             "vertical": spawn["vertical"] if spawn else 0.0,
             "size": size, "r": _rnd(i, 10, seed), "r2": _rnd(i, 11, seed)}
        if m.get("rotate", True):
            q["angle0"] = 2.0 * math.pi * _rnd(i, 14, seed)
            q["spin"] = 2.0 * math.pi * (m.get("Rotation", 0.0)
                                         + (2.0 * _rnd(i, 15, seed) - 1.0) * m.get("RotationVariation", 0.0))
        q.update({k: node[k] for k in ("local_offset", "world_offset", "node_hue", "node_light", "ambient")
                  if k in node})
        out.append(q)
    if len(out) > p["max_particles"]:
        out = out[-p["max_particles"]:]
    return out


def _basis(forward: Vector):
    """two unit vectors perpendicular to ``forward``"""
    helper = Vector((0.0, 0.0, 1.0)) if abs(forward.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = forward.cross(helper).normalized()
    return u, forward.cross(u).normalized()


def _spawn_particle(s: dict, forward: Vector, i: int, seed: int):
    """(start offset, start velocity) of particle ``i`` from GPU spawn values, emitter space (Blender axes).

    In-game tests: shape 1 point (+ axial spread U17, guess), shape 2 ring around the emission axis
    (radius, width, arc, axial start/end; swirl/outward speed are guesses), shape 3 box (centre + size, TM axes),
    cone half angle U13 around the direction, speed U11 +- U12. The vertical speed U10 is added by the caller."""
    u, v = _basis(forward)
    shape = s["shape"]
    radial = Vector()
    if shape == 2:
        a = math.radians(s["arc_deg"]) * _rnd(i, 1, seed)
        radial = u * math.cos(a) + v * math.sin(a)
        r = max(0.0, s["ring_radius"] + s["ring_width"] * _rnd(i, 2, seed))
        axial = s["axial_start"] + (s["axial_end"] - s["axial_start"]) * _rnd(i, 3, seed)
        pos = radial * r + forward * axial
    elif shape == 3:
        c, size = s["box"][:3], s["box"][3:]
        pos = tm_to_blender([c[k] + (_rnd(i, 4 + k, seed) - 0.5) * size[k] for k in range(3)])
    elif shape == 1:
        pos = forward * (max(0.0, s["axial_spread"]) * _rnd(i, 3, seed))
    else:
        pos = Vector()
    # direction inside the cone (uniform on the spherical cap)
    cone = math.radians(min(180.0, max(0.0, s["cone_deg"])))
    cos_t = 1.0 - _rnd(i, 7, seed) * (1.0 - math.cos(cone))
    sin_t = math.sqrt(max(0.0, 1.0 - cos_t * cos_t))
    phi = 2.0 * math.pi * _rnd(i, 8, seed)
    direction = forward * cos_t + (u * math.cos(phi) + v * math.sin(phi)) * sin_t
    speed = max(0.0, s["speed"] + (2.0 * _rnd(i, 12, seed) - 1.0) * s["speed_var"])
    vel = direction * speed
    if shape == 2:
        vel = vel + radial * s["outward"] + forward.cross(radial) * s["swirl"]
    return pos, vel


def motion(p0: Vector, v0: Vector, grav: Vector, drag: float, t: float) -> Vector:
    """position after ``t`` s with linear air drag ``drag`` (1/s, GPU model Viscosity) and constant gravity"""
    if drag < 1e-4:
        return p0 + v0 * t + grav * (0.5 * t * t)
    e = (1.0 - math.exp(-drag * t)) / drag
    return p0 + v0 * e + grav * ((t - e) / drag)


def particle_look(m: dict, p: dict, q: dict):
    """(size, alpha, atlas cell index) of particle ``q`` at its age."""
    f = q["age"] / q["life"]
    size = q["size"] * (1.0 + (m["SizeEndScale"] - 1.0) * f)
    alpha = 1.0
    if p["fade"]:
        fi, fo = m["IntensityFadeIn"], m["IntensityFadeOut"]
        if fi > 0.0 and f < fi:
            alpha = f / fi
        elif fo < 1.0 and f > fo:
            # IntensityPower 0 = no fade (in-game test)
            alpha = max(0.0, (1.0 - f) / (1.0 - fo)) ** max(0.0, m.get("IntensityPower", 1.0))
        alpha *= 1.0 - min(1.0, max(0.0, m.get("IntensityVariation", 0.0))) * q["r2"]
    cells = m["TextureAtlasDimX"] * m["TextureAtlasDimY"]
    if p["atlas"] == "LIFE":
        cell = min(cells - 1, int(f * cells))
    elif p["atlas"] == "RANDOM":
        cell = min(cells - 1, int(q["r"] * cells))
    else:
        cell = 0
    return max(0.0, size), alpha, cell


LEAF_MAX_LIFE = 20.0   # s, leaves that never reach the ground disappear after this


def simulate_propagation(tv: dict, p: dict, t: float, seed: int = 0) -> list:
    """Falling leaves alive at time ``t`` for tree values ``tv``.

    ``tv["positions"]`` are emitter positions relative to the item origin (Blender axes),
    the ground is at z = 0 (the tree's height). Returns dicts with ``pos`` (relative to the
    item origin), ``age``, ``life``, ``size``, ``r`` and ``angle``.
    """
    positions = tv["positions"]
    rate = tv["rate"] * p["leaf_rate"]
    if not positions or rate <= 0.0:
        return []
    cone = math.radians(min(89.9, max(0.0, tv["cone_deg"])))
    speed = max(0.01, p["leaf_fall_speed"])
    max_life = min(LEAF_MAX_LIFE, max(0.1, p["leaf_life"]))
    first = max(0, math.floor((t - max_life) * rate))
    last = math.floor(t * rate)
    if last - first > p["max_particles"] * 4:
        first = last - p["max_particles"] * 4
    out = []
    for i in range(first, last + 1):
        age = t - i / rate
        if age < 0.0:
            continue
        origin = Vector(positions[min(len(positions) - 1, int(_rnd(i, 0, seed) * len(positions)))])
        # uniform in a horizontal disc: the game spawns leaves in one plane at the emission height
        a0 = 2.0 * math.pi * _rnd(i, 1, seed)
        d0 = tv["radius"] * math.sqrt(_rnd(i, 3, seed))
        start = origin + Vector((math.cos(a0) * d0, math.sin(a0) * d0, 0.0))
        # direction inside the cone around -Z
        a = 2.0 * math.pi * _rnd(i, 4, seed)
        tilt = math.acos(1.0 - _rnd(i, 5, seed) * (1.0 - math.cos(cone)))
        direction = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), -math.cos(tilt)))
        fall = -direction.z * speed
        # the tree's height only ends leaves that started above it; emitters at or below it use the full life
        life = min(max_life, start.z / fall) if start.z > 0.0 else max_life
        if age >= life:
            continue
        # gentle sway (preview only)
        sway = Vector((math.sin(age * 2.1 + 6.0 * _rnd(i, 6, seed)),
                       math.cos(age * 1.7 + 6.0 * _rnd(i, 7, seed)), 0.0))
        pos = start + direction * (speed * age) + sway * (0.15 * min(1.0, age))
        spin = (2.0 * _rnd(i, 8, seed) - 1.0) * p["leaf_spin"] * 2.0 * math.pi
        out.append({"pos": pos, "age": age, "life": life, "size": tv["size"], "r": _rnd(i, 9, seed),
                    "angle": 2.0 * math.pi * _rnd(i, 10, seed) + spin * age})
    if len(out) > p["max_particles"]:
        out = out[-p["max_particles"]:]
    return out


def leaf_alpha(q: dict) -> float:
    """Short fade in after spawning and before touching the ground."""
    life = q["life"]
    return max(0.0, min(1.0, q["age"] / 0.2, (life - q["age"]) / 0.3)) if life > 0.0 else 0.0


# ------------------------------------------------------------------ model gathering
def _spawn_values(spawn):
    """Values of a GPU spawn's Spawn struct (meanings from in-game tests, see the overlay)."""
    if spawn is None:
        return None
    g = lambda k: float(getattr(spawn, k, 0.0) or 0.0)
    shape = getattr(spawn, "U15", 1)
    try:
        shape = int(shape)
    except (TypeError, ValueError):
        shape = 1
    box = getattr(spawn, "U28", None)
    try:
        rate_mode = int(getattr(spawn, "U01", 1))
    except (TypeError, ValueError):
        rate_mode = 1
    return {"rate": g("U04"), "rate_mode": rate_mode, "max": g("U08"), "speed": g("U11"), "speed_var": g("U12"),
            "cone_deg": g("U13"), "vertical": g("U10"), "shape": shape,
            "axial_spread": g("U17"),                                    # shape 1
            "ring_radius": g("U20"), "ring_width": g("U21"),             # shape 2
            "axial_start": g("U22"), "axial_end": g("U23"), "arc_deg": g("U25"),
            "swirl": g("U26"), "outward": g("U27"),
            "box": [float(x) for x in box] if box is not None and len(box) == 6 else [0.0] * 6}  # shape 3


def _model_values(gm, node=None, spawn=None, settings=None, node_path="", use_expressions=True) -> dict:
    """GPU model values; ``node`` is its effect node (direction / offset / colour expressions), ``spawn`` the sibling
    GPU spawn's Spawn struct, if any. With ``use_expressions`` the node's expressions, variables and conditions are
    evaluated per particle birth (``m["program"]``); otherwise only float3/number constants are read."""
    g = lambda k, d: getattr(gm, k, d)
    num = lambda k, d: _const_float(getattr(node, k, ""), d) if node is not None else d
    dov = parse_float3(getattr(node, "U09", "")) if node is not None else None
    local_off = parse_float3(getattr(node, "U02", "")) if node is not None else None
    world_off = parse_float3(getattr(node, "U03", "")) if node is not None else None
    reverse = bool(g("c000_U04", False))
    m = {
        "spawn": _spawn_values(spawn),
        "reverse": reverse,
        "forward": _direction(dov, reverse),
        "local_offset": tm_to_blender(local_off) if local_off else Vector(),
        "world_offset": tm_to_blender(world_off) if world_off else Vector(),
        "local_space": _int(getattr(node, "U12", 1), 1) != 0 if node is not None else True,
        "node_hue": num("U14", -1.0), "node_light": num("U15", 0.5), "ambient": num("U07", 1.0),
        "rate_mul": num("U05", 1.0),
        "program": None,
        "Viscosity": max(0.0, float(g("Viscosity", 0.0))),
        "IntensityPower": float(g("IntensityPower", 1.0)), "IntensityVariation": float(g("IntensityVariation", 0.0)),
        "LifeMax": float(g("LifeMax", 1.0)), "LifeVar01": float(g("LifeVar01", 0.0)),
        "SizeMax": float(g("SizeMax", 0.2)), "SizeVar01": float(g("SizeVar01", 0.0)),
        "SizeEndScale": float(g("SizeEndScale", 1.0)), "Weight": float(g("Weight", 0.0)),
        "Intensity": float(g("Intensity", 1.0)),
        "IntensityFadeIn": float(g("IntensityFadeIn", 0.0)), "IntensityFadeOut": float(g("IntensityFadeOut", 1.0)),
        "TextureAtlasDimX": max(1, int(g("TextureAtlasDimX", 1))),
        "TextureAtlasDimY": max(1, int(g("TextureAtlasDimY", 1))),
        # look (in-game tests, see the overlays)
        "rotate": _int(g("c002_U13", 1), 1) != 0,
        "Rotation": float(g("Rotation", 0.0)), "RotationVariation": float(g("RotationVariation", 0.0)),
        "use_emitter_hue": bool(g("UseEmitterHue", False)), "use_hue_shift": bool(g("UseHueShift", False)),
        "Hue": float(g("Hue", 0.0)), "energy": bool(g("UseEnergyOverLife", False)),
        "glow": float(g("c002_U10", 0.0)) > 0.0 or bool(g("c002_U11", False)),
        "distortion": bool(g("c002_U04", False)),
        "loop_period": max(0.0, float(g("c000_U02", 0.0))),
    }
    if use_expressions and node is not None and settings is not None and node_path:
        prog = build_program(settings, node_path, node)
        if prog["dynamic"]:
            m["program"] = prog
        else:   # constant: evaluate once
            vals = evaluate_program(prog, 0.0, lambda: 0.5)
            if vals is None:
                m["inactive"] = True        # a condition is never true: the game shows nothing
            else:
                _apply_node_values(m, vals, m)
    return m


def _int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _const_float(text, default):
    try:
        return float(str(text).strip().rstrip("fF"))
    except (TypeError, ValueError):
        return default


def _direction(dov, reverse=False) -> Vector:
    """emission direction (Blender axes) for a DOV vector (TM axes): particles travel along -DOV"""
    fwd = tm_to_blender([-c for c in (dov or TM_FORWARD)])
    if fwd.length < 1e-6:
        fwd = Vector((0.0, -1.0, 0.0))
    fwd = fwd.normalized()
    return -fwd if reverse else fwd


def _apply_node_values(dst: dict, vals: dict | None, m: dict) -> dict:
    """evaluated node values -> particle/model keys (Blender axes)"""
    if not vals:
        return dst
    if "dov" in vals:
        dst["forward"] = _direction(vals["dov"], m.get("reverse", False))
    if "local" in vals:
        dst["local_offset"] = tm_to_blender(vals["local"])
    if "world" in vals:
        dst["world_offset"] = tm_to_blender(vals["world"])
    for src, key in (("hue", "node_hue"), ("light", "node_light"), ("ambient", "ambient"), ("rate", "rate_mul")):
        if src in vals:
            dst[key] = vals[src]
    return dst


def _asset_image(mat):
    """Source image of an Image/Bitmap asset material, or None."""
    props = getattr(mat, "tm_asset_properties", None)
    return props.image if props is not None and props.is_asset else None


def _bitmap_image(gm):
    """Source image of the GPU model's bitmap asset, or None."""
    if getattr(gm, "BitmapIsFile", False):
        return None
    return _asset_image(getattr(gm, "Bitmap", None))


# ------------------------------------------------------------------ effect tree program (expressions)
_NODE_SEG = re.compile(r"\.(?:Children|Child)\[\d+\]")


def _node_type(node) -> int:
    try:
        return int(getattr(node, "Type", 0))
    except (TypeError, ValueError):
        return 0


def _float_bits(i) -> float:
    try:
        return struct.unpack("<f", struct.pack("<i", int(i)))[0]
    except (struct.error, TypeError, ValueError, OverflowError):
        return 0.0


def _walk_nodes(node, conds, out):
    """(conditions, node) of every effect node below ``node`` in tree order"""
    t = _node_type(node)
    here = conds + [getattr(node, "Condition", "")] if t == 1 else conds
    out.append((conds, node))
    for child in getattr(node, "Children", ()) if t == 0 else ():
        _walk_nodes(child, here, out)
    if t == 1:
        for child in getattr(node, "Child", ()):
            _walk_nodes(child, here, out)
    return out


def _compile_all(texts):
    return [e for e in (fxexpr.compile_expr(x) for x in texts) if e is not None]


def build_program(settings, node_path: str, node) -> dict:
    """Expressions that drive one emitter node: variable updates of the whole system (with their conditions),
    the conditions above the emitter, and its own expressions (TM axes). Evaluated per particle birth."""
    variables = {}
    for v in getattr(settings.vfx, "Variables", ()):
        variables[v.Name] = _float_bits(getattr(v, "U02", 0)) if _node_type(v) == 2 else 0.0
    updates = []
    try:
        root = bridge.resolve(settings, "vfx.Root")
        for conds, n in _walk_nodes(root, [], []):
            if _node_type(n) == 3 and n.VariableName:
                e = fxexpr.compile_expr(n.Expression)
                if e is not None:
                    updates.append((_compile_all(conds), n.VariableName, e))
    except (AttributeError, IndexError, KeyError):
        pass
    conds = []
    for m in _NODE_SEG.finditer(node_path):   # ancestors of the emitter node (the last match is the node itself)
        if m.end() >= len(node_path):
            break
        try:
            anc = bridge.resolve(settings, node_path[:m.end()])
        except (AttributeError, IndexError, KeyError):
            continue
        if _node_type(anc) == 1:
            c = fxexpr.compile_expr(anc.Condition)
            conds.append(c if c is not None else fxexpr.compile_expr("0"))   # broken condition: never true
    g = lambda k: fxexpr.compile_expr(getattr(node, k, ""))
    prog = {"variables": variables, "updates": updates, "conds": conds,
            "rate": g("U05"), "local": g("U02"), "world": g("U03"), "dov": g("U09"),
            "hue": g("U14"), "light": g("U15"), "ambient": g("U07")}
    exprs = [e for e in (prog["rate"], prog["local"], prog["world"], prog["dov"], prog["hue"], prog["light"],
                         prog["ambient"]) if e is not None] + conds
    prog["dynamic"] = bool(updates) or any(not e.const for e in exprs)
    # without rand the values only depend on Time: the simulation may share them within a short time step
    prog["random"] = any("rand" in e.text for e in exprs) or any("rand" in e.text for _c, _n, e in updates)
    return prog


def evaluate_program(prog: dict, time_ms: float, rnd) -> dict | None:
    """node values at ``time_ms`` (None when a condition is false); vectors stay in TM axes"""
    env = dict(prog["variables"])
    env["Time"] = time_ms
    for conds, name, e in prog["updates"]:
        if all(fxexpr.truthy(c.eval(env, rnd)) for c in conds):
            env[name] = e.eval(env, rnd)
    for c in prog["conds"]:
        if not fxexpr.truthy(c.eval(env, rnd)):
            return None
    out = {}
    for key in ("rate", "hue", "light", "ambient"):
        e = prog[key]
        if e is not None:
            v = e.eval(env, rnd)
            out[key] = float(v[0] if isinstance(v, tuple) else v) if not isinstance(v, str) else 0.0
    for key in ("local", "world", "dov"):
        e = prog[key]
        if e is not None:
            v = e.eval(env, rnd)
            if isinstance(v, tuple) and len(v) >= 3:
                out[key] = v[:3]
            elif isinstance(v, (int, float)):
                out[key] = (float(v),) * 3
    return out


def gpu_emitters(settings) -> list:
    """(GPU model, its effect node or None, sibling GPU spawn's Spawn struct or None, effect node path)
    for every GPU model."""
    out = []
    spawn_rows = {r.path.rsplit(".", 1)[0]: r.path for r in settings.outline if r.cls == "CPlugParticleGpuSpawn"}
    for row in settings.outline:
        if row.cls != GPU_MODEL:
            continue
        try:
            gm = bridge.resolve(settings, row.path)
        except (AttributeError, IndexError, KeyError):
            continue
        node, node_path = None, ""
        if ".Emitter" in row.path:
            node_path = row.path.rsplit(".Emitter", 1)[0]
            try:
                node = bridge.resolve(settings, node_path)
            except (AttributeError, IndexError, KeyError):
                node = None
        spawn = None
        spawn_path = spawn_rows.get(row.path.rsplit(".", 1)[0])
        if spawn_path is not None:
            try:
                spawn = bridge.resolve(settings, spawn_path + ".Spawn")
            except (AttributeError, IndexError, KeyError):
                spawn = None
        out.append((gm, node, spawn, node_path))
    return out


def gpu_models(settings) -> list:
    """Every GPU model of the effect."""
    return [e[0] for e in gpu_emitters(settings)]


def _tree_values(tree) -> dict:
    g = lambda k, d: getattr(tree, k, d)
    gx, gy = g("propagation_atlas_grid", (1, 1))
    return {
        "positions": [tuple(e.value) for e in g("propagation_emission_positions", [])],
        "radius": float(g("propagation_emission_spawn_radius", 0.0)),
        "rate": float(g("propagation_leaf_per_second", 0)),
        "cone_deg": math.degrees(g("propagation_cone_half_angle_degree", 0.0)),
        "size": float(g("propagation_leaf_size", 0.1)),
        "atlas": (max(1, int(gx)), max(1, int(gy))),
    }


def tree_anchor(col):
    """World transform (location + rotation, no scale) of the tree model: its first mesh object by name,
    the node the converter places the tree at. None for a tree model without meshes."""
    from ..utils.FunctionsV2 import get_item_collection_objects
    meshes = sorted((o for o in get_item_collection_objects(col) if o.type == "MESH"), key=lambda o: o.name)
    if not meshes:
        return None
    loc, rot, _ = meshes[0].matrix_world.decompose()
    return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()


def tree_models(context) -> list:
    """(collection, tree settings, tree anchor matrix) of every visible tree model with propagation enabled."""
    from ..properties.PropertyIdentifiers import CollectionProp
    from ..utils.FunctionsV2 import is_tree_model_collection
    out = []
    for col in bpy.data.collections:
        if not is_tree_model_collection(col) or col.hide_viewport:
            continue
        tree = getattr(col, CollectionProp.VEGET_TREE, None)
        if tree is None or not tree.enable_propagation:
            continue
        anchor = tree_anchor(col)
        if anchor is not None:
            out.append((col, tree, anchor))
    return out


def _fx_objects(context, p):
    if p.scope == "ACTIVE":
        ob = context.object
        return [ob] if is_fx_node(ob) and ob.visible_get() else []
    return [ob for ob in context.scene.objects if is_fx_node(ob) and ob.visible_get()]


# ------------------------------------------------------------------ drawing
_gpu = {"shader": None, "white": None, "textures": {}}


def _shader():
    if _gpu["shader"] is None:
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant("MAT4", "ViewProjectionMatrix")
        info.sampler(0, "FLOAT_2D", "image")
        info.vertex_in(0, "VEC3", "pos")
        info.vertex_in(1, "VEC2", "uv")
        info.vertex_in(2, "VEC4", "col")
        iface = gpu.types.GPUStageInterfaceInfo("tmfx_preview_iface")
        iface.smooth("VEC2", "uvInterp")
        iface.smooth("VEC4", "colInterp")
        info.vertex_out(iface)
        info.fragment_out(0, "VEC4", "FragColor")
        info.vertex_source(
            "void main() { uvInterp = uv; colInterp = col; gl_Position = ViewProjectionMatrix * vec4(pos, 1.0); }")
        info.fragment_source("void main() { FragColor = texture(image, uvInterp) * colInterp; }")
        _gpu["shader"] = gpu.shader.create_from_info(info)
    return _gpu["shader"]


def _texture(image):
    if image is None:
        if _gpu["white"] is None:
            buf = gpu.types.Buffer("FLOAT", 4, [1.0, 1.0, 1.0, 1.0])
            _gpu["white"] = gpu.types.GPUTexture((1, 1), format="RGBA16F", data=buf)
        return _gpu["white"]
    key = (image.name, image.as_pointer(), image.size[0], image.size[1])
    tex = _gpu["textures"].get(key)
    if tex is None:
        tex = gpu.texture.from_image(image)
        _gpu["textures"][key] = tex
    return tex


def _build(parts, atlas, tint, alpha_scale, view_rot, view_pos):
    """Camera facing quads (pos, uv, col) for ``parts`` = (world, size, alpha, cell, angle[, rgb]), back to front."""
    right0, up0 = view_rot.col[0].xyz, view_rot.col[1].xyz
    dx, dy = atlas
    parts = sorted(parts, key=lambda x: -(x[0] - view_pos).length)
    pos, uv, col = [], [], []
    for part in parts:
        w, size, alpha, cell, angle = part[:5]
        rgb = part[5] if len(part) > 5 else (1.0, 1.0, 1.0)
        h = size * 0.5
        c, sn = math.cos(angle), math.sin(angle)
        r = (right0 * c + up0 * sn) * h
        u = (up0 * c - right0 * sn) * h
        cx, cy = cell % dx, cell // dx
        u0, u1 = cx / dx, (cx + 1) / dx
        v1, v0 = 1.0 - cy / dy, 1.0 - (cy + 1) / dy
        corners = (w - r - u, w + r - u, w + r + u, w - r + u)
        uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        colour = (tint[0] * rgb[0], tint[1] * rgb[1], tint[2] * rgb[2], alpha * alpha_scale)
        for idx in (0, 1, 2, 0, 2, 3):
            pos.append(corners[idx][:])
            uv.append(uvs[idx])
            col.append(colour)
    return pos, uv, col


def particle_colour(m: dict, q: dict) -> tuple:
    """RGB multiplier of particle ``q`` (in-game tests, approximations):
    - UseEmitterHue + UseHueShift: node LinearHue01 / HueLightness (outside [0;1] -> hue 0 = red, lightness 0.5)
    - UseHueShift alone: GPU model Hue (untested, mild)
    - UseEnergyOverLife: white -> red over the life
    - node LAmbient (U07): 0 dark, 1 normal, 3 bright"""
    r = g = b = 1.0
    if m.get("use_hue_shift"):
        if m.get("use_emitter_hue"):
            h, light = q.get("node_hue", m.get("node_hue", -1.0)), q.get("node_light", m.get("node_light", 0.5))
            if not 0.0 <= h <= 1.0:
                h, light = 0.0, 0.5
            r, g, b = colorsys.hls_to_rgb(h % 1.0, min(1.0, max(0.0, light)), 1.0)
        else:
            r, g, b = colorsys.hls_to_rgb(m.get("Hue", 0.0) % 1.0, 0.6, 0.5)
    if m.get("energy"):
        f = min(1.0, max(0.0, q["age"] / q["life"])) if q.get("life") else 0.0
        r, g, b = r, g * (1.0 - 0.8 * f), b * (1.0 - min(1.0, 1.6 * f))
    a = q.get("ambient", m.get("ambient", 1.0))
    k = 0.3 + 0.7 * max(0.0, min(3.0, float(a)))
    return (r * k, g * k, b * k)


def _fx_parts(ob, m, p, t, seed):
    mw = ob.matrix_world
    rot = mw.to_3x3().normalized()
    origin = mw.translation
    # Weight: negative falls, positive rises (in-game tests); magnitude taken as m/s² x the scale setting
    grav = Vector((0.0, 0.0, m["Weight"] * p["gravity"]))
    frame = rot if m.get("local_space", True) else Matrix.Identity(3)   # DOVAndUpAreLocalSpace (node U12)
    drag = m.get("Viscosity", 0.0)
    parts = []
    for q in simulate(m, p, t + max(0.01, m["LifeMax"]), seed):   # pre-warmed: running at the first frame
        start = (origin + rot @ q.get("local_offset", m.get("local_offset", Vector()))
                 + q.get("world_offset", m.get("world_offset", Vector())))
        v0 = frame @ q["vel"] + Vector((0.0, 0.0, q.get("vertical", 0.0)))
        world = motion(start + frame @ q["pos"], v0, grav, drag, q["age"])
        size, alpha, cell = particle_look(m, p, q)
        if size > 0.0 and alpha > 0.0:
            angle = q.get("angle0", 0.0) + q.get("spin", 0.0) * q["age"]
            parts.append((world, size, alpha, cell, angle, particle_colour(m, q)))
    return parts


def _tree_parts(tv, origin, p, t, seed):
    cells = tv["atlas"][0] * tv["atlas"][1]
    parts = []
    for q in simulate_propagation(tv, p, t + LEAF_MAX_LIFE, seed):   # pre-warmed: running at the first frame
        alpha = leaf_alpha(q)
        if alpha > 0.0:
            parts.append((origin + q["pos"], q["size"], alpha, min(cells - 1, int(q["r"] * cells)), q["angle"]))
    return parts


def _batch(shader, image, quads):
    pos, uv, col = quads
    if pos:
        shader.uniform_sampler("image", _texture(image))
        batch_for_shader(shader, "TRIS", {"pos": pos, "uv": uv, "col": col}).draw(shader)


def _draw():
    context = bpy.context
    scene = context.scene
    p = getattr(scene, PREVIEW_ATTR, None)
    rv3d = context.region_data
    if p is None or not (p.show or p.show_trees) or rv3d is None:
        return
    t = preview_time_s(scene)
    pd ={k: getattr(p, k) for k in ("shape", "radius", "rate", "speed", "spread", "gravity",
                                      "atlas", "fade", "max_particles", "use_spawn", "leaf_fall_speed", "leaf_spin", "leaf_life", "leaf_rate")}
    view_inv = rv3d.view_matrix.inverted()
    view_rot, view_pos = view_inv.to_3x3(), view_inv.translation
    shader = _shader()
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS_EQUAL")
    gpu.state.depth_mask_set(False)
    try:
        shader.bind()
        shader.uniform_float("ViewProjectionMatrix", rv3d.perspective_matrix)
        for ob in (_fx_objects(context, p) if p.show else ()):
            settings = getattr(ob, OBJECT_ATTR)
            for seed, (gm, node, spawn, node_path) in enumerate(gpu_emitters(settings)):
                m = _model_values(gm, node, spawn, settings, node_path, p.use_expressions)
                image = _bitmap_image(gm)
                k = max(0.0, m["Intensity"])
                tint = (k, k, k) if image is not None else (k, 0.85 * k, 0.5 * k)
                alpha_scale = 1.0 if image is not None else 0.6
                if m.get("distortion"):
                    alpha_scale *= 0.25            # heat haze: only a faint hint, the blur is not drawn
                quads = _build(_fx_parts(ob, m, pd, t, seed), (m["TextureAtlasDimX"], m["TextureAtlasDimY"]),
                               tint, alpha_scale, view_rot, view_pos)
                gpu.state.blend_set("ADDITIVE" if m.get("glow") else "ALPHA")   # additive glow (sparks)
                _batch(shader, image, quads)
            gpu.state.blend_set("ALPHA")
        for seed, (col, tree, anchor) in enumerate(tree_models(context) if p.show_trees else ()):
            tv = _tree_values(tree)
            origin = anchor.translation   # leaves fall in world -Z down to the tree's height
            tv["positions"] = [tuple(anchor @ Vector(v) - origin) for v in tv["positions"]]
            image = _asset_image(getattr(tree, "propagation_base_color", None))
            tint = (1.0, 1.0, 1.0) if image is not None else (0.45, 0.8, 0.3)
            quads = _build(_tree_parts(tv, origin, pd, t, 1000 + seed), tv["atlas"], tint,
                           1.0 if image is not None else 0.7, view_rot, view_pos)
            _batch(shader, image, quads)
    except Exception as e:   # never break the viewport
        print("tm_fx preview:", e)
    finally:
        gpu.state.depth_mask_set(True)
        gpu.state.depth_test_set("NONE")
        gpu.state.blend_set("NONE")


# ------------------------------------------------------------------ legacy cleanup
def legacy_data():
    """Objects/collections/... left over from the old particle system preview."""
    found = []
    for base in LEGACY_NAMES:
        for coll, names in ((bpy.data.objects, (base + "_Emitter", base + "_Blob")),
                            (bpy.data.collections, (base,)), (bpy.data.particles, (base,)),
                            (bpy.data.materials, (base + "_Mat",)),
                            (bpy.data.meshes, (base + "_Emitter", base + "_Blob", base + "_Sprite"))):
            found += [(coll, n) for n in names if coll.get(n) is not None]
    return found


class TMFX_OT_preview_cleanup(bpy.types.Operator):
    """Remove the objects/collection created by the old particle system preview"""
    bl_idname, bl_label = "tm_fx.preview_cleanup", "Remove old preview objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        found = legacy_data()
        for coll, name in found:   # objects first (listed first), then their data
            item = coll.get(name)
            if item is not None:
                coll.remove(item)
        self.report({"INFO"}, f"Removed {len(found)} old preview data-blocks")
        return {"FINISHED"}


class TMFX_PT_preview(bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Preview (approximate)", "TMFX_PT_preview", "TMFX_PT_main"
    bl_category, bl_space_type, bl_region_type = "Blendermania", "VIEW_3D", "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        return settings_of(context) is not None

    def draw_header(self, context):
        self.layout.prop(getattr(context.scene, PREVIEW_ATTR), "show", text="")

    def draw(self, context):
        p = getattr(context.scene, PREVIEW_ATTR)
        lay = self.layout
        lay.label(text="Overlay only, not the game.", icon="INFO")
        lay.label(text="Play / time: Blendermania > Preview panel", icon="PLAY")
        if p.show and not gpu_models(settings_of(context)):
            lay.label(text="No GPU model in this effect: add an Emitter in Structure", icon="ERROR")
        lay.row().prop(p, "scope", expand=True)
        col = lay.column(align=True)
        col.enabled = p.show
        col.label(text="Spawn")
        col.prop(p, "use_spawn")
        col.prop(p, "use_expressions")
        sub = col.column(align=True)
        sub.enabled = not p.use_spawn
        sub.prop(p, "shape")
        sub.prop(p, "radius")
        sub.prop(p, "rate")
        sub.prop(p, "speed")
        sub.prop(p, "spread")
        col.separator()
        col.label(text="Interpretation")
        col.prop(p, "gravity")
        col.prop(p, "atlas")
        col.prop(p, "fade")
        col.prop(p, "max_particles")
        n = len(gpu_models(settings_of(context)))
        lay.label(text=f"{n} GPU model(s) in this effect", icon="PARTICLES")
        if legacy_data():
            lay.operator(TMFX_OT_preview_cleanup.bl_idname, icon="TRASH")


def tree_preview_issues(col, tree) -> list:
    """Why the propagation preview of this tree model shows nothing (empty list = it draws)."""
    issues = []
    if tree_anchor(col) is None:
        issues.append("No mesh in the tree model: leaves are placed relative to its first mesh")
    if not len(tree.propagation_emission_positions):
        issues.append("No emission positions")
    if tree.propagation_leaf_per_second <= 0:
        issues.append("Leaves Per Second is 0")
    if col.hide_viewport:
        issues.append("Tree model collection is disabled in viewports")
    return issues


def draw_tree_preview(layout, context, collection=None):
    """Leaf animation preview settings, drawn in the tree model collection panel."""
    p = getattr(context.scene, PREVIEW_ATTR)
    box = layout.box()
    box.prop(p, "show_trees", text="Show Leaf Animation", icon="PLAY" if p.show_trees else "HIDE_ON")
    if p.show_trees and collection is not None:
        from ..properties.PropertyIdentifiers import CollectionProp
        for msg in tree_preview_issues(collection, getattr(collection, CollectionProp.VEGET_TREE)):
            box.label(text=msg, icon="ERROR")
    col = box.column(align=True)
    col.enabled = p.show_trees
    col.prop(p, "leaf_rate", slider=True)
    col.prop(p, "leaf_fall_speed")
    col.prop(p, "leaf_life")
    col.prop(p, "leaf_spin")
    col.label(text="Overlay only, these settings are not exported.", icon="INFO")
    col.label(text="Play / time: Blendermania > Preview panel", icon="PLAY")


_CLASSES = (FXPreview, TMFX_OT_preview_cleanup, TMFX_PT_preview)
_handle = {"draw": None}


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)
    setattr(bpy.types.Scene, PREVIEW_ATTR, PointerProperty(type=FXPreview))
    if not bpy.app.background:
        _handle["draw"] = bpy.types.SpaceView3D.draw_handler_add(_draw, (), "WINDOW", "POST_VIEW")


def unregister():
    if _handle["draw"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle["draw"], "WINDOW")
        _handle["draw"] = None
    _gpu.update(shader=None, white=None, textures={})
    delattr(bpy.types.Scene, PREVIEW_ATTR)
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
