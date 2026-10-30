import math
import time

import bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

# How often the generator hands control back to Blender (seconds of work between yields).
# Small enough that the UI can redraw, large enough that yield overhead is negligible.
_YIELD_EVERY = 0.02


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


def find_uv_overlaps_steps(objects, layer_name=None, min_area=1e-10, eps=1e-6):
    """Generator version of find_uv_overlaps.

    Yields (fraction 0..1, text) regularly so the caller can redraw the UI.
    RETURNS (pairs, skipped), read it from StopIteration.value or use `yield from`.

    pairs:   set of ((obj_name, face_idx), (obj_name, face_idx)), sorted tuples
    skipped: names of objects without usable UVs
    layer_name: UV layer to check (None = active layer)
    min_area:   triangles smaller than this are ignored (degenerate)
    eps:        overlap depth in UV units that is ignored.
                For lightmaps ~0.25 / texture_size is a sensible value.
    """
    faces = []
    skipped = []
    meshes = [o for o in objects if o.type == 'MESH']
    n_objs = max(len(meshes), 1)
    last = time.perf_counter()

    # --- phase 1 (0% - 50%): collect faces ----------------------------------
    for oi, obj in enumerate(meshes):
        # always report at the start of an object, BEFORE its blocking UV read
        yield 0.5 * oi / n_objs, f"Reading UVs: {obj.name}"
        last = time.perf_counter()

        data = _read_face_uvs(obj, layer_name)
        if data is None:
            skipped.append(obj.name)
            continue

        found = False
        n_faces = max(len(data), 1)
        for fi, (face_idx, coords) in enumerate(data):
            # time check FIRST in the loop body, so the `continue`s below can't skip it
            now = time.perf_counter()
            if now - last > _YIELD_EVERY:
                last = now
                yield 0.5 * (oi + fi / n_faces) / n_objs, f"Reading UVs: {obj.name}"

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

    # --- phase 2 (50% - 100%): sweep along U, test only faces whose bounds overlap
    faces.sort(key=lambda f: f["bounds"][0])
    total = max(len(faces), 1)
    pairs = set()
    active = []
    last = time.perf_counter()

    for i, face in enumerate(faces):
        now = time.perf_counter()
        if now - last > _YIELD_EVERY:
            last = now
            yield 0.5 + 0.5 * i / total, f"Comparing faces {i}/{len(faces)}"

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

    yield 1.0, "Done"
    return pairs, skipped


def find_uv_overlaps(objects, layer_name=None, min_area=1e-10, eps=1e-6):
    """Blocking version with the original signature: returns (pairs, skipped)."""
    gen = find_uv_overlaps_steps(objects, layer_name, min_area, eps)
    while True:
        try:
            next(gen)
        except StopIteration as stop:
            return stop.value