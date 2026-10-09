import bpy
from bpy.props import *
from .Functions import toggle_infix, toggleNameSpecialPrefix
from .PropertyFunctions import enum_items, subscribe_to_msgbus
from .PropertyIdentifiers import ObjectProp
from ..utils.Constants import *
from ..utils.ItemsExportV2Models import LegacyGameplayId

# when prop A is turned ON, these props are turned OFF
EXCLUSIVE_PROPERTIES = {
    ObjectProp.NON_COLLIDABLE:    [ObjectProp.INVISIBLE, ObjectProp.SOCKET],
    ObjectProp.INVISIBLE:         [ObjectProp.NON_COLLIDABLE, ObjectProp.SOCKET],
    ObjectProp.SOCKET:            [ObjectProp.NON_COLLIDABLE, ObjectProp.INVISIBLE, ObjectProp.TRIGGER_WAYPOINT, ObjectProp.TRIGGER_EFFECT],
    ObjectProp.TRIGGER_EFFECT:    [ObjectProp.TRIGGER_WAYPOINT, ObjectProp.SOCKET],
    ObjectProp.TRIGGER_WAYPOINT:  [ObjectProp.TRIGGER_EFFECT, ObjectProp.SOCKET],
}

class TM_LodIndex(bpy.types.PropertyGroup):
    value: IntProperty()

def _make_update(prop, extra_update=None):
    def update(self, context):
        if getattr(self, prop):
            for other in EXCLUSIVE_PROPERTIES.get(prop, []):
                if getattr(self, other):
                    setattr(self, other, False)  # may trigger other's update, which returns early (it's OFF now)
        if extra_update:
            extra_update(self, context)
    return update

def _bool(name, desc, prop, update=None):
    return BoolProperty(name=name, description=desc, default=False,
                        update=_make_update(prop, extra_update=update))


def register_object_properties():
    setattr(bpy.types.Object, ObjectProp.NON_COLLIDABLE, _bool("Not Collidable", "Object should not collide", ObjectProp.NON_COLLIDABLE, _update_tm_non_collidable))
    setattr(bpy.types.Object, ObjectProp.INVISIBLE, _bool("Invisible", "Object should not be visible", ObjectProp.INVISIBLE, _update_tm_invisible))
    setattr(bpy.types.Object, ObjectProp.TRIGGER_WAYPOINT, _bool("Trigger Waypoint", "Object is a waypoint trigger", ObjectProp.TRIGGER_WAYPOINT, _update_tm_trigger_waypoint))
    setattr(bpy.types.Object, ObjectProp.TRIGGER_EFFECT, _bool("Trigger Effect", "Object is an effect trigger", ObjectProp.TRIGGER_EFFECT, _update_tm_trigger_effect))
    setattr(bpy.types.Object, ObjectProp.SOCKET, _bool("Spawn", "Object is a spawn point", ObjectProp.SOCKET, _update_tm_socket))
    setattr(bpy.types.Object, ObjectProp.IGNORE, _bool("Ignore", "Object should be ignored", ObjectProp.IGNORE, _update_tm_ignore))
    setattr(bpy.types.Object, ObjectProp.PIVOT, _bool("Pivot", "Object is a pivot point", ObjectProp.PIVOT, _update_tm_pivot))
    setattr(bpy.types.Object, ObjectProp.ORIGIN, _bool("Origin", "Object is an origin point", ObjectProp.ORIGIN, _update_tm_origin))

    setattr(bpy.types.Object, ObjectProp.TRIGGER_EFFECT_TYPE, EnumProperty(name="Trigger Effect Type", description="Type of trigger effect", items=enum_items(LegacyGameplayId), default=LegacyGameplayId.None_.value,))
    setattr(bpy.types.Object, ObjectProp.GAMEPLAY_MAIN_DIR, FloatVectorProperty(name="Gameplay Main Dir", description="Main directory for gameplay", default=(0.0, 0.0, 0.0)))

    setattr(bpy.types.Object, ObjectProp.ENABLE_LODS, BoolProperty(name="LODs", description="Enable Level of Detail for this object", default=False))
    setattr(bpy.types.Object, ObjectProp.LOD_INDEXES, CollectionProperty(type=TM_LodIndex)) 
    
    setattr(bpy.types.Object, ObjectProp.OVERRIDE_LIGHTMAP_SIZE, _bool("Override Lightmap Size", "Override lightmap size", ObjectProp.OVERRIDE_LIGHTMAP_SIZE))
    setattr(bpy.types.Object, ObjectProp.LIGHTMAP_SIZE, FloatProperty(name="Lightmap Size", description="Lightmap size", default=100.0))

    setattr(bpy.types.Object, ObjectProp.ICON_ONLY, _bool("Icon Only", "Object is only for icon generation", ObjectProp.ICON_ONLY, update=_update_tm_icon_only))
    
    subscribe_to_msgbus(_msgbus_owner, bpy.types.Object, "name", _on_object_renamed)
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)

def unregister_object_properties():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
    bpy.msgbus.clear_by_owner(_msgbus_owner)

    for prop in ObjectProp:
        if hasattr(bpy.types.Object, prop):
            delattr(bpy.types.Object, prop)


# automatic renames on property change
def _update_tm_ignore(self, context):
    if _syncing: return
    toggleNameSpecialPrefix(self, SPECIAL_NAME_PREFIX_IGNORE)

def _update_tm_socket(self, context):
    if _syncing: return
    toggleNameSpecialPrefix(self, SPECIAL_NAME_PREFIX_SOCKET)

def _update_tm_origin(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_ORIGIN)

def _update_tm_pivot(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_PIVOT)

def _update_tm_trigger_effect(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_TRIGGEREFFECT)

def _update_tm_trigger_waypoint(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_TRIGGERWAYPOINT)

def _update_tm_invisible(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_NOTVISIBLE)

def _update_tm_non_collidable(self, context):
    if _syncing: return
    toggle_infix(self, SPECIAL_NAME_INFIX_NOTCOLLIDABLE)

def _update_tm_icon_only(self, context):
    if _syncing: return
    toggleNameSpecialPrefix(self, SPECIAL_NAME_PREFIX_ICON_ONLY)



# name changes sets property
# syncing to avoid infinite loops
from bpy.app.handlers import persistent

_msgbus_owner = object()
_syncing = False

def _on_object_renamed():
    global _syncing
    if _syncing: return
    _syncing = True
    try:
        for obj in bpy.data.objects:
            # all properties that should be a part of the node name must update here

            # prefixes
            if getattr(obj, ObjectProp.IGNORE) != obj.name.startswith(SPECIAL_NAME_PREFIX_IGNORE):
                setattr(obj, ObjectProp.IGNORE, obj.name.startswith(SPECIAL_NAME_PREFIX_IGNORE))
            if getattr(obj, ObjectProp.SOCKET) != obj.name.startswith(SPECIAL_NAME_PREFIX_SOCKET):
                setattr(obj, ObjectProp.SOCKET, obj.name.startswith(SPECIAL_NAME_PREFIX_SOCKET))
            if getattr(obj, ObjectProp.ICON_ONLY) != obj.name.startswith(SPECIAL_NAME_PREFIX_ICON_ONLY):
                setattr(obj, ObjectProp.ICON_ONLY, obj.name.startswith(SPECIAL_NAME_PREFIX_ICON_ONLY))


            # infixes
            if getattr(obj, ObjectProp.ORIGIN) != (SPECIAL_NAME_INFIX_ORIGIN in obj.name):
                setattr(obj, ObjectProp.ORIGIN, (SPECIAL_NAME_INFIX_ORIGIN in obj.name))
            if getattr(obj, ObjectProp.PIVOT) != (SPECIAL_NAME_INFIX_PIVOT in obj.name):
                setattr(obj, ObjectProp.PIVOT, (SPECIAL_NAME_INFIX_PIVOT in obj.name))
            if getattr(obj, ObjectProp.TRIGGER_EFFECT) != (SPECIAL_NAME_INFIX_TRIGGEREFFECT in obj.name):
                setattr(obj, ObjectProp.TRIGGER_EFFECT, (SPECIAL_NAME_INFIX_TRIGGEREFFECT in obj.name))
            if getattr(obj, ObjectProp.TRIGGER_WAYPOINT) != (SPECIAL_NAME_INFIX_TRIGGERWAYPOINT in obj.name):
                setattr(obj, ObjectProp.TRIGGER_WAYPOINT, (SPECIAL_NAME_INFIX_TRIGGERWAYPOINT in obj.name))
            if getattr(obj, ObjectProp.NON_COLLIDABLE) != (SPECIAL_NAME_INFIX_NOTCOLLIDABLE in obj.name):
                setattr(obj, ObjectProp.NON_COLLIDABLE, (SPECIAL_NAME_INFIX_NOTCOLLIDABLE in obj.name))
            if getattr(obj, ObjectProp.INVISIBLE) != (SPECIAL_NAME_INFIX_NOTVISIBLE in obj.name):
                setattr(obj, ObjectProp.INVISIBLE, (SPECIAL_NAME_INFIX_NOTVISIBLE in obj.name))
    finally:
        _syncing = False

@persistent
def _on_load_post(_):
    subscribe_to_msgbus(_msgbus_owner, bpy.types.Object, "name", _on_object_renamed)

def sync_object_properties_with_names():
    _on_object_renamed()

