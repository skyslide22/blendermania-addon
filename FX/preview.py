"""Approximate particle preview, drawn as a viewport overlay.

NOT the game: only fields with a clear meaning are used. Nothing is added to the
scene (no objects, collections, meshes or materials), so nothing can be exported by
accident. Particles are simulated from the timeline time (deterministic, scrubbing
works) and drawn as camera facing sprites with the GPU model's bitmap asset.

Taken from every GPU model of the effect:
    LifeMax, LifeVar01              lifetime and its randomness (s)
    SizeMax, SizeVar01              start size and its randomness
    SizeEndScale                    size at the end of life (linear over life)
    Weight x gravity scale          gravity (Weight's meaning is a guess, scale 0 by default)
    Intensity                       brightness of the sprite
    IntensityFadeIn/Out, IntensityPower, IntensityVariation
                                    fade in/out as fraction of the life, power-shaped fade out,
                                    per particle brightness (guess, can be switched off)
    EffectNode U09 (forward axis)   emission direction, Trackmania axes (default float3(0,0,-1) = Blender +Y)
    Bitmap, TextureAtlasDimX/Y      texture; atlas cells first / over life / random (how the game picks is unknown)
GPU spawn (found in game tests): U04 rate, U11 speed, U12 speed variation (option "From GPU spawn").
Preview only (never exported): spawn shape, size, spread, and rate/speed when "From GPU spawn" is off.

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
import math

import bpy
import gpu
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from . import bridge
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
                            description="Rate and speed from the GPU spawn fields found in game tests: "
                                        "U04 rate, U11 speed, U12 speed variation (the manual values below are ignored)")
    rate: FloatProperty(name="Rate /s", default=20.0, min=0.1, soft_max=500.0, update=_redraw, description="Preview only")
    speed: FloatProperty(name="Speed", default=0.5, min=0.0, update=_redraw,
                         description="Preview only: start speed along the emitter's forward axis (effect node expression, "
                                     "TM -Z = Blender +Y of the empty; sphere/box: outwards)")
    spread: FloatProperty(name="Spread", default=0.2, min=0.0, max=1.0, subtype="FACTOR", update=_redraw,
                          description="Preview only: random direction added to the start speed")
    gravity: FloatProperty(name="Gravity scale", default=0.0, soft_min=-1.0, soft_max=1.0, update=_redraw,
                           description="Gravity = -9.81 m/s² x Weight x this (Weight's meaning is a guess)")
    atlas: EnumProperty(name="Atlas", items=ATLAS, default="LIFE", update=_redraw)
    fade: BoolProperty(name="Fade (guess)", default=True, update=_redraw,
                       description="Fade in over IntensityFadeIn, fade out from IntensityFadeOut (fractions of the life) "
                                   "with IntensityPower as curve exponent; IntensityVariation varies the brightness")
    max_particles: IntProperty(name="Max particles", default=2000, min=10, soft_max=10000, update=_redraw,
                               description="Per GPU model / tree model, keeps the viewport responsive")
    # veget tree propagation
    show_trees: BoolProperty(name="Tree Leaves", default=False, update=_toggled,
                             description="Draw the falling leaves of every visible tree model with propagation enabled (overlay)")
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
    spawn = m.get("spawn") if p.get("use_spawn") else None
    rate = max(0.1, spawn["rate"] if spawn else p["rate"])
    life_max = max(0.01, m["LifeMax"])
    first = max(0, math.floor((t - life_max) * rate))
    last = math.floor(t * rate)
    if last - first > p["max_particles"]:
        first = last - p["max_particles"]
    out = []
    for i in range(first, last + 1):
        birth = i / rate
        age = t - birth
        life = life_max * (1.0 - min(0.99, max(0.0, m["LifeVar01"])) * _rnd(i, 0, seed))
        if age < 0.0 or age >= life:
            continue
        shape, radius = p["shape"], p["radius"]
        forward = m.get("forward", Vector((0.0, 1.0, 0.0)))
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
        direction = (base + _rnd_dir(i, 7, seed) * p["spread"]).normalized()
        if spawn:
            speed = max(0.0, spawn["speed"] + (2.0 * _rnd(i, 12, seed) - 1.0) * spawn["speed_var"])
        else:
            speed = p["speed"]
        size = m["SizeMax"] * (1.0 - min(1.0, max(0.0, m["SizeVar01"])) * _rnd(i, 9, seed))
        out.append({"pos": pos, "vel": direction * speed, "age": age, "life": life,
                    "size": size, "r": _rnd(i, 10, seed), "r2": _rnd(i, 11, seed)})
    return out


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
            alpha = max(0.0, (1.0 - f) / (1.0 - fo)) ** max(1.0, m.get("IntensityPower", 1.0))
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
    """Rate/speed of a GPU spawn's Spawn struct (U04 rate, U11 speed, U12 speed variation, found in game tests)."""
    if spawn is None:
        return None
    return {"rate": float(getattr(spawn, "U04", 0.0)), "speed": float(getattr(spawn, "U11", 0.0)),
            "speed_var": float(getattr(spawn, "U12", 0.0))}


def _model_values(gm, node=None, spawn=None) -> dict:
    """GPU model values; ``node`` is its effect node (forward axis expression U09), ``spawn`` the sibling
    GPU spawn's Spawn struct, if any."""
    g = lambda k, d: getattr(gm, k, d)
    forward = parse_float3(getattr(node, "U09", "")) if node is not None else None
    fwd = tm_to_blender(forward or TM_FORWARD)
    return {
        "spawn": _spawn_values(spawn),
        "forward": fwd.normalized() if fwd.length > 1e-6 else Vector((0.0, 1.0, 0.0)),
        "IntensityPower": float(g("IntensityPower", 1.0)), "IntensityVariation": float(g("IntensityVariation", 0.0)),
        "LifeMax": float(g("LifeMax", 1.0)), "LifeVar01": float(g("LifeVar01", 0.0)),
        "SizeMax": float(g("SizeMax", 0.2)), "SizeVar01": float(g("SizeVar01", 0.0)),
        "SizeEndScale": float(g("SizeEndScale", 1.0)), "Weight": float(g("Weight", 0.0)),
        "Intensity": float(g("Intensity", 1.0)),
        "IntensityFadeIn": float(g("IntensityFadeIn", 0.0)), "IntensityFadeOut": float(g("IntensityFadeOut", 1.0)),
        "TextureAtlasDimX": max(1, int(g("TextureAtlasDimX", 1))),
        "TextureAtlasDimY": max(1, int(g("TextureAtlasDimY", 1))),
    }


def _asset_image(mat):
    """Source image of an Image/Bitmap asset material, or None."""
    props = getattr(mat, "tm_asset_properties", None)
    return props.image if props is not None and props.is_asset else None


def _bitmap_image(gm):
    """Source image of the GPU model's bitmap asset, or None."""
    if getattr(gm, "BitmapIsFile", False):
        return None
    return _asset_image(getattr(gm, "Bitmap", None))


def gpu_emitters(settings) -> list:
    """(GPU model, its effect node or None, sibling GPU spawn's Spawn struct or None) for every GPU model."""
    out = []
    spawn_rows = {r.path.rsplit(".", 1)[0]: r.path for r in settings.outline if r.cls == "CPlugParticleGpuSpawn"}
    for row in settings.outline:
        if row.cls != GPU_MODEL:
            continue
        try:
            gm = bridge.resolve(settings, row.path)
        except (AttributeError, IndexError, KeyError):
            continue
        node = None
        if ".Emitter" in row.path:
            try:
                node = bridge.resolve(settings, row.path.rsplit(".Emitter", 1)[0])
            except (AttributeError, IndexError, KeyError):
                node = None
        spawn = None
        spawn_path = spawn_rows.get(row.path.rsplit(".", 1)[0])
        if spawn_path is not None:
            try:
                spawn = bridge.resolve(settings, spawn_path + ".Spawn")
            except (AttributeError, IndexError, KeyError):
                spawn = None
        out.append((gm, node, spawn))
    return out


def gpu_models(settings) -> list:
    """Every GPU model of the effect."""
    return [gm for gm, _, _ in gpu_emitters(settings)]


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
    """Camera facing quads (pos, uv, col) for ``parts`` = (world, size, alpha, cell, angle), back to front."""
    right0, up0 = view_rot.col[0].xyz, view_rot.col[1].xyz
    dx, dy = atlas
    parts = sorted(parts, key=lambda x: -(x[0] - view_pos).length)
    pos, uv, col = [], [], []
    for w, size, alpha, cell, angle in parts:
        h = size * 0.5
        c, sn = math.cos(angle), math.sin(angle)
        r = (right0 * c + up0 * sn) * h
        u = (up0 * c - right0 * sn) * h
        cx, cy = cell % dx, cell // dx
        u0, u1 = cx / dx, (cx + 1) / dx
        v1, v0 = 1.0 - cy / dy, 1.0 - (cy + 1) / dy
        corners = (w - r - u, w + r - u, w + r + u, w - r + u)
        uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        colour = (tint[0], tint[1], tint[2], alpha * alpha_scale)
        for idx in (0, 1, 2, 0, 2, 3):
            pos.append(corners[idx][:])
            uv.append(uvs[idx])
            col.append(colour)
    return pos, uv, col


def _fx_parts(ob, m, p, t, seed):
    mw = ob.matrix_world
    rot = mw.to_3x3().normalized()
    origin = mw.translation
    grav = Vector((0.0, 0.0, -9.81 * m["Weight"] * p["gravity"]))
    parts = []
    for q in simulate(m, p, t + max(0.01, m["LifeMax"]), seed):   # pre-warmed: running at the first frame
        a = q["age"]
        world = origin + rot @ q["pos"] + (rot @ q["vel"]) * a + grav * (0.5 * a * a)
        size, alpha, cell = particle_look(m, p, q)
        if size > 0.0 and alpha > 0.0:
            parts.append((world, size, alpha, cell, 0.0))
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
            for seed, (gm, node, spawn) in enumerate(gpu_emitters(settings)):
                m = _model_values(gm, node, spawn)
                image = _bitmap_image(gm)
                k = max(0.0, m["Intensity"])
                tint = (k, k, k) if image is not None else (k, 0.85 * k, 0.5 * k)
                quads = _build(_fx_parts(ob, m, pd, t, seed), (m["TextureAtlasDimX"], m["TextureAtlasDimY"]),
                               tint, 1.0 if image is not None else 0.6, view_rot, view_pos)
                _batch(shader, image, quads)
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
        col.label(text="Spawn (shape, size and spread are preview only)")
        col.prop(p, "shape")
        col.prop(p, "radius")
        col.prop(p, "use_spawn")
        sub = col.column(align=True)
        sub.enabled = not p.use_spawn
        sub.prop(p, "rate")
        sub.prop(p, "speed")
        col.prop(p, "spread")
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
    """Propagation preview settings, drawn in the tree model collection panel."""
    p = getattr(context.scene, PREVIEW_ATTR)
    box = layout.box()
    box.prop(p, "show_trees", text="Show Propagation", icon="PLAY" if p.show_trees else "HIDE_ON")
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
