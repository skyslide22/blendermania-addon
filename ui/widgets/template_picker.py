"""
Shared template picker, save and manage operators for every template kind (utils/TemplateLibrary.py).

Context pointers (set by the drawing code, only present during invoke):
    tm_placement      PlacementProperties  - placement insert / save, placement class insert / save
    tm_placement_ref  PlacementPropertiesRef - placement assignment by name
Particle fx use the active particle fx empty.
"""
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator

from ...utils import TemplateLibrary as TL

ACTIONS = [("ASSIGN", "Assign", "Use the template by name (placement parameters)"),
           ("INSERT", "Insert", "Copy the template's values"),
           ("ADD", "Add", "Add the template's emitters to the current effect")]

_items_cache: list = []        # Blender keeps no reference to dynamic enum strings
_target: dict = {}             # context pointers of the running pick (only in the context during invoke)


def _owner(context, key):
    return getattr(context, key, None) or _target.get(key)


def _fx_settings(context):
    from ...FX.props import settings_of
    return settings_of(context)


# ------------------------------------------------------------------ items per kind
def template_items(kind: str) -> list:
    """(id, label, description, icon, number) for a picker"""
    items = []
    if kind == TL.KIND_PLACEMENT:
        from ...utils.ItemsExportV2Models import list_placement_templates
        for tid, source, _t in list_placement_templates():
            items.append((tid, tid, TL.SOURCE_LABELS[source], TL.SOURCE_ICONS[source]))
    else:
        for e in TL.file_entries(kind):
            items.append((e.id, e.label, TL.SOURCE_LABELS[e.source], TL.SOURCE_ICONS[e.source]))
    return [(i, lbl, desc, icon, n) for n, (i, lbl, desc, icon) in enumerate(items)]


def _pick_items(self, context):
    global _items_cache
    _items_cache = template_items(self.kind) or [("NONE", "No templates", "", "INFO", 0)]
    return _items_cache


def _local_data(kind: str, context):
    """data of the current thing for 'save as local template', or (None, error)"""
    if kind == TL.KIND_PLACEMENT:
        placement = _owner(context, "tm_placement")
        if placement is None:
            return None, "No placement in context"
        from ...utils.FunctionsV2 import props_to_dict
        return props_to_dict(placement), ""
    if kind == TL.KIND_PLACEMENT_CLASS:
        placement = _owner(context, "tm_placement")
        if placement is None:
            return None, "No placement in context"
        from ...utils.Placement import placement_class_dict
        return placement_class_dict(placement), ""
    if kind == TL.KIND_PARTICLE_FX:
        s = _fx_settings(context)
        if s is None:
            return None, "Select a particle fx empty"
        from ...FX import bridge
        return bridge.export_document(s), ""
    return None, f"Unknown template kind {kind}"


def _after_local_change(kind: str):
    if kind == TL.KIND_PLACEMENT:
        from ...operators.OT_Settings import reload_local_placement_templates
        reload_local_placement_templates()


def _redraw(context):
    for area in context.screen.areas if context.screen else []:
        area.tag_redraw()


# ------------------------------------------------------------------ operators
class TM_OT_TemplatePick(Operator):
    bl_idname = "tm.template_pick"
    bl_label = "Choose Template"
    bl_description = "Search templates (built-in, local and blend file) and use one"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_property = "choice"

    kind: StringProperty(options={"HIDDEN"})
    action: EnumProperty(items=ACTIONS, options={"HIDDEN"})
    choice: EnumProperty(name="Template", items=_pick_items)

    def invoke(self, context, event):
        _target.clear()
        for key in ("tm_placement", "tm_placement_ref"):
            v = getattr(context, key, None)
            if v is not None:
                _target[key] = v
        if self.kind == TL.KIND_PARTICLE_FX and _fx_settings(context) is None:
            self.report({"ERROR"}, "Select a particle fx empty")
            return {"CANCELLED"}
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if self.choice == "NONE":
            return {"CANCELLED"}
        try:
            msg = self._apply(context)
        except Exception as e:   # template files are user data: report instead of failing silently
            self.report({"ERROR"}, f"Template '{self.choice}' could not be used: {e}")
            return {"CANCELLED"}
        finally:
            _target.clear()
        if msg:
            self.report({"WARNING"}, msg)
        _redraw(context)
        return {"FINISHED"}

    def _apply(self, context) -> str:
        if self.kind == TL.KIND_PLACEMENT:
            from ...utils.ItemsExportV2Models import load_itemconfig_placement_template
            if self.action == "ASSIGN":
                ref = _owner(context, "tm_placement_ref")
                if ref is None:
                    raise RuntimeError("no placement reference")
                ref.template_name = self.choice
            else:
                load_itemconfig_placement_template(_owner(context, "tm_placement"), self.choice)
            return ""
        entry = TL.find_entry(self.kind, self.choice)
        if entry is None:
            raise RuntimeError("template not found")
        data = TL.read(entry)
        if self.kind == TL.KIND_PLACEMENT_CLASS:
            from ...utils.Placement import apply_placement_class_dict
            apply_placement_class_dict(_owner(context, "tm_placement"), data)
            return ""
        if self.kind == TL.KIND_PARTICLE_FX:
            from ...FX import templates as fx_templates
            warnings = fx_templates.apply(_fx_settings(context), data, add=self.action == "ADD")
            for w in warnings:
                print("tm template:", w)
            return f"{len(warnings)} warning(s), see console: {warnings[0]}" if warnings else ""
        raise RuntimeError(f"unknown kind {self.kind}")


class TM_OT_TemplateSaveLocal(Operator):
    bl_idname = "tm.template_save_local"
    bl_label = "Save as Local Template"
    bl_description = "Save the current values as a template on this computer (not in the blend file)"
    bl_options = {"REGISTER", "INTERNAL"}

    kind: StringProperty(options={"HIDDEN"})
    template_name: StringProperty(name="Name")
    overwrite: BoolProperty(name="Overwrite existing", default=False)

    def invoke(self, context, event):
        data, err = _local_data(self.kind, context)
        if data is None:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self._data = data
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        lay = self.layout
        lay.label(text=TL.KIND_LABELS.get(self.kind, self.kind), icon=TL.SOURCE_ICONS[TL.SOURCE_LOCAL])
        lay.prop(self, "template_name")
        if self.template_name.strip() and TL.find_local(self.kind, self.template_name.strip()):
            lay.label(text="A local template with this name exists.", icon="ERROR")
            lay.prop(self, "overwrite")

    def execute(self, context):
        data = getattr(self, "_data", None)
        if data is None:
            data, err = _local_data(self.kind, context)
            if data is None:
                self.report({"ERROR"}, err)
                return {"CANCELLED"}
        name = self.template_name.strip()
        if not name:
            self.report({"ERROR"}, "Name cannot be empty")
            return {"CANCELLED"}
        if TL.find_local(self.kind, name) and not self.overwrite:
            self.report({"ERROR"}, f"'{name}' already exists locally (tick Overwrite)")
            return {"CANCELLED"}
        path = TL.save_local(self.kind, name, data)
        _after_local_change(self.kind)
        self.report({"INFO"}, f"Saved local template '{name}' ({path})")
        _redraw(context)
        return {"FINISHED"}


class TM_OT_TemplateDeleteLocal(Operator):
    bl_idname = "tm.template_delete_local"
    bl_label = "Delete Local Template"
    bl_description = "Delete this template from this computer (built-in and blend file templates are not affected)"
    bl_options = {"REGISTER", "INTERNAL"}

    kind: StringProperty(options={"HIDDEN"})
    template_name: StringProperty(options={"HIDDEN"})

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event, message=f"Delete local template '{self.template_name}'?")

    def execute(self, context):
        if not TL.delete_local(self.kind, self.template_name):
            self.report({"ERROR"}, f"No local template '{self.template_name}'")
            return {"CANCELLED"}
        _after_local_change(self.kind)
        _redraw(context)
        return {"FINISHED"}


class TM_OT_TemplateOpenFolder(Operator):
    bl_idname = "tm.template_open_folder"
    bl_label = "Open Local Template Folder"
    bl_description = "Open the folder with this computer's templates (files can be copied to other computers)"
    bl_options = {"INTERNAL"}

    kind: StringProperty(options={"HIDDEN"})

    def execute(self, context):
        bpy.ops.wm.path_open(filepath=TL.local_dir(self.kind, create=True))
        return {"FINISHED"}


class TM_OT_TemplateManageLocal(Operator):
    bl_idname = "tm.template_manage_local"
    bl_label = "Local Templates"
    bl_description = "List, delete and open this computer's templates of this kind"
    bl_options = {"INTERNAL"}

    kind: StringProperty(options={"HIDDEN"})

    def invoke(self, context, event):
        kind = self.kind

        def draw(menu, _context):
            lay = menu.layout
            entries = TL.local_entries(kind)
            if not entries:
                lay.label(text="No local templates yet", icon="INFO")
            for e in entries:
                op = lay.operator(TM_OT_TemplateDeleteLocal.bl_idname, text=e.name, icon="TRASH")
                op.kind, op.template_name = kind, e.name
            lay.separator()
            lay.operator(TM_OT_TemplateOpenFolder.bl_idname, icon="FILE_FOLDER").kind = kind

        context.window_manager.popup_menu(draw, title=f"Local {TL.KIND_LABELS.get(kind, kind)} Templates")
        return {"FINISHED"}


def draw_template_buttons(layout, kind: str, action: str = "INSERT", text: str = "Insert Template...",
                          save: bool = True, manage: bool = True):
    """picker button (+ save local / manage local); set context pointers on ``layout`` before calling"""
    row = layout.row(align=True)
    op = row.operator(TM_OT_TemplatePick.bl_idname, text=text, icon="IMPORT")
    op.kind, op.action = kind, action
    if save:
        row.operator(TM_OT_TemplateSaveLocal.bl_idname, text="", icon="FILE_NEW").kind = kind
    if manage:
        row.operator(TM_OT_TemplateManageLocal.bl_idname, text="", icon="PRESET").kind = kind
    return row


classes = (TM_OT_TemplatePick, TM_OT_TemplateSaveLocal, TM_OT_TemplateDeleteLocal, TM_OT_TemplateOpenFolder,
           TM_OT_TemplateManageLocal)
