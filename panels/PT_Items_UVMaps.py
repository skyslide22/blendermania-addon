from bpy.types import (Panel)

from ..utils.Functions import *

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
        tm_props = get_global_props()
        show =  not tm_props.CB_showConvertPanel \
                and not tm_props.LI_exportType.lower() == "convert" \
                and isSelectedNadeoIniFilepathValid()
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genLightMap",         text="",    icon_only=True, icon="CHECKMARK",)
        row.prop(tm_props, "CB_uv_fixLightMap",         text="",    icon_only=True, icon="FILE_REFRESH")
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        
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
        tm_props = get_global_props()
        show =  not tm_props.CB_showConvertPanel \
                and not tm_props.LI_exportType.lower() == "convert" \
                and isSelectedNadeoIniFilepathValid()
        return (show)
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genBaseMaterialCubeMap",  text="", icon_only=True, icon="CHECKMARK",)
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        
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
