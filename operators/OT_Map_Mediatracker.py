import bpy
from ..utils.MediaTracker import (
    export_object_as_triangle
)
from ..utils.Functions import (
    get_global_props,
    show_report_popup,
)

class OT_UIMapExportMediatrackerTriangle(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_mediatracker_triangle"
    bl_description = "Export triangle"
    bl_label = "Export triangle to MediaTracker"
        
    def execute(self, context):
        tm_props = get_global_props()
        sequence = tm_props.LI_map_mt_type
        obj = tm_props.PT_map_mt_triangle_object
        if obj is None:
            show_report_popup("Invalid object!", ["Object is not selected!"], "ERROR")

        message = export_object_as_triangle(obj, tm_props.ST_map_filepath, sequence)
        if message == "SUCCESS":
            show_report_popup(message, ["Triangled added"], "INFO")
        else:
            show_report_popup("Export failed!", [message], "ERROR")

        return {"FINISHED"}
