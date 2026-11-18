# NOTE: no ``from __future__ import annotations`` here - Blender needs real
# annotation objects on PropertyGroup classes.
"""Generate Blender PropertyGroups from the schema.

For every schema class (node or inline struct) one ``PropertyGroup`` is created
whose properties are exactly the schema fields, so the UI can only ever expose
what the GBX layout can represent.  Child nodes and structs are attached in a
second pass *after* registration, which also makes recursive structures (a
``Parameter`` containing ``Parameter`` children) trivial.

Bitmap references (``Field.asset_type``) are pointers to addon asset materials
(``tm_asset_properties``, type BITMAP), exported as asset id like the veget tree bitmaps.

Per-group bookkeeping properties (not part of the GBX data):
    en_<chunk>   module (chunk) enabled   ui_<chunk>   panel expanded state
    on_<key>     optional child node present
    extra_json   unknown wire data carried through untouched
"""
import contextlib

import bpy
from bpy.props import (BoolProperty, BoolVectorProperty, CollectionProperty, EnumProperty,
                       FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty,
                       PointerProperty, StringProperty)

from . import expr
from . import schema as S
from .codec import ROOT_CLASS
from ..properties.PropertyIdentifiers import ObjectProp
from ..utils.AssetLibraryFunctions import poll_asset

OBJECT_ATTR = "tm_fx"   # bpy.types.Object.tm_fx ; ObjectProp.PARTICLE_FX marks the object as particle fx node

_state = {"schema": None, "classes": {}, "reverse": {}, "registered": [], "suspend": 0}


# -------------------------------------------------------------------- helpers
def get_schema() -> S.Schema:
    if _state["schema"] is None:
        _state["schema"] = S.load_schema()
    return _state["schema"]


def reload_schema() -> S.Schema:
    _state["schema"] = S.load_schema()
    return _state["schema"]


def pg_class(cname: str):
    return _state["classes"][cname]


def is_fx_node(obj) -> bool:
    """Empty marked as particle fx node (name infix ``_particleFX_``)."""
    return obj is not None and obj.type == "EMPTY" and bool(getattr(obj, ObjectProp.PARTICLE_FX, False))


def settings_of(context):
    """FX settings of the active object when it is a particle fx node, else None."""
    ob = getattr(context, "object", None)
    return getattr(ob, OBJECT_ATTR, None) if is_fx_node(ob) else None


def class_name_of(pg) -> str:
    return _state["reverse"][type(pg).__name__]


@contextlib.contextmanager
def suspend():
    """Silence structure-changed callbacks while code writes many properties."""
    _state["suspend"] += 1
    try:
        yield
    finally:
        _state["suspend"] -= 1


def on_key(f: S.Field) -> str:
    return "on_" + f.key


def is_enum_like(f: S.Field) -> bool:
    return f.choices is not None and f.type in ("int", "enum") and f.array is None


def enum_items(f: S.Field):
    return [(str(v), lbl, "") for v, lbl in f.choices]


def description(f: S.Field) -> str:
    parts = []
    if f.tooltip:
        parts.append(f.tooltip)
    if f.unit:
        parts.append(f"Unit: {f.unit}")
    if f.note:
        parts.append(f.note)
    addr = {"node": f.member, "chunk": f"Chunk{f.module[2:]}.{f.member}",
            "archive": f".{f.member}"}.get(f.scope, f.member)
    parts.append(f"[{f.status}] GBX.NET: {addr}")
    if f.when is not None:
        parts.append("Only written when: " + expr.to_str(f.when))
    return "\n".join(parts)


def _structure_changed(self, context):
    if _state["suspend"]:
        return
    try:
        from . import bridge
        owner = getattr(self, "id_data", None)
        settings = getattr(owner, OBJECT_ATTR, None) if isinstance(owner, bpy.types.Object) else None
        if settings is not None:
            bridge.rebuild_outline(settings)
    except Exception as e:  # never let a UI callback raise
        print("tm_fx: outline rebuild failed:", e)


def _cond_keys(cs: S.ClassSchema) -> set:
    keys = set()

    def walk(a):
        if a[0] == "key":
            keys.add(a[1])
        elif a[0] in ("un",):
            walk(a[2])
        elif a[0] == "isnull":
            walk(a[1])
        elif a[0] == "tern":
            for x in a[1:]:
                walk(x)
        elif a[0] == "bin":
            walk(a[2])
            walk(a[3])

    for f in cs.fields:
        if f.when is not None:
            walk(f.when)
    for k in cs.title_fields:
        keys.add(k)
    return keys


def make_prop(f: S.Field, structural: bool):
    """Return a bpy property for a scalar-ish field, or None when it needs the 2nd pass."""
    upd = _structure_changed if structural else None
    kw = {"name": f.label, "description": description(f)}
    if upd:
        kw["update"] = upd
    t = f.type
    if f.is_list and t in ("int", "float", "bool", "string", "enum"):
        return None  # collection of items, 2nd pass
    if f.asset_type:
        return PointerProperty(type=bpy.types.Material, poll=poll_asset(f.asset_type), **kw)
    if is_enum_like(f):
        items = enum_items(f)
        d = S.type_default(f)
        if str(d) not in [i[0] for i in items]:
            d = int(items[0][0])
        return EnumProperty(items=items, default=str(d), **kw)
    if t == "bool":
        return BoolProperty(default=bool(S.type_default(f)), **kw)
    if t == "int":
        if S.is_uint32(f):   # stored as signed bit pattern, full range
            lo, hi = -(2**31), 2**31 - 1
        else:
            lo, hi = S.int_range(f)
        mn = lo if f.min is None else int(f.min)
        mx = hi if f.max is None else int(f.max)
        d = max(mn, min(mx, S.to_blender_int(f, S.type_default(f))))
        extra = {}
        if f.soft_min is not None:
            extra["soft_min"] = int(f.soft_min)
        if f.soft_max is not None:
            extra["soft_max"] = int(f.soft_max)
        return IntProperty(default=d, min=mn, max=mx, **extra, **kw)
    if t == "float":
        extra = {}
        for k in ("min", "max", "soft_min", "soft_max", "step"):
            v = getattr(f, k)
            if v is not None:
                extra[k] = v
        d = float(S.type_default(f))
        if f.min is not None:
            d = max(d, f.min)
        if f.max is not None:
            d = min(d, f.max)
        return FloatProperty(default=d, precision=f.precision if f.precision is not None else 3,
                             **extra, **kw)
    if t in ("string", "ref", "blob"):
        return StringProperty(default=str(S.type_default(f) or ""), **kw)
    if t == "vec":
        d = tuple(S.type_default(f))
        if f.kind == "int":
            return IntVectorProperty(size=f.size, default=d, **kw)
        return FloatVectorProperty(size=f.size, default=d, precision=3, **kw)
    if t == "iso4":
        return FloatVectorProperty(size=12, default=tuple(S.type_default(f)), precision=3, **kw)
    if t == "box":
        return FloatVectorProperty(size=6, default=tuple(S.type_default(f)), precision=3, **kw)
    return None


# --------------------------------------------------------------- static groups
INTERP_ITEMS = [
    ("0", "Linear", "Linear interpolation between keys"),
    ("1", "Step", "Hold each key's value until the next key"),
    ("2", "Smooth", "Smooth-step interpolation"),
    ("16", "Hermite", "Hermite (cubic) interpolation"),
]


def _curve_interp_changed(self, context):
    from . import curves
    curves.apply_interp(self)


def _curve_range_changed(self, context):
    from . import curves
    curves.apply_range(self)


def _static_classes():
    def mk(name, ann):
        return type(name, (bpy.types.PropertyGroup,), {"__annotations__": ann})

    item_str = mk("FXItemStr", {"v": StringProperty(name="Value")})
    item_int = mk("FXItemInt", {"v": IntProperty(name="Value")})
    item_float = mk("FXItemFloat", {"v": FloatProperty(name="Value")})
    item_bool = mk("FXItemBool", {"v": BoolProperty(name="Value")})
    point = mk("FXCurvePoint", {
        "t": FloatProperty(name="Time", precision=3),
        "v": FloatProperty(name="Value", precision=3),
    })
    curve = mk("FXCurve", {
        "interp": EnumProperty(name="Interpolation", items=INTERP_ITEMS, default="0", update=_curve_interp_changed,
                               description="Derived from the PlugCurve flag bits (see GBX.NET PlugCurve)"),
        "uid": StringProperty(options={"HIDDEN"}),
        "x_max": FloatProperty(name="Max T", default=1.0, min=0.001, update=_curve_range_changed,
                               description="Right edge of the curve editor"),
        "y_min": FloatProperty(name="Min V", default=0.0, update=_curve_range_changed,
                               description="Bottom edge of the curve editor"),
        "y_max": FloatProperty(name="Max V", default=1.0, update=_curve_range_changed,
                               description="Top edge of the curve editor"),
        "tangent_max_x": BoolProperty(name="Force tangent at max X",
                                      description="PlugCurve flag 0x20"),
        "flags_other": IntProperty(name="Other flag bits", min=0, max=65535,
                                   description="Flag bits this tool does not interpret; kept verbatim"),
        "points": CollectionProperty(type=point),
        "active": IntProperty(),
    })
    outline = mk("FXOutlineItem", {"path": StringProperty(), "cls": StringProperty(),
                                   "label": StringProperty(),
                                   "depth": IntProperty()})
    return {"str": item_str, "int": item_int, "float": item_float, "bool": item_bool,
            "point": point, "curve": curve, "outline": outline}


MODE_ITEMS = [
    ("VERIFIED", "Verified", "Only fields confirmed in game"),
    ("KNOWN", "Known", "Verified, named and guessed fields (hide fully unknown ones)"),
    ("ALL", "All", "Every field including unknown ones"),
]


def _selected_changed(self, context):
    if _state["suspend"]:
        return
    try:
        if 0 <= self.outline_index < len(self.outline):
            self.selected_path = self.outline[self.outline_index].path
    except Exception:
        pass


# --------------------------------------------------------------- registration
def _register(cls):
    bpy.utils.register_class(cls)
    _state["registered"].append(cls)


def register():
    schema = reload_schema()
    st = _static_classes()
    _state["static"] = st
    for k in ("str", "int", "float", "bool", "point", "curve", "outline"):
        _register(st[k])

    # pass 1: create + register all groups with their scalar properties
    cond = {}
    for cname, cs in schema.classes.items():
        ann = {"extra_json": StringProperty(options={"HIDDEN"})}
        cond[cname] = _cond_keys(cs)
        for i, m in enumerate(cs.modules):
            if cs.kind == "node":
                ann[m.en_key] = BoolProperty(name=m.label, default=m.default_enabled,
                                             update=_structure_changed,
                                             description=f"Write chunk {m.id}")
            ann[m.open_key] = BoolProperty(default=(i == 0), options={"HIDDEN"})
            for f in m.fields:
                if f.type == "node" and not f.is_list and not f.boxed:
                    ann[on_key(f)] = BoolProperty(name=f.label, default=False, update=_structure_changed,
                                                  description=description(f))
                p = make_prop(f, structural=(f.key in cond[cname]))
                if p is not None:
                    ann[f.key] = p
        cls = type(cs.pg_name, (bpy.types.PropertyGroup,), {"__annotations__": ann})
        _state["classes"][cname] = cls
        _state["reverse"][cls.__name__] = cname
        _register(cls)

    # pass 2: children, curves, scalar lists (may reference any group, including itself)
    for cname, cs in schema.classes.items():
        cls = _state["classes"][cname]
        for f in cs.fields:
            if f.type in ("node", "struct"):
                target = _state["classes"][f.ref]
                if f.is_list or f.boxed:    # boxed: 0..1 items, closes a pointer cycle
                    setattr(cls, f.key, CollectionProperty(type=target, name=f.label))
                elif f.type == "struct":
                    setattr(cls, f.key, PointerProperty(type=target, name=f.label))
                else:
                    setattr(cls, f.key, PointerProperty(type=target, name=f.label))
            elif f.type == "curve":
                setattr(cls, f.key, PointerProperty(type=st["curve"], name=f.label,
                                                    description=description(f)))
            elif f.is_list and f.type in ("int", "float", "bool", "string", "enum"):
                item = {"int": "int", "enum": "int", "float": "float", "bool": "bool",
                        "string": "str"}[f.type]
                setattr(cls, f.key, CollectionProperty(type=st[item], name=f.label,
                                                       description=description(f)))

    root = type("FXRoot", (bpy.types.PropertyGroup,), {"__annotations__": {
        "vfx": PointerProperty(type=_state["classes"][ROOT_CLASS]),
        "outline": CollectionProperty(type=st["outline"]),
        "outline_index": IntProperty(update=_selected_changed),
        "selected_path": StringProperty(default="vfx"),
        "mode": EnumProperty(name="Show", items=MODE_ITEMS, default="KNOWN"),
        "search": StringProperty(name="Search", options={"TEXTEDIT_UPDATE"}),
        "template_json": StringProperty(options={"HIDDEN"}),
        "schema_id": StringProperty(),
    }})
    _state["root"] = root
    _register(root)
    setattr(bpy.types.Object, OBJECT_ATTR, PointerProperty(type=root))


def unregister():
    if hasattr(bpy.types.Object, OBJECT_ATTR):
        delattr(bpy.types.Object, OBJECT_ATTR)
    for cls in reversed(_state["registered"]):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    _state["registered"].clear()
    _state["classes"].clear()
    _state["reverse"].clear()
