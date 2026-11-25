"""
Viewport preview of custom material UV animations, driven by the shared preview clock (Preview panel, "UV Anims").

The custom material preview (AssetLibraryFunctions._sync_custommaterial_preview) moves the UVs of the glow texture
of the models that animate in game (UV_ANIM_MODELS) with shader nodes (build_uv_anim_vector). The animation settings
are node constants; the time comes from the hidden scene custom property TIME_PROP, read by an Attribute node
(type View Layer). A tick therefore only writes that one value: the material itself never changes during playback
(writing node values per tick made every frame a material update: shader update + icon re-render -> very laggy).
Settings changes rebuild the nodes (property update callbacks; added/removed animations by signature check).

Like the game: only the first 2 animations, only layer SelfIllum. Directions are derived from the game convention
(uv += offset, V pointing down in the texture) and the FBX V flip, not checked side by side in game yet:
  Scroll     offset = Speed * t / Period (wrapped to 0..1)
  Flip-book  the game shrinks the UVs to one cell (1/FramesX x 1/FramesY, seen in game: the mesh UVs cover the
             whole atlas); frame = floor(frac(t / Period) * FrameCount), row by row from the top left cell.
  preview UV = mesh UV * uv_scale + uv_offset (Mapping node: scale, then location)
"""
import math

import bpy

TIME_PROP = "_tm_uv_anim_time"      # "_": hidden in the Custom Properties panel
NODE_PREFIX = "GBX_CM_UVAnim"
MAPPING_NODE = NODE_PREFIX
MAX_ANIMS = 2

_signatures: dict[str, tuple] = {}  # material name -> animation settings the nodes were built from


# ---------- reference math (pure, testable headless; the nodes compute the same) ----------
def _scroll(anim, t_s: float) -> tuple[float, float]:
    cycles = t_s / max(anim.period, 1e-6)
    # game V points down, Blender V up (FBX flips V) -> negate V
    return (anim.speed_u * cycles) % 1.0, (-anim.speed_v * cycles) % 1.0


def _frames(anim) -> tuple[int, int, int]:
    fx, fy = max(anim.frames_x, 1), max(anim.frames_y, 1)
    return fx, fy, (anim.frame_count if anim.frame_count > 0 else fx * fy)


def _flipbook(anim, t_s: float) -> tuple[float, float]:
    """offset of the current cell (UVs already scaled to one cell). Blender V points up: row 0 = top =
    v in [1 - 1/fy, 1]"""
    fx, fy, count = _frames(anim)
    phase = (t_s / max(anim.period, 1e-6)) % 1.0
    frame = min(int(math.floor(phase * count)), count - 1)
    col, row = frame % fx, (frame // fx) % fy
    return col / fx, (fy - 1 - row) / fy


def uv_scale(anims) -> tuple[float, float]:
    """one cell of the first flip-book animation, else unscaled"""
    for anim in active_anims(anims):
        if anim.anim_type == "TransSubTexture":
            fx, fy, _ = _frames(anim)
            return 1.0 / fx, 1.0 / fy
    return 1.0, 1.0


def active_anims(anims) -> list:
    return [a for a in list(anims)[:MAX_ANIMS] if a.layer == "SelfIllum"]


def uv_offset(anims, t_s: float) -> tuple[float, float]:
    """summed UV offset of the animations at t_s seconds"""
    u = v = 0.0
    for anim in active_anims(anims):
        du, dv = _flipbook(anim, t_s) if anim.anim_type == "TransSubTexture" else _scroll(anim, t_s)
        u += du
        v += dv
    return u, v


def signature(cm) -> tuple:
    return tuple((a.anim_type, a.layer, a.period, a.speed_u, a.speed_v, a.frame_count, a.frames_x, a.frames_y)
                 for a in active_anims(cm.uv_anims))


# ---------- shader nodes ----------
def build_uv_anim_vector(nt, cm, uv_socket, mat_name: str):
    """nodes moving uv_socket by the animations of cm; returns the moved UV socket"""
    _signatures[mat_name] = signature(cm)
    nodes, links = nt.nodes, nt.links
    pos = [-1500, -400]

    def node(kind, label, **inputs):
        n = nodes.new(kind)
        n.name = n.label = f"{NODE_PREFIX}_{label}"
        n.location = tuple(pos)
        pos[0] += 160
        for key, value in inputs.items():
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, n.inputs[key])
            else:
                n.inputs[key].default_value = value
        return n

    def math_node(op, a, b=0.0, label="Math"):
        n = node("ShaderNodeMath", label)
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    time = nodes.new("ShaderNodeAttribute")
    time.name = time.label = f"{NODE_PREFIX}_Time"
    time.attribute_type = "VIEW_LAYER"
    time.attribute_name = TIME_PROP
    time.location = (pos[0], pos[1])
    t = time.outputs["Fac"]

    offsets = []
    for i, anim in enumerate(active_anims(cm.uv_anims)):
        pos[0], pos[1] = -1350, -400 - 180 * i
        k = 1.0 / max(anim.period, 1e-6)
        if anim.anim_type == "TransSubTexture":
            fx, fy, count = _frames(anim)
            phase = math_node("FRACT", math_node("MULTIPLY", t, k))
            frame = math_node("FLOOR", math_node("MULTIPLY", phase, float(count)))
            u = math_node("DIVIDE", math_node("FLOORED_MODULO", frame, float(fx)), float(fx))
            row = math_node("FLOORED_MODULO", math_node("FLOOR", math_node("DIVIDE", frame, float(fx))), float(fy))
            v = math_node("DIVIDE", math_node("SUBTRACT", float(fy - 1), row), float(fy))
        else:
            u = math_node("FRACT", math_node("MULTIPLY", t, anim.speed_u * k))
            v = math_node("FRACT", math_node("MULTIPLY", t, -anim.speed_v * k))
        offsets.append(node("ShaderNodeCombineXYZ", f"Offset{i}", X=u, Y=v).outputs[0])

    mapping = node("ShaderNodeMapping", "Map", Vector=uv_socket)
    mapping.name = mapping.label = MAPPING_NODE
    su, sv = uv_scale(cm.uv_anims)
    mapping.inputs["Scale"].default_value = (su, sv, 1.0)
    if offsets:
        total = offsets[0]
        for extra in offsets[1:]:
            add = node("ShaderNodeVectorMath", "Sum")
            add.operation = "ADD"
            links.new(total, add.inputs[0])
            links.new(extra, add.inputs[1])
            total = add.outputs[0]
        links.new(total, mapping.inputs["Location"])
    return mapping.outputs["Vector"]


# ---------- clock ----------
def preview_time_s(scene) -> float:
    """seconds on the shared preview clock, 0 while the UV anim preview is off"""
    if scene is None or not getattr(scene, "tm_preview_uv_anims", False):
        return 0.0
    from .Animations import current_time_ms
    return current_time_ms(scene) / 1000.0


def _rebuild_changed() -> None:
    """animations added/removed (no update callback for collection changes): rebuild those previews"""
    from ..properties.AssetProperties import UV_ANIM_MODELS
    from .AssetLibraryFunctions import sync_preview
    for mat in bpy.data.materials:
        nt = mat.node_tree
        if nt is None or mat.library is not None or MAPPING_NODE not in nt.nodes:
            continue
        cm = mat.tm_asset_properties.custom_material
        if cm.model in UV_ANIM_MODELS and _signatures.get(mat.name) != signature(cm):
            sync_preview(mat)


def set_time(scene) -> None:
    """the only per-tick write: the time the Attribute nodes read"""
    if scene is None:
        return
    t_s = preview_time_s(scene)
    if abs(scene.get(TIME_PROP, -1.0) - t_s) > 1e-7:
        scene[TIME_PROP] = t_s
        scene.update_tag()
    _rebuild_changed()


def on_anim_prop_changed(self, context):
    """update= callback of the uv anim properties: rebuild the node constants"""
    mat = self.id_data
    if isinstance(mat, bpy.types.Material):
        from .AssetLibraryFunctions import sync_preview
        sync_preview(mat)
