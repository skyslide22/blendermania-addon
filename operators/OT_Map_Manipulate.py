import bpy

from ..utils.Constants import ICON_ERROR, ICON_SUCCESS

from ..utils.Functions import (
    get_global_props,
    save_blend_file,
    show_report_popup,
)
from ..utils.MapObjects import (
    export_map_collection,
    validate_map_collection,
    create_update_map_object,
    import_mediatracker_clips
)

class OT_UICollectionToMap(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map"
    bl_label = "Export collection to the map"
        
    def execute(self, context):
        if save_blend_file():
            res = export_map_collection()
            if not res.success:
                show_report_popup("Exporting error!", [res.message], "ERROR")
            else:
                show_report_popup("Successfully exported!", ["Map updated successfully. If it contains brand new object you must restart the game!"], "INFO")
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}

    def invoke(self, context, event):
        tm_props = get_global_props()
        ovwr_map = tm_props.CB_map_use_overwrite

        if ovwr_map:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 0.7
        col.alert = True
        col.label(text="Overwriting .Map.Gbx File...")
        col.label(text="Are you sure? This can NOT be undone !!!")


class OT_UIValidateMapCollection(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_validate_map_coll"
    bl_description = "Validate map collection"
    bl_label = "Validate map collection"
        
    def execute(self, context):
        err = validate_map_collection()
        if err:
            show_report_popup("Validation error!", [err], icon=ICON_ERROR)
        else:
            show_report_popup("Map has no issues", icon=ICON_SUCCESS)
        return {"FINISHED"}
        

class OT_UICreateUpdateMapItemBlock(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_create_update_map_item_block"
    bl_description = "Create|Update Item|Block"
    bl_label = "Mark or update map item|block"
        
    def execute(self, context):
        err = create_update_map_object()
        if err:
            show_report_popup("Something wrong!", [err], "ERROR")
        else:
            get_global_props().PT_map_object.object_item = None
            get_global_props().PT_map_object.object_path = ""

        return {"FINISHED"}


class OT_UIImportMediatrackerClips(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_import_mediatracker_clips"
    bl_description = "Import Mediatracker Clips"
    bl_label = "Import Mediatracker Clips"
        
    def execute(self, context):
        res = import_mediatracker_clips()
        if not res.success:
            show_report_popup("Import failed", [
                "Importing of mediatracker clips failed", res.message
            ])
        return {"FINISHED"}