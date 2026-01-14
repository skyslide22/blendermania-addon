import json
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..utils.ServerActions import process_editor_trails
from ..utils.Functions import show_report_popup


class TM_OT_EditorTrails_ImportJSON(Operator, ImportHelper):
    """Import Editor Route from JSON file"""
    bl_idname = "view3d.tm_import_editortrails_json"
    bl_label = "Import Editor Route JSON"

    filter_glob: StringProperty(
        default='*.json',
        options={'HIDDEN'}
    )

    def execute(self, context):
        try:
            with open(self.filepath, 'r') as f:
                json_data = json.load(f)

            # Wrap in list if it's a single object (EditorRoute saves as object, not array)
            if isinstance(json_data, dict):
                json_data = [json_data]

            process_editor_trails(json_data)
            self.report({'INFO'}, f"Imported editor trail from {self.filepath}")
            return {'FINISHED'}

        except json.JSONDecodeError as e:
            show_report_popup("Import Error", [f"Invalid JSON file: {e}"], "ERROR")
            return {'CANCELLED'}
        except Exception as e:
            show_report_popup("Import Error", [str(e)], "ERROR")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
