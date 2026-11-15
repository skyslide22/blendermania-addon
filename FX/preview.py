"""Approximate viewport preview using Blender's native particle system.

NOT the game: only fields with a clear meaning are mapped (see MAPPING in the
README).  Emission rate, speed and spawn shape are not known from the GBX data
yet, so they are *preview-only* settings that are never exported.  Particles are
drawn as instanced low-poly blobs (Blender has no billboard particles).
"""
import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty

from . import bridge
from .props import settings_of

PREVIEW_ATTR = "tm_fx_preview"
NAME = "TMFX_Preview"
SHAPES = [("POINT", "Point", ""), ("SPHERE", "Sphere", ""), ("BOX", "Box", "")]


class FXPreview(bpy.types.PropertyGroup):
    shape: EnumProperty(name="Shape", items=SHAPES, default="POINT")
    radius: FloatProperty(name="Spawn size", default=0.5, min=0.01, description="Preview only")
    rate: FloatProperty(name="Rate /s", default=20.0, min=0.1, description="Preview only")
    speed: FloatProperty(name="Speed", default=0.5, min=0.0, description="Preview only")
    gravity: FloatProperty(name="Gravity scale", default=0.0, min=0.0, soft_max=1.0,
                           description="Multiplies the Weight field (a guess at its meaning)")
    auto: BoolProperty(name="Auto update", default=False)


def _g(pg, key, default):
    return getattr(pg, key, default) if pg is not None else default


def find_gpu_model(settings):
    """GPU model under the selected node (or the first one in the tree)."""
    rows = [r for r in settings.outline if r.cls == "CPlugParticleGpuModel"]
    sel = settings.selected_path
    pick = next((r for r in rows if r.path.startswith(sel) or sel.startswith(r.path)), None) \
        or (rows[0] if rows else None)
    return bridge.resolve(settings, pick.path) if pick else None


def _coll(scene):
    c = bpy.data.collections.get(NAME)
    if c is None:
        c = bpy.data.collections.new(NAME)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    return c


def _mesh(name, kind, r):
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    me.clear_geometry()
    bm = bmesh.new()
    if kind == "POINT":
        bm.verts.new((0, 0, 0))
    elif kind == "SPHERE":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    elif kind == "BOX":
        bmesh.ops.create_cube(bm, size=r * 2)
    elif kind == "BLOB":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
    bm.to_mesh(me)
    bm.free()
    return me


def _obj(name, mesh, coll):
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, mesh)
        coll.objects.link(ob)
    else:
        ob.data = mesh
    return ob


def clear(scene):
    for n in (NAME + "_Emitter", NAME + "_Blob"):
        ob = bpy.data.objects.get(n)
        if ob:
            bpy.data.objects.remove(ob)
    for n in (NAME,):
        for d in (bpy.data.particles, bpy.data.collections):
            if d.get(n):
                d.remove(d[n])


def sync(scene, s) -> str:
    p = getattr(scene, PREVIEW_ATTR)
    gm = find_gpu_model(s)
    if gm is None:
        return "No GPU model in the tree"
    fps = scene.render.fps / scene.render.fps_base
    coll = _coll(scene)
    emitter = _obj(NAME + "_Emitter", _mesh(NAME + "_Emitter", p.shape, p.radius), coll)
    blob = _obj(NAME + "_Blob", _mesh(NAME + "_Blob", "BLOB", 0.5), coll)
    blob.hide_render = True
    blob.location = (0, 0, -1000)          # parked out of view; only used as instance source
    emitter.display_type = "WIRE"

    ps = bpy.data.particles.get(NAME) or bpy.data.particles.new(NAME)
    seconds = max(1.0, (scene.frame_end - scene.frame_start + 1) / fps)
    life = max(0.01, _g(gm, "LifeMax", 1.0))
    ps.type = "EMITTER"
    ps.frame_start, ps.frame_end = scene.frame_start, scene.frame_end
    ps.count = int(min(100000, max(1, p.rate * seconds)))
    ps.lifetime = max(1.0, life * fps)
    ps.lifetime_random = min(1.0, max(0.0, _g(gm, "LifeVar01", 0.0)))
    ps.emit_from = "VERT" if p.shape == "POINT" else "VOLUME"
    ps.normal_factor = 0.0 if p.shape == "POINT" else p.speed
    ps.object_align_factor = (0.0, 0.0, p.speed if p.shape == "POINT" else 0.0)
    ps.render_type = "OBJECT"
    ps.instance_object = blob
    ps.particle_size = max(0.001, _g(gm, "SizeMax", 0.2))
    ps.size_random = min(1.0, max(0.0, _g(gm, "SizeVar01", 0.0)))
    ps.effector_weights.gravity = min(10.0, max(0.0, _g(gm, "Weight", 0.0) * p.gravity))
    ps.use_advanced_hair = False

    mod = emitter.modifiers.get(NAME) or emitter.modifiers.new(NAME, "PARTICLE_SYSTEM")
    mod.particle_system.settings = ps
    return f"Preview updated ({ps.count} particles, life {life:g}s, size {ps.particle_size:g})"


class TMFX_OT_preview(bpy.types.Operator):
    bl_idname, bl_label = "tm_fx.preview", "Update approximate preview"
    bl_options = {"REGISTER", "UNDO"}
    action: EnumProperty(items=[("SYNC", "Sync", ""), ("CLEAR", "Clear", "")])

    def execute(self, context):
        if self.action == "CLEAR":
            clear(context.scene)
        else:
            s = settings_of(context)
            if s is None or not s.enabled:
                self.report({"ERROR"}, "Active object is not a particle effect node")
                return {"CANCELLED"}
            msg = sync(context.scene, s)
            self.report({"INFO"}, msg)
        return {"FINISHED"}


class TMFX_PT_preview(bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Preview (approximate)", "TMFX_PT_preview", "TMFX_PT_main"
    bl_category, bl_space_type, bl_region_type = "Blendermania", "VIEW_3D", "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        s = settings_of(context)
        return s is not None and s.enabled

    def draw(self, context):
        p = getattr(context.scene, PREVIEW_ATTR)
        col = self.layout.column(align=True)
        col.label(text="Not the game. Rate/speed/shape are preview-only.", icon="INFO")
        for k in ("shape", "radius", "rate", "speed", "gravity"):
            col.prop(p, k)
        row = self.layout.row(align=True)
        row.operator("tm_fx.preview", text="Update", icon="FILE_REFRESH").action = "SYNC"
        row.operator("tm_fx.preview", text="Clear", icon="X").action = "CLEAR"


_CLASSES = (FXPreview, TMFX_OT_preview, TMFX_PT_preview)


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)
    setattr(bpy.types.Scene, PREVIEW_ATTR, PointerProperty(type=FXPreview))


def unregister():
    delattr(bpy.types.Scene, PREVIEW_ATTR)
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
