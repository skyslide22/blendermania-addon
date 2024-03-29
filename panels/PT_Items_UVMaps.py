from bpy.types import (Panel)

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..properties.Functions import is_convert_panel_active

from ..utils.Functions import *

class TM_PT_Items_UVmaps_LightMap(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = ""
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
        row = layout.row()
        row.enabled = tm_props.CB_uv_genLightMap
        row.label(text="UV LightMap")
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        # col = row.column(align=True)
        # col.label(text="", icon=ICON_CHECKED)

        col = row.column(align=True)
        col.prop(tm_props, "CB_uv_genLightMap",         text="", icon=ICON_UPDATE,)
        
        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Lightmap UV Layer Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure the generated lightmap",
            "-> This uv layer is mandatory & created if it does not exist on export",
            "-> It is OPTIONAL to enable this auto generation",
            "-> The lightmap is used to calculate the shadows of your object",
            "----> Think of a 32x32 pixel image, your uv map(lightmap) will be used for this texture", 
            "-> The lightmap should NOT have overlapping islands",
            "-> The lightmap is shared between all objects in a collection, as all objects were one object!",
            "-> Best to make your own lightmap",
            "----> Use 'Mark Seam' (CTRL + E) and then (U) > Unwrap", 
            "----> 'Smart UV Project' (U) is OK, check the addon wiki for more info" , 
            "----> 'Lightmap Pack' (U) is NOT OK, never use this unwrapping method", 
            # "-> ",
            # "-> ",
            # "-> ",
            # "-> ",
            # "----> ", 
            # "----> ", 
            # "----> ", 

        )        

    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        
        if tm_props.CB_showConvertPanel:
            return
    
        # if tm_props.CB_uv_genLightMap is False:
        #     return

        layout.enabled = tm_props.CB_uv_genLightMap

        row = layout.row()
        row.prop(tm_props, "CB_uv_fixLightMap",   text="Generate only when uv islands overlap")
        if tm_props.CB_uv_fixLightMap:
            col = layout.column()
            col.scale_y = 0.7
            col.alert = True
            col.label(text="This can be a very expensive task!")
            col.label(text="This can take up to 16GB RAM, or more")
            col.label(text="This can freeze & crash blender")
            layout.separator(factor=1)


        col = layout.column(align=True)
        col.row(align=True).prop(tm_props, "NU_uv_angleLimitLM")
        col.row(align=True).prop(tm_props, "NU_uv_islandMarginLM")
        col.row(align=True).prop(tm_props, "NU_uv_areaWeightLM")
        
        row = col.row(align=True)
        row.prop(tm_props, "CB_uv_scaleToBoundsLM", expand=True, toggle=True)
        row.prop(tm_props, "CB_uv_correctAspectLM", expand=True, toggle=True)
        
        col = layout.column(align=True)
        col.scale_y = 0.7
        col.alert = True
        col.label(text="Generating the lightmap is not recommended")
        col.label(text="This generator should only be used in development")
        col.label(text="Make your own lightmap at the end of your project!")
        col.label(text="Best to E -> 'Mark Seam' your object")
        col.label(text="   and then U -> 'Unwrap' with some margin")
        # row.label(text="Generating the lightmap is only recommended")
        
                    
        layout.separator(factor=UI_SPACER_FACTOR)


class TM_PT_Items_UVmaps_BaseMaterial_CubeProject(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_UVMaps_BaseMaterial_CubeProject"
    bl_parent_id = "TM_PT_Items_Export"
    # endregion
    
    @classmethod
    def poll(cls, context):
        return not is_convert_panel_active()
    

    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row()
        row.enabled = tm_props.CB_uv_genBaseMaterialCubeMap
        row.alert = tm_props.CB_uv_genBaseMaterialCubeMap
        row.label(text="UV BaseMaterial")
        
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        col.prop(tm_props, "CB_uv_genBaseMaterialCubeMap",         text="", icon=ICON_CHECKED,)
        row=layout.row()


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        col = row.column(align=True)
        col.prop(tm_props, "CB_uv_genBaseMaterialCubeMap",  text="", icon=ICON_UPDATE,)
        
        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.title = "BaseMaterial UV Layer Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure the generated lightmap",
            "-> This uv layer is mandatory & created if it does not exist on export",
            "-> The auto generation on export is optional and for DEV only, uncheck recommended in production",
            "-> The basematerial is used for the texturing of your object, a 2d represenation of your 3d object",
        )  
    
    def draw(self, context):
        layout = self.layout
        tm_props        = get_global_props()
        
        if tm_props.CB_showConvertPanel:
            return
        
        layout.enabled = tm_props.CB_uv_genBaseMaterialCubeMap
            
        row = layout.row(align=True)
        row.alert = tm_props.CB_uv_genBaseMaterialCubeMap
        col = row.column()
        col.scale_y = 0.7
        col.label(text="This is a random generator")
        col.label(text="Use it only in development")
        col.separator(factor=UI_SPACER_FACTOR)
        col.label(text="When do i use this?")
        col.label(text="For repating textures (eg. StadiumPlatform)")
            
    
        if tm_props.CB_uv_genBaseMaterialCubeMap is True:
            row = layout.row(align=True)
            row.prop(tm_props, "NU_uv_cubeProjectSize")
                    
        layout.separator(factor=UI_SPACER_FACTOR)
