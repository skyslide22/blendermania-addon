from enum import StrEnum, unique

@unique
class ObjectProp(StrEnum):
    #Flags
    NON_COLLIDABLE   = "tm_non_collidable"
    INVISIBLE        = "tm_invisible"
    TRIGGER_WAYPOINT = "tm_trigger_waypoint"
    TRIGGER_EFFECT   = "tm_trigger_effect"
    SOCKET           = "tm_socket"
    IGNORE           = "tm_ignore"
    PIVOT            = "tm_pivot"
    ORIGIN           = "tm_origin"
    NO_MERGE         = "tm_no_merge"

    #other
    TRIGGER_EFFECT_TYPE = "tm_trigger_effect_type"
    GAMEPLAY_MAIN_DIR   = "tm_gameplay_main_dir"
    GAMEPLAY_STRENGTH   = "tm_gameplay_strength"
    ENABLE_LODS          = "tm_enable_lods"
    LOD_INDEXES          = "tm_lod_indexes"

    OVERRIDE_LIGHTMAP_SIZE          = "tm_override_lightmap_size"
    LIGHTMAP_SIZE          = "tm_lightmap_size"

    ICON_ONLY = "tm_icon_only"

@unique
class CollectionProp(StrEnum):
    CONFIG = "tm_item_config"

    COLLECTION_TYPE = "tm_collection_type"
    MOVING_GROUP = "tm_moving_group"  # read-only bool derived from COLLECTION_TYPE
    CONTAINER_GROUP = "tm_container_group"    # read-only bool derived from COLLECTION_TYPE
    
    LODS = "tm_lods"
    SELECTED_LODS = "tm_selected_lods"
    WAYPOINT_TYPE = "tm_waypoint_type"
    NO_RESPAWN = "tm_waypoint_no_respawn"
    IGNORE = "tm_collection_ignore"

    DEFAULT_GRAVITY_SPAWN = "tm_default_gravity_spawn"
    TORQUE_X = "tm_torque_x"
    TORQUE_DURATION = "tm_torque_duration"

    MOVING_ANCHOR = "tm_moving_anchor"
    RELATIVE_MOVING_GROUP = "tm_relative_moving_group"

    KINEMATIC_CAST_SHADOW = "tm_kinematic_cast_shadow"
    KINEMATIC_IS_KINEMATIC = "tm_kinematic_is_kinematic"
    KINEMATIC_PERIODIC_SC = "tm_kinematic_periodic_sc"
    KINEMATIC_PERIODIC_SC_MAX = "tm_kinematic_periodic_sc_max"
    KINEMATIC_PHASE_01 = "tm_kinematic_phase_01"
    KINEMATIC_PHASE_01_MAX = "tm_kinematic_phase_01_max"
    KINEMATIC_TEXTURE_ID = "tm_kinematic_texture_id"

    KINEMATIC_TRANS_AXIS = "tm_kinematic_trans_axis"
    KINEMATIC_TRANS_MIN = "tm_kinematic_trans_min"
    KINEMATIC_TRANS_MAX = "tm_kinematic_trans_max"
    KINEMATIC_ROT_AXIS = "tm_kinematic_rot_axis"
    KINEMATIC_ROT_MIN = "tm_kinematic_angle_min"
    KINEMATIC_ROT_MAX = "tm_kinematic_angle_max"
    KINEMATIC_TRANS_ANIMS = "tm_kinematic_trans_anims"
    KINEMATIC_ROT_ANIMS = "tm_kinematic_rot_anims"

    KINEMATIC_HAS_MOVING_TEXTURE = "tm_kinematic_has_moving_texture"
    KINEMATIC_MOVING_TEXTURE_NUM = "tm_kinematic_moving_texture_num"
    KINEMATIC_MOVING_TEXTURE_PER_LINE = "tm_kinematic_moving_texture_per_line"
    KINEMATIC_MOVING_TEXTURE_PER_COLUMN = "tm_kinematic_moving_texture_per_column"
    KINEMATIC_MOVING_TEXTURE_TOP_TO_BOTTOM = "tm_kinematic_moving_texture_top_to_bottom"
    KINEMATIC_MOVING_TEXTURE_ANIMS = "tm_kinematic_moving_texture_anims"

@unique
class LightProp(StrEnum):
    LIGHT_NIGHT_ONLY = "night_only" # backwards compatibility
    LIGHT_EMITTING_RADIUS = "tm_light_emitting_radius"
    LIGHT_EMITTING_LENGTH = "tm_light_emitting_length"