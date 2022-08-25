from bpy.types import (Panel)

from ..properties.Functions import is_convert_panel_active

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
        return not is_convert_panel_active()
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genLightMap",         text="", icon=ICON_CHECKED,)
        row.prop(tm_props, "CB_uv_fixLightMap",         text="", icon=ICON_UPDATE)
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        
        if tm_props.CB_showConvertPanel:
            return
    
        if tm_props.CB_uv_genLightMap is True:

            row = layout.row()
            row.label(text="Generate a dev lightmap with smart uv project")

            col = layout.column(align=True)
            col.row(align=True).prop(tm_props, "NU_uv_angleLimitLM")
            col.row(align=True).prop(tm_props, "NU_uv_islandMarginLM")
            col.row(align=True).prop(tm_props, "NU_uv_areaWeightLM")
            
            row = col.row(align=True)
            row.prop(tm_props, "CB_uv_correctAspectLM", expand=True, toggle=True)
            row.prop(tm_props, "CB_uv_scaleToBoundsLM", expand=True, toggle=True)
            
                    
        layout.separator(factor=UI_SPACER_FACTOR)


class TM_PT_Items_UVmaps_BaseMaterial_CubeProject(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = "BaseMaterial Cube Project"
    bl_idname = "TM_PT_Items_UVMaps_BaseMaterial_CubeProject"
    bl_parent_id = "TM_PT_Items_Export"
    # endregion
    
    @classmethod
    def poll(cls, context):
        return not is_convert_panel_active()
    
    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_uv_genBaseMaterialCubeMap",  text="", icon=ICON_CHECKED,)
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        
        if tm_props.CB_showConvertPanel:
            return
            
        row = layout.row(align=True)
        row.alert = tm_props.CB_uv_genBaseMaterialCubeMap
        col = row.column()
        col.scale_y = 0.6
        col.label(text="This is a random generator")
        col.label(text="Use it only in development")
        col.separator(factor=UI_SPACER_FACTOR)
        col.label(text="When do i use this?")
        col.label(text="For repating textures (eg. StadiumPlatform)")
            
    
        if tm_props.CB_uv_genBaseMaterialCubeMap is True:
            row = layout.row(align=True)
            row.prop(tm_props, "NU_uv_cubeProjectSize")
                    
        layout.separator(factor=UI_SPACER_FACTOR)
