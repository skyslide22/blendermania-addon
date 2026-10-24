import bpy
from bpy.props import *

from ..properties.ItemConfigProperties import ItemConfigProperties
from .Functions import has_infix, has_prefix, apply_collection_type, toggle_infix, toggleNameSpecialPrefix
from .PropertyFunctions import enum_items, subscribe_to_msgbus
from .PropertyIdentifiers import CollectionProp
from ..utils.Constants import *
from ..utils.FunctionsV2 import get_active_item_collection, get_item_collection_objects, get_item_moving_groups
from ..utils.ItemsExportV2Models import EAxis, AnimEase, ItemConfig

_sorting = False

def _sort_lods(self, context):
    global _sorting
    if _sorting: return
    lods = self.id_data.tm_lods
    values = [l.distance for l in lods]
    if values == sorted(values): return
    _sorting = True
    try:
        for l, v in zip(lods, sorted(values)):
            l.distance = v
    finally:
        _sorting = False

        
class TM_LodDistanceProperties(bpy.types.PropertyGroup):
    distance: FloatProperty(name="Distance", default=64.0, min=0.0, step=100, update=_sort_lods)

class TM_TextureAnimProperties(bpy.types.PropertyGroup):
    duration: IntProperty(name="Duration", subtype='UNSIGNED', default=1000, min=0, step=100)
    textureIndex: IntProperty(name="Texture ID",subtype='UNSIGNED', default=0, min=0)

class TM_SubAnimProperties(bpy.types.PropertyGroup):
    reverse: BoolProperty(name="Reverse", default=False)
    duration: IntProperty(name="Duration", subtype='UNSIGNED', default=1000, min=0, step=100)
    ease: EnumProperty(
        name="Ease",
        description="Easing function for the animation",
        items=enum_items(AnimEase),
        default=AnimEase.Constant.value)




def _icon_for_tag(tag):
    return 'OUTLINER_COLLECTION' if tag == 'NONE' else f"COLLECTION_{tag}"

WAYPOINT_ENUM_ITEMS = [
    (name, name, f"Mark collection as {name}", _icon_for_tag(WAYPOINTS[name]), i)
    for i, name in enumerate(WAYPOINT_ORDER)
]
AXIS_ENUM_ITEMS = [
    ('X', 'X', "X Axis", 'NONE', 0),
    ('Y', 'Y', "Y Axis", 'NONE', 1),
    ('Z', 'Z', "Z Axis", 'NONE', 2),
]

COLLECTION_TYPE_ENUM_ITEMS = [
    (type_id, label, desc, 'NONE', i)
    for i, (type_id, label, desc, _infix) in enumerate(COLLECTION_TYPES)
]
_TYPE_INFIXES = {type_id: infix for type_id, _l, _d, infix in COLLECTION_TYPES if infix}

def _type_from_name(name):
    for type_id, infix in _TYPE_INFIXES.items():
        if has_infix(name, infix):
            return type_id
    return COLLECTION_TYPE_DEFAULT

def _apply_type_to_name(col, type_id):
    """remove all type infixes from the name, add the one of type_id"""
    for infix in _TYPE_INFIXES.values():
        if has_infix(col.name, infix):
            toggle_infix(col, infix)
    if type_id in _TYPE_INFIXES:
        toggle_infix(col, _TYPE_INFIXES[type_id])

def _type_toggle_setter(type_id):
    def _set(self, value):
        current = getattr(self, CollectionProp.COLLECTION_TYPE)
        if value:
            setattr(self, CollectionProp.COLLECTION_TYPE, type_id)
        elif current == type_id:
            setattr(self, CollectionProp.COLLECTION_TYPE, COLLECTION_TYPE_DEFAULT)
    return _set

def register_collection_properties():
    bpy.types.Collection.tm_itemxml_template = StringProperty(
        name="Item XML Template", 
        default=""
    )

    setattr(bpy.types.Collection, CollectionProp.CONFIG, PointerProperty(
        name="Item Config",
        description="Item configuration for the collection",
        type=ItemConfigProperties
    ))

    setattr(bpy.types.Collection, CollectionProp.NO_RESPAWN, BoolProperty(
        name="No Respawn",
        description="Indicates if the waypoint should not respawn",
        default=False
    ))

    setattr(bpy.types.Collection, CollectionProp.WAYPOINT_TYPE, EnumProperty(
        name="Waypoint",
        description="Type of the waypoint",
        items=WAYPOINT_ENUM_ITEMS,
        default=WAYPOINT_NAME_NONE,
        update=_update_waypoint
    ))
    setattr(bpy.types.Collection, CollectionProp.COLLECTION_TYPE, EnumProperty(
        name="Collection Type",
        description="Type of the collection",
        items=COLLECTION_TYPE_ENUM_ITEMS,
        default=COLLECTION_TYPE_DEFAULT,
        update=_update_collection_type
    ))
    # toggle buttons: enabling sets the type, disabling falls back to Default
    setattr(bpy.types.Collection, CollectionProp.MOVING_GROUP, BoolProperty(
        name="Moving Group",
        description="Collection type is Moving Group",
        get=lambda self: getattr(self, CollectionProp.COLLECTION_TYPE) == COLLECTION_GROUP_MOVING,
        set=_type_toggle_setter(COLLECTION_GROUP_MOVING),
    ))
    setattr(bpy.types.Collection, CollectionProp.CONTAINER_GROUP, BoolProperty(
        name="Container",
        description="Collection type is Container (structural only)",
        get=lambda self: getattr(self, CollectionProp.COLLECTION_TYPE) == COLLECTION_GROUP_CONTAINER,
        set=_type_toggle_setter(COLLECTION_GROUP_CONTAINER),
    ))

    setattr(bpy.types.Collection, CollectionProp.LODS, CollectionProperty(
        name="LODs",
        description="LOD distance settings for the collection",
        type=TM_LodDistanceProperties
    ))

    setattr(bpy.types.Collection, CollectionProp.IGNORE, BoolProperty(
        name="Ignore Collection",
        description="Indicates if the collection should be ignored",
        default=False,
        update=_update_ignore
    ))

    setattr(bpy.types.Collection, CollectionProp.TORQUE_X, FloatProperty(
        name="TorqueX",
        description="Torque around the X axis",
        default=0.0,
    ))
    setattr(bpy.types.Collection, CollectionProp.TORQUE_DURATION, IntProperty(
        name="Torque Duration (ms)",
        description="Duration of the torque effect",
        default=0,
        min=0,
    ))
    setattr(bpy.types.Collection, CollectionProp.DEFAULT_GRAVITY_SPAWN, FloatVectorProperty(
        name="Default Gravity Spawn", 
        description="Default gravity spawn",
        size=3,
        default=(0.0, 1.0, 0.0)
    ))

    # moving group
    setattr(bpy.types.Collection, CollectionProp.MOVING_ANCHOR, PointerProperty(
        name="Moving Anchor", 
        description="Moving anchor round which is rotated in the animation",
        type=bpy.types.Object,
        poll=_anchor_poll,
    ))
    setattr(bpy.types.Collection, CollectionProp.RELATIVE_MOVING_GROUP, PointerProperty(
        name="Attached to Moving Group",
        description="Animations are attached to this moving group, so they are relative to it",
        type=bpy.types.Collection,
        poll=_moving_group_poll,
    ))


    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_CAST_SHADOW, BoolProperty(
        name="Cast Shadow",
        description="Indicates if the kinematic object should cast shadows",
        default=True
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_IS_KINEMATIC, BoolProperty(
        name="Is Kinematic",
        description="Indicates if the object is kinematic",
        default=True
    ))

    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_PERIODIC_SC, FloatProperty(
        name="Periodic SC",
        description="Periodic SC value for the kinematic object",
        default=1.0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_PERIODIC_SC_MAX, FloatProperty(
        name="Periodic SC Max",
        description="Maximum Periodic SC value for the kinematic object",
        default=-1.0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_PHASE_01, FloatProperty(
        name="Phase 01",
        description="Phase 01 value for the kinematic object",
        default=-1.0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_PHASE_01_MAX, FloatProperty(
        name="Phase 01 Max",
        description="Maximum Phase 01 value for the kinematic object",
        default=-1.0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_TEXTURE_ID, IntProperty(
        name="Texture ID",
        description="Texture ID for the kinematic object",
        subtype='UNSIGNED',
        default=0,
        min=0
    ))

    # moving params
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_TRANS_AXIS, EnumProperty(
        name="Translation Axis",
        description="Axis of translation for the kinematic object",
        items=AXIS_ENUM_ITEMS,
        default=EAxis.X
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_TRANS_MIN, FloatProperty(
        name="Translation Min",
        description="Start translation value for the kinematic object",
        default=0.0,
        step=100,
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_TRANS_MAX, FloatProperty(
        name="Translation Max",
        description="End translation value for the kinematic object",
        default=0.0,
        step=100,
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_ROT_AXIS, EnumProperty(
        name="Rotation Axis",
        description="Axis of rotation for the kinematic object",
        items=AXIS_ENUM_ITEMS,
        default=EAxis.X
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_ROT_MIN, FloatProperty(
        name="Angle Min",
        description="Start rotation angle for the kinematic object",
        subtype='ANGLE',
        default=0.0,
        step=100,
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_ROT_MAX, FloatProperty(
        name="Angle Max",
        description="End rotation angle for the kinematic object",
        subtype='ANGLE',
        default=0.0,
        step=100,
    ))

    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_TRANS_ANIMS, CollectionProperty(
        name="Translation Animations",
        description="Animation settings for the moving texture of the kinematic object",
        type=TM_SubAnimProperties
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_ROT_ANIMS, CollectionProperty(
        name="Rotation Animations",
        description="Animation settings for the rotation of the kinematic object",
        type=TM_SubAnimProperties
    ))


    # Moving Texture
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_HAS_MOVING_TEXTURE, BoolProperty(
        name="Has Moving Texture",
        description="Indicates if the kinematic object has a moving texture",
        default=False
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_NUM, IntProperty(
        name="Num Textures",
        description="Number of moving textures for the kinematic object",
        subtype='UNSIGNED',
        default=8,
        min=0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_LINE, IntProperty(
        name="Textures Per Line",
        description="Number of moving textures per line for the kinematic object",
        subtype='UNSIGNED',
        default=1,
        min=0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_COLUMN, IntProperty(
        name="Textures Per Column",
        description="Number of moving textures per column for the kinematic object",
        subtype='UNSIGNED',
        default=8,
        min=0
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_TOP_TO_BOTTOM, BoolProperty(
        name="Top to Bottom",
        description="Indicates if the moving texture is arranged top to bottom",
        default=False
    ))
    setattr(bpy.types.Collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS, CollectionProperty(
        name="Moving Texture Animations",
        description="Animation settings for the moving texture of the kinematic object",
        type=TM_TextureAnimProperties
    ))

    subscribe_to_msgbus(_msgbus_owner, bpy.types.Collection, "name", _on_collection_renamed)
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)


def unregister_collection_properties():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
    bpy.msgbus.clear_by_owner(_msgbus_owner)

    del bpy.types.Collection.tm_itemxml_template

    for prop in CollectionProp:
        if hasattr(bpy.types.Collection, prop):
            delattr(bpy.types.Collection, prop)



#
def _update_collection_type(self, context):
    if _syncing: return
    type_id = getattr(self, CollectionProp.COLLECTION_TYPE)
    _apply_type_to_name(self, type_id)
    apply_collection_type(self, type_id)


def _update_waypoint(self, context):
    waypoint = getattr(self, CollectionProp.WAYPOINT_TYPE)
    self.color_tag = WAYPOINTS[waypoint]

def _update_ignore(self, context):
    if _syncing: return
    toggleNameSpecialPrefix(self, SPECIAL_NAME_PREFIX_IGNORE)

def _anchor_poll(self, obj):
    # self = the owner of the property (here: the PropertyGroup)
    coll = get_active_item_collection()
    if coll is None: return False
    return obj in get_item_collection_objects(coll)   # containers/moving groups flattened, nested items excluded

def _moving_group_poll(self, obj):
    # self = the owner of the property (here: the PropertyGroup)
    coll = get_active_item_collection()
    if coll is None: return False
    self_coll = getattr(self, "id_data", self)
    return obj != self_coll and obj in get_item_moving_groups(coll)



# name changes sets property
# syncing to avoid infinite loops
from bpy.app.handlers import persistent

_msgbus_owner = object()
_syncing = False

def _on_collection_renamed():
    global _syncing
    if _syncing: return
    _syncing = True
    try:
        for obj in bpy.data.collections:
            # all properties that should be a part of the collection name must update here
            # prefix
            if getattr(obj, CollectionProp.IGNORE) != has_prefix(obj.name, SPECIAL_NAME_PREFIX_IGNORE):
                setattr(obj, CollectionProp.IGNORE, has_prefix(obj.name, SPECIAL_NAME_PREFIX_IGNORE))

            # infixes
            name_type = _type_from_name(obj.name)
            if getattr(obj, CollectionProp.COLLECTION_TYPE) != name_type:
                setattr(obj, CollectionProp.COLLECTION_TYPE, name_type)
                apply_collection_type(obj, name_type)
    finally:
        _syncing = False


@persistent
def _on_load_post(_):
    subscribe_to_msgbus(_msgbus_owner, bpy.types.Collection, "name", _on_collection_renamed)