"""Schema loading: generated *base* files merged with hand-written *overlay* files.

Pure Python (no ``bpy``).  The base layer (``schema/base/*.json``) is produced by
``tools/gen_schema.py`` from GBX.NET and is never edited by hand.  The overlay
layer (``schema/overlay/*.json``) carries everything only a human knows: labels,
ranges, grouping, tooltips and - most importantly - the *confidence status* of
each field.

Overlay file layout (all sections optional)::

    {
      "class": "CPlugParticleGpuModel",
      "title": "GPU particle model",
      "modules": { "0x000": {"label": "Lifetime & size", "default_enabled": true} },
      "fields":  { "LifeMax": {"label": "Max life", "unit": "s", "min": 0.01,
                               "status": "verified", "tooltip": "..."} },
      "archives": { "Parameter": { "title": "Parameter", "title_fields": ["Type", "Name"],
                                   "fields": { ... } } }
    }

Field overlay keys: label, group, tooltip, unit, min, max, soft_min, soft_max,
step, precision, status (verified|named|guess|unknown), hidden, choices
([[value, label], ...]), note, visible_if (expression over field keys),
default (overrides the base default), subtype.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Optional

from . import expr

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"

STATUSES = ("verified", "named", "guess", "unknown")
SCALAR_TYPES = {"int", "float", "bool", "string", "enum"}


def prettify(name: str) -> str:
    """``SizeVar01`` -> ``Size Var 01``; ``UseEmitterHue`` -> ``Use Emitter Hue``."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=\d)", " ", name)
    return s.replace("_", " ").strip()


@dataclass
class Field:
    key: str
    member: str
    scope: str                    # node | chunk | archive
    name: Optional[str]
    type: str                     # int float bool string enum vec iso4 box blob curve struct node ref opaque
    array: Any = None             # None | "list" | int (fixed length)
    ref: Optional[str] = None     # class / struct / ref target
    enum: Optional[str] = None
    items: list = dc_field(default_factory=list)      # enum items [(name, value)]
    bits: int = 32
    signed: bool = True
    kind: str = "float"           # vec element kind
    size: int = 0                 # vec size
    length: Optional[int] = None  # blob length
    sub: Optional[str] = None
    default: Any = None
    when: Optional[list] = None
    when_unresolved: list = dc_field(default_factory=list)
    attrs: list = dc_field(default_factory=list)
    module: str = ""              # chunk id this field was declared in ("" for archives)
    # overlay ------------------------------------------------------------
    label: str = ""
    group: str = ""
    tooltip: str = ""
    unit: str = ""
    min: Optional[float] = None
    max: Optional[float] = None
    soft_min: Optional[float] = None
    soft_max: Optional[float] = None
    step: Optional[float] = None
    precision: Optional[int] = None
    status: str = "unknown"
    hidden: bool = False
    choices: Optional[list] = None
    note: str = ""
    subtype: Optional[str] = None

    # convenience ------------------------------------------------------------
    @property
    def is_list(self) -> bool:
        return self.array == "list"

    @property
    def is_fixed(self) -> bool:
        return isinstance(self.array, int)

    @property
    def is_child(self) -> bool:
        """Fields that are children in the outline tree (nodes, and lists of structs)."""
        return self.type == "node" or (self.type == "struct" and self.is_list)

    @property
    def is_known(self) -> bool:
        return self.status != "unknown"


@dataclass
class Module:
    id: str                       # full chunk id, e.g. "0x090C6000"
    offset: str
    version: Optional[int]
    label: str
    comment: str = ""
    default_enabled: bool = True
    fields: list = dc_field(default_factory=list)
    skippable: bool = False

    @property
    def en_key(self) -> str:
        return "en_" + self.offset[2:]

    @property
    def open_key(self) -> str:
        return "ui_" + self.offset[2:]


@dataclass
class ClassSchema:
    name: str                     # "CPlugParticleGpuModel" or "CPlugVFXFile.Parameter"
    kind: str                     # node | struct
    id: Optional[str]
    title: str
    modules: list
    title_fields: list = dc_field(default_factory=list)
    version: Optional[int] = None  # archive version (structs)
    source: str = ""

    @property
    def fields(self):
        for m in self.modules:
            yield from m.fields

    def field(self, key: str) -> Optional[Field]:
        for f in self.fields:
            if f.key == key:
                return f
        return None

    @property
    def pg_name(self) -> str:
        return "FX_" + self.name.replace(".", "_")


@dataclass
class Schema:
    classes: dict
    meta: dict
    warnings: list = dc_field(default_factory=list)

    def __getitem__(self, name) -> ClassSchema:
        return self.classes[name]

    def get(self, name) -> Optional[ClassSchema]:
        return self.classes.get(name)

    @property
    def schema_id(self) -> str:
        return f"{self.meta.get('gbxnet_commit', '?')[:12]}/{self.meta.get('overlay_hash', '?')}"


# --------------------------------------------------------------------- loading
def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _apply_overlay(f: Field, o: dict, keyset: set, warnings: list, where: str):
    for k, v in o.items():
        if k == "choices":
            f.choices = [(int(a), str(b)) for a, b in v]
        elif k == "visible_if":
            try:
                ast = expr.rewrite(expr.parse(v), lambda n: ["key", n] if n in keyset else None)
                f.when = expr.AND(f.when, ast)
            except expr.ParseError:
                warnings.append(f"{where}: bad visible_if {v!r}")
        elif k in ("label", "group", "tooltip", "unit", "min", "max", "soft_min", "soft_max",
                   "step", "precision", "status", "hidden", "note", "subtype", "default"):
            setattr(f, k, v)
        else:
            warnings.append(f"{where}: unknown overlay property {k!r}")
    if f.status not in STATUSES:
        warnings.append(f"{where}: invalid status {f.status!r}")
        f.status = "named" if f.name else "unknown"


def _build_fields(raw_fields, module_id, ov_fields, warnings, owner):
    keyset = {rf["key"] for rf in raw_fields}
    out = []
    for rf in raw_fields:
        f = Field(
            key=rf["key"], member=rf["member"], scope=rf["scope"], name=rf.get("name"),
            type=rf["type"], array=rf.get("array"), ref=rf.get("ref"), enum=rf.get("enum"),
            items=[tuple(i) for i in rf.get("items", [])], bits=rf.get("bits", 32),
            signed=rf.get("signed", True), kind=rf.get("kind", "float"), size=rf.get("size", 0),
            length=rf.get("length"), sub=rf.get("sub"), default=rf.get("default"),
            when=rf.get("when"), when_unresolved=rf.get("when_unresolved", []),
            attrs=rf.get("attrs", []), module=module_id,
        )
        f.label = prettify(f.name) if f.name else f"Unknown {f.member[1:]}"
        f.status = "named" if f.name else "unknown"
        o = ov_fields.get(f.key)
        if o:
            _apply_overlay(f, o, keyset, warnings, f"{owner}.{f.key}")
        if f.choices is None and f.type == "enum":
            f.choices = [(v, prettify(n)) for n, v in f.items]
        out.append(f)
    return out


def load_schema(base_dir: Path = None, overlay_dir: Path = None) -> Schema:
    """Load and merge the schema.  Safe to call repeatedly (cheap, ~ms)."""
    base_dir = Path(base_dir) if base_dir else SCHEMA_DIR / "base"
    overlay_dir = Path(overlay_dir) if overlay_dir else SCHEMA_DIR / "overlay"
    warnings: list = []
    meta = {}
    idx = base_dir / "_index.json"
    if idx.exists():
        meta = _read_json(idx)
    classes: dict = {}
    overlay_blob = []
    for p in sorted(base_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        raw = _read_json(p)
        cname = raw["class"]
        ovp = overlay_dir / f"{cname}.json"
        ov = _read_json(ovp) if ovp.exists() else {}
        if ovp.exists():
            overlay_blob.append(ovp.read_text(encoding="utf-8"))
        ov_mod = ov.get("modules", {})

        modules = []
        for ch in raw["chunks"]:
            om = ov_mod.get(ch["id"], ov_mod.get(ch["offset"], {}))
            label = om.get("label") or f"Chunk {ch['offset']}"
            m = Module(
                id=ch["id"], offset=ch["offset"], version=ch.get("version"), label=label,
                comment=ch.get("comment", ""), default_enabled=om.get("default_enabled", True),
                skippable="skippable" in ch.get("attrs", []),
            )
            m.fields = _build_fields(ch["fields"], ch["id"], ov.get("fields", {}), warnings, cname)
            modules.append(m)
        cs = ClassSchema(
            name=cname, kind="node", id=raw.get("id"), title=ov.get("title") or prettify(cname.replace("CPlug", "")),
            modules=modules, title_fields=ov.get("title_fields", []), source=raw.get("source", ""),
        )
        classes[cname] = cs

        for aname, ar in raw.get("archives", {}).items():
            oa = ov.get("archives", {}).get(aname, {})
            qual = f"{cname}.{aname}"
            mod = Module(id="", offset="0x000", version=ar.get("version"), label=oa.get("label", "Fields"))
            mod.fields = _build_fields(ar["fields"], "", oa.get("fields", {}), warnings, qual)
            classes[qual] = ClassSchema(
                name=qual, kind="struct", id=None, title=oa.get("title") or prettify(aname),
                modules=[mod], title_fields=oa.get("title_fields", []),
                version=ar.get("version"), source=raw.get("source", ""),
            )
        # orphan check
        known_keys = {f.key for c in modules for f in c.fields}
        for k in ov.get("fields", {}):
            if k not in known_keys:
                warnings.append(f"overlay {cname}: field {k!r} does not exist in the base schema "
                                f"(renamed or removed in GBX.NET?)")
        for aname, oa in ov.get("archives", {}).items():
            ak = {f.key for f in classes.get(f"{cname}.{aname}", ClassSchema("", "", None, "", [])).fields}
            for k in oa.get("fields", {}):
                if k not in ak:
                    warnings.append(f"overlay {cname}.{aname}: field {k!r} does not exist in the base schema")
    # validate references
    for cs in classes.values():
        for f in cs.fields:
            if f.type in ("node", "struct") and f.ref not in classes:
                warnings.append(f"{cs.name}.{f.key} references unknown class {f.ref}")
    import hashlib
    meta = dict(meta)
    meta["overlay_hash"] = hashlib.sha1("".join(overlay_blob).encode()).hexdigest()[:8]
    return Schema(classes=classes, meta=meta, warnings=warnings)


# ----------------------------------------------------------------- value helpers
def type_default(f: Field):
    """Default for one *element* of a field (ignores arrays)."""
    if f.default is not None and f.type not in ("vec", "iso4", "box"):
        return f.default
    t = f.type
    if t == "bool":
        return False
    if t == "int":
        return 0
    if t == "float":
        return 0.0
    if t == "string" or t == "ref":
        return ""
    if t == "enum":
        if f.choices:
            return f.choices[0][0]
        return f.items[0][1] if f.items else 0
    if t == "vec":
        if isinstance(f.default, list) and len(f.default) == f.size:
            return list(f.default)
        return [0] * f.size if f.kind == "int" else [0.0] * f.size
    if t == "iso4":
        return [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    if t == "box":
        return [0.0] * 6
    if t == "blob":
        return "00" * f.length if f.length else ""
    if t == "curve":
        return {"flags": 0, "points": []}
    return None


def field_default(f: Field):
    """Default of the whole field (handles arrays)."""
    if f.type in ("node",):
        return [] if f.is_list else None
    if f.type == "struct":
        return []
    if f.type == "opaque":
        return None
    if f.is_list:
        return []
    if f.is_fixed and f.type in ("int", "float", "bool"):
        base = type_default(f)
        return [base] * f.array
    return type_default(f)


def int_range(f: Field):
    bits = f.bits or 32
    if f.type != "int":
        return (-(2**31), 2**31 - 1)
    if f.signed:
        lo, hi = -(2 ** (bits - 1)), 2 ** (bits - 1) - 1
    else:
        lo, hi = 0, 2 ** bits - 1
    return (max(lo, -(2**31)), min(hi, 2**31 - 1))


def is_visible(f: Field, lookup) -> bool:
    """Evaluate a field's ``when`` against ``lookup(key)``; unresolved -> visible."""
    if f.when is None:
        return True
    try:
        return bool(expr.evaluate(f.when, lookup))
    except expr.Unresolved:
        return True
    except Exception:
        return True
