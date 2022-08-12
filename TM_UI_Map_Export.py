from bpy.types import (Operator, Panel)

from .TM_Dotnet         import *
from .TM_Functions      import *
from .TM_Items_Export   import *

class PT_UIMapManipulation(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Manipulate Map Files"
    bl_idname  = "TM_PT_Map_Manipulate"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    # endregion
    def draw(self, context):

        layout = self.layout
        tm_props = getTmProps()

        if requireValidNadeoINI(self) is False: return

        row = layout.row()
        row.prop(tm_props, "ST_map_filepath", text="Map file")

        box = layout.box()
        box.operator(OT_UIExportAndCreateMap.bl_idname, text="Export selected collections and place them on a Map")

class OT_UIExportAndCreateMap(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map gbx"
    bl_label = "Save as map"
        
    def execute(self, context):
        if saveBlendFile():
            export_and_place_on_map(getTmProps().ST_map_filepath)
        else:
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}


# External methods
def export_and_place_on_map(map_path: str):
    def callback(exported_items: list[ExportedItem]):
        dotnet_items = list[DotnetItem]()
        for item in exported_items:
            dotnet_items.append(item.to_dotnet_item())
        
        return run_place_objects_on_map(map_path, dotnet_items)

    exportAndOrConvert(callback)