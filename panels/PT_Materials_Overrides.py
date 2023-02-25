from bpy.types import (Panel)
from ..properties.Functions import is_convert_panel_active
from ..utils.Functions import *
from ..operators.OT_Materials_Overrides import *

class TM_PT_Items_MaterailsOverwrites(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_MaterailsOverwrites"
    bl_parent_id = "TM_PT_Items_Export"
    # endregion
    
    @classmethod
    def poll(cls, context):
        return not is_convert_panel_active()
    

    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row()
        row.enabled = tm_props.CB_export_MaterialsOverwrites
        row.label(text="Material overrides")

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
        row.enabled = True if not tm_props.CB_showConvertPanel else False
        row.prop(tm_props, "CB_export_MaterialsOverwrites",  text="", icon=ICON_CHECKED,)
        row=layout.row()
    
    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        
        if tm_props.CB_showConvertPanel:
            return
            
        row = layout.row()
        row.scale_y = 0.6
        row.label(text="This pannel allows you to override nadeo materials physics")

        if len(tm_props.DICT_MaterialsOverrides):
            box = layout.box()
            box.enabled = tm_props.CB_export_MaterialsOverwrites
            for i, mat in enumerate(tm_props.DICT_MaterialsOverrides):
                row = box.row(align=False)
            
                row.prop(mat, "link", icon=ICON_LINKED, text="link")
                row.prop(mat, "physic_id", text="physics")
                row.prop(mat, "enabled", text="")
                row.operator(TM_OT_RemoveMaterialOverride.bl_idname, text="", icon=ICON_REMOVE).index = i

        row = layout.row()
        row.enabled = tm_props.CB_export_MaterialsOverwrites
        row.operator(TM_OT_AddMaterialOverride.bl_idname, icon=ICON_ADD)