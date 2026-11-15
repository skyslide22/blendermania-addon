"""Real Blender curve widgets for FX curves.

Blender cannot create a ``CurveMapping`` property directly, so every FX curve
that is edited as a widget owns one *Float Curve* node inside a hidden node
group (``TMFX_CurveStore``, fake user).  The node is the source of truth while
it exists; ``FXCurve.points`` is only a mirror / fallback.  All functions that
create or modify datablocks must be called from operators or update
callbacks, never from ``draw()``.
"""
import uuid

import bpy

STORE = "TMFX_CurveStore"

# FXCurve.interp -> CurveMapPoint.handle_type.  Step has no native widget equivalent:
# it is kept in the flag bits and drawn like linear.
_HANDLE = {"0": "VECTOR", "1": "VECTOR", "2": "AUTO", "16": "AUTO"}


def _tree(create=False):
    tree = bpy.data.node_groups.get(STORE)
    if tree is None and create:
        tree = bpy.data.node_groups.new(STORE, "ShaderNodeTree")
        tree.use_fake_user = True
    return tree


def get_node(c):
    tree = _tree()
    return tree.nodes.get(c.uid) if (tree and c.uid) else None


def has_node(c):
    return get_node(c) is not None


def read_points(c):
    n = get_node(c)
    if n is not None:
        return [[float(p.location[0]), float(p.location[1])] for p in n.mapping.curves[0].points]
    return [[p.t, p.v] for p in c.points]


def _fit_range(c, pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    c.x_max = max(1.0, max(xs))
    c.y_min = min(0.0, min(ys))
    c.y_max = max(1.0, max(ys))


def apply_range(c):
    n = get_node(c)
    if n is None:
        return
    m = n.mapping
    m.use_clip = True
    m.clip_min_x, m.clip_max_x = 0.0, max(c.x_max, 0.001)
    lo, hi = c.y_min, c.y_max
    if hi <= lo:
        hi = lo + 1.0
    m.clip_min_y, m.clip_max_y = lo, hi
    m.update()


def apply_interp(c):
    n = get_node(c)
    if n is None:
        return
    for p in n.mapping.curves[0].points:
        p.handle_type = _HANDLE.get(c.interp, "AUTO")
    n.mapping.update()


def _set_points(c, node, pts):
    pts = sorted(([float(t), float(v)] for t, v in pts), key=lambda p: p[0])
    if len(pts) < 2:
        pts = pts + [[pts[0][0] + 1.0, pts[0][1]]]
    cur = node.mapping.curves[0]
    apply_range(c)
    while len(cur.points) > 2:
        cur.points.remove(cur.points[-1])
    cur.points[0].location = pts[0]
    cur.points[1].location = pts[-1]
    for t, v in pts[1:-1]:
        cur.points.new(t, v)
    node.mapping.update()
    apply_interp(c)


def write_points(c, pts):
    """Make the widget (and the mirror) hold ``pts``; empty list removes the widget."""
    if not pts:
        clear(c)
        return
    node = get_node(c)
    if node is None:
        tree = _tree(create=True)
        c.uid = uuid.uuid4().hex[:12]
        node = tree.nodes.new("ShaderNodeFloatCurve")
        node.name = c.uid
    _fit_range(c, pts)
    _set_points(c, node, pts)
    c.points.clear()
    for t, v in read_points(c):
        p = c.points.add()
        p.t, p.v = t, v


def create(c):
    """Widget from the mirrored keys, or a default 0..1 ramp."""
    pts = [[p.t, p.v] for p in c.points] or [[0.0, 0.0], [1.0, 1.0]]
    write_points(c, pts)


def clear(c):
    n = get_node(c)
    if n is not None:
        _tree().nodes.remove(n)
    c.uid = ""
    c.points.clear()
