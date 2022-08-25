from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty

from ..utils.ItemsImport import import_item_gbx
from ..utils.Functions import get_game_doc_path, show_report_popup

class TM_OT_ImportItem(Operator, ImportHelper):
    bl_idname = "view3d.import_item_gbx"
    bl_label = "Import item"

    filename_ext = ".gbx"
    filter_glob: StringProperty(
        default='*.gbx;',
        options={'HIDDEN'}
    )

    def execute(self, context):
        err = import_item_gbx(self.filepath)
        if err:
            show_report_popup("Exporting error!", [err], "ERROR")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = get_game_doc_path() + "/"
        wm = context.window_manager.fileselect_add(self)
        print(self.filepath)
        return {'RUNNING_MODAL'}

