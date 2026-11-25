import bpy
import bmesh
from ..utils.Functions      import *
from ..utils.FunctionsV2    import get_item_collection_objects

def _is_uv_editable(obj: bpy.types.Object) -> bool:
    """uv operators need edit mode: mesh with faces, visible in the viewport (not disabled/excluded), local data"""
    return (obj.type == "MESH"
            and obj.name in bpy.context.view_layer.objects
            and not obj.hide_viewport and not obj.hide_get() and obj.visible_get()
            and obj.library is None and obj.data.library is None
            and len(obj.data.polygons) > 0)


def _run_uv_op_in_editmode(objs: list[bpy.types.Object], uv_op) -> None:
    """select exactly objs, run uv_op on all their faces in edit mode, always return to object mode"""
    if not objs:
        return
    # bpy.ops.object.select_all skips hidden objects, those would stay selected and break mode_set
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]
    editmode()
    try:
        bpy.ops.mesh.select_all(action='SELECT')
        uv_op()
    finally:
        objectmode()


def generate_base_material_cube_projection(coll: bpy.types.Collection) -> None:
    """generate basematerial uvlayer with cube project method, only useful for repeating textures"""
    tm_props    = get_global_props()
    bpy.context.view_layer.update()   # visible_get() is stale for objects changed since the last depsgraph update
    objs        = [obj for obj in get_item_collection_objects(coll) if select_obj(obj)]
    bm_objs     = []

    debug(f"overwrite basematerial with cubeproject for <{coll.name}>")

    CUBE_FACTOR = tm_props.NU_uv_cubeProjectSize

    deselect_all_objects()

    for obj in objs:
        if not _is_uv_editable(obj):
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if   is_obj_visible_by_name(obj.name)\
        and  "basematerial" in obj_uvs:
            bm_objs.append(obj)

            obj.data.uv_layers.active_index = 0 # 0=BaseMaterial; 1=LightMap

    _run_uv_op_in_editmode(bm_objs, lambda: bpy.ops.uv.cube_project(
        cube_size=CUBE_FACTOR,
        correct_aspect=True,
        scale_to_bounds=False
    ))

def generate_lightmap(col, use_overlapping_check=False) -> None:
    """generate lightmap of all mesh objects from given collection"""
    tm_props    = get_global_props()
    bpy.context.view_layer.update()   # visible_get() is stale for objects changed since the last depsgraph update
    objs        = [obj for obj in get_item_collection_objects(col) if select_obj(obj)]
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
        if not _is_uv_editable(obj):
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if is_obj_visible_by_name(obj.name)\
        and "lightmap" in obj_uvs:
            lm_objs.append(obj)

            if len(obj.data.uv_layers) > 1:
                obj.data.uv_layers.active_index = 1 # 0=BaseMaterial; 1=LightMap
            

    if lm_objs:
        if  use_overlapping_check\
        and has_overlaps\
        or  use_overlapping_check is False:
            #editmode with all selected objects
            _run_uv_op_in_editmode(lm_objs, lambda: bpy.ops.uv.smart_project(
                angle_limit     = ANGLE,
                island_margin   = MARGIN,
                area_weight     = AREA,
                correct_aspect  = ASPECT,
                scale_to_bounds = BOUNDS
            ))
    
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
    
    bpy.context.view_layer.update()   # visible_get() is stale for objects changed since the last depsgraph update
    objs = [obj for obj in get_item_collection_objects(col)  if  obj.type == "MESH" \
                                            and _is_uv_editable(obj) \
                                            and is_obj_visible_by_name(obj.name) ]
    if not objs:
        return False
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]

    objs_active_layernames = {} # { "myobj123": "BaseMaterial" }

    for obj in objs:
        if len(obj.data.uv_layers) != 0:
            objs_active_layernames[ obj.name ] = obj.data.uv_layers.active.name

    def reset_objs_active_uvlayer():
        for obj_name, uv_name in objs_active_layernames.items():
            bpy.data.objects[ obj_name ].data.uv_layers[ uv_name ].active = True

    debug(f"check overlapping of uvlayer <{uv_name}> for {[obj.name for obj in objs]}")

    # select_overlap works on the active uv layer
    for obj in objs:
        layer = obj.data.uv_layers.get(uv_name)
        if layer is not None:
            obj.data.uv_layers.active = layer

    overlapping = False
    try:
        bpy.ops.object. mode_set(mode="EDIT")
        try:
            bpy.ops.mesh.   select_all(action='SELECT')
            bpy.ops.uv.     select_all(action='DESELECT')
            bpy.ops.uv.     select_overlap()

            # Blender 5: with uv sync selection (default) the uv operators select mesh faces, otherwise they set the
            # per loop uv flags (shared by all uv layers, not cleared by a deselect in sync mode). Edit mode only.
            sync = bpy.context.scene.tool_settings.use_uv_select_sync
            for obj in objs:
                if obj.data.uv_layers.get(uv_name) is None:
                    continue #uvlayer name does not exist
                bm = bmesh.from_edit_mesh(obj.data)
                if any(face.select for face in bm.faces) if sync else \
                   any(loop.uv_select_vert for face in bm.faces for loop in face.loops):
                    overlapping = True
                    break
        finally:
            bpy.ops.object. mode_set(mode="OBJECT")

    except RuntimeError as err:
        debug(f"lightmap overlap check error: {err}")
        if bpy.context.mode != "OBJECT":
            objectmode()

    if overlapping:
        debug("overlapping: True")
        reset_objs_active_uvlayer()
        return True


    debug("overlapping: False")
    reset_objs_active_uvlayer()
    return False

