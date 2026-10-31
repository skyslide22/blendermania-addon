import re
import bpy
from ...utils.Constants import *


# =============================================================================
# 2. LIST CORE (shared by both list modules)
#    Owner resolving, hooks, and the helper that fills operator properties.
# =============================================================================

LIST_HOOKS = {}

def register_list_hooks(owner_cls, collection, before_add=None, after_add=None,
                        before_remove=None, after_remove=None):
    LIST_HOOKS[(owner_cls.bl_rna.identifier, collection)] = {
        "before_add": before_add,
        "after_add": after_add,
        "before_remove": before_remove,
        "after_remove": after_remove,
    }

def unregister_list_hooks(owner_cls, collection):
    LIST_HOOKS.pop((owner_cls.bl_rna.identifier, collection), None)

def _resolve(context, owner_path):
    if not owner_path:
        return context.scene
    return context.scene.path_resolve(owner_path)

def _hooks(owner, collection):
    return LIST_HOOKS.get((owner.bl_rna.identifier, collection), {})


def _op(layout, idname, owner, collection, *,
        text="", icon='NONE', emboss=True,
        index_owner=None, index_prop="", **kw):
    """Draws an operator button. The owner objects are passed through the
    layout's context, so the operator receives real objects, not paths."""
    layout.context_pointer_set("tm_list_owner", owner)
    layout.context_pointer_set("tm_list_index_owner",
                               owner if index_owner is None else index_owner)

    op = layout.operator(idname, text=text or "", icon=icon or 'NONE', emboss=emboss)
    op.collection = collection
    op.index_prop = index_prop or ""
    for k, v in kw.items():
        setattr(op, k, v)
    return op

def _snapshot(item):
    """Stores values in a temporary scene-independent dict clipboard."""
    data = {}
    for prop in item.bl_rna.properties:
        pid = prop.identifier
        if pid == "rna_type":
            continue
        if prop.type == 'COLLECTION':
            data[pid] = [_snapshot(s) for s in getattr(item, pid)]
        elif prop.type == 'POINTER':
            sub = getattr(item, pid)
            if sub is not None and not isinstance(sub, bpy.types.ID):
                data[pid] = _snapshot(sub)
            elif prop.is_readonly is False:
                data[pid] = sub
        elif not prop.is_readonly:
            value = getattr(item, pid)
            if hasattr(value, "__len__") and not isinstance(value, str):
                value = tuple(value)
            data[pid] = value
    return data


def _restore(item, data, skip=()):
    for pid, value in data.items():
        if pid in skip:
            continue
        prop = item.bl_rna.properties.get(pid)
        if prop is None:
            continue
        try:
            if prop.type == 'COLLECTION':
                coll = getattr(item, pid)
                coll.clear()
                for d in value:
                    _restore(coll.add(), d)
            elif isinstance(value, dict):
                _restore(getattr(item, pid), value)
            else:
                setattr(item, pid, value)
        except (AttributeError, TypeError, ValueError):
            pass


LIST_CLIPBOARD = {"type": None, "data": None}

# =============================================================================
#    LIST OPERATORS (registered)
#    Generic add/remove used by every list.
# =============================================================================

def _make_name_unique(items, item):
    """Increments a trailing number (or appends one) until the name is unique."""
    if "name" not in item.bl_rna.properties or item.bl_rna.properties["name"].is_readonly:
        return
    used = {i.name for i in items if i != item}
    name = item.name
    if name not in used:
        return
    m = re.match(r"^(.*?)(\d+)$", name)
    base, num, width = (m.group(1), int(m.group(2)), len(m.group(2))) if m else (name + "_", 0, 1)
    while name in used:
        num += 1
        name = f"{base}{num:0{width}d}"
    item.name = name


WIDGET_NEW_ENTRY_MODE_NONE = "NONE"
WIDGET_NEW_ENTRY_MODE_LAST = "LAST"
WIDGET_NEW_ENTRY_MODE_SELECTED = "SELECTED"

class TM_OT_List_Add(bpy.types.Operator):
    bl_idname = "tm.list_add"
    bl_label = "Add"
    bl_options = {'UNDO'}

    collection: bpy.props.StringProperty()
    index_prop: bpy.props.StringProperty()
    open_prop: bpy.props.StringProperty()
    copy_from: bpy.props.EnumProperty(
        items=[(WIDGET_NEW_ENTRY_MODE_NONE, "None", ""), (WIDGET_NEW_ENTRY_MODE_SELECTED, "Selected", ""), (WIDGET_NEW_ENTRY_MODE_LAST, "Last", "")],
        default=WIDGET_NEW_ENTRY_MODE_NONE)

    def execute(self, context):
        owner = getattr(context, "tm_list_owner", None)
        index_owner = getattr(context, "tm_list_index_owner", None)
        if owner is None:
            return {'CANCELLED'}

        items = getattr(owner, self.collection)
        hooks = _hooks(owner, self.collection)

        if (hook := hooks.get("before_add")) and hook(owner) is False:
            return {'CANCELLED'}

        source = None
        if len(items) > 0 and self.copy_from != WIDGET_NEW_ENTRY_MODE_NONE:
            src_i = len(items) - 1
            if self.copy_from == WIDGET_NEW_ENTRY_MODE_SELECTED and self.index_prop and index_owner is not None:
                sel = getattr(index_owner, self.index_prop)
                if 0 <= sel < len(items):
                    src_i = sel
            source = items[src_i]
            snapshot = _snapshot(source)

        item = items.add()
        index = len(items) - 1
        if source is not None:
            _restore(item, snapshot)
            _make_name_unique(items, item)

        if hook := hooks.get("after_add"):
            hook(owner, item, index)

        if self.index_prop and index_owner is not None:
            setattr(index_owner, self.index_prop, index)
        if self.open_prop:
            setattr(owner, self.open_prop, True)
        return {'FINISHED'}


class TM_OT_List_Remove(bpy.types.Operator):
    bl_idname = "tm.list_remove"
    bl_label = "Remove"
    bl_options = {'UNDO'}

    collection: bpy.props.StringProperty()
    index_prop: bpy.props.StringProperty()
    index: bpy.props.IntProperty(default=-1)   # -1 = use the active index

    def execute(self, context):
        owner = getattr(context, "tm_list_owner", None)
        index_owner = getattr(context, "tm_list_index_owner", None)
        if owner is None:
            return {'CANCELLED'}

        items = getattr(owner, self.collection)
        hooks = _hooks(owner, self.collection)

        i = self.index
        if i < 0 and self.index_prop and index_owner is not None:
            i = getattr(index_owner, self.index_prop)
        if not (0 <= i < len(items)):
            return {'CANCELLED'}

        if (hook := hooks.get("before_remove")) and hook(owner, items[i], i) is False:
            return {'CANCELLED'}

        items.remove(i)

        if self.index_prop and index_owner is not None:
            active = getattr(index_owner, self.index_prop)
            if i < active:
                active -= 1                     # keep the same item active
            setattr(index_owner, self.index_prop, max(0, min(active, len(items) - 1)))

        if hook := hooks.get("after_remove"):
            hook(owner, i)
        return {'FINISHED'}


class TM_OT_List_Move(bpy.types.Operator):
    bl_idname = "tm.list_move"
    bl_label = "Move"
    bl_options = {'UNDO'}

    collection: bpy.props.StringProperty()
    index_prop: bpy.props.StringProperty()
    index: bpy.props.IntProperty(default=-1)   # -1 = use the active index
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        owner = getattr(context, "tm_list_owner", None)
        index_owner = getattr(context, "tm_list_index_owner", None)
        if owner is None:
            return {'CANCELLED'}

        items = getattr(owner, self.collection)
        i = self.index
        if i < 0 and self.index_prop and index_owner is not None:
            i = getattr(index_owner, self.index_prop)
        j = i - 1 if self.direction == 'UP' else i + 1
        if not (0 <= i < len(items) and 0 <= j < len(items)):
            return {'CANCELLED'}

        items.move(i, j)
        if self.index_prop and index_owner is not None \
                and getattr(index_owner, self.index_prop) == i:
            setattr(index_owner, self.index_prop, j)
        return {'FINISHED'}


class TM_OT_List_Clipboard(bpy.types.Operator):
    bl_idname = "tm.list_clipboard"
    bl_label = "Copy / Paste"
    bl_options = {'UNDO'}

    action: bpy.props.EnumProperty(
        items=[('COPY', "Copy Entry", "Copy the entry values"),
               ('PASTE', "Paste Entry Values", "Paste copied values onto the entry")])

    def execute(self, context):
        item = getattr(context, "tm_list_item", None)
        if item is None:
            return {'CANCELLED'}

        type_id = item.bl_rna.identifier
        if self.action == 'COPY':
            LIST_CLIPBOARD["type"] = type_id
            LIST_CLIPBOARD["data"] = _snapshot(item)
            return {'FINISHED'}

        if LIST_CLIPBOARD["type"] != type_id:
            self.report({'WARNING'}, "Clipboard is empty or from a different entry type")
            return {'CANCELLED'}
        _restore(item, LIST_CLIPBOARD["data"], skip=("name",))
        return {'FINISHED'}

# =============================================================================
# MODULE 1: LIST + INSPECTOR (Blender UIList)
# =============================================================================

ROW_DRAWERS = {}   # PropertyGroup class name -> fn(layout, item, index)

def register_row_drawer(prop_group_cls, fn):
    ROW_DRAWERS[prop_group_cls.__name__] = fn

def unregister_row_drawer(prop_group_cls):
    ROW_DRAWERS.pop(prop_group_cls.__name__, None)

class TM_UL_Generic(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        fn = ROW_DRAWERS.get(item.bl_rna.identifier)
        if fn:
            fn(layout, item, index)
        elif hasattr(item, "name"):
            layout.prop(item, "name", text="", emboss=False)
        else:
            layout.label(text=f"Item {index + 1}")

       

def _list_id(owner, collection):
    """Unique per list instance, also for ID owners (Collection, Object...)."""
    uid = getattr(owner, "session_uid", None)   # ID datablocks (Collection, Object...)
    return f"TM_{collection}_{uid}" if uid is not None else f"TM_{collection}"

class TM_MT_List_Clipboard(bpy.types.Menu):
    bl_idname = "TM_MT_List_Clipboard"
    bl_label = "Entry"

    def draw(self, context):
        # the item comes from the context pointer set on the button's layout
        self.layout.operator("tm.list_clipboard", text="Copy Entry",
                             icon='COPYDOWN').action = 'COPY'
        self.layout.operator("tm.list_clipboard", text="Paste Entry Values",
                             icon='PASTEDOWN').action = 'PASTE'


def _clipboard_menu(layout, item):
    sub = layout.column(align=True)
    sub.context_pointer_set("tm_list_item", item)
    sub.menu("TM_MT_List_Clipboard", text="", icon='DOWNARROW_HLT')


def list_inspector(layout, owner, collection, index_prop, index_owner=None,
                   draw_detail=None, draw_footer=None, rows=4,
                   show_move=False, copy_on_add=None, show_clipboard=False):
    """Blender list with add/remove column. draw_detail(layout, item, index)
    draws the active item below. draw_footer(layout) draws a fixed non-data row
    under the list. index_owner: where index_prop lives (defaults to owner)."""
    if index_owner is None:
        index_owner = owner

    row = layout.row()

    left = row.column(align=True)              # list and footer stack vertically
    left.template_list("TM_UL_Generic", _list_id(owner, collection),
                       owner, collection, index_owner, index_prop, rows=rows)
    if draw_footer:
        items = getattr(owner, collection)
        last_index = len(items) - 1
        last_item = items[last_index] if last_index >= 0 else None

        footer = left.box()
        footer.enabled = False
        draw_footer(footer, last_item, last_index)

    col = row.column(align=True)
    _op(col, "tm.list_add", owner, collection, icon='ADD',
        index_owner=index_owner, index_prop=index_prop,
        copy_from=copy_on_add or 'NONE')
    _op(col, "tm.list_remove", owner, collection, icon='REMOVE',
        index_owner=index_owner, index_prop=index_prop)
    items = getattr(owner, collection)
    i = getattr(index_owner, index_prop)
    if show_clipboard and 0 <= i < len(items):
        col.separator()
        _clipboard_menu(col, items[i])
    if show_move and len(items) >= 2:
        col.separator()
        _op(col, "tm.list_move", owner, collection, icon='TRIA_UP',
            index_owner=index_owner, index_prop=index_prop, direction='UP')
        _op(col, "tm.list_move", owner, collection, icon='TRIA_DOWN',
            index_owner=index_owner, index_prop=index_prop, direction='DOWN')

    if draw_detail:
        items = getattr(owner, collection)
        i = getattr(index_owner, index_prop)
        if 0 <= i < len(items):
            draw_detail(layout, items[i], i)

# =============================================================================
# MODULE 2: DIRECT-EDIT LIST (plain functions)
# =============================================================================

WIDGET_ADD_BUTTON_NONE = None
WIDGET_ADD_BUTTON_TOP = 'TOP'
WIDGET_ADD_BUTTON_BOTTOM = 'BOTTOM'


def item_list(layout, owner, collection: str, draw_item,
              add=WIDGET_ADD_BUTTON_NONE, add_icon='ADD', add_text="",
              numbered: bool = False, open_prop="", draw_footer=None,
              show_move=False, copy_on_add=None, show_clipboard=False,
              inline_buttons=False):
    """Items drawn directly, remove button per item.
    inline_buttons: True puts move/remove/clipboard buttons in ONE row
    (use when draw_item draws a single line) instead of stacked columns.
    add: 'TOP' | 'BOTTOM' | None (draw the add button yourself)
    draw_item(layout, item, index) is your function."""
    items = getattr(owner, collection)

    def add_button(lay):
        _op(lay, "tm.list_add", owner, collection,
            icon=add_icon, text=add_text, open_prop=open_prop,
            copy_from=copy_on_add or 'NONE')

    if add == WIDGET_ADD_BUTTON_TOP:
        add_button(layout.row())

    for i, item in enumerate(items):
        row = layout.row(align=True)
        if numbered:
            num = row.row(align=True)
            num.alignment = 'LEFT'
            num.ui_units_x = 1.2
            num.label(text=f"{i + 1}.")
        content = row.column(align=True)
        draw_item(content, item, i)
        # right of the entry: move column, then delete / dropdown column
        if show_move and len(items) >= 2:
            move = row.row(align=True) if inline_buttons else row.column(align=True)
            _op(move, "tm.list_move", owner, collection, icon='TRIA_UP', index=i, direction='UP')
            _op(move, "tm.list_move", owner, collection, icon='TRIA_DOWN', index=i, direction='DOWN')
        buttons = row.row(align=True) if inline_buttons else row.column(align=True)
        if inline_buttons:
            if show_clipboard:
                _clipboard_menu(buttons, item)
            _op(buttons, "tm.list_remove", owner, collection, icon='X', index=i)
        else:
            _op(buttons, "tm.list_remove", owner, collection, icon='X', index=i)
            if show_clipboard:
                _clipboard_menu(buttons, item)

    if draw_footer:
        last_index = len(items) - 1
        last_item = items[last_index] if last_index >= 0 else None

        row = layout.row(align=True)
        row.active = False                 # dimmed, still editable
        draw_footer(row, last_item, last_index)

    if add == WIDGET_ADD_BUTTON_BOTTOM:
        add_button(layout.row())

def list_button(layout, idname, owner, collection, *, text="", icon='NONE', emboss=True,
                index_owner=None, index_prop="", **kw):
    _op(layout, idname, owner, collection, text=text, icon=icon, emboss=emboss,
        index_owner=index_owner, index_prop=index_prop, **kw)
    
def list_add_button(layout, owner, collection, **kw):
    return list_button(layout, "tm.list_add", owner, collection, **kw)

def list_remove_button(layout, owner, collection, **kw):
    return list_button(layout, "tm.list_remove", owner, collection, **kw)