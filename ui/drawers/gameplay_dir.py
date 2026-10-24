import bpy
import math
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix

from ...properties.PropertyIdentifiers import ObjectProp
from ...utils.materialLib import has_material_with_gameplay_effect

_draw_handle = None
_drag_start = {}  # (object name, axis) -> tip offset when the drag started
_AXES = (
    (Vector((1, 0, 0)), (1.0, 0.2, 0.32), Matrix.Rotation(math.pi / 2, 4, 'Y')),
    (Vector((0, 1, 0)), (0.55, 0.86, 0.0), Matrix.Rotation(-math.pi / 2, 4, 'X')),
    (Vector((0, 0, 1)), (0.16, 0.55, 1.0), Matrix.Identity(4)),
)
_COLOR = (1.0, 0.55, 0.1, 1.0)


def _has_gameplay_dir(obj) -> bool:
    if obj is None or obj.type != 'MESH':
        return False
    if getattr(obj, ObjectProp.IGNORE, False):
        return False
    return bool(getattr(obj, ObjectProp.TRIGGER_EFFECT, False)) or bool(has_material_with_gameplay_effect(obj))


def _eligible_objects(context):
    return [o for o in context.selected_objects if _has_gameplay_dir(o)]


def _arrow_length(obj) -> float:
    return max(1.0, max(obj.dimensions) * 0.75)


def _world_tip_offset(obj) -> Vector:
    """Absolute direction (not affected by object rotation) scaled to arrow length."""
    d = Vector(getattr(obj, ObjectProp.GAMEPLAY_MAIN_DIR))
    if d.length < 1e-6:
        d = Vector((0.0, -1.0, 0.0))
    d.normalize()
    return d * _arrow_length(obj)


def _draw_arrows():
    context = bpy.context
    objs = _eligible_objects(context)
    if not objs:
        return

    lines = []
    heads = []
    for obj in objs:
        start = obj.matrix_world.translation.copy()
        offset = _world_tip_offset(obj)
        tip = start + offset
        lines += [start, tip]

        # arrow head
        direction = offset.normalized()
        side = direction.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = direction.cross(Vector((1, 0, 0)))
        side.normalize()
        size = offset.length * 0.15
        back = tip - direction * size
        heads += [tip, back + side * size * 0.5, tip, back - side * size * 0.5]

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.line_width_set(3.0)
    gpu.state.depth_test_set('NONE')
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", _COLOR)
    batch_for_shader(shader, 'LINES', {"pos": lines + heads}).draw(shader)
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def _redraw_ui():
    """Python-side property writes don't redraw the sidebar/properties editor by themselves."""
    wm = bpy.context.window_manager
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES'}:
                area.tag_redraw()


def _push_undo():
    try:
        bpy.ops.ed.undo_push(message="Edit Gameplay Direction")
    except RuntimeError:
        pass
    return None


class TM_GGT_GameplayMainDir(bpy.types.GizmoGroup):
    bl_idname = "TM_GGT_GameplayMainDir"
    bl_label = "Gameplay Main Direction"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def setup(self, context):
        self._names = []
        self._was_modal = False

    def refresh(self, context):
        objs = _eligible_objects(context)
        names = [(o.name, i) for o in objs for i in range(len(_AXES))]
        # Never rebuild while unchanged: clearing gizmos during an active drag
        # (property write -> depsgraph -> refresh) crashes Blender.
        if names == self._names and len(self.gizmos) == len(names):
            return

        self.gizmos.clear()
        self._names = []
        for obj in objs:
            name = obj.name
            for axis_index, (axis, color, _rot) in enumerate(_AXES):
                gz = self.gizmos.new("GIZMO_GT_arrow_3d")
                gz.draw_style = 'NORMAL'
                gz.length = 0.5
                gz.scale_basis = 0.5
                gz.use_draw_modal = True
                gz.color = color
                gz.alpha = 0.6
                gz.color_highlight = color
                gz.alpha_highlight = 1.0

                def get_fn():
                    return 0.0

                def set_fn(value, name=name, axis_index=axis_index):
                    o = bpy.data.objects.get(name)
                    start = _drag_start.get((name, axis_index))
                    if o is None or start is None:
                        return
                    v = start + _AXES[axis_index][0] * value
                    if v.length < 1e-6:
                        return
                    v.normalize()
                    setattr(o, ObjectProp.GAMEPLAY_MAIN_DIR, tuple(v))
                    _redraw_ui()

                gz.target_set_handler("offset", get=get_fn, set=set_fn)
                self._names.append((name, axis_index))

    def draw_prepare(self, context):
        any_modal = False
        for gz, (name, kind) in zip(self.gizmos, self._names):
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            # keep the gizmo fixed while it is dragged (the drag delta is relative to its start)
            if gz.is_modal:
                any_modal = True
                continue
            tip = _world_tip_offset(obj)
            _drag_start[(name, kind)] = tip.copy()
            axis_rot = _AXES[kind][2]
            gz.matrix_basis = Matrix.Translation(obj.matrix_world.translation + tip) @ axis_rot

        # drag finished -> register one undo step (cannot call operators from draw directly)
        if self._was_modal and not any_modal:
            bpy.app.timers.register(_push_undo, first_interval=0.0)
        self._was_modal = any_modal


def register_gameplay_dir():
    global _draw_handle
    bpy.utils.register_class(TM_GGT_GameplayMainDir)
    if _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_arrows, (), 'WINDOW', 'POST_VIEW')


def unregister_gameplay_dir():
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
    bpy.utils.unregister_class(TM_GGT_GameplayMainDir)
