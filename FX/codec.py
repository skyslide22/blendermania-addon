"""The FX wire format and the pure-Python rules around it (no ``bpy``).

The root is a ``CPlugFxSystem`` (what item prefab ents reference, see Nadeo's
*.FxSys.Gbx).  The document ``{"format": "tm-fx/1", "vfx": <root>}`` is embedded in the
item config (``ItemConfig.ParticleFx[].Fx``) and converted by TM_GenericMapping's
``ParticleFxConverter``.

A *node* (a GBX class instance, e.g. ``CPlugParticleGpuModel``) is exported as::

    {
      "$class": "CPlugParticleGpuModel",
      "props":  { "LifeMax": 1.0, "SizeVar01": 0.4 },          # named node members
      "chunks": { "0x090C6000": { "Version": 6, "U01": 1.0 } }, # one entry per chunk that exists;
                                                                # anonymous members + chunk version
      "extra":  { ... }                                         # optional, unknown data passed through
    }

A *struct* (an inline GBX archive, e.g. a ``CPlugFxSystem.EffectNode``) is::

    { "$struct": "CPlugFxSystem.EffectNode", "props": { "Type": 4, "Name": "fog", "Emitter": {...} } }

Child nodes/structs are nested in place of the member value; a null node reference
is ``null``; lists are JSON arrays.  Member names are the real GBX.NET C# member
names, so a converter can apply them by reflection:

    named members       ->  node.<Name>
    anonymous members   ->  node.GetChunk<Chunk….>().<Unn>     (chunk id given in ``chunks``)
    archive members     ->  archive.<Name or Unn>

Value encodings: int/float/bool/string as JSON; enums as their integer value;
vectors as arrays; ``blob`` as lower-case hex; ``ref`` as a string (``""`` for none):
an asset id (``ItemConfig.Assets[].Id``) for asset refs (``Field.asset_type``), else a .Gbx path; ``curve`` as ``{"version":3,"flags":int,"points":[[t,v],...]}``.
"""
from __future__ import annotations

import copy
import math
import re
from typing import Any, Optional

from . import expr
from .schema import (ClassSchema, Field, Schema, child_path, field_default, int_range, is_visible,
                     type_default)

FORMAT = "tm-fx/1"
ROOT_CLASS = "CPlugFxSystem"
MISSING = object()
CURVE_VERSION = 3


# ------------------------------------------------------------------ value coding
def normalize_scalar(f: Field, v):
    """Coerce a value to the canonical wire type for field ``f`` (element, not list)."""
    t = f.type
    if t == "float":
        return float(v)
    if t == "int":
        lo, hi = int_range(f)
        return max(lo, min(hi, int(v)))
    if t == "bool":
        return bool(v)
    if t in ("string", "ref"):
        return "" if v is None else str(v)
    if t == "enum":
        return int(v)
    if t == "vec":
        cast = int if f.kind == "int" else float
        out = [cast(x) for x in v]
        if len(out) != f.size:
            raise ValueError(f"{f.key}: expected {f.size} components, got {len(out)}")
        return out
    if t == "iso4":
        out = [float(x) for x in v]
        if len(out) != 12:
            raise ValueError(f"{f.key}: iso4 needs 12 floats")
        return out
    if t == "box":
        out = [float(x) for x in v]
        if len(out) != 6:
            raise ValueError(f"{f.key}: box needs 6 floats")
        return out
    if t == "blob":
        s = re.sub(r"\s+", "", str(v or "")).lower()
        if s and (len(s) % 2 or re.search(r"[^0-9a-f]", s)):
            raise ValueError(f"{f.key}: blob must be an even number of hex digits")
        if f.length is not None and len(s) != f.length * 2:
            raise ValueError(f"{f.key}: blob must be exactly {f.length} bytes")
        return s
    if t == "curve":
        return normalize_curve(v)
    return v


def normalize_curve(v) -> dict:
    v = v or {}
    pts = [[float(a), float(b)] for a, b in v.get("points", [])]
    return {"version": CURVE_VERSION, "flags": int(v.get("flags", 0)), "points": pts}


# ---------------------------------------------------------------------- defaults
def default_values(schema: Schema, cs: ClassSchema) -> dict:
    """key -> default value for every field of a class/struct.

    Single inline structs are ``None`` here and built lazily when they are written
    (they can be recursive, e.g. ``EffectNode.Child``); node references are null and
    lists are empty until something is added.
    """
    out = {}
    for f in cs.fields:
        out[f.key] = None if (f.type == "struct" and not f.is_list) else copy.deepcopy(field_default(f))
    return out


def default_node(schema: Schema, cname: str) -> dict:
    cs = schema[cname]
    return node_to_wire(schema, cname, default_values(schema, cs),
                        {m.id for m in cs.modules if m.default_enabled})


def default_struct(schema: Schema, qname: str) -> dict:
    cs = schema[qname]
    return struct_to_wire(schema, qname, default_values(schema, cs))


# ------------------------------------------------------------------ to the wire
def _elem_to_wire(f: Field, v):
    if f.type in ("node", "struct"):
        return v
    if f.type == "opaque":
        return None
    return normalize_scalar(f, v)


def _field_to_wire(schema: Schema, f: Field, v):
    if f.type == "opaque":
        return None
    if f.type in ("node", "struct"):
        if f.is_list:
            return list(v or [])
        if f.type == "struct" and v is None:      # inline structs are not nullable
            return default_struct(schema, f.ref)
        return v
    if f.is_list:
        return [normalize_scalar(f, x) for x in (v or [])]
    if f.is_fixed and f.type in ("int", "float", "bool"):
        return [normalize_scalar(f, x) for x in v]
    return normalize_scalar(f, v)


def _lookup_from(values: dict):
    def lookup(key):
        v = values.get(key, MISSING)
        if v is MISSING:
            raise KeyError(key)
        return v
    return lookup


def node_to_wire(schema: Schema, cname: str, values: dict, enabled, extra: Optional[dict] = None) -> dict:
    """Build the wire dict of a node from ``key -> value`` (children already wire dicts)."""
    cs = schema[cname]
    lookup = _lookup_from(values)
    props: dict = {}
    chunks: dict = {}
    for m in cs.modules:
        if m.id not in enabled:
            continue
        ch: dict = {}
        if m.version is not None:
            ch["Version"] = m.version
        for f in m.fields:
            if f.type == "opaque" or not is_visible(f, lookup):
                continue
            v = _field_to_wire(schema, f, values.get(f.key, field_default(f)))
            if f.scope == "node":
                props.setdefault(f.member, v)
            else:
                ch[f.member] = v
        chunks[m.id] = ch
    out = {"$class": cname, "props": props, "chunks": chunks}
    if extra:
        out["extra"] = extra
    return out


def struct_to_wire(schema: Schema, qname: str, values: dict, extra: Optional[dict] = None) -> dict:
    cs = schema[qname]
    lookup = _lookup_from(values)
    props = {}
    for f in cs.fields:
        if f.type == "opaque" or not is_visible(f, lookup):
            continue
        props[f.member] = _field_to_wire(schema, f, values.get(f.key, field_default(f)))
    out = {"$struct": qname, "props": props}
    if extra:
        out["extra"] = extra
    return out


# ---------------------------------------------------------------- from the wire
def _decode_field(f: Field, v, warnings, where):
    """Wire value -> value usable to fill a property (children stay wire dicts)."""
    if f.type == "opaque":
        return MISSING
    if f.type in ("node", "struct"):
        return v
    try:
        if f.is_list:
            return [normalize_scalar(f, x) for x in v]
        if f.is_fixed and f.type in ("int", "float", "bool"):
            return [normalize_scalar(f, x) for x in v]
        return normalize_scalar(f, v)
    except (ValueError, TypeError) as e:
        warnings.append(f"{where}: {e}")
        return MISSING


def node_from_wire(schema: Schema, cname: str, wire: dict, warnings: list):
    """Split a node wire dict into ``(values, enabled_module_ids, extra)``.

    Anything the schema does not know goes to ``extra`` so it survives a round trip.
    """
    cs = schema[cname]
    if wire.get("$class") not in (None, cname):
        warnings.append(f"{cname}: wire node is of class {wire.get('$class')}")
    props = dict(wire.get("props", {}))
    chunks = {k: dict(v) for k, v in wire.get("chunks", {}).items()}
    values: dict = {}
    enabled = set()
    known_members = set()
    has_chunks = "chunks" in wire
    for m in cs.modules:
        if (m.id in chunks) if has_chunks else m.default_enabled:
            enabled.add(m.id)
        ch = chunks.get(m.id, {})
        if m.version is not None and ch.get("Version", m.version) != m.version:
            warnings.append(f"{cname} chunk {m.id}: file has Version {ch['Version']}, schema writes {m.version}")
        for f in m.fields:
            if f.scope == "node":
                v = props.get(f.member, MISSING)
                known_members.add(("p", f.member))
            else:
                v = ch.get(f.member, MISSING)
                known_members.add(("c", m.id, f.member))
            if v is MISSING:
                continue
            dv = _decode_field(f, v, warnings, f"{cname}.{f.key}")
            if dv is not MISSING:
                values.setdefault(f.key, dv)
    extra = dict(wire.get("extra", {}))
    leftovers_p = {k: v for k, v in props.items() if ("p", k) not in known_members}
    leftovers_c = {}
    for cid, ch in chunks.items():
        mod = next((m for m in cs.modules if m.id == cid), None)
        if mod is None:
            leftovers_c[cid] = ch
            continue
        rest = {k: v for k, v in ch.items() if k != "Version" and ("c", cid, k) not in known_members}
        if rest:
            leftovers_c[cid] = rest
    if leftovers_p:
        extra.setdefault("props", {}).update(leftovers_p)
    if leftovers_c:
        extra.setdefault("chunks", {}).update(leftovers_c)
    return values, enabled, extra


def struct_from_wire(schema: Schema, qname: str, wire: dict, warnings: list):
    cs = schema[qname]
    props = dict(wire.get("props", {}))
    values, known = {}, set()
    for f in cs.fields:
        known.add(f.member)
        v = props.get(f.member, MISSING)
        if v is MISSING:
            continue
        dv = _decode_field(f, v, warnings, f"{qname}.{f.key}")
        if dv is not MISSING:
            values[f.key] = dv
    extra = dict(wire.get("extra", {}))
    left = {k: v for k, v in props.items() if k not in known}
    if left:
        extra.setdefault("props", {}).update(left)
    return values, extra


# --------------------------------------------------------------- tree traversal
def flatten(schema: Schema, cname: str, wire: dict, path: str, out: Optional[dict] = None,
            is_struct: bool = False) -> dict:
    """``path.key -> value`` for every field of a wire tree (paths match Blender paths).

    Extra entries: ``path@en_<offset>`` (module enabled) and ``path.key@on`` (child present).
    """
    out = {} if out is None else out
    warnings: list = []
    if is_struct:
        values, _ = struct_from_wire(schema, cname, wire, warnings)
        enabled = None
    else:
        values, enabled, _ = node_from_wire(schema, cname, wire, warnings)
    cs = schema[cname]
    for m in cs.modules:
        if enabled is not None:
            out[f"{path}@{m.en_key}"] = m.id in enabled
        for f in m.fields:
            if f.key not in values:
                continue
            v = values[f.key]
            p = f"{path}.{f.key}"
            if f.type == "node":
                if f.is_list:
                    for i, child in enumerate(v):
                        flatten(schema, f.ref, child, f"{p}[{i}]", out)
                else:
                    out[f"{p}@on"] = v is not None
                    if v is not None:
                        flatten(schema, f.ref, v, child_path(path, f), out)
            elif f.type == "struct":
                if f.is_list:
                    for i, child in enumerate(v):
                        flatten(schema, f.ref, child, f"{p}[{i}]", out, is_struct=True)
                elif v is not None:
                    flatten(schema, f.ref, v, child_path(path, f), out, is_struct=True)
            else:
                out[p] = v
    return out


def values_equal(a, b, tol=1e-6) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
        except (TypeError, ValueError):
            return False
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(values_equal(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(values_equal(a[k], b[k], tol) for k in a)
    return a == b


# ------------------------------------------------------------------- validation
def validate(schema: Schema, wire: dict, cname: Optional[str] = None, path: str = "vfx") -> list:
    """Return human readable problems with a wire tree (empty list = fine)."""
    problems: list = []
    cname = cname or wire.get("$class") or wire.get("$struct")
    if cname not in schema.classes:
        return [f"{path}: unknown class {cname}"]
    cs = schema[cname]
    is_struct = cs.kind == "struct"
    warnings: list = []
    if is_struct:
        values, _ = struct_from_wire(schema, cname, wire, warnings)
    else:
        values, _, _ = node_from_wire(schema, cname, wire, warnings)
    problems += [f"{path}: {w}" for w in warnings]
    lookup = _lookup_from(values)
    for f in cs.fields:
        if f.key not in values or not is_visible(f, lookup):
            continue
        v, p = values[f.key], f"{path}.{f.key}"
        if f.type == "node":
            kids = v if f.is_list else ([v] if v is not None else [])
            for i, k in enumerate(kids):
                problems += validate(schema, k, f.ref, f"{p}[{i}]" if f.is_list else p)
        elif f.type == "struct":
            kids = v if f.is_list else ([v] if v is not None else [])
            for i, k in enumerate(kids):
                problems += validate(schema, k, f.ref, f"{p}[{i}]" if f.is_list else p)
        elif f.type == "enum" and f.choices is not None and not f.is_list:
            if v not in [c[0] for c in f.choices]:
                problems.append(f"{p}: {v} is not a known value (known: {[c[0] for c in f.choices]})")
        elif f.type == "curve":
            pts = v["points"]
            if any(pts[i][0] > pts[i + 1][0] for i in range(len(pts) - 1)):
                problems.append(f"{p}: curve keys are not sorted by time")
    return problems


# ------------------------------------------------------------------------ presets
# Structure only: every value comes from the generated schema defaults.
def _find_node_field(cs: ClassSchema, ref: str):
    for f in cs.fields:
        if f.type == "node" and f.ref == ref:
            return f
    return None


def preset_gpu_submodel(schema: Schema) -> dict:
    """SubModel with its GPU spawn + model children present (all modules enabled)."""
    cs = schema["CPlugParticleEmitterSubModel"]
    sv = default_values(schema, cs)
    for ref in ("CPlugParticleGpuSpawn", "CPlugParticleGpuModel"):
        f = _find_node_field(cs, ref)
        if f is None:
            raise KeyError(f"SubModel has no field referencing {ref}")
        sv[f.key] = default_node(schema, ref)
    return node_to_wire(schema, "CPlugParticleEmitterSubModel", sv, {m.id for m in cs.modules})


def preset_emitter_node(schema: Schema, name: str = "Emitter") -> dict:
    """EffectNode(Type=4) -> EmitterModel -> SubModel -> GpuSpawn + GpuModel, schema defaults."""
    em_cs = schema["CPlugParticleEmitterModel"]
    ev = default_values(schema, em_cs)
    lst = next(f for f in em_cs.fields if f.type == "node" and f.ref == "CPlugParticleEmitterSubModel")
    ev[lst.key] = [preset_gpu_submodel(schema)]
    emitter = node_to_wire(schema, "CPlugParticleEmitterModel", ev, {m.id for m in em_cs.modules})

    qname = f"{ROOT_CLASS}.EffectNode"
    nv = default_values(schema, schema[qname])
    nv["Type"] = 4
    nv["Name"] = name
    nv["Emitter"] = emitter
    return struct_to_wire(schema, qname, nv)


def new_item_wire(schema: Schema, ref: str) -> dict:
    """Wire for a freshly added list item of class/struct ``ref`` (used by the UI's add button)."""
    if ref == "CPlugParticleEmitterSubModel":
        return preset_gpu_submodel(schema)
    cs = schema[ref]
    return default_node(schema, ref) if cs.kind == "node" else default_struct(schema, ref)


def root_wire(schema: Schema) -> dict:
    """Empty fx system: the root effect node is a group (Type 0) without children."""
    cs = schema[ROOT_CLASS]
    v = default_values(schema, cs)
    qname = f"{ROOT_CLASS}.EffectNode"
    rv = default_values(schema, schema[qname])
    rv["Type"] = 0
    rv["Name"] = "Root"
    v["Root"] = struct_to_wire(schema, qname, rv)
    return node_to_wire(schema, ROOT_CLASS, v, {m.id for m in cs.modules})


def wrap_emitter(schema: Schema, emitter: dict, name: str = "Emitter") -> dict:
    """fx system whose group root holds one emitter node (Type 4) with ``emitter``
    (a CPlugParticleEmitterModel wire, e.g. read from a Nadeo *.ParticleModel.Gbx)."""
    qname = f"{ROOT_CLASS}.EffectNode"
    nv = default_values(schema, schema[qname])
    nv["Type"] = 4
    nv["Name"] = name
    nv["Emitter"] = emitter
    root = root_wire(schema)
    root["props"]["Root"]["props"]["Children"] = [struct_to_wire(schema, qname, nv)]
    return root


def document(schema: Schema, root: dict) -> dict:
    return {"format": FORMAT, "game": schema.meta.get("game", "TM2020"),
            "gbxnet_commit": schema.meta.get("gbxnet_commit", "unknown"), "vfx": root}
