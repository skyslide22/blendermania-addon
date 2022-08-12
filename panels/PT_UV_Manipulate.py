import bpy
import bmesh
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import *




class TM_PT_UVManipulations(Panel):
    bl_label   = "UV Manipulation"
    bl_idname  = "TM_PT_UVManipulations"
    bl_context = "mesh_edit"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="UV")

    def draw(self, context):
        ob = bpy.context.edit_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        layout = self.layout
        scale_box = layout.box()

        enabled = False
        if (
            bpy.context.scene.tool_settings.mesh_select_mode[2] and
            len([f for f in bm.faces if f.select]) > 1
        ):
            enabled = True
            
        row = scale_box.row(align=True)
        row.label(text="UV Unwrap", icon="CON_SIZELIKE")

        if not enabled:
            row = scale_box.row(align=True)
            row.scale_y = 0.5
            row.label(text="In the face selection mode select face loop.'")
            
            row = scale_box.row(align=True)
            row.scale_y = 0.5
            row.label(text="The function will go over each face and unwrap")
            
            row = scale_box.row(align=True)
            row.scale_y = 0.5
            row.label(text="perpendicular face loop with 'follow active quads'")

        row = scale_box.row(align=True)
        row.enabled = enabled
        row.scale_y = 1
        row.operator("wm.tm_follow_active_quads_face_loop", text="Follow active quads for face loop", icon="UV_DATA")
        
