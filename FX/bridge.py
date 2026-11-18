"""Bridge between Blender PropertyGroups and the pure wire format (codec)."""
import json
import re

import bpy

from . import codec, curves
from . import schema as S
from .props import ROOT_CLASS, get_schema, is_enum_like, on_key, suspend

MISSING = codec.MISSING
_PATH = re.compile(r"\.?([A-Za-z_]\w*)|\[(\d+)\]")


def resolve(settings, path):
    pg = settings
    for name, idx in _PATH.findall(path):
        pg = getattr(pg, name) if name else pg[int(idx)]
    return pg


# ------------------------------------------------------------------ assets
def _asset_name(mat) -> str:
    return mat.name if mat is not None else ""


def find_asset(name: str, asset_type: str):
    """Asset material ``name`` of ``asset_type`` (asset id = material name), or None."""
    mat = bpy.data.materials.get(name) if name else None
    props = getattr(mat, "tm_asset_properties", None)
    if props is None or not props.is_asset or props.asset_type != asset_type:
        return None
    return mat


# ------------------------------------------------------------------ children
# Single node/struct fields are pointers, except ``boxed`` ones (they close a cycle, see
# schema._mark_boxed), which are collections holding 0..1 items.
def has_child(pg, f) -> bool:
    """Single child present (nodes: switched on; structs: always, boxed: when its item exists)."""
    if f.boxed:
        return len(getattr(pg, f.key)) > 0
    return f.type == "struct" or bool(getattr(pg, on_key(f)))


def set_child(pg, f, on: bool):
    if f.boxed:
        coll = getattr(pg, f.key)
        if on and not len(coll):
            coll.add()
        elif not on:
            coll.clear()
    elif f.type == "node":
        setattr(pg, on_key(f), on)


def child_pg(pg, f):
    """PropertyGroup of a present single child, or None."""
    if not has_child(pg, f):
        return None
    v = getattr(pg, f.key)
    return v[0] if f.boxed else v


# ------------------------------------------------------------------ values
def get_value(pg, f):
    """Current value in wire form (scalars/curves) or a child marker for lookups."""
    if f.type == "node" and not f.is_list:
        return True if has_child(pg, f) else None
    if f.type in ("struct", "node", "opaque"):
        raise KeyError(f.key)
    if f.asset_type:
        return _asset_name(getattr(pg, f.key))
    if f.type == "curve":
        return read_curve(getattr(pg, f.key))
    if f.is_list:
        return [S.from_blender_int(f, i.v) if f.type == "int" else i.v for i in getattr(pg, f.key)]
    v = getattr(pg, f.key)
    if is_enum_like(f):
        return int(v)
    if f.type == "int":
        return S.from_blender_int(f, v)
    if f.type in ("vec", "iso4", "box"):
        return list(v)
    return v


def make_lookup(pg, cs):
    fields = {f.key: f for f in cs.fields}
    return lambda key: get_value(pg, fields[key])


def read_curve(c):
    flags = int(c.interp) | (0x20 if c.tangent_max_x else 0) | c.flags_other
    return {"flags": flags, "points": curves.read_points(c)}


def write_curve(c, v):
    v = v or {}
    flags = int(v.get("flags", 0))
    bit = 1 if flags & 1 else (0x10 if flags & 0x10 else (2 if flags & 2 else 0))
    c.interp = str(bit)
    c.tangent_max_x = bool(flags & 0x20)
    c.flags_other = flags & ~(bit | 0x20) & 0xFFFF
    pts = v.get("points", [])
    if pts:
        curves.write_points(c, pts)
    else:
        curves.clear(c)


# -------------------------------------------------------------- read (PG -> wire)
def _read_values(pg, cs, asset_ref):
    """Only visible fields are read: hidden children are never written and inline structs
    can be recursive (``EffectNode.Child``), so descending into hidden ones would not end."""
    out = {}
    lookup = make_lookup(pg, cs)
    for f in cs.fields:
        if f.type == "opaque" or not S.is_visible(f, lookup):
            continue
        if f.type == "node":
            if f.is_list:
                out[f.key] = [read_node(c, f.ref, asset_ref) for c in getattr(pg, f.key)]
            else:
                c = child_pg(pg, f)
                out[f.key] = read_node(c, f.ref, asset_ref) if c is not None else None
        elif f.type == "struct":
            if f.is_list:
                out[f.key] = [read_struct(c, f.ref, asset_ref) for c in getattr(pg, f.key)]
            else:   # absent boxed struct -> None -> codec writes the schema default
                c = child_pg(pg, f)
                out[f.key] = read_struct(c, f.ref, asset_ref) if c is not None else None
        elif f.asset_type and asset_ref is not None:
            mat = getattr(pg, f.key)
            out[f.key] = (asset_ref(mat) or "") if mat is not None else ""
        else:
            out[f.key] = get_value(pg, f)
    return out


def _extra(pg):
    return json.loads(pg.extra_json) if pg.extra_json else None


def read_node(pg, cname, asset_ref=None):
    """``asset_ref(material) -> asset id`` maps asset refs (default: the material name)."""
    cs = get_schema()[cname]
    enabled = {m.id for m in cs.modules if getattr(pg, m.en_key)}
    return codec.node_to_wire(get_schema(), cname, _read_values(pg, cs, asset_ref), enabled, _extra(pg))


def read_struct(pg, qname, asset_ref=None):
    cs = get_schema()[qname]
    return codec.struct_to_wire(get_schema(), qname, _read_values(pg, cs, asset_ref), _extra(pg))


def used_assets(pg, cname) -> list:
    """Asset materials referenced by the visible fields of a node/struct tree."""
    found = []
    _read_values(pg, get_schema()[cname], lambda mat: found.append(mat) or mat.name)
    return found


# ------------------------------------------------------------- write (wire -> PG)
def set_value(pg, f, v, warnings=None):
    if f.asset_type:
        mat = find_asset(v, f.asset_type)
        if v and mat is None and warnings is not None:
            warnings.append(f"{f.key}: no {f.asset_type.lower()} asset named '{v}', left empty")
        setattr(pg, f.key, mat)
    elif f.type == "curve":
        write_curve(getattr(pg, f.key), v)
    elif f.is_list:
        coll = getattr(pg, f.key)
        coll.clear()
        for x in v:
            coll.add().v = S.to_blender_int(f, x) if f.type == "int" else x
    elif is_enum_like(f):
        if str(int(v)) not in [str(c[0]) for c in f.choices]:
            if warnings is not None:
                warnings.append(f"{f.key}: value {v} not in known choices, left unchanged")
            return
        setattr(pg, f.key, str(int(v)))
    elif f.type in ("vec", "iso4", "box"):
        setattr(pg, f.key, tuple(v))
    elif f.type == "int":
        setattr(pg, f.key, S.to_blender_int(f, v))
    else:
        setattr(pg, f.key, v)


def _write_fields(pg, cs, values, warnings):
    schema = get_schema()
    lookup = codec._lookup_from(values)
    for f in cs.fields:
        v = values.get(f.key, MISSING)
        if f.type == "opaque":
            continue
        if f.type == "node":
            if f.is_list:
                coll = getattr(pg, f.key)
                coll.clear()
                for w in ([] if v is MISSING else v):
                    write_node(coll.add(), f.ref, w, warnings)
            else:
                on = v not in (MISSING, None)
                set_child(pg, f, on)
                if on:
                    write_node(child_pg(pg, f), f.ref, v, warnings)
        elif f.type == "struct":
            if f.is_list:
                coll = getattr(pg, f.key)
                coll.clear()
                for w in ([] if v is MISSING else v):
                    write_struct(coll.add(), f.ref, w, warnings)
            elif v not in (MISSING, None):
                set_child(pg, f, True)
                write_struct(child_pg(pg, f), f.ref, v, warnings)
            elif f.boxed:
                set_child(pg, f, False)         # absent: written as schema default
            elif S.is_visible(f, lookup):       # hidden structs are left alone
                write_struct(getattr(pg, f.key), f.ref, codec.default_struct(schema, f.ref), warnings)
        else:
            set_value(pg, f, S.field_default(f) if v is MISSING else v, warnings)


def write_node(pg, cname, wire, warnings):
    schema = get_schema()
    values, enabled, extra = codec.node_from_wire(schema, cname, wire, warnings)
    cs = schema[cname]
    with suspend():
        for m in cs.modules:
            setattr(pg, m.en_key, m.id in enabled)
        _write_fields(pg, cs, values, warnings)
        pg.extra_json = json.dumps(extra) if extra else ""


def write_struct(pg, qname, wire, warnings):
    schema = get_schema()
    values, extra = codec.struct_from_wire(schema, qname, wire, warnings)
    with suspend():
        _write_fields(pg, schema[qname], values, warnings)
        pg.extra_json = json.dumps(extra) if extra else ""


# ---------------------------------------------------------------- template diff
_tpl = {"src": None, "flat": {}}


def template_flat(settings) -> dict:
    src = settings.template_json
    if src != _tpl["src"]:
        _tpl["src"] = src
        _tpl["flat"] = codec.flatten(get_schema(), ROOT_CLASS, json.loads(src), "vfx") if src else {}
    return _tpl["flat"]


def baseline(settings, path, f):
    flat = template_flat(settings)
    v = flat.get(f"{path}.{f.key}", MISSING)
    return S.field_default(f) if v is MISSING else v


def is_changed(settings, path, pg, f) -> bool:
    if f.type in ("node", "struct", "opaque"):
        return False
    try:
        return not codec.values_equal(get_value(pg, f), baseline(settings, path, f))
    except Exception:
        return False


# ---------------------------------------------------------------------- outline
def row_title(pg, cs, label: str = "") -> str:
    parts = [label or cs.title]
    for k in cs.title_fields:
        f = cs.field(k)
        if f is None or f.type in ("node", "struct", "opaque", "curve") or f.is_list:
            continue
        try:
            v = get_value(pg, f)
        except Exception:
            continue
        if f.choices:
            v = dict(f.choices).get(v, v)
        if v not in ("", None):
            parts.append(str(v))
    return " · ".join(parts)


def rebuild_outline(settings):
    schema = get_schema()
    keep = settings.selected_path
    with suspend():
        settings.outline.clear()

        def visit(pg, cname, path, depth, label=""):
            row = settings.outline.add()
            row.path, row.cls, row.depth, row.label = path, cname, depth, label
            cs = schema[cname]
            lookup = make_lookup(pg, cs)
            for m in cs.modules:
                if cs.kind == "node" and not getattr(pg, m.en_key):
                    continue
                for f in m.fields:
                    if not f.is_child or not S.is_visible(f, lookup):
                        continue
                    if f.is_list:
                        for i, c in enumerate(getattr(pg, f.key)):
                            visit(c, f.ref, f"{path}.{f.key}[{i}]", depth + 1)
                    elif has_child(pg, f):
                        visit(child_pg(pg, f), f.ref, S.child_path(path, f), depth + 1,
                              f.label if f.is_known else "")
        visit(settings.vfx, ROOT_CLASS, "vfx", 0)
        paths = [r.path for r in settings.outline]
        settings.outline_index = paths.index(keep) if keep in paths else 0
        if settings.outline:
            settings.selected_path = settings.outline[settings.outline_index].path


# -------------------------------------------------------------------- public API
def export_document(settings, asset_ref=None):
    """Wire document (``{"format", "vfx"}``) for ``ItemConfig.ParticleFx[].Fx``."""
    return codec.document(get_schema(), read_node(settings.vfx, ROOT_CLASS, asset_ref))


def import_document(settings, data: dict, as_template=False) -> list:
    root = data.get("vfx", data)
    warnings: list = []
    if root.get("$class") not in (None, ROOT_CLASS):
        return [f"root is {root.get('$class')}, expected {ROOT_CLASS}: nothing imported"]
    write_node(settings.vfx, ROOT_CLASS, root, warnings)
    settings.schema_id = get_schema().schema_id
    settings.template_json = json.dumps(root) if as_template else ""
    rebuild_outline(settings)
    return warnings


def init_document(settings) -> None:
    """Give a fresh node a group root effect node (nothing else, values come from the schema)."""
    if settings.schema_id:
        return
    write_node(settings.vfx, ROOT_CLASS, codec.root_wire(get_schema()), [])
    settings.schema_id = get_schema().schema_id
    settings.selected_path = "vfx"
    rebuild_outline(settings)
