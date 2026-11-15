import json
import re

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import bridge, codec, curves
from .props import class_name_of, get_schema, settings_of

_ITEM = re.compile(r"^(.*)\.(\w+)\[(\d+)\]$")


def _s(context):
    return settings_of(context)


def _select(settings, path):
    settings.selected_path = path
    bridge.rebuild_outline(settings)


class _Base(bpy.types.Operator):
    bl_options = {"REGISTER", "UNDO"}


class TMFX_OT_import(_Base, ImportHelper):
    bl_idname, bl_label = "tm_fx.import_json", "Import FX JSON"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})
    as_template: BoolProperty(name="Use as template", default=True,
                              description="Changed values are highlighted relative to this file")

    def execute(self, context):
        with open(self.filepath, encoding="utf-8") as fh:
            data = json.load(fh)
        for w in bridge.import_document(_s(context), data, self.as_template)[:8]:
            self.report({"WARNING"}, w)
        return {"FINISHED"}


class TMFX_OT_export(_Base, ExportHelper):
    bl_idname, bl_label = "tm_fx.export_json", "Export FX JSON"
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        doc = bridge.export_document(_s(context))
        if doc is None:
            self.report({"ERROR"}, "FX export is disabled")
            return {"CANCELLED"}
        for p in codec.validate(get_schema(), doc["vfx"])[:8]:
            self.report({"WARNING"}, p)
        with open(self.filepath, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        return {"FINISHED"}


class TMFX_OT_template(_Base):
    bl_idname, bl_label = "tm_fx.template", "Template"
    action: EnumProperty(items=[("SET", "Set", ""), ("CLEAR", "Clear", "")])

    def execute(self, context):
        s = _s(context)
        s.template_json = json.dumps(bridge.read_node(s.vfx, "CPlugVFXFile")) if self.action == "SET" else ""
        return {"FINISHED"}


class TMFX_OT_add(_Base):
    bl_idname, bl_label = "tm_fx.add", "Add"
    path: StringProperty()
    key: StringProperty()
    preset: BoolProperty(default=False)

    def execute(self, context):
        s, schema = _s(context), get_schema()
        pg = bridge.resolve(s, self.path)
        cs = schema[class_name_of(pg)]
        f = cs.field(self.key)
        coll, warn = getattr(pg, self.key), []
        item = coll.add()
        if self.preset:
            wire = codec.preset_gpu_emitter(schema, f"Emitter{len(coll)}")
        else:
            wire = codec.new_item_wire(schema, f.ref)
        (bridge.write_node if schema[f.ref].kind == "node" else bridge.write_struct)(item, f.ref, wire, warn)
        _select(s, f"{self.path}.{self.key}[{len(coll) - 1}]")
        return {"FINISHED"}


class TMFX_OT_item(_Base):
    """Remove / duplicate / move the selected outline item."""
    bl_idname, bl_label = "tm_fx.item", "Item"
    action: EnumProperty(items=[(a, a.title(), "") for a in ("REMOVE", "DUPLICATE", "UP", "DOWN")])

    def execute(self, context):
        s, schema = _s(context), get_schema()
        m = _ITEM.match(s.selected_path)
        if not m:
            if self.action == "REMOVE" and s.selected_path != "vfx":   # single child node: switch it off
                parent, key = s.selected_path.rsplit(".", 1)
                setattr(bridge.resolve(s, parent), "on_" + key, False)
                _select(s, parent)
            return {"FINISHED"}
        parent_path, key, i = m.group(1), m.group(2), int(m.group(3))
        parent = bridge.resolve(s, parent_path)
        coll = getattr(parent, key)
        f = schema[class_name_of(parent)].field(key)
        if self.action == "REMOVE":
            coll.remove(i)
            _select(s, parent_path)
        elif self.action == "DUPLICATE":
            kind = schema[f.ref].kind
            read = bridge.read_node if kind == "node" else bridge.read_struct
            write = bridge.write_node if kind == "node" else bridge.write_struct
            wire = read(coll[i], f.ref)
            write(coll.add(), f.ref, wire, [])
            coll.move(len(coll) - 1, i + 1)
            _select(s, f"{parent_path}.{key}[{i + 1}]")
        else:
            j = i - 1 if self.action == "UP" else i + 1
            if 0 <= j < len(coll):
                coll.move(i, j)
                _select(s, f"{parent_path}.{key}[{j}]")
        return {"FINISHED"}


class TMFX_OT_reset(_Base):
    bl_idname, bl_label = "tm_fx.reset", "Reset to template/default"
    path: StringProperty()
    key: StringProperty()

    def execute(self, context):
        s = _s(context)
        pg = bridge.resolve(s, self.path)
        f = get_schema()[class_name_of(pg)].field(self.key)
        bridge.set_value(pg, f, bridge.baseline(s, self.path, f))
        return {"FINISHED"}


class TMFX_OT_edit(_Base):
    """Add/remove entries of curves and scalar lists."""
    bl_idname, bl_label = "tm_fx.edit", "Edit list"
    path: StringProperty()
    key: StringProperty()
    action: EnumProperty(items=[(a, a.title(), "") for a in ("ADD", "REMOVE", "SORT")])

    def execute(self, context):
        pg = bridge.resolve(_s(context), self.path)
        f = get_schema()[class_name_of(pg)].field(self.key)
        if f.type == "curve":
            c = getattr(pg, self.key)
            if self.action == "ADD":
                curves.create(c)
            elif self.action == "REMOVE":
                curves.clear(c)
        else:
            coll = getattr(pg, self.key)
            coll.add() if self.action == "ADD" else (coll.remove(len(coll) - 1) if len(coll) else None)
        return {"FINISHED"}


class TMFX_OT_goto(_Base):
    bl_idname, bl_label = "tm_fx.goto", "Open in outline"
    path: StringProperty()

    def execute(self, context):
        _select(_s(context), self.path)
        return {"FINISHED"}


class TMFX_OT_pick_texture(_Base, ImportHelper):
    """Pick a texture/material file for a ref or string field."""
    bl_idname, bl_label = "tm_fx.pick_texture", "Pick texture"
    filter_glob: StringProperty(default="*.dds;*.png;*.jpg;*.jpeg;*.tga;*.tif;*.webp;*.gbx;*.txt", options={"HIDDEN"})
    path: StringProperty(options={"HIDDEN"})
    key: StringProperty(options={"HIDDEN"})
    relative: BoolProperty(name="Game relative", default=True,
                           description="Strip everything before Work/Skins/Media folders (path as the game expects it)")

    _MARKERS = ("/work/", "/skins/", "/media/")

    def _convert(self, p):
        p = p.replace("\\", "/")
        if self.relative:
            low = p.lower()
            for m in self._MARKERS:
                i = low.find(m)
                if i >= 0:
                    return p[i + 1:]
        return p

    def execute(self, context):
        pg = bridge.resolve(_s(context), self.path)
        f = get_schema()[class_name_of(pg)].field(self.key)
        setattr(pg, f.key, self._convert(self.filepath))
        if f.key == "BitmapFile" and hasattr(pg, "BitmapIsFile"):
            pg.BitmapIsFile = True
        return {"FINISHED"}


class TMFX_OT_reload_layout(_Base):
    bl_idname, bl_label = "tm_fx.reload_layout", "Reload layout.json"

    def execute(self, context):
        from . import layout
        data = layout.load(force=True)
        if data["error"]:
            self.report({"ERROR"}, data["error"])
            return {"CANCELLED"}
        self.report({"INFO"}, f"{len(data['sections'])} sections loaded")
        return {"FINISHED"}


_CLASSES = (TMFX_OT_import, TMFX_OT_export, TMFX_OT_template, TMFX_OT_add, TMFX_OT_item,
            TMFX_OT_reset, TMFX_OT_edit, TMFX_OT_goto, TMFX_OT_pick_texture, TMFX_OT_reload_layout)


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
