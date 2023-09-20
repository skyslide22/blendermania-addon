import json
import bpy
import math
from bpy.app.handlers import persistent

from ..utils.Dotnet import (
    DotnetInt3,
    DotnetItem,
    DotnetBlock,
    DotnetMediatrackerClip,
    DotnetVector3,
    run_get_mediatracker_clips,
    run_place_mediatracker_clips_on_map,
    run_place_objects_on_map,
    get_block_dir_for_angle,
    DotnetExecResult
)
from ..utils.BlenderObjects import duplicate_object_to, move_obj_to_coll
from ..utils.Functions import (
    deselect_all_objects,
    fix_slash,
    ireplace,
    is_file_existing,
    get_global_props,
    radians,
    set_active_object,
    get_game_doc_path,
    is_game_trackmania2020,
    debug,
)
from ..utils.Constants import (
    MAP_GRID_GEO_NODES_NAME,
    MAP_GRID_OBJECT_NAME,
    MAP_OBJECT_ITEM,
    MAP_OBJECT_BLOCK,
    SPECIAL_NAME_PREFIX_MTTRIGGER,
    ADDON_ITEM_FILEPATH_MT_TRIGGER_10_66x8,
)

def _make_object_name(path: str, type: str) -> str:
    doc_path = get_game_doc_path()

    prefix = "TM" if is_game_trackmania2020() else "MP"
    # short_name = ireplace(doc_path+"/", "", path)
    short_name = fix_slash(path).split("/")[-1]#.split(".")[0]
    return f"{prefix}_{type.upper()}: {short_name}"

def get_selected_map_objects() -> list[bpy.types.Object]:
    res:list[bpy.types.Object] = []

    for obj in bpy.context.selected_objects:
        if "tm_map_object_kind" in obj:
            res.append(obj)

    return res

def is_all_selected_in_map_collection() -> bool:
    tm_props                      = get_global_props()
    map_coll:bpy.types.Collection = tm_props.PT_map_collection
    is_in                         = True

    if tm_props.PT_map_collection is None:
        return False

    for obj in bpy.context.selected_objects:
        if not map_coll.all_objects.get(obj.name):
            is_in = False

    return is_in

def create_update_map_object():
    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    object_item:bpy.types.Object     = tm_props.PT_map_object.object_item
    object_type:str                  = tm_props.PT_map_object.object_type
    object_path:str                  = fix_slash(tm_props.PT_map_object.object_path)
    doc_path                         = get_game_doc_path()
    selected_objects                 = get_selected_map_objects()
    all_selected                     = bpy.context.selected_objects
    is_all_in_map_coll               = is_all_selected_in_map_collection()
    
    if not map_coll:
        return "No map collection selected"

    obj_to_update:bpy.types.Object = None

    if doc_path.lower() in object_path.lower():
        if not is_file_existing(object_path):
            return f"There is no item with path {object_path}. You have to export it first"

    if len(object_path) == 0:
        return f"Name/Path can not be empty"


    # update path on selected objects if there is more than one selected
    if is_all_in_map_coll and len(all_selected) > 0:
        for obj in all_selected:
            obj.name = _make_object_name(object_path, object_type)
            obj["tm_map_object_kind"] = object_type
            obj["tm_map_object_path"] = object_path

        set_active_object(object_item)
    elif len(selected_objects) > 1:
        for obj in selected_objects:
            obj.name = _make_object_name(object_path, object_type)
            obj["tm_map_object_kind"] = object_type
            obj["tm_map_object_path"] = object_path

        set_active_object(object_item)
    else:
        # update object if it's already map_object else create a new one
        if object_item and "tm_map_object_kind" in object_item:
            obj_to_update = object_item
        else:
            if not object_item:
                bpy.ops.mesh.primitive_cube_add(size=32, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
                obj_to_update = bpy.context.active_object
                move_obj_to_coll(obj_to_update, map_coll)
            else:
                obj_to_update = duplicate_object_to(object_item, map_coll, True)
        
        obj_to_update.name = _make_object_name(object_path, object_type)
        obj_to_update["tm_map_object_kind"] = object_type
        obj_to_update["tm_map_object_path"] = object_path

        set_active_object(obj_to_update)

def validate_map_collection() -> str:
    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    doc_path                         = get_game_doc_path()
    
    if not map_coll:
        return "No map collection!"

    for obj in map_coll.all_objects:
        obj:bpy.types.Object = obj

        if "tm_map_object_kind" not in obj or "tm_map_object_path" not in obj:
            return f"Map collection contains invalid object: {obj.name}"

        if obj["tm_map_object_kind"] == MAP_OBJECT_BLOCK:
            if min(obj.location) < 0:
                return f"Block position can not be negative! Object: {obj.name}"

            if obj.rotation_euler[0] != 0 or obj.rotation_euler[1] != 0:
                return f"Only rotation on Z axis supported! Object: {obj.name}"
            
            if (round(math.degrees(obj.rotation_euler[2]))) % 90 != 0:
                return f"Rotation on Z must be multiple of 90deg! Object: {obj.name}"
        
        if obj["tm_map_object_kind"] == MAP_OBJECT_ITEM:
            if doc_path in obj["tm_map_object_path"] and not is_file_existing(obj["tm_map_object_path"]):
                return f"Item with path: {obj['tm_map_object_path']} does not exist. Object name: {obj.name}"

def export_map_collection() -> DotnetExecResult:
    err = validate_map_collection()
    if err: return DotnetExecResult(err, False)

    tm_props                         = get_global_props()
    map_coll:bpy.types.Collection    = tm_props.PT_map_collection
    map_path:str                     = tm_props.ST_map_filepath
    use_overwrite:bool               = tm_props.CB_map_use_overwrite
    map_suffix:str                   = tm_props.ST_map_suffix
    clean_blocks:bool                = False#tm_props.CB_map_clean_blocks
    clean_items:bool                 = tm_props.CB_map_clean_items
    doc_path                         = get_game_doc_path()
    dotnet_items                     = list[DotnetItem]()
    dotnet_blocks                    = list[DotnetBlock]()
    env                              = "Stadium2020" if is_game_trackmania2020() else tm_props.LI_DL_TextureEnvi

    if len(map_suffix.strip()) == 0:
        map_suffix = "_modified"

    for obj in map_coll.all_objects:
        obj:bpy.types.Object = obj

        if obj["tm_map_object_kind"] == MAP_OBJECT_ITEM:
            name = obj["tm_map_object_path"]
            is_custom_item = fix_slash(doc_path.lower()) in fix_slash(name.lower())

            if is_custom_item:
                name = ireplace(doc_path+"/Items/", "", name)
            elif is_game_trackmania2020(): # replace .Item.Gbx for 2020 vanilla items
                name = ireplace(".Gbx", "", ireplace(".Item", "", name))

            # TODO apply rotation on original before make item ()
            # like bpy.ops.object.transform_apply( rotation = True )
            # obj which is used to create item(map) needs to have rotation(0,0,0) else invalid data
            dotnet_items.append(DotnetItem(
                Name=name,
                Path=obj["tm_map_object_path"] if is_custom_item else "",
                Position=DotnetVector3(obj.location[1], obj.location[2]+8, obj.location[0]),
                # Rotation=DotnetVector3(obj.rotation_euler[2] - math.radians(90), obj.rotation_euler[1], obj.rotation_euler[0]),
                Rotation=DotnetVector3(obj.rotation_euler[2] - math.radians(90), obj.rotation_euler[0], math.radians((math.degrees(obj.rotation_euler[1]))*-1)),
                Pivot=DotnetVector3(0),
            ))
        elif obj["tm_map_object_kind"] == MAP_OBJECT_BLOCK:
            dotnet_blocks.append(DotnetBlock(
                Name=obj["tm_map_object_path"],
            Direction=get_block_dir_for_angle(math.degrees(obj.rotation_euler[2])),
                Position=DotnetInt3(int(int(obj.location[1])/32), int(int(obj.location[2])/32)+9, int(int(obj.location[0])/32)),
            ))

    return run_place_objects_on_map(
        map_path,
        dotnet_blocks,
        dotnet_items,
        use_overwrite,
        map_suffix,
        clean_blocks,
        clean_items,
        env,
    )



def create_grid_obj() -> bpy.types.Object:
    obj = bpy.data.objects.get(MAP_GRID_OBJECT_NAME, None)
    if obj: 
        if obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
        return obj

    mesh = bpy.data.meshes.new(name=MAP_GRID_OBJECT_NAME)
    obj  = bpy.data.objects.new(name=MAP_GRID_OBJECT_NAME, object_data=mesh)

    obj.hide_select = True

    bpy.context.scene.collection.objects.link(obj)
    return obj


def create_grid_obj_geom_nodes_modifier() -> bpy.types.Modifier:
    obj      = create_grid_obj()
    modifier = obj.modifiers.get(MAP_GRID_GEO_NODES_NAME, None)

    if modifier is None:
        modifier = obj.modifiers.new(name=MAP_GRID_GEO_NODES_NAME, type="NODES")
    
    bpy_nodes = bpy.data.node_groups
    nodes     = bpy_nodes.get(MAP_GRID_GEO_NODES_NAME, None)

    if nodes is None:
        nodes = bpy_nodes.new(MAP_GRID_GEO_NODES_NAME, "GeometryNodeTree")
    
    links = nodes.links
    nodes = nodes

    modifier.node_group = nodes
    nodes = nodes.nodes

    xstep = 300
    ystep = 300
    x = lambda step:  (xstep * step)
    y = lambda step: -(ystep * step)


    node_grid = nodes.new(type="GeometryNodeMeshGrid")
    node_grid.location[0] = x(0)

    node_mesh_to_curve= nodes.new(type="GeometryNodeMeshToCurve")
    node_mesh_to_curve.location[0] = x(1)
    
    node_set_pos = nodes.new(type="GeometryNodeSetPosition")
    node_set_pos.location[0] = x(2)
    
    node_output = nodes.get("Group Output", None) or nodes.new(type="NodeGroupOutput")
    node_output.location[0] = x(3)

    links.new(
        node_mesh_to_curve.inputs["Mesh"],
        node_grid.outputs["Mesh"]   
    )
    links.new(
        node_set_pos.inputs["Geometry"],
        node_mesh_to_curve.outputs["Curve"]
    )
    links.new(
        node_output.inputs[0],
        node_set_pos.outputs["Geometry"]
    )
    # ??? use 0
    # node_output.inputs["Geometry"],
    # KeyError: 'bpy_prop_collection[key]: key "Geometry" not found'

    return modifier


def delete_map_grid_helper_and_cleanup() -> None:
    if obj := bpy.data.objects.get(MAP_GRID_OBJECT_NAME, None):
        bpy.data.objects.remove(obj)
    if node := bpy.data.node_groups.get(MAP_GRID_GEO_NODES_NAME, None):
        bpy.data.node_groups.remove(node)


@persistent
def listen_object_move(scene):
    tm_props = get_global_props()
    use_global_grid = tm_props.CB_map_use_grid_helper
    
    if not hasattr(bpy.context, "object"):
        return

    if not bpy.context.object:
        return

    if objs := bpy.context.selected_objects:

        for obj in objs:
            if obj.tm_force_grid_helper == True:
                handle_object_movement_self_grid(obj)
            elif use_global_grid:
                handle_object_movement_for_grid_helper(obj)

        


def handle_object_movement_self_grid(obj: bpy.types.Object) -> None:
    x_step = obj.tm_forced_grid_helper_step_x
    y_step = obj.tm_forced_grid_helper_step_y
    z_step = obj.tm_forced_grid_helper_step_z

    if obj.location_before != obj.location:
        obj.location_before = obj.location

    obj.location[0] = get_obj_grid_pos(x_step, obj.location[0])
    obj.location[1] = get_obj_grid_pos(y_step, obj.location[1])
    obj.location[2] = get_obj_grid_pos(z_step, obj.location[2])


def get_obj_grid_pos(step: float, position: float) -> float:
    remainder = (position + (step/2)) % step
    range     = remainder - (step/2)

    if range == 0: 
        new_pos = position
    else:
        new_pos = position - remainder + step/2
    
    return new_pos


def handle_object_movement_for_grid_helper(obj: bpy.types.Object) -> None:

    if obj.location_before != obj.location:
        obj.location_before = obj.location
    
    # todo make dynamic
    z_step   = 8
    x_step   = 32
    y_step   = 32
    xy_step  = x_step + y_step
    min_steps= 2

    grid_obj = bpy.data.objects.get(MAP_GRID_GEO_NODES_NAME, None) or create_grid_obj()
    nodes    = grid_obj.modifiers.get(MAP_GRID_GEO_NODES_NAME, None)
    
    if nodes is None:
        nodes = create_grid_obj_geom_nodes_modifier()
   
    elif nodes.node_group is None:    
        nodes = create_grid_obj_geom_nodes_modifier()
    
    nodes =  nodes.node_group.nodes
    
    # scale as int interval(15,99 = 8 and 16,1 = 16 if step is 8) (min is step, never zero)
    obj_size_x = max(int( obj.dimensions[0] - (int(obj.dimensions[0]) % x_step) ) + x_step , x_step*min_steps)
    obj_size_y = max(int( obj.dimensions[1] - (int(obj.dimensions[1]) % y_step) ) + y_step , y_step*min_steps)
    obj_size_z = max(int( obj.dimensions[2] - (int(obj.dimensions[2]) % z_step) ) + z_step , z_step*min_steps)

    obj_loc_x = int(obj.location[0] - int(x_step / 2))
    obj_loc_y = int(obj.location[1] - int(y_step / 2))
    obj_loc_z = int(obj.location[2] - int(z_step / 2))

    grid_obj_loc_x = obj_loc_x - (obj_loc_x % x_step) + x_step
    grid_obj_loc_y = obj_loc_y - (obj_loc_y % y_step) + y_step
    grid_obj_loc_z = obj_loc_z - (obj_loc_z % z_step) + z_step

    grid_obj.location[0] = grid_obj_loc_x
    grid_obj.location[1] = grid_obj_loc_y
    grid_obj.location[2] = grid_obj_loc_z

    obj_xy_size = max(obj_size_x, obj_size_y)
    grid_size   = obj_xy_size * min_steps

    node_grid    = nodes["Grid"]
    input_size_x = node_grid.inputs[0]
    input_size_y = node_grid.inputs[1]
    input_vert_x = node_grid.inputs[2]
    input_vert_y = node_grid.inputs[3]

    input_size_x.default_value = grid_size
    input_size_y.default_value = grid_size
    
    input_vert_x.default_value = int(grid_size / xy_step) * min_steps + 1
    input_vert_y.default_value = int(grid_size / xy_step) * min_steps + 1
    

def import_mediatracker_clips() -> DotnetExecResult:
    tm_props = get_global_props()
    map_path = tm_props.ST_map_filepath
    map_coll = tm_props.PT_map_collection
    
    res = run_get_mediatracker_clips(map_path)
    if not res.success:
        return res

    # TODO dynamic cleanup
    clean_up = True

    if clean_up:
        objs = set(map_coll.all_objects)
        for obj in objs:
            if obj.name.startswith(SPECIAL_NAME_PREFIX_MTTRIGGER):
                bpy.data.objects.remove(obj)

    jsonpath = res.message
    
    with open(jsonpath, "r") as f:
        data = json.load(f)

        deselect_all_objects()

        bpy.ops.import_scene.fbx(
            filepath=ADDON_ITEM_FILEPATH_MT_TRIGGER_10_66x8,
            use_custom_props=True
        )

        mt_trigger_base_obj = bpy.context.selected_objects[-1] # imported object#

        trigger_clip_step_xy = 32/3
        trigger_clip_step_z  = 8

        mt_objs = []
        for clip in data:
            for trigger in clip["Triggers"]:
                obj = mt_trigger_base_obj.copy()
                obj.data = mt_trigger_base_obj.data.copy()
                obj.name = SPECIAL_NAME_PREFIX_MTTRIGGER
                obj.tm_map_clip_name = clip["ClipName"]
                obj.location = (
                    trigger["Z"] * trigger_clip_step_xy,
                    trigger["X"] * trigger_clip_step_xy,
                    trigger["Y"] * 8,
                )
                obj.lock_scale[0]    = True
                obj.lock_scale[1]    = True
                obj.lock_scale[2]    = True
                obj.lock_rotation[0] = True
                obj.lock_rotation[1] = True
                obj.lock_rotation[2] = True

                obj.tm_force_grid_helper         = True
                obj.tm_forced_grid_helper_step_x = trigger_clip_step_xy
                obj.tm_forced_grid_helper_step_y = trigger_clip_step_xy
                obj.tm_forced_grid_helper_step_z = trigger_clip_step_z

                map_coll.objects.link(obj)

        bpy.data.objects.remove(mt_trigger_base_obj)

    return res


def export_mediatracker_clips() -> DotnetExecResult:
    tm_props = get_global_props()
    map_path:str                  = tm_props.ST_map_filepath
    map_coll:bpy.types.Collection = tm_props.PT_map_collection
    
    clips: list[DotnetMediatrackerClip] = []
    temp_clips = {}

    for obj in map_coll.all_objects:
        if obj.name.startswith(SPECIAL_NAME_PREFIX_MTTRIGGER):
            mtclip_name = obj.tm_map_clip_name
            
            known_clip = mtclip_name in temp_clips
            if not known_clip:
                temp_clips[mtclip_name] = []

            X = round(obj.location.x / (32/3))
            Y = round(obj.location.y / (32/3))
            Z = round(obj.location.z / 8)

            position = DotnetInt3(Y, Z, X)
            temp_clips[mtclip_name].append(position)

    for clip_name, intarrs in temp_clips.items():
        clip = DotnetMediatrackerClip(clip_name, intarrs)
        clips.append(clip)

    return run_place_mediatracker_clips_on_map(map_path, clips)