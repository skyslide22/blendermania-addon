import bpy
import bmesh
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import *




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