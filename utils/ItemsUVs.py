import bpy
from ..utils.Functions      import *

def generate_base_material_cube_projection(coll: bpy.types.Collection) -> None:
    """generate basematerial uvlayer with cube project method, only useful for repeating textures"""
    tm_props    = get_global_props()
    objs        = [obj for obj in coll.objects if select_obj(obj)]
    bm_objs     = []

    debug(f"overwrite basematerial with cubeproject for <{coll.name}>")

    CUBE_FACTOR = tm_props.NU_uv_cubeProjectSize

    deselect_all_objects()

    for obj in objs:
        if obj.type != "MESH":
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if   is_obj_visible_by_name(obj.name)\
        and  "basematerial" in obj_uvs:
            set_active_object(obj)
            bm_objs.append(obj)

            obj.data.uv_layers.active_index = 0 # 0=BaseMaterial; 1=LightMap

    editmode()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(
        cube_size=CUBE_FACTOR, 
        correct_aspect=True,
        scale_to_bounds=False
    )
    objectmode()

def generate_lightmap(col, use_overlapping_check=False) -> None:
    """generate lightmap of all mesh objects from given collection"""
    tm_props    = get_global_props()
    objs        = [obj for obj in col.all_objects if select_obj(obj)]
    lm_objs     = []

    debug(f"create lightmap for <{col.name}>")

    ANGLE = tm_props.NU_uv_angleLimitLM
    MARGIN= tm_props.NU_uv_islandMarginLM
    AREA  = tm_props.NU_uv_areaWeightLM
    ASPECT= tm_props.CB_uv_correctAspectLM
    BOUNDS= tm_props.CB_uv_scaleToBoundsLM
    
    if use_overlapping_check:
        has_overlaps = _check_uv_layer_overlaps_of_col(col=col, uv_name="LightMap")

    deselect_all_objects()

    #select only objs which need a lightmap
    for obj in objs:
        if obj.type != "MESH":
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if is_obj_visible_by_name(obj.name)\
        and "lightmap" in obj_uvs:
            set_active_object(obj)
            lm_objs.append(obj)

            obj.data.uv_layers.active_index = 1 # 0=BaseMaterial; 1=LightMap
            

    if lm_objs:
        if  use_overlapping_check\
        and has_overlaps\
        or  use_overlapping_check is False:
            #editmode with all selected objects
            editmode()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(
                angle_limit     = ANGLE, 
                island_margin   = MARGIN,
                area_weight     = AREA,
                correct_aspect  = ASPECT,
                scale_to_bounds = BOUNDS
            )
            objectmode()
    
    for obj in objs:
        if obj.type != "MESH":
            continue
        
        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        # reset active uvlayer to basematerial
        if "basematerial" in obj_uvs:
            obj.data.uv_layers.active_index = 0 #BaseMaterial

def _check_uv_layer_overlaps_of_col(uv_name: str, col: bpy.types.Collection)-> bool:
    """checks if uvlayer has overlapping islands, return bool"""

    deselect_all_objects()
    
    objs = [obj for obj in col.objects  if  obj.type == "MESH" \
                                            and is_obj_visible_by_name(obj.name) \
                                            and select_obj(obj) ]

    objs_active_layernames = {} # { "myobj123": "BaseMaterial" }

    for obj in objs:
        if len(obj.data.uv_layers) != 0:
            objs_active_layernames[ obj.name ] = obj.data.uv_layers.active.name

    def reset_objs_active_uvlayer():
        for obj_name, uv_name in objs_active_layernames.items():
            bpy.data.objects[ obj_name ].data.uv_layers[ uv_name ].active = True

    debug(f"check overlapping of uvlayer <{uv_name}> for {[obj.name for obj in objs]}")

    try:
        bpy.ops.object. mode_set(mode="EDIT")
        bpy.ops.uv.     select_all(action='DESELECT')
        bpy.ops.uv.     select_overlap() 
        bpy.ops.object. mode_set(mode="OBJECT")

        for obj in objs:
            for loop in obj.data.loops:
                

                try:    uvs = obj.data.uv_layers[ uv_name ].data[ loop.index ]
                except: continue #uvlayer name does not exist

                if uvs.select: 
                    debug("overlapping: True")
                    reset_objs_active_uvlayer()
                    return True

    
    except RuntimeError as err:
        debug(f"lightmap overlap check error: {err}")


    debug("overlapping: False")
    reset_objs_active_uvlayer()
    return False

