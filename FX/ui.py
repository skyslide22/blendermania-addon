import copy

import bpy

from . import bridge, curves, layout
from . import schema as S
from .props import ROOT_CLASS, class_name_of, get_schema, is_enum_like, on_key, settings_of

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
    elif t == "node" and not f.is_list:
        row = layout.row(align=True)
        row.prop(pg, on_key(f), text=label)
        if getattr(pg, on_key(f)):
            _op(row, "tm_fx.goto", "Edit", "RIGHTARROW", path=p)
    elif t in ("node", "struct") and f.is_list:
        row = layout.row(align=True)
        row.label(text=f"{label}: {len(getattr(pg, f.key))}")
        _op(row, "tm_fx.add", "Add", "ADD", path=path, key=f.key)
        if f.ref == "CPlugVFXFile.Parameter":
            _op(row, "tm_fx.add", "GPU emitter", "PARTICLES", path=path, key=f.key, preset=True)
    elif t == "struct":
        box = layout.box()
        box.label(text=label)
        draw_node(box, getattr(pg, f.key), settings, p)
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


def _find_field(cs, key):
    for m in cs.modules:
        for f in m.fields:
            if f.key == key:
                return m, f
    return None, None


def draw_layout_section(layout_ui, pg, cs, settings, path, sec):
    """One box of layout.json for the node ``pg``."""
    box = layout_ui.box()
    box.label(text=sec["title"])
    lookup = bridge.make_lookup(pg, cs)
    col = box.column(align=True)
    chunks_off = set()
    for spec in sec["fields"]:
        m, f = _find_field(cs, spec["key"])
        if f is None:
            col.label(text=f"layout.json: unknown field {spec['key']}", icon="ERROR")
            continue
        if not S.is_visible(f, lookup):
            continue
        if not getattr(pg, m.en_key) and m.id not in chunks_off:
            chunks_off.add(m.id)
            col.prop(pg, m.en_key, text=f"Enable chunk: {m.label}", toggle=True)
        f2 = copy.copy(f)
        if spec.get("label"):
            f2.label = spec["label"]
        row = col.row(align=True)
        row.enabled = bool(getattr(pg, m.en_key))
        if spec.get("widget") == "texture" and f.type in ("ref", "string"):
            row.prop(pg, f.key, text=f2.label)
            _op(row, "tm_fx.pick_texture", "", "FILEBROWSER", path=path, key=f.key)
        else:
            draw_field(row, pg, f2, settings, path)


class TMFX_UL_targets(bpy.types.UIList):
    """Outline filtered to the classes that layout.json has sections for."""

    def draw_item(self, context, layout_ui, data, item, icon, active_data, active_propname):
        try:
            title = bridge.row_title(bridge.resolve(data, item.path), get_schema()[item.cls], item.label)
        except Exception:
            title = item.cls
        layout_ui.label(text=title, icon="PARTICLES")

    def filter_items(self, context, data, propname):
        wanted = layout.targets()
        flags = [self.bitflag_filter_item if it.cls in wanted else 0 for it in getattr(data, propname)]
        return flags, []


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
    bl_category, bl_space_type, bl_region_type = "Blendermania", "VIEW_3D", "UI"

    @classmethod
    def poll(cls, context):
        return settings_of(context) is not None


class TMFX_PT_main(_Panel, bpy.types.Panel):
    bl_label, bl_idname = "TM Item FX", "TMFX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        s = settings_of(context)
        lay = self.layout
        lay.prop(s, "enabled", text="Particle effect node")
        if not s.enabled:
            lay.label(text="Tick to edit/export FX on this object", icon="INFO")
            return
        row = lay.row(align=True)
        row.operator("tm_fx.import_json", text="Import", icon="IMPORT")
        row.operator("tm_fx.export_json", text="Export", icon="EXPORT")
        row = lay.row(align=True)
        row.label(text="Template: " + ("set" if s.template_json else "none"))
        _op(row, "tm_fx.template", "Use current", action="SET")
        _op(row, "tm_fx.template", "", "X", action="CLEAR")
        row = lay.row(align=True)
        row.prop(s, "mode", expand=True)
        lay.prop(s, "search", icon="VIEWZOOM")


class TMFX_PT_particle(_Panel, bpy.types.Panel):
    """Simple UI, driven by layout.json."""
    bl_label, bl_idname, bl_parent_id = "Particle", "TMFX_PT_particle", "TMFX_PT_main"

    @classmethod
    def poll(cls, context):
        s = settings_of(context)
        return False
        return s is not None and s.enabled

    def draw(self, context):
        s = settings_of(context)
        lay = self.layout
        data = layout.load()

        row = lay.row()
        row.template_list("TMFX_UL_targets", "", s, "outline", s, "outline_index", rows=4)
        col = row.column(align=True)
        plist = next((f for f in get_schema()[ROOT_CLASS].fields if f.ref == "CPlugVFXFile.Parameter"), None)
        if plist is not None:
            _op(col, "tm_fx.add", "", "ADD", path="vfx", key=plist.key, preset=True)
        for a, ic in (("REMOVE", "REMOVE"), ("DUPLICATE", "DUPLICATE")):
            _op(col, "tm_fx.item", "", ic, action=a)
        col.separator()
        _op(col, "tm_fx.reload_layout", "", "FILE_REFRESH")

        if data["error"]:
            lay.label(text=data["error"], icon="ERROR")
            return
        try:
            pg = bridge.resolve(s, s.selected_path)
            cls = class_name_of(pg)
        except (AttributeError, IndexError, KeyError):
            lay.label(text="Add or select an emitter", icon="INFO")
            return
        cs = get_schema()[cls]
        secs = [x for x in data["sections"] if x["target"] == cls]
        if not secs:
            lay.label(text=f"No layout for {cls}: select an item in the list", icon="INFO")
        for sec in secs:
            draw_layout_section(lay, pg, cs, s, s.selected_path, sec)


class TMFX_PT_tree(_Panel, bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Advanced: structure", "TMFX_PT_tree", "TMFX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        s = settings_of(context)
        return s is not None and s.enabled

    def draw(self, context):
        s = settings_of(context)
        row = self.layout.row()
        row.template_list("TMFX_UL_outline", "", s, "outline", s, "outline_index", rows=6)
        col = row.column(align=True)
        for a, ic in (("REMOVE", "REMOVE"), ("DUPLICATE", "DUPLICATE"), ("UP", "TRIA_UP"), ("DOWN", "TRIA_DOWN")):
            _op(col, "tm_fx.item", "", ic, action=a)


class TMFX_PT_node(_Panel, bpy.types.Panel):
    bl_label, bl_idname, bl_parent_id = "Advanced: selected node (all fields)", "TMFX_PT_node", "TMFX_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        s = settings_of(context)
        return s is not None and s.enabled

    def draw(self, context):
        s = settings_of(context)
        try:
            pg = bridge.resolve(s, s.selected_path)
        except (AttributeError, IndexError):
            s.selected_path = "vfx"
            return
        draw_node(self.layout, pg, s, s.selected_path)


_CLASSES = (TMFX_UL_outline, TMFX_UL_targets, TMFX_PT_main, TMFX_PT_particle, TMFX_PT_tree, TMFX_PT_node)


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
