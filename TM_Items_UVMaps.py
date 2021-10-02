import bpy
import os.path
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)


from .TM_Functions      import *
from .TM_Items_Convert  import *
from .TM_Items_XML      import *



class TM_PT_Items_UVmaps_LightMap(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "LightMap UVlayer"
    bl_idname = "TM_PT_Items_UVMaps_LightMap"
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
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = context.scene.tm_props
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genLightMap",         text="",    icon_only=True, icon="CHECKMARK",)
        row.prop(tm_props, "CB_uv_fixLightMap",         text="",    icon_only=True, icon="FILE_REFRESH")
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = context.scene.tm_props
        tm_props_pivots = context.scene.tm_props_pivots
        
        if tm_props.CB_showConvertPanel:
            return
    
        if tm_props.CB_uv_genLightMap is True:
            col = layout.column(align=True)
            col.row(align=True).prop(tm_props, "NU_uv_angleLimitLM")
            col.row(align=True).prop(tm_props, "NU_uv_islandMarginLM")
            col.row(align=True).prop(tm_props, "NU_uv_areaWeightLM")
            col.row(align=True).prop(tm_props, "CB_uv_correctAspectLM")
            col.row(align=True).prop(tm_props, "CB_uv_scaleToBoundsLM")
            
                    
        layout.separator(factor=UI_SPACER_FACTOR)


class TM_PT_Items_UVmaps_BaseMaterial_CubeProject(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "BaseMaterial Cube Project"
    bl_idname = "TM_PT_Items_UVMaps_BaseMaterial_CubeProject"
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
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = context.scene.tm_props
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genBaseMaterialCubeMap",  text="", icon_only=True, icon="CHECKMARK",)
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = context.scene.tm_props
        
        if tm_props.CB_showConvertPanel:
            return
            
        row = layout.row(align=True)
        row.alert = tm_props.CB_uv_genBaseMaterialCubeMap
        col = row.column()
        col.label(text="This is a random generator")
        col.label(text="Use it only in development")
        col.separator(factor=UI_SPACER_FACTOR)
        col.label(text="When do i use this?")
        col.label(text="For repating textures (eg. StadiumPlatform)")
            
    
        if tm_props.CB_uv_genBaseMaterialCubeMap is True:
            row = layout.row(align=True)
            row.prop(tm_props, "NU_uv_cubeProjectSize")
                    
        layout.separator(factor=UI_SPACER_FACTOR)




def generateBaseMaterialCubeProject(col) -> None:
    """generate basematerial uvlayer with cube project method, only useful for repeating textures"""
    tm_props    = bpy.context.scene.tm_props
    objs        = [obj for obj in col.all_objects if selectObj(obj)]
    bm_objs     = []

    debug(f"overwrite basematerial with cubeproject for <{col.name}>")

    CUBE_FACTOR = tm_props.NU_uv_cubeProjectSize

    deselectAll()

    for obj in objs:
        if obj.type != "MESH":
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if   "trigger" not in obj.name.lower()\
        and  "socket"  not in obj.name.lower()\
        and  obj.name.startswith("_") is False\
        and  "basematerial" in obj_uvs:
            selectObj(obj)
            setActiveObj(obj)
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




def generateLightmap(col, fix=False) -> None:
    """generate lightmap of all mesh objects from given collection"""
    tm_props    = bpy.context.scene.tm_props
    objs        = [obj for obj in col.all_objects if selectObj(obj)]
    lm_objs     = []

    debug(f"create lightmap for <{col.name}>")

    ANGLE = tm_props.NU_uv_angleLimitLM
    MARGIN= tm_props.NU_uv_islandMarginLM
    AREA  = tm_props.NU_uv_areaWeightLM
    ASPECT= tm_props.CB_uv_correctAspectLM
    BOUNDS= tm_props.CB_uv_scaleToBoundsLM

    has_overlaps = checkUVLayerOverlapsOfCol(col=col, uv_name="LightMap")
    only_if_olaps= tm_props.CB_uv_fixLightMap

    deselectAll()

    #select only objs which need a lightmap
    for obj in objs:
        if obj.type != "MESH":
            continue

        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if   "trigger" not in obj.name.lower()\
        and  "socket"  not in obj.name.lower()\
        and  obj.name.startswith("_") is False\
        and  "lightmap" in obj_uvs:
            selectObj(obj)
            setActiveObj(obj)
            lm_objs.append(obj)

            obj.data.uv_layers.active_index = 1 # 0=BaseMaterial; 1=LightMap
            

    if lm_objs:
        if  only_if_olaps\
        and has_overlaps\
        or  only_if_olaps is False:
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

    
                        


def checkUVLayerOverlapsOfCol(uv_name: str, col: bpy.types.Collection)-> bool:
    """checks if uvlayer has overlapping islands, return bool"""

    deselectAll()
    
    objs = [obj for obj in col.all_objects  if  obj.type == "MESH" \
                                            and obj.name.startswith("_") is False \
                                            and selectObj(obj) ]

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

