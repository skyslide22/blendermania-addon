import bpy
from bpy.props import StringProperty, CollectionProperty

ADDON_ID ="blendermania-addon"

class TM_HiddenView(bpy.types.PropertyGroup):
    view_id: StringProperty()

class TM_Preferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID
 
    hidden_views: CollectionProperty(type=TM_HiddenView)
 
    def draw(self, context):
        self.layout.label(text="Panel visibility is managed in the 'Views' panel.")


def get_prefs(context=None):
    context = context or bpy.context
    addons = context.preferences.addons
    return context.preferences.addons[ADDON_ID].preferences

def is_hidden(view_id, context=None):
    return any(h.view_id == view_id for h in get_prefs(context).hidden_views)

def set_hidden(view_id, hidden, context=None):
    prefs = get_prefs(context)
    idx = next((i for i, h in enumerate(prefs.hidden_views)
                if h.view_id == view_id), -1)
    if hidden and idx < 0:
        prefs.hidden_views.add().view_id = view_id
    elif not hidden and idx >= 0:
        prefs.hidden_views.remove(idx)

# Registry

VIEW_REGISTRY = []   # list of panel classes that can be toggled

class ViewPanelMixin:
    view_id = ""          # stable id, never change once released
    view_label = ""       # shown in the Views panel
    view_group = "Core"   # used to group the toggles
 
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.view_id:
            VIEW_REGISTRY.append(cls)
 
    @classmethod
    def poll(cls, context):
        if is_hidden(cls.view_id, context):
            return False
        return cls.view_poll(context)
 
    @classmethod
    def view_poll(cls, context):
        """Override: panel-specific conditions."""
        return True


# --------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------
 
class TM_OT_toggle_view(bpy.types.Operator):
    bl_idname = "tm.toggle_view"
    bl_label = "Toggle View"
    bl_options = {'INTERNAL'}
 
    view_id: StringProperty()
 
    def execute(self, context):
        set_hidden(self.view_id, not is_hidden(self.view_id, context), context)
        _redraw()
        return {'FINISHED'}
 
 
class TM_OT_view_preset(bpy.types.Operator):
    bl_idname = "tm.view_preset"
    bl_label = "Apply View Preset"
    bl_options = {'INTERNAL'}
 
    preset: StringProperty()   # "ALL", "MINIMAL" or a group name
 
    def execute(self, context):
        for cls in VIEW_REGISTRY:
            if self.preset == "ALL":
                hide = False
            elif self.preset == "NONE":
                hide = True
            elif self.preset == "MINIMAL":
                hide = cls.view_group != "Core"
            else:   # show only the named group
                hide = cls.view_group != self.preset
            set_hidden(cls.view_id, hide, context)
        _redraw()
        return {'FINISHED'}
 
 
def _redraw():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

# registration

def _classes():
    return (
        TM_HiddenView,
        TM_Preferences,        
        TM_OT_toggle_view,
        TM_OT_view_preset,
        *VIEW_REGISTRY,
    )


def register_panel_widgets():
    for cls in _classes():
        bpy.utils.register_class(cls)
 
 
def unregister_panel_widgets():
    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)