import bpy
import os.path
import re
import math
import statistics as stats
from bpy.types import (
    Panel,
    Operator,
)
from .TM_Functions import *




class TM_OT_Items_Icon_Test(Operator):
    """generate test icon, no save"""
    bl_idname = "view3d.tm_make_test_icon"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Open convert report"
        
    def execute(self, context):
        obj = bpy.context.object

        if obj:
            col = obj.users_collection[0]
            generateIcon(col=col, filepath="", save=False)
            selectObj(obj)
            setActiveObj(obj)

        else:
            makeReportPopup("Icon test failed", ["No object selected"], "ERROR")

        return {"FINISHED"}





    
class TM_PT_Items_Icon(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Create Icons"
    bl_idname = "TM_PT_Items_Icon"
    bl_parent_id = "TM_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    @classmethod
    def poll(cls, context):
        tm_props = context.scene.tm_props
        show =  not tm_props.CB_showConvertPanel \
                and not tm_props.LI_exportType.lower() == "convert" \
                and isNadeoIniValid()
        return show
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = context.scene.tm_props
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_icon_genIcons",         text="",    icon_only=True, icon="CHECKMARK",)
        row.prop(tm_props, "CB_icon_overwriteIcons",    text="",    icon_only=True, icon="FILE_REFRESH")
        row=layout.row()
    
    def draw(self, context):
        scene  = context.scene
        layout = self.layout
        tm_props        = scene.tm_props
        tm_props_pivots = scene.tm_props_pivots
        useTransparentBG= scene.render.film_transparent

        layout.row().label(text="Camera direction is positive Y")

        row = layout.row()
        row.prop(tm_props, "LI_icon_perspective", text="Cam")

        #bpy.context.scene.view_settings.view_transform = 'Standard'

        row = layout.row()
        row.prop(scene.view_settings, "view_transform", text="Style")

        row = layout.row()
        row.prop(tm_props, "NU_icon_padding", text="Fill space", expand=True)

        row = layout.row(align=True)
        row2= row.row(align=True)
        row2.label(text="Bground")
        
        row2 = row.row(align=True)
        row2.prop(scene.render, "film_transparent", text="None", toggle=True, icon="GHOST_DISABLED")
        
        row3 = row.row(align=True)
        row3.enabled = True if not useTransparentBG else False
        row3.prop(tm_props, "NU_icon_bgColor",  text="")


        row = layout.row(align=True)
        row2= row.row(align=True)
        row2.label(text="Size")
        
        row2 = row.row(align=True)
        row2.prop(tm_props, "LI_icon_pxDimension", expand=True)

        layout.separator(factor=UI_SPACER_FACTOR)

        row = layout.row()
        row.scale_y = 1
        row.operator("view3d.tm_make_test_icon", text="Do a test render", icon="CAMERA_DATA")

        
        
        
        
        

def generateIcon(col, filepath, save=True) -> None:
    """generate icon of """
    scene           = bpy.context.scene
    col_objs        = [obj for obj in col.all_objects if obj.type == "MESH"]
    tm_props        = scene.tm_props
    overwrite_icon  = tm_props.CB_icon_overwriteIcons
    icon_path       = getIconPathOfFBXpath(filepath=filepath)
    icon_size       = tm_props.NU_icon_padding / 100
    icon_name       = getFilenameOfPath(icon_path)
    objs            = bpy.data.objects
    scene_objs      = scene.collection.objects
    scene_col       = scene.collection
    view_layers     = scene.view_layers
    window          = bpy.context.window
    objs_to_delete  = []
    
    if overwrite_icon is False and save is True:
        if doesFileExist(filepath=icon_path):
            debug(f"icon creation cancelled, <{ icon_name }> already exists")
            return

    debug(f"create icon <icon_name>")


    # MAKE ICON OBJ----------
    deselectAll()

    for obj in col_objs:
        if  obj.type == "MESH"\
        and obj.name.startswith("_") is False\
        and not "lod1" in obj.name.lower():
            if selectObj(obj):
                setActiveObj(obj)

    duplicateObjects()
    joinObjects()

    icon_obj = bpy.context.object
    objs_to_delete.append(icon_obj)
    originToCenterOfMass()

    style = getCamStyle()

    icon_obj.name = "ICON_OBJ"
    icon_obj.hide_render = False
    icon_obj.rotation_euler = style
    bpy.ops.object.transform_apply(location=False, scale=True, rotation=True)
    
    dimX = icon_obj.dimensions[0]
    dimY = icon_obj.dimensions[1]
    dimZ = icon_obj.dimensions[2]
    
    dim_max = max(dimX, dimY, dimZ)

    scene_col.objects.link( icon_obj )

    


    # MAKE VIEW LAYERS-------------
    current_view_layer = bpy.context.scene.view_layers[ window.view_layer.name ]
    ICON_VW_NAME = "ICON_VIEW_LAYER"

    icon_view_layer = view_layers.get(ICON_VW_NAME, None)

    if not icon_view_layer:
        bpy.ops.scene.view_layer_add(type="NEW")
        icon_view_layer = window.view_layer
        icon_view_layer.name = ICON_VW_NAME

    window.view_layer = icon_view_layer

    for vl_col in view_layers[ICON_VW_NAME].layer_collection.children:
        vl_col.exclude = True





    # HIDE ALL ------------------
    for obj in scene.collection.objects:
        if obj.name != icon_obj.name:
            setActiveObj(obj)
            bpy.context.object.hide_render = True
    



    # CAM------------------
    cams     = bpy.data.cameras
    icon_cam = cams.get("ICON_CAM", None)

    if not icon_cam:
        new_cam  = cams.new("ICON_CAMERA")
        icon_cam = objs.new("ICON_CAMERA", new_cam)

    if not "ICON_CAMERA" in scene_objs:
        scene_objs.link(icon_cam)
    
    objs_to_delete.append(icon_cam)

    icon_cam.data.type        = "ORTHO"
    icon_cam.data.show_limits = False
    icon_cam.data.ortho_scale = dim_max / icon_size
    icon_cam.data.clip_end    = 10_000
    
    bpy.context.scene.camera  = icon_cam

    icon_cam.location       = icon_obj.location
    icon_cam.location[1]    = icon_obj.location[1] - dim_max*2
    icon_cam.rotation_euler = rList(90, 0, 0)
    

    # RENDER----------------------
    scene.render.image_settings.file_format = "TARGA"
    scene.render.filepath = icon_path
    scene.render.use_single_layer = True
    scene.render.resolution_x = int(tm_props.LI_icon_pxDimension)
    scene.render.resolution_y = int(tm_props.LI_icon_pxDimension)
    scene.eevee.taa_render_samples = 16

    generateWorldNode()

    bpy.ops.render.render(write_still=save)
    if not save:
        bpy.ops.render.view_show("INVOKE_DEFAULT")

    # CLEAN UP -----------------
    for obj in objs_to_delete:
        deselectAll()
        setActiveObj(obj)
        debug("delete: ", obj.name)
        bpy.ops.object.delete()
    window.view_layer = current_view_layer

    
    



def getCamStyle() -> list:
    """return roation_euler list for the icon_obj"""
    tm_props = bpy.context.scene.tm_props
    style    = tm_props.LI_icon_perspective

    if style == "CLASSIC":  return   rList(35.3,    30,    -35.3)
    if style == "TOP":      return   rList(90,      0,      0)      
    if style == "LEFT":     return   rList(0,       0,      90)
    if style == "RIGHT":    return   rList(0,       0,     -90)
    if style == "BACK":     return   rList(0,       0,      180)
    if style == "FRONT":    return   rList(0,       0,      0)
    if style == "BOTTOM":   return   rList(-90,     0,      0)
    

    
    
    
def generateWorldNode():
    
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    