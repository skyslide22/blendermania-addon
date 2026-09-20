from ast import main
import bpy
from bpy.types import (Panel)

from ..operators.OT_Items_ExportV2 import TM_OT_Items_ExportV2

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..utils.Functions      import *

class TM_PT_Items_ExportV2(Panel):
    bl_label   = "Export Items V2"
    bl_idname  = "TM_PT_Items_ExportV2"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    # @classmethod
    # def poll(self, context):
    #     return is_selected_nadeoini_file_name_ok()


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_EXPORT)

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Export Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here configure the export settings",
            "1. Select your game",
            "2. Select your destination folder (needs to be in Trackmania/Works/Items/<HERE>)",
            "3. Choose your preferred way of the collection which will be exported",
            "4. Enable optional features",
            "----> 'Multi Convert' will convert your exported items all at the same time", 
            "----> 'Notify' will make a popup in windows which informs you that the convert is finished", 
            "5. Export your collection(s)",
            "----> Files for the meshmodeler import can be generated optionally", 
            "",
            "Keep in mind, collections are exported, not individual objects",
            "-> If you want to export objecs only, mark them as _item_",
            "",
            "Embed size means the item file size, the total map maximums embed size are:",
            f"-> {MAX_EMBED_SIZE_TRACKMANIA2020} kilobytes for trackmania2020",
            f"-> {MAX_EMBED_SIZE_MANIAPLANET} kilobytes for maniaplanet",
        )

    def draw(self, context):
        tm_props = get_global_props()
        show_convert_panel = tm_props.CB_showConvertPanel
        show_invalid_materials_panel = tm_props.CB_showInvalidMatsPanel

        draw_export_panel(self)

        
        



def draw_export_panel(self:Panel) -> None:
    layout = self.layout
    tm_props = get_global_props()

    # simple export button
    row = layout.row(align=True)
    row.operator(TM_OT_Items_ExportV2.bl_idname, text="Export Collection", icon=ICON_EXPORT)




