import bpy
from pprint import pprint
from ..utils.ItemsExportV2Models import *

from ..utils.Functions import get_global_props, show_report_popup, is_collection_root

from ..utils import Constants


import json



def export_collection_to_dotnet(collection) -> bool:
    if not collection:
        return False

    if is_collection_root(collection):
        show_report_popup("Error", ("The root collection cannot be exported!",))
        return False

    cfg = _generate_item_config_from_collection(collection)
    cfg_dict = item_config_to_dict(cfg)

    pprint(cfg_dict)

    # write file to desktop
    with open(f"{Constants.PATH_DESKTOP}/item.info.json", "w") as f:
        json.dump(cfg_dict, f, indent=4)



    return True



def _generate_item_config_from_collection(collection) -> ItemConfig:
    cfg = ItemConfig()
    tm_props = get_global_props()

    cfg.AuthorName = tm_props.ST_author or "blendermania"
    cfg.Collection = cfg.Collection #todo
    cfg.Name = collection.name
    cfg.Description = collection.get("description", "N/A")
    cfg.Lights = _get_light_configs_from_collection(collection)
    cfg.LodParameters = _get_lod_parameters_from_collection(collection)
    cfg.Scale = 1.0 #todo
    cfg.Waypoint = _get_waypoint_from_collection(collection)


    return cfg

def _get_lod_parameters_from_collection(collection: bpy.types.Collection) -> LodParameters:
    params = LodParameters()
    params.MaxLodDistances = [100, 200, 400]
    print("used dummy maxloddistances!")

    return params


def _get_waypoint_from_collection(collection: bpy.types.Collection) -> Waypoint | None:
    coll_wp_type = Constants.WAYPOINTS.get(collection.color_tag, None)

    wp_type = None

    match coll_wp_type:
        case Constants.WAYPOINT_NAME_CHECKPOINT:
            wp_type = EWaypointType.Checkpoint
        case Constants.WAYPOINT_NAME_START:
            wp_type = EWaypointType.Start
        case Constants.WAYPOINT_NAME_FINISH:
            wp_type = EWaypointType.Finish
        case Constants.WAYPOINT_NAME_STARTFINISH:
            wp_type = EWaypointType.StartFinish
        case _:
            return None

    wp = Waypoint()
    wp.Type = wp_type
    # wp.DefaultGravitySpawn = ...
    wp.NoRespawn = collection.tm_waypoint_no_respawn

    return wp



def get_waypointtype_of_collection(col: bpy.types.Collection) -> str:
    col_color = col.color_tag
    waypoint = WAYPOINTS.get(col_color, None)
    return waypoint


def _get_light_configs_from_collection(collection: bpy.types.Collection) -> list[LightConfig]:
    light_configs = []
    objs: list[bpy.types.Object] = collection.objects
    for obj in objs:
        if obj.type == 'LIGHT':
            light_cfg = LightConfig()
            light_cfg.Name = obj.name
            light_cfg.Type = obj.data.type
            light_cfg.Color = "2222ff" #todo
            light_cfg.Intensity = 2
            light_cfg.NightOnly = False #todo
            light_cfg.Distance = 100 #todo
            light_cfg.PointEmissionLength = 1.0 #todo
            light_cfg.PointEmissionRadius = 1.0 #todo
            light_cfg.SpotEmissionSizeX = 1.0 #todo
            light_cfg.SpotEmissionSizeY = 1.0 #todo
            light_cfg.SpotInnerAngle = 30.0 #todo
            light_cfg.SpotOuterAngle = 45.0 #todo
            light_configs.append(light_cfg)

    return light_configs