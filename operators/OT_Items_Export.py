import bpy
from bpy.types import (Operator)

from ..utils.ItemsExport import export_collections, export_objects
from ..utils.Functions import *

class TM_OT_Items_Export_ExportAndOrConvert(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash
        
    def execute(self, context):
        if save_blend_file():
            export_and_convert()
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}
    

class TM_OT_Items_Export_CloseConvertSubPanel(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_closeconvertsubpanel"
    bl_description = "Ok, close this panel"
    bl_icon = 'MATERIAL'
    bl_label = "Close Convert Sub Panel"
        
    def execute(self, context):
        close_convert_panel()
        return {"FINISHED"}


def close_convert_panel():
    tm_props                              = get_global_props()
    tm_props.CB_converting                = False
    tm_props.CB_showConvertPanel          = False
    tm_props.CB_stopAllNextConverts       = False
    tm_props.CB_uv_genBaseMaterialCubeMap = False # for stupid mistakes ... :)
    debug("CB_showConvertPanel = " + str(tm_props.CB_showConvertPanel))


def export_and_convert():
    tm_props = get_global_props()
    
    selected_only = tm_props.LI_exportWhichObjs == "SELECTED"

    # atleast one _item_ is selected
    objs = get_exportable_objects(bpy.context.selected_objects    if selected_only 
                                                                else bpy.context.scene.objects)
    if objs:
        return export_objects(objs)


    
    colls = get_exportable_collections(bpy.context.selected_objects   if selected_only 
                                                                    else bpy.context.scene.objects)
    return export_collections(colls)
