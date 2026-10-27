import math
import bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


def _orient(a, b, c):
    """Twice the signed area of triangle abc (points are (x, y) tuples)."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _tri_overlap(t1, t2, eps):
    """True only if the triangles overlap with positive area.
    Touching (shared edge or vertex) is NOT an overlap.
    eps: overlap depth in UV units that is still ignored."""
    for tri in (t1, t2):
        for i in range(3):
            x1, y1 = tri[i]
            x2, y2 = tri[(i + 1) % 3]
            nx, ny = y1 - y2, x2 - x1
            ln = math.hypot(nx, ny)
            if ln == 0:
                continue
            nx, ny = nx / ln, ny / ln
            a = [nx * x + ny * y for x, y in t1]
            b = [nx * x + ny * y for x, y in t2]
            if max(a) <= min(b) + eps or max(b) <= min(a) + eps:
                return False          # separating axis found
    return True


def _read_face_uvs(obj, layer_name):
    """Returns [(face_index, [(u, v), ...]), ...] or None if there is no UV layer.
    Works in edit mode (bmesh) and object mode (mesh data)."""
    me = obj.data

    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(me)             # live edit data, do NOT free
        layers = bm.loops.layers.uv
        uv = layers.get(layer_name) if layer_name else layers.active
        if uv is None:
            return None
        bm.faces.index_update()
        return [(f.index, [tuple(l[uv].uv) for l in f.loops]) for f in bm.faces]

    uv = me.uv_layers.get(layer_name) if layer_name else me.uv_layers.active
    if uv is None or len(uv.data) == 0:
        return None
    return [(p.index, [tuple(uv.data[i].uv) for i in p.loop_indices])
            for p in me.polygons]


def find_uv_overlaps(objects, layer_name=None, min_area=1e-10, eps=1e-6):
    """Returns (pairs, skipped).
    pairs:   set of ((obj_name, face_idx), (obj_name, face_idx)), sorted tuples
    skipped: names of objects without usable UVs
    layer_name: UV layer to check (None = active layer)
    min_area:   triangles smaller than this are ignored (degenerate)
    eps:        overlap depth in UV units that is ignored.
                For lightmaps ~0.25 / texture_size is a sensible value."""
    faces = []
    skipped = []

    # --- collect faces ------------------------------------------------------
    for obj in objects:
        if obj.type != 'MESH':
            continue

        data = _read_face_uvs(obj, layer_name)
        if data is None:
            skipped.append(obj.name)
            continue

        found = False
        for face_idx, coords in data:
            if len(coords) < 3:
                continue

            pts = [Vector((u, v, 0.0)) for u, v in coords]
            tris = []
            for tri in tessellate_polygon([pts]):
                t = tuple((pts[i].x, pts[i].y) for i in tri)
                if abs(_orient(*t)) * 0.5 > min_area:      # skip degenerate triangles
                    tris.append(t)
            if not tris:
                continue

            us = [c[0] for c in coords]
            vs = [c[1] for c in coords]
            faces.append({
                "owner": (obj.name, face_idx),
                "tris": tris,
                "bounds": (min(us), min(vs), max(us), max(vs)),
            })
            found = True

        if not found:
            skipped.append(obj.name)

    # --- sweep along U, test only faces whose bounds overlap ----------------
    faces.sort(key=lambda f: f["bounds"][0])
    pairs = set()
    active = []

    for face in faces:
        x0, y0, x1, y1 = face["bounds"]
        active = [f for f in active if f["bounds"][2] > x0 + eps]

        for other in active:
            ox0, oy0, ox1, oy1 = other["bounds"]
            if oy1 <= y0 + eps or y1 <= oy0 + eps:
                continue

            hit = any(
                _tri_overlap(t1, t2, eps)
                for t1 in face["tris"]
                for t2 in other["tris"]
            )
            if hit:
                pairs.add(tuple(sorted((face["owner"], other["owner"]))))

        active.append(face)

    return pairs, skipped
