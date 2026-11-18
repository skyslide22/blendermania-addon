import bpy

from . import api, bridge, curves
from . import schema as S
from .props import ROOT_CLASS, class_name_of, get_schema, on_key, settings_of
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS

ICON = {"verified": "CHECKMARK", "guess": "QUESTION"}


def _passes(f, mode, q):
    if mode == "VERIFIED" and f.status != "verified":
        return False
    if mode == "KNOWN" and f.status == "unknown":
        return False
    return not q or q in f.label.lower() or q in f.key.lower() or q in f.member.lower()


def _op(layout, idname, text="", icon="NONE", **kw):
    op = layout.operator(idname, text=text, icon=icon)
    for k, v in kw.items():
        setattr(op, k, v)
    return op


def draw_field(layout, pg, f, settings, path):
    t = f.type
    label = f.label + (" ?" if f.status == "guess" else "")
    p = f"{path}.{f.key}"
    if t == "opaque":
        layout.label(text=f"{f.label}: not editable ({f.ref}), omitted", icon="LOCKED")
    elif f.asset_type:
        row = layout.row(align=True)
        row.prop(pg, f.key, text=label, icon="TEXTURE")
        if bridge.is_changed(settings, path, pg, f):
            _op(row, "tm_fx.reset", "", "LOOP_BACK", path=path, key=f.key)
    elif t in ("node", "struct") and f.boxed:   # optional single child stored as 0..1 collection
        row = layout.row(align=True)
        row.label(text=label + ("" if bridge.has_child(pg, f) else " (default)" if t == "struct" else ": none"))
        if bridge.has_child(pg, f):
            _op(row, "tm_fx.goto", "Edit", "RIGHTARROW", path=f"{p}[0]")
        else:
            _op(row, "tm_fx.add", "Add", "ADD", path=path, key=f.key)
    elif t == "node" and not f.is_list:
        row = layout.row(align=True)
        row.prop(pg, on_key(f), text=label)
        if getattr(pg, on_key(f)):
            _op(row, "tm_fx.goto", "Edit", "RIGHTARROW", path=p)
    elif t in ("node", "struct") and f.is_list:
        row = layout.row(align=True)
        row.label(text=f"{label}: {len(getattr(pg, f.key))}")
        _op(row, "tm_fx.add", "Add", "ADD", path=path, key=f.key)
        if f.ref == f"{ROOT_CLASS}.EffectNode":
            _op(row, "tm_fx.add", "Emitter", "PARTICLES", path=path, key=f.key, preset=True)
    elif t == "struct":   # inline struct: its own outline row (may be recursive)
        row = layout.row(align=True)
        row.label(text=bridge.row_title(getattr(pg, f.key), get_schema()[f.ref], label))
        _op(row, "tm_fx.goto", "Edit", "RIGHTARROW", path=p)
    elif t == "curve":
        c = getattr(pg, f.key)
        box = layout.box()
        box.label(text=label)
        node = curves.get_node(c)
        if node is None:
            _op(box, "tm_fx.edit", "Add curve" if not len(c.points) else "Edit as curve", "FCURVE",
                path=path, key=f.key, action="ADD")
        else:
            box.template_curve_mapping(node, "mapping", type="NONE", levels=False, brush=False,
                                       use_negative_slope=True, show_presets=False)
            box.prop(c, "interp", text="")
            if c.interp == "1":
                box.label(text="Step: stored as flag, drawn as linear", icon="INFO")
            row = box.row(align=True)
            row.prop(c, "x_max", text="Max T")
            row.prop(c, "y_min", text="Min V")
            row.prop(c, "y_max", text="Max V")
            row = box.row(align=True)
            row.prop(c, "tangent_max_x")
            _op(row, "tm_fx.edit", "", "X", path=path, key=f.key, action="REMOVE")
    elif f.is_list:
        box = layout.box()
        box.label(text=label)
        for it in getattr(pg, f.key):
            box.prop(it, "v", text="")
        row = box.row(align=True)
        for a, ic in (("ADD", "ADD"), ("REMOVE", "REMOVE")):
            _op(row, "tm_fx.edit", "", ic, path=path, key=f.key, action=a)
    elif t == "iso4":
        col = layout.column(align=True)
        col.label(text=label)
        for r in range(4):
            row = col.row(align=True)
            for c in range(3):
                row.prop(pg, f.key, index=r * 3 + c, text="")
    elif t == "box":
        col = layout.column(align=True)
        col.label(text=label)
        for r in range(2):
            row = col.row(align=True)
            for c in range(3):
                row.prop(pg, f.key, index=r * 3 + c, text="")
    else:
        row = layout.row(align=True)
        row.prop(pg, f.key, text=label)
        if bridge.is_changed(settings, path, pg, f):
            _op(row, "tm_fx.reset", "", "LOOP_BACK", path=path, key=f.key)


def draw_node(layout, pg, settings, path):
    cs = get_schema()[class_name_of(pg)]
    lookup = bridge.make_lookup(pg, cs)
    q = settings.search.lower()
    hidden = 0
    for m in cs.modules:
        fields = [f for f in m.fields if not f.hidden and S.is_visible(f, lookup)]
        shown = [f for f in fields if _passes(f, settings.mode, q)]
        hidden += len(fields) - len(shown)
        if not shown:
            continue
        if cs.kind == "node":
            box = layout.box()
            row = box.row(align=True)
            is_open = getattr(pg, m.open_key) or bool(q)
            row.prop(pg, m.open_key, text=m.label, emboss=False,
                     icon="TRIA_DOWN" if is_open else "TRIA_RIGHT")
            row.label(text=f"v{m.version}" if m.version is not None else "")
            row.prop(pg, m.en_key, text="")
            if not (is_open and getattr(pg, m.en_key)):
                continue
        else:
            box = layout
        group = None
        col = box.column(align=True)
        for f in shown:
            if f.group != group and f.group:
                col.label(text=f.group)
            group = f.group
            draw_field(col, pg, f, settings, path)
    if hidden and cs.kind == "node":
        layout.label(text=f"{hidden} field(s) hidden by filter", icon="HIDE_ON")


class TMFX_UL_outline(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        for _ in range(item.depth):
            row.label(text="", icon="BLANK1")
        try:
            title = bridge.row_title(bridge.resolve(data, item.path), get_schema()[item.cls], item.label)
        except Exception:
            title = item.cls
        row.label(text=title, icon="PARTICLES" if item.depth else "FILE_BLANK")


class _Panel:
    locals().update(PANEL_CLASS_COMMON_DEFAULT_PROPS)

    @classmethod
    def poll(cls, context):
        return settings_of(context) is not None


class TMFX_PT_main(_Panel, bpy.types.Panel):
    """Particle fx of the active empty, written to ItemConfig.ParticleFx on export"""
    bl_label, bl_idname = "Particle FX", "TMFX_PT_main"
    bl_parent_id = "TM_PT_ObjectManipulationsV2"
    bl_order = 15

    def draw_header(self, context):
        self.layout.label(icon="PARTICLES")

    def draw(self, context):
        s = settings_of(context)
        obj = context.object
        lay = self.layout
        row = lay.row(align=True)
        row.operator("tm_fx.import_gbx", text="Import GBX", icon="IMPORT")
        row.operator("tm_fx.import_json", text="Import JSON", icon="IMPORT")
        row.operator("tm_fx.export_json", text="Export JSON", icon="EXPORT")
        row = lay.row(align=True)
        row.label(text="Template: " + ("set" if s.template_json else "none"))
        _op(row, "tm_fx.template", "Use current", action="SET")
        _op(row, "tm_fx.template", "", "X", action="CLEAR")
        row = lay.row(align=True)
        row.prop(s, "mode", expand=True)
        lay.prop(s, "search", icon="VIEWZOOM")

        issues = api.get_fx_issues(obj)
        if issues:
            box = lay.box()
            box.alert = True
            for msg in issues:
                box.label(text=msg, icon="CANCEL")


class TMFX_PT_tree(_Panel, bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Structure", "TMFX_PT_tree", "TMFX_PT_main"
    bl_options = set()

    def draw(self, context):
        s = settings_of(context)
        row = self.layout.row()
        row.template_list("TMFX_UL_outline", "", s, "outline", s, "outline_index", rows=6)
        col = row.column(align=True)
        for a, ic in (("REMOVE", "REMOVE"), ("DUPLICATE", "DUPLICATE"), ("UP", "TRIA_UP"), ("DOWN", "TRIA_DOWN")):
            _op(col, "tm_fx.item", "", ic, action=a)


class TMFX_PT_node(_Panel, bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Selected node", "TMFX_PT_node", "TMFX_PT_main"
    bl_options = set()

    def draw_header_preset(self, context):
        s = settings_of(context)
        try:
            pg = bridge.resolve(s, s.selected_path)
            self.layout.label(text=bridge.row_title(pg, get_schema()[class_name_of(pg)]))
        except (AttributeError, IndexError, KeyError):
            pass

    def draw(self, context):
        s = settings_of(context)
        try:
            pg = bridge.resolve(s, s.selected_path)
        except (AttributeError, IndexError):   # stale selection (no writes allowed while drawing)
            self.layout.label(text="Select a node in the structure list", icon="INFO")
            return
        draw_node(self.layout, pg, s, s.selected_path)


_CLASSES = (TMFX_UL_outline, TMFX_PT_main, TMFX_PT_tree, TMFX_PT_node)


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
