import re
import bpy
from .Functions import (
    debug,
    deselect_all_objects,
    get_global_props,
    get_path_filename,
    is_file_exist,
    is_obj_visible_by_name,
    rList,
    set_active_object,
    fixSlash,
)

def _get_cam_position() -> list:
    """return roation_euler list for the icon_obj"""
    tm_props = get_global_props()
    style    = tm_props.LI_icon_perspective
    if style == "CLASSIC_SE":  return   rList(-35.5,   -30,    145.5)
    if style == "CLASSIC_SW":  return   rList(-35.5,   30,    -145.5)
    if style == "CLASSIC_NW":  return   rList(35.5,    30,    -35.5)
    if style == "CLASSIC_NE":  return   rList(35.5,    -30,    35.5)
    if style == "CLASSIC":     return   rList(35.3,    30,    -35.3)
    if style == "TOP":         return   rList(90,      0,      0)      
    if style == "LEFT":        return   rList(0,       0,      90)
    if style == "RIGHT":       return   rList(0,       0,     -90)
    if style == "BACK":        return   rList(0,       0,      180)
    if style == "FRONT":       return   rList(0,       0,      0)
    if style == "BOTTOM":      return   rList(-90,     0,      0)

def _make_joined_object(coll: bpy.types.Collection) -> bpy.types.Object:
    deselect_all_objects()
    for obj in coll.objects:
        if  obj.type == "MESH"\
        and is_obj_visible_by_name(obj.name)\
        and not "lod1" in obj.name.lower():
            set_active_object(obj)

    bpy.ops.object.duplicate(linked=False)
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
    joined_obj = bpy.context.object

    style = _get_cam_position()
    joined_obj.name = "JOINED_OBJECT_FOR_ICON"
    joined_obj.hide_render = False
    joined_obj.rotation_euler = style
    bpy.ops.object.transform_apply(location=False, scale=True, rotation=True)

    bpy.context.scene.collection.objects.link(joined_obj)

    return joined_obj

def _add_view_layer() -> bpy.types.ViewLayer:
    ICON_VW_NAME = "ICON_VIEW_LAYER"
    icon_view_layer = bpy.context.scene.view_layers.get(ICON_VW_NAME, None)

    if not icon_view_layer:
        bpy.ops.scene.view_layer_add(type="NEW")
        icon_view_layer = bpy.context.window.view_layer
        icon_view_layer.name = ICON_VW_NAME

    bpy.context.window.view_layer = icon_view_layer
    for vl_col in  bpy.context.scene.view_layers[ICON_VW_NAME].layer_collection.children:
        vl_col.exclude = True

    return icon_view_layer

def _add_camera(obj: bpy.types.Object, size: int) -> bpy.types.Camera:
    dim_max = max(obj.dimensions)

    cams     = bpy.data.cameras
    icon_cam = cams.get("ICON_CAM", None)

    if not icon_cam:
        new_cam  = cams.new("ICON_CAMERA")
        icon_cam = bpy.data.objects.new("ICON_CAMERA", new_cam)

    if not "ICON_CAMERA" in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(icon_cam)

    icon_cam.data.type        = "ORTHO"
    icon_cam.data.show_limits = False
    icon_cam.data.ortho_scale = dim_max / size
    icon_cam.data.clip_end    = 10_000
    
    bpy.context.scene.camera  = icon_cam

    icon_cam.location       = obj.location
    icon_cam.location[1]    = obj.location[1] - dim_max*2
    icon_cam.rotation_euler = rList(90, 0, 0)

    return icon_cam


def generate_collection_icon(coll: bpy.types.Collection, export_path: str = None):
    tm_props           = get_global_props()
    overwrite_icon     = tm_props.CB_icon_overwriteIcons
    icon_name          = get_path_filename(export_path) if export_path is not None else coll.name
    icon_size          = tm_props.NU_icon_padding / 100
    current_view_layer = bpy.context.window.view_layer
    current_selection  = bpy.context.selected_objects.copy()

    if overwrite_icon is False and export_path:
        if is_file_exist(export_path):
            debug(f"icon creation cancelled, <{ icon_name }> already exists")
            return

    debug(f"creating icon <{icon_name}>")
    
    joined_obj = _make_joined_object(coll)
    _add_view_layer()

    # HIDE ALL BUT JOINED
    dim_max = max(joined_obj.dimensions)
    for obj in bpy.context.scene.collection.objects:
        if obj.name != joined_obj.name:
            obj.hide_render = True

    # CAM------------------
    camera = _add_camera(joined_obj, icon_size)
    
    # RENDER----------------------
    bpy.context.scene.render.image_settings.file_format = "TARGA"
    bpy.context.scene.render.filepath = export_path if export_path is not None else ""
    bpy.context.scene.render.use_single_layer = True
    bpy.context.scene.render.resolution_x = int(tm_props.LI_icon_pxDimension)
    bpy.context.scene.render.resolution_y = int(tm_props.LI_icon_pxDimension)
    bpy.context.scene.eevee.taa_render_samples = 16

    generate_world_node()

    bpy.ops.render.render(write_still=export_path is not None)

    # CLEAN UP -----------------
    bpy.context.window.view_layer = current_view_layer
    bpy.data.objects.remove(joined_obj, do_unlink=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    for obj in current_selection:
        try: set_active_object(obj)
        except: pass

    debug(f"created icon <{icon_name}>")

    if export_path is None:
        bpy.ops.render.view_show("INVOKE_DEFAULT")



def generate_world_node():
    worlds   = bpy.data.worlds
    tm_world = "tm_icon_world"
    white    = (1,1,1,1)
    scene    = bpy.context.scene
    
    if not tm_world in worlds:
        worlds.new( tm_world )
    
    tm_world = worlds[ tm_world ]
    tm_world.use_nodes = True
    nodes = tm_world.node_tree.nodes
    links = tm_world.node_tree.links

    scene.world = tm_world

    rgb_node    = "TM_RGB"
    bg_node     = "TM_BACKGROUND"
    output_node = "TM_OUTPUT"
    mix_node    = "TM_MIX_SHADER"
    camera_node = "TM_LIGHT_NODE"
    
    # walrus here? print(a) //ref err ... print(a:=5) //5 ... print(a) //5
    # blender >=2.93 with python 3.9
    reqNodes = [
        rgb_node,
        bg_node,
        output_node,
        mix_node,
        camera_node
    ]

    allFine = True
    
    for required_node in reqNodes:
        if required_node not in nodes:

            allFine = False
            debug("generate world node, atleast one was missing")
            for node in nodes: nodes.remove(node) #clear all

            nodes.new("ShaderNodeRGB" )         .name = rgb_node
            nodes.new("ShaderNodeBackground")   .name = bg_node
            nodes.new("ShaderNodeOutputWorld")  .name = output_node
            nodes.new("ShaderNodeMixShader")    .name = mix_node
            nodes.new("ShaderNodeLightPath")    .name = camera_node
            break

    if allFine: return

    xy = lambda x,y:  ((150*x), -(200*y))
    
    camera_node = nodes[camera_node]
    camera_node.location = xy(0,0)
    
    rgb_node = nodes[rgb_node]
    rgb_node.outputs[0].default_value = white
    rgb_node.location = xy(0,2)
    
    bg_node = nodes[bg_node]
    bg_node.location = xy(0,3) 
    
    mix_node = nodes[mix_node]
    mix_node.location = xy(2,2)
    
    output_node = nodes[output_node]
    output_node.location = xy(4,2)
    
    links.new( camera_node.outputs[0],  mix_node.inputs[0])
    links.new( rgb_node.outputs[0],     mix_node.inputs[1])
    links.new( bg_node.outputs[0],      mix_node.inputs[2])
    links.new( mix_node.outputs[0],     output_node.inputs[0])

def get_icon_path_from_fbx_path(filepath) -> str:
    icon_path = get_path_filename(filepath)
    icon_path = filepath.replace(icon_path, f"/Icon/{icon_path}")
    icon_path = re.sub("fbx", "tga", icon_path, re.IGNORECASE)
    return fixSlash(icon_path)