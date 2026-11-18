import json
import re

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import bridge, codec, curves
from .codec import ROOT_CLASS
from .props import class_name_of, get_schema, settings_of

_ITEM = re.compile(r"^(.*)\.(\w+)\[(\d+)\]$")


def _s(context):
    return settings_of(context)


def _select(settings, path):
    settings.selected_path = path
    bridge.rebuild_outline(settings)


class _Base(bpy.types.Operator):
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return settings_of(context) is not None


class TMFX_OT_import(_Base, ImportHelper):
    """Load a tm-fx/1 document (root CPlugFxSystem), e.g. dumped from a working item"""
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


class TMFX_OT_import_gbx(_Base, ImportHelper):
    """Load a particle GBX from the game (*.ParticleModel.Gbx emitter or *.FxSys.Gbx), e.g. from a pak extract.
    Bitmaps are matched to bitmap assets by name; other references are left empty"""
    bl_idname, bl_label = "tm_fx.import_gbx", "Import Particle GBX"
    filter_glob: StringProperty(default="*.Gbx;*.gbx", options={"HIDDEN"})
    as_template: BoolProperty(name="Use as template", default=True,
                              description="Changed values are highlighted relative to this file")

    def execute(self, context):
        import os
        import tempfile
        from ..utils.Dotnet import run_convert_fx_to_json

        out = os.path.join(tempfile.gettempdir(), "tm_fx_import.json")
        res = run_convert_fx_to_json(self.filepath, out)
        if not res.success:
            self.report({"ERROR"}, res.message[:400])
            return {"CANCELLED"}
        with open(out, encoding="utf-8") as fh:
            data = json.load(fh)
        try:
            os.remove(out)
        except OSError:
            pass
        schema = get_schema()
        root = data.get("vfx", data)
        if root.get("$class") == "CPlugParticleEmitterModel":
            name = os.path.basename(self.filepath).split(".")[0]
            root = codec.wrap_emitter(schema, root, name)
        elif root.get("$class") != ROOT_CLASS:
            self.report({"ERROR"}, f"{root.get('$class')} is not a particle emitter or fx system")
            return {"CANCELLED"}
        warnings = [line[len("WARNING: "):] for line in res.stdout.splitlines() if line.startswith("WARNING: ")]
        warnings += bridge.import_document(_s(context), {"vfx": root}, self.as_template)
        for w in warnings[:8]:
            self.report({"WARNING"}, w)
        self.report({"INFO"}, f"Imported {os.path.basename(self.filepath)}"
                              + (f" ({len(warnings)} warnings, see console)" if warnings else ""))
        for w in warnings:
            print("tm_fx import:", w)
        return {"FINISHED"}


class TMFX_OT_export(_Base, ExportHelper):
    """Save the fx document as it is written to the item config (bitmaps as asset names)"""
    bl_idname, bl_label = "tm_fx.export_json", "Export FX JSON"
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        doc = bridge.export_document(_s(context))
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
        s.template_json = json.dumps(bridge.read_node(s.vfx, ROOT_CLASS)) if self.action == "SET" else ""
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
        if f.boxed and len(coll):              # single child: at most one item
            _select(s, f"{self.path}.{self.key}[0]")
            return {"FINISHED"}
        item = coll.add()
        if self.preset:   # structure only, values are schema defaults
            wire = codec.preset_emitter_node(schema, f"Emitter{len(coll)}")
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
                parent_pg = bridge.resolve(s, parent)
                if hasattr(parent_pg, "on_" + key):    # inline structs can not be removed
                    setattr(parent_pg, "on_" + key, False)
                    _select(s, parent)
            return {"FINISHED"}
        parent_path, key, i = m.group(1), m.group(2), int(m.group(3))
        parent = bridge.resolve(s, parent_path)
        coll = getattr(parent, key)
        f = schema[class_name_of(parent)].field(key)
        if f.boxed and self.action != "REMOVE":   # single child: nothing to duplicate or move
            return {"FINISHED"}
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


_CLASSES = (TMFX_OT_import, TMFX_OT_import_gbx, TMFX_OT_export, TMFX_OT_template, TMFX_OT_add, TMFX_OT_item,
            TMFX_OT_reset, TMFX_OT_edit, TMFX_OT_goto)


def register():
    for c in _CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_CLASSES):
        bpy.utils.unregister_class(c)
