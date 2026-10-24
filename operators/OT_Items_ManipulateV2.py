import bpy
from bpy.types import Panel
from bpy.types import Operator
from bpy.props import *

from mathutils import Vector

from ..properties.PropertyFunctions import get_lod_indexes, set_lod_indexes

from ..utils.Functions import *
from ..utils.Constants import * 
from ..properties.PropertyIdentifiers import CollectionProp, ObjectProp

class TM_OT_Lod_Add(bpy.types.Operator):
    bl_idname = "tm.lod_add"
    bl_label = "Add LOD"

    def execute(self, context):
        col = context.collection
        last = col.tm_lods[-1].distance if col.tm_lods else 0.0
        entry = col.tm_lods.add()
        entry.distance = last + 64.0        # larger than the last, so it stays sorted
        return {"FINISHED"}

class TM_OT_Lod_Remove(bpy.types.Operator):
    bl_idname = "tm.lod_remove"
    bl_label = "Remove LOD"

    index: IntProperty()

    def execute(self, context):
        context.collection.tm_lods.remove(self.index)
        return {"FINISHED"}

class TM_OT_Toggle_Lod(bpy.types.Operator):
    bl_idname = "tm.toggle_lod"
    bl_label = "Toggle LOD"

    index: IntProperty()
    tip: StringProperty()

    def execute(self, context):
        obj = context.object
        indexes = set(get_lod_indexes(obj))
        indexes ^= {self.index}   # add if missing, remove if present
        set_lod_indexes(obj, indexes)
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, properties):
        return properties.tip

class TM_OT_Create_Anchor(Operator):
    bl_idname = "tm.create_anchor"
    bl_label = "Create Anchor"
    bl_description = "Create an axis empty in this collection and use it as the moving anchor"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            self.report({'ERROR'}, "Collection not found")
            return {'CANCELLED'}

       #item_collection = get_item_root(coll, context.scene)
        center = self._collection_center(coll)
        empty = bpy.data.objects.new(f"anchor", None)  # None = empty
        empty.empty_display_type = 'ARROWS'    # the 3-axis look
        empty.empty_display_size = 1.0
        empty.location = center
        coll.objects.link(empty)

        setattr(coll, CollectionProp.MOVING_ANCHOR, empty)
        return {'FINISHED'}


    def _collection_center(self, coll):
        """Center of the combined world-space bounding box of all objects in the
        collection hierarchy. Falls back to the origin if nothing has geometry."""
        points = []
        for obj in coll.all_objects:
            if obj.type == 'EMPTY' or not obj.bound_box:
                # no real bounds: use the object's origin
                points.append(obj.matrix_world.translation.copy())
                continue
            for corner in obj.bound_box:
                points.append(obj.matrix_world @ Vector(corner))

        if not points:
            return Vector((0.0, 0.0, 0.0))

        min_v = Vector((min(p[i] for p in points) for i in range(3)))
        max_v = Vector((max(p[i] for p in points) for i in range(3)))
        return (min_v + max_v) / 2

class TM_OT_Texture_Anim_Add(Operator):
    bl_idname = "tm.texture_anim_add"
    bl_label = "Add Texture Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS)
        if len(anims) >= MAX_TEXTURE_ANIMS:
            self.report({'WARNING'}, f"Maximum of {MAX_TEXTURE_ANIMS} animations reached")
            return {'CANCELLED'}
        anims.add()
        return {'FINISHED'}


class TM_OT_Texture_Anim_Remove(Operator):
    bl_idname = "tm.texture_anim_remove"
    bl_label = "Remove Texture Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()
    index: IntProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS)
        if not (0 <= self.index < len(anims)):
            return {'CANCELLED'}
        anims.remove(self.index)
        return {'FINISHED'}

class TM_OT_Trans_Anim_Add(Operator):
    bl_idname = "tm.trans_anim_add"
    bl_label = "Add Translation Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_TRANS_ANIMS)
        if len(anims) >= MAX_ANIMS:
            self.report({'WARNING'}, f"Maximum of {MAX_ANIMS} animations reached")
            return {'CANCELLED'}
        anims.add()
        return {'FINISHED'}


class TM_OT_Trans_Anim_Remove(Operator):
    bl_idname = "tm.trans_anim_remove"
    bl_label = "Remove Translation Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()
    index: IntProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_TRANS_ANIMS)
        if not (0 <= self.index < len(anims)):
            return {'CANCELLED'}
        anims.remove(self.index)
        return {'FINISHED'}

class TM_OT_Rot_Anim_Add(Operator):
    bl_idname = "tm.rot_anim_add"
    bl_label = "Add Rotation Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_ROT_ANIMS)
        if len(anims) >= MAX_ANIMS:
            self.report({'WARNING'}, f"Maximum of {MAX_ANIMS} animations reached")
            return {'CANCELLED'}
        anims.add()
        return {'FINISHED'}


class TM_OT_Rot_Anim_Remove(Operator):
    bl_idname = "tm.rot_anim_remove"
    bl_label = "Remove Rotation Animation"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty()
    index: IntProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            return {'CANCELLED'}
        anims = getattr(coll, CollectionProp.KINEMATIC_ROT_ANIMS)
        if not (0 <= self.index < len(anims)):
            return {'CANCELLED'}
        anims.remove(self.index)
        return {'FINISHED'}