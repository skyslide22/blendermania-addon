import bpy
import bmesh
from bpy.types import Panel
from bpy.types import Operator

from .TM_Functions import *

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
        

class TM_OT_Items_UVManipulationsFollowActiveQuadsForFaceLoop(Operator):
    bl_idname      = "wm.tm_follow_active_quads_face_loop"
    bl_description = "Follow active quads for face loop"
    bl_icon        = 'UV_DATA'
    bl_label       = "Follow active quads for face loop"
   
    def execute(self, context):
        obj = bpy.context.edit_object
        me  = obj.data
        bm  = bmesh.from_edit_mesh(me)

        # get current selected loop
        selected_loop = [f for f in bm.faces if f.select]

        # reset UV for the whole object
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.reset()
        
        # select loop back and unwrap it
        bpy.ops.mesh.select_all(action='DESELECT')
        for selected_face in selected_loop:
            selected_face.select = True

        bpy.ops.uv.unwrap()

        # go over each face in the original loop
        for selected_face in selected_loop:
            # select perpendicular loop
            bpy.ops.mesh.select_all(action='DESELECT')
            selected_face.select = True
            
            bpy.ops.mesh.loop_multi_select()
            for original_face in selected_loop:
                for edge in original_face.edges:
                    edge.select = False
            
            selected_face.select = True
            bm.faces.active = selected_face
            bpy.ops.mesh.loop_to_region()

            # unwrap perpendicular loop
            bpy.ops.uv.follow_active_quads(mode='EVEN')

        # reset selection and select original loop
        bpy.ops.mesh.select_all(action='DESELECT')
        for selected_face in selected_loop:
            selected_face.select = True

        bmesh.update_edit_mesh(me)

        return {"FINISHED"}