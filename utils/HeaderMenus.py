import bpy
from .FunctionsV2 import is_editor_object_mode

def _draw_header_export(self, context):
    row = self.layout.row()
    row.enabled = bool(context.selected_objects) and is_editor_object_mode()
    op = row.operator("view3d.tm_export_v2", text="Export", icon="EXPORT")
    op.scope = "SELECTED"

def register_header_menus():
    bpy.types.VIEW3D_HT_header.append(_draw_header_export)

def unregister_header_menus():
    bpy.types.VIEW3D_HT_header.remove(_draw_header_export)