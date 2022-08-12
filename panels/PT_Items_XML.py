
import bpy
import re
from bpy.types import (
    Panel,
    Operator,
)
from ..utils.Functions import *
from ..utils.Constants import * 



class TM_PT_Items_ItemXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Item XML file"
    bl_idname = "TM_PT_Items_Export_ItemXML"
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
        row.prop(tm_props, "CB_xml_genItemXML",         text="",    icon_only=True, icon="CHECKMARK",)
        row.prop(tm_props, "CB_xml_overwriteItemXML",   text="",    icon_only=True, icon="FILE_REFRESH")
        row=layout.row()
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()
        
        if tm_props.CB_showConvertPanel \
        or tm_props.CB_xml_genItemXML is False:
            return
        
        
        display_type = tm_props.LI_xml_simpleOrAdvanced
        display_simple = display_type.upper() == "SIMPLE"
        
        layout.label(text="Placement paramters:")

        row = layout.row(align=True)
        row.prop(tm_props, "LI_xml_simpleOrAdvanced", expand=True)

        if isGameTypeManiaPlanet():
            row = layout.row()
            row.prop(tm_props, "LI_materialCollection", text="Envi")

        if display_simple:
            main_col = layout.column(align=True)
            
            x_row = main_col.row(align=True)
            x_row.label(text="", icon ="AXIS_TOP")
            x_row.prop(tm_props, "LI_xml_simpleGridXY", expand=True)
            
            z_row = main_col.row(align=True)
            z_row.label(text="", icon="AXIS_FRONT")
            z_row.prop(tm_props, "LI_xml_simpleGridZ", expand=True)

            gridXYis0 = tm_props.LI_xml_simpleGridXY == "0"
            gridZis0  = tm_props.LI_xml_simpleGridZ  == "0"
            row = main_col.row(align=True)
            row_ghost = row.column(align=True).row(align=True)
            row.prop(tm_props, "CB_xml_ghostMode",   icon="GHOST_DISABLED")
            row_autorot = row.column(align=True).row(align=True)
            row_autorot.enabled = gridXYis0 and gridZis0
            row_autorot.prop(tm_props, "CB_xml_autoRot", icon="GIZMO")


        else: # advanced
            layout.row().prop(tm_props, "CB_xml_syncGridLevi", icon="UV_SYNC_SELECT")
            sync = tm_props.CB_xml_syncGridLevi
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = True if sync else False
            boxRow.prop(tm_props, "NU_xml_gridAndLeviX")
            boxRow.prop(tm_props, "NU_xml_gridAndLeviY")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(tm_props, "NU_xml_gridX")
            boxRow.prop(tm_props, "NU_xml_gridY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "NU_xml_gridXoffset")
            boxRow.prop(tm_props, "NU_xml_gridYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.prop(tm_props, "NU_xml_leviX")
            boxRow.prop(tm_props, "NU_xml_leviY")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "NU_xml_leviXoffset")
            boxRow.prop(tm_props, "NU_xml_leviYoffset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_ghostMode",   icon="GHOST_DISABLED")
            boxRow.prop(tm_props, "CB_xml_autoRot",     icon="GIZMO")
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_oneAxisRot",  icon="NORMALS_FACE")
            boxRow.prop(tm_props, "CB_xml_notOnItem",   icon="SNAP_OFF")
            
            layout.separator(factor=UI_SPACER_FACTOR)
            
            layout.row().prop(tm_props, "CB_xml_pivots",        icon="EDITMODE_HLT")
            
            if tm_props.CB_xml_pivots is True:
                row = layout.row(align=True)
                row.prop(tm_props, "CB_xml_pivotSwitch",    text="Switch")
                row.prop(tm_props, "NU_xml_pivotSnapDis",   text="SnapDist")
                
                row = layout.row(align=True)
                row.operator("view3d.tm_addpivot",    text="Add",       icon="ADD")
                row.operator("view3d.tm_removepivot", text="Delete",    icon="REMOVE")
                # row.operator("view3d.removepivot", text="Del end",   icon="REMOVE")
                
                layout.separator(factor=UI_SPACER_FACTOR)
                
                for i, pivot in enumerate(tm_props_pivots):
                    boxRow = layout.row(align=True)
                    boxRow.prop(tm_props_pivots[i], "NU_pivotX", text="X" )
                    boxRow.prop(tm_props_pivots[i], "NU_pivotY", text="Y" )
                    boxRow.prop(tm_props_pivots[i], "NU_pivotZ", text="Z" )
                    
        layout.separator(factor=UI_SPACER_FACTOR)


class TM_PT_Items_MeshXML(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Mesh XML file"
    bl_idname = "TM_PT_Items_Export_MeshXML"
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
        row.prop(tm_props, "CB_xml_genMeshXML",         text="",            icon_only=True, icon="CHECKMARK")
        row.prop(tm_props, "CB_xml_overwriteMeshXML",   text="",            icon_only=True, icon="FILE_REFRESH")
        row=layout.row()

    
    def draw(self, context):
        layout = self.layout
        tm_props        = get_global_props()
        
        
        if tm_props.CB_showConvertPanel:
            return
    
        if tm_props.CB_xml_genItemXML is False:
            return
        

        layout.label(text="Overwrite all objects/lights settings:")

        #--- object scale
        row = layout.row(align=True)
        col = row.column(align=True)
        col.enabled = True
        col.prop(tm_props, "CB_xml_scale", toggle=True, icon="OBJECT_ORIGIN", text="Object scale")
        col = row.column(align=True)
        col.enabled = False if not tm_props.CB_xml_scale else True
        # col.scale_x = .75
        col.prop(tm_props, "NU_xml_scale", text="")

        
        #--- light power
        col_light = layout.column(align=True)
        row = col_light.row(align=True)
        col = row.column(align=True)
        col.enabled = True
        col.prop(tm_props, "CB_xml_lightPower", icon="OUTLINER_OB_LIGHT", text="Light power")
        col = row.column(align=True)
        col.enabled = False if not tm_props.CB_xml_lightPower else True
        col.prop(tm_props, "NU_xml_lightPower", text="")


        #--- light color
        row = col_light.row(align=True)
        col = row.column(align=True)
        col.enabled = True
        col.prop(tm_props, "CB_xml_lightGlobColor", icon="COLORSET_13_VEC", text="Light color")
        col = row.column(align=True)
        col.enabled = False if not tm_props.CB_xml_lightGlobColor else True
        col.prop(tm_props, "NU_xml_lightGlobColor", text="")
        
        
        #--- light distance
        row = col_light.row(align=True)
        col = row.column(align=True)
        col.enabled = True
        col.prop(tm_props, "CB_xml_lightGlobDistance", icon="LIGHT_SUN", text="Light radius")
        col = row.column(align=True)
        col.enabled = False if not tm_props.CB_xml_lightGlobDistance else True
        col.prop(tm_props, "NU_xml_lightGlobDistance", text="")
        
        

        layout.separator(factor=UI_SPACER_FACTOR)


