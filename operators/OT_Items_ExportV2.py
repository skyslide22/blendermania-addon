import bpy
from bpy.types import (Operator)

from ..utils.FunctionsV2 import *
from ..utils.ItemsExportV2 import *
from ..utils.Animations import disable_animation_preview

class TM_OT_Items_ExportV2(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_v2"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert items"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    scope: bpy.props.EnumProperty(
        name="Scope",
        items=[
            ("PANEL",    "Panel setting", "Use the scope chosen in the export panel"),
            ("SELECTED", "Selected",      "Export only selected objects"),
            ("VISIBLE",  "Visible",       "Export all visible objects"),
            ("COLLECTIONS", "Collections", "Export the selected collections (Outliner selection or active collection)"),
        ],
        default="PANEL",
        options={"SKIP_SAVE"},   # don't remember the last used value
    )

    @classmethod
    def poll(cls, context):
        if not is_editor_object_mode():
            cls.poll_message_set("Only available in Object Mode")  # Blender 3.0+
            return False
        return True
    
    def execute(self, context):
        tm_props = get_global_props()
        disable_animation_preview()

        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
            return {"CANCELLED"}
        
        collections = None
        if self.scope == "COLLECTIONS":
            collections = get_selected_collections(context)
            if not collections:
                show_report_popup("Nothing to export", ["Select a collection first"], "ERROR")
                return {"CANCELLED"}

        export_and_convert(
            which=None if self.scope in ("PANEL", "COLLECTIONS") else self.scope,
            collections=collections,
        )
        return {"FINISHED"}


class TM_OT_Items_Export_ExportAndOrConverFailedOnesV2(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export_failed_ones_v2"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert the collection which failed in the last approach"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    def execute(self, context):
        tm_props = get_global_props()
        disable_animation_preview()

        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
            return {"CANCELLED"}
        
        export_and_convert(only_failed_ones=True)

        return {"FINISHED"}




# def close_convert_panel():
#     tm_props                              = get_global_props()
#     tm_props.CB_converting                = False
#     tm_props.CB_showConvertPanel          = False
#     tm_props.CB_stopAllNextConverts       = False
#     tm_props.CB_uv_genBaseMaterialCubeMap = False # for stupid mistakes ... :)
#     debug("CB_showConvertPanel = " + str(tm_props.CB_showConvertPanel))




