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
        tm_props = get_global_props()
        
        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
        elif not tm_props.ST_author:
            show_report_popup("Author name is empty!", ["Please fill in your name in the author input field", "You can find it in the settings panel of blendermania."], "ERROR")
        else:
            export_and_convert()

        return {"FINISHED"}


class TM_OT_Items_Export_ExportAndOrConverFailedOnes(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_failed_ones"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert the collection which failed in the last approach"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash
        
    def execute(self, context):
        tm_props = get_global_props()
        
        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
        elif not tm_props.ST_author:
            show_report_popup("Author name is empty!", ["Please fill in your name in the author input field", "You can find it in the settings panel of blendermania."], "ERROR")
        else:
            export_and_convert(only_failed_ones=True)

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





def export_and_convert(only_failed_ones: bool=False):
    tm_props = get_global_props()
    failed = get_convert_items_failed_props()
    
    selected_only = tm_props.LI_exportWhichObjs == "SELECTED"

    objs = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
    objs = [obj.object for obj in failed.objects] if only_failed_ones else objs

    # atleast one object whose name startswith _item_ is selected
    if single_objs := get_exportable_objects(objs):
        return export_objects(single_objs)
    
    # export normal way
    if colls := get_exportable_collections(objs):
        return export_collections(colls)
    
    show_report_popup("Error", ("No objects/collections found to export!",))

    
    
