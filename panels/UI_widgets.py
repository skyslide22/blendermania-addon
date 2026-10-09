from operator import index

from ..utils.Constants import *
import bpy

# =============================================================================
# 1. FOLDOUTS
#    Native collapsible headers. No registration needed.
# =============================================================================

FOLDOUT_STYLE_PANEL = 'PANEL'
FOLDOUT_STYLE_FLAT = 'FLAT'

def foldout_toggle(layout, obj, prop, label, enable_prop=None, enable_owner=None, indent=0.0, style=FOLDOUT_STYLE_PANEL):
    """Native foldout header. Returns the layout to draw content into, or None if collapsed.
    indent: horizontal indent in separator units (0 = none, ~2 = visible)."""
    header, body = layout.panel_prop(obj, prop)
    if enable_prop:
        header.prop(enable_owner if enable_owner else obj, enable_prop, text="")
    header.label(text=label)

    if not body:
        return None, header

    if indent > 0:
        if style == FOLDOUT_STYLE_PANEL:
            row = body.row()
        else:
            row = layout.row()
        row.separator(factor=indent)    # horizontal gap
        content = row.column()          # content goes here
    else:
        if style == FOLDOUT_STYLE_PANEL:
            content = body.column()
        else:
            content = layout.column()

    if enable_prop:
        content.active = getattr(enable_owner if enable_owner else obj, enable_prop)
    return content, header

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

# =============================================================================
#    LIST OPERATORS (registered)
#    Generic add/remove used by every list.
# =============================================================================

class TM_OT_List_Add(bpy.types.Operator):
    bl_idname = "tm.list_add"
    bl_label = "Add"
    bl_options = {'UNDO'}

    collection: bpy.props.StringProperty()
    index_prop: bpy.props.StringProperty()
    open_prop: bpy.props.StringProperty()

    def execute(self, context):
        owner = getattr(context, "tm_list_owner", None)
        index_owner = getattr(context, "tm_list_index_owner", None)
        if owner is None:
            return {'CANCELLED'}

        items = getattr(owner, self.collection)
        hooks = _hooks(owner, self.collection)

        if (hook := hooks.get("before_add")) and hook(owner) is False:
            return {'CANCELLED'}

        item = items.add()
        index = len(items) - 1

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
    id_block = owner.id_data
    path = "" if owner is id_block else owner.path_from_id()
    return f"{id_block.name}.{path}.{collection}"

def list_inspector(layout, owner, collection, index_prop, index_owner=None,
                   draw_detail=None, draw_footer=None, rows=4):
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
        index_owner=index_owner, index_prop=index_prop)
    _op(col, "tm.list_remove", owner, collection, icon='REMOVE',
        index_owner=index_owner, index_prop=index_prop)

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
              numbered: bool = False, open_prop="", draw_footer=None):
    """Items drawn directly, remove button per item.
    add: 'TOP' | 'BOTTOM' | None (draw the add button yourself)
    draw_item(layout, item, index) is your function."""
    items = getattr(owner, collection)

    def add_button(lay):
        _op(lay, "tm.list_add", owner, collection,
            icon=add_icon, text=add_text, open_prop=open_prop)

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
        _op(row, "tm.list_remove", owner, collection, icon='X', index=i)

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