"""Bridge between Blender PropertyGroups and the pure wire format (codec)."""
import json
import re

from . import codec, curves
from . import schema as S
from .props import (ROOT_CLASS, class_name_of, get_schema, is_enum_like, on_key, suspend)

MISSING = codec.MISSING
_PATH = re.compile(r"\.?([A-Za-z_]\w*)|\[(\d+)\]")


def resolve(settings, path):
    pg = settings
    for name, idx in _PATH.findall(path):
        pg = getattr(pg, name) if name else pg[int(idx)]
    return pg


# ------------------------------------------------------------------ values
def get_value(pg, f):
    """Current value in wire form (scalars/curves) or a child marker for lookups."""
    if f.type == "node" and not f.is_list:
        return True if getattr(pg, on_key(f)) else None
    if f.type in ("struct", "node", "opaque"):
        raise KeyError(f.key)
    if f.type == "curve":
        return read_curve(getattr(pg, f.key))
    if f.is_list:
        return [i.v for i in getattr(pg, f.key)]
    v = getattr(pg, f.key)
    if is_enum_like(f):
        return int(v)
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
def _read_values(pg, cs):
    out = {}
    for f in cs.fields:
        if f.type == "opaque":
            continue
        if f.type == "node":
            if f.is_list:
                out[f.key] = [read_node(c, f.ref) for c in getattr(pg, f.key)]
            else:
                out[f.key] = read_node(getattr(pg, f.key), f.ref) if getattr(pg, on_key(f)) else None
        elif f.type == "struct":
            kids = getattr(pg, f.key)
            out[f.key] = [read_struct(c, f.ref) for c in kids] if f.is_list else read_struct(kids, f.ref)
        else:
            out[f.key] = get_value(pg, f)
    return out


def _extra(pg):
    return json.loads(pg.extra_json) if pg.extra_json else None


def read_node(pg, cname):
    cs = get_schema()[cname]
    enabled = {m.id for m in cs.modules if getattr(pg, m.en_key)}
    return codec.node_to_wire(get_schema(), cname, _read_values(pg, cs), enabled, _extra(pg))


def read_struct(pg, qname):
    cs = get_schema()[qname]
    return codec.struct_to_wire(get_schema(), qname, _read_values(pg, cs), _extra(pg))


# ------------------------------------------------------------- write (wire -> PG)
def set_value(pg, f, v, warnings=None):
    if f.type == "curve":
        write_curve(getattr(pg, f.key), v)
    elif f.is_list:
        coll = getattr(pg, f.key)
        coll.clear()
        for x in v:
            coll.add().v = x
    elif is_enum_like(f):
        if str(int(v)) not in [str(c[0]) for c in f.choices]:
            if warnings is not None:
                warnings.append(f"{f.key}: value {v} not in known choices, left unchanged")
            return
        setattr(pg, f.key, str(int(v)))
    elif f.type in ("vec", "iso4", "box"):
        setattr(pg, f.key, tuple(v))
    else:
        setattr(pg, f.key, v)


def _write_fields(pg, cs, values, warnings):
    schema = get_schema()
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
                setattr(pg, on_key(f), on)
                if on:
                    write_node(getattr(pg, f.key), f.ref, v, warnings)
        elif f.type == "struct":
            if f.is_list:
                coll = getattr(pg, f.key)
                coll.clear()
                for w in ([] if v is MISSING else v):
                    write_struct(coll.add(), f.ref, w, warnings)
            else:
                write_struct(getattr(pg, f.key), f.ref,
                             codec.default_struct(schema, f.ref) if v is MISSING else v, warnings)
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
    return " \u00b7 ".join(parts)


def rebuild_outline(settings):
    schema = get_schema()
    keep = settings.selected_path
    with suspend():
        settings.outline.clear()
        if settings.enabled:
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
                        elif getattr(pg, on_key(f)):
                            named = getattr(f, "name", None) or f.status != "unknown"
                            visit(getattr(pg, f.key), f.ref, f"{path}.{f.key}", depth + 1,
                                  f.label if named else "")
            visit(settings.vfx, ROOT_CLASS, "vfx", 0)
        paths = [r.path for r in settings.outline]
        settings.outline_index = paths.index(keep) if keep in paths else 0
        if settings.outline:
            settings.selected_path = settings.outline[settings.outline_index].path


# -------------------------------------------------------------------- public API
def export_document(settings):
    """Wire document for the item JSON, or None when FX export is disabled."""
    if not settings.enabled:
        return None
    return codec.document(get_schema(), read_node(settings.vfx, ROOT_CLASS))


def import_document(settings, data: dict, as_template=False) -> list:
    root = data.get("vfx", data)
    warnings: list = []
    write_node(settings.vfx, ROOT_CLASS, root, warnings)
    settings.enabled = True
    settings.schema_id = get_schema().schema_id
    if as_template:
        settings.template_json = json.dumps(root)
    rebuild_outline(settings)
    return warnings
