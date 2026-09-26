import bpy
from pprint import pprint
from ..utils.ItemsExportV2Models import *
from ..utils.Functions import get_global_props, show_report_popup, is_collection_root
from ..utils import Constants

import json
import math



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
    waypoint = Constants.WAYPOINTS.get(col_color, None)
    return waypoint


def _get_light_configs_from_collection(collection: bpy.types.Collection) -> list[LightConfig]:
    light_configs = []
    objs: list[bpy.types.Object] = collection.objects
    
    for obj in objs:
        if obj.type != 'LIGHT':
            continue
        
        light: bpy.types.Light = obj.data
        light_is_spot = light.type == 'SPOT'
        light_is_point = light.type == 'POINT'

        if not (light_is_spot or light_is_point):
            continue

        light_cfg = LightConfig()

        light_cfg.Name  = light.name
        light_cfg.Type  = light.type
        
        light_cfg.Color     = f"{int(light.color[0]*255):02x}{int(light.color[1]*255):02x}{int(light.color[2]*255):02x}"
        light_cfg.Intensity = light.energy
        light_cfg.NightOnly = light.night_only # custom prop
        light_cfg.Distance  = light.shadow_soft_size
        
        light_cfg.PointEmissionLength = 1.0 #todo
        light_cfg.PointEmissionRadius = 1.0 #todo

        # convert euler to degree
        spot_size_degree = light.spot_size * (180.0 / math.pi) if light_is_spot else 0.0
        light_cfg.SpotEmissionSizeX = spot_size_degree
        light_cfg.SpotEmissionSizeY = spot_size_degree
        light_cfg.SpotInnerAngle = spot_size_degree
        light_cfg.SpotOuterAngle = spot_size_degree
        light_configs.append(light_cfg)

    return light_configs