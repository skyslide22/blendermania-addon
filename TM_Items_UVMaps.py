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




def generateLightmap(col, fix=False) -> None:
    """generate lightmap of all mesh objects from given collection"""
    tm_props    = bpy.context.scene.tm_props
    objs        = col.all_objects
    lm_objs     = []

    ANGLE = tm_props.NU_uv_angleLimitLM
    MARGIN= tm_props.NU_uv_islandMarginLM
    AREA  = tm_props.NU_uv_areaWeightLM
    ASPECT= tm_props.CB_uv_correctAspectLM
    BOUNDS= tm_props.CB_uv_scaleToBoundsLM

    has_overlaps = False
    only_if_olaps= tm_props.CB_uv_fixLightMap

    deselectAll()

    #select only objs which need a lightmap
    for obj in objs:
        if obj.type == "MESH" is False:
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
            
            if hasUVLayerOverlaps(obj, "LightMap"): 
                has_overlaps: True
            

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
        obj_uvs = [k.lower() for k in obj.data.uv_layers.keys()]

        if "basematerial" in obj_uvs:
            obj.data.uv_layers.active_index = 0 #BaseMaterial

    
                        


def hasUVLayerOverlaps(obj, uvName)-> bool:
    """checks if uvlayer has overlapping islands, return bool"""
    loops = obj.data.loops
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.uv.select_overlap()
    
    bpy.ops.object.mode_set(mode="OBJECT")

    for loop in loops:
        uvs = obj.data.uv_layers[ uvName ].data[loop.index]
        pos = uvs.uv #<vector>
        if uvs.select: return True
    
    return False

