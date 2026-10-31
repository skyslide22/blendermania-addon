import bpy
from bpy.types import Panel
from bpy.types import Operator
from bpy.props import *

from mathutils import Vector

from ..properties.PropertyFunctions import get_lod_indexes, set_lod_indexes

from ..utils.Functions import *
from ..utils.FunctionsV2 import get_active_item_collection, get_item_collections_in_hierarchy, get_item_meshes_which_require_uvmaps, get_offset_from_item_origin
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
        center = self._moving_group_origin(coll)
        empty = bpy.data.objects.new(f"anchor", None)  # None = empty
        empty.empty_display_type = 'ARROWS'    # the 3-axis look
        empty.empty_display_size = 1.0
        empty.location = center
        coll.objects.link(empty)

        setattr(coll, CollectionProp.MOVING_ANCHOR, empty)
        return {'FINISHED'}


    def _moving_group_origin(self, coll):
        """World position of the current moving group origin: the anchor if set,
        otherwise the item origin object. Falls back to the world origin."""
        anchor = getattr(coll, CollectionProp.MOVING_ANCHOR, None)
        if anchor is not None:
            return anchor.location.copy()

        offset = get_offset_from_item_origin(list(coll.all_objects))
        return Vector(offset) if offset else Vector((0.0, 0.0, 0.0))

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



class GroupOperatorBase:
    """Base for operators that act on every node of one plan group."""
    bl_options = {'REGISTER', 'UNDO'}

    collection: StringProperty(options={'HIDDEN'})   # collection holding the plan
    group_index: IntProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def get_group(self):
        col = bpy.data.collections.get(self.collection)
        plan = getattr(col, CollectionProp.ANALYZED_FBXGBX_PLAN, None) if col else None
        if plan is None or not (0 <= self.group_index < len(plan.groups)):
            return None
        return plan.groups[self.group_index]

    def get_objects(self, context, group):
        objs = []
        for n in group.nodes:
            o = n.obj
            if o is not None and o.name in context.view_layer.objects:
                objs.append(o)
        return objs

    def process(self, context, group, objs):
        """Override. Return a status string for the info bar, or None."""
        raise NotImplementedError

    def execute(self, context):
        group = self.get_group()
        if group is None:
            self.report({'ERROR'}, "Group no longer exists, re-analyze")
            return {'CANCELLED'}
        objs = self.get_objects(context, group)
        if not objs:
            self.report({'WARNING'}, "No valid objects in group")
            return {'CANCELLED'}
        msg = self.process(context, group, objs)
        if msg:
            self.report({'INFO'}, msg)
        return {'FINISHED'}

class FBX_OT_group_select(GroupOperatorBase, bpy.types.Operator):
    bl_idname = "tm.group_select"
    bl_label = "Select Group Nodes"

    def process(self, context, group, objs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        context.view_layer.objects.active = objs[0]
        return f"Selected {len(objs)} objects"



def showUVMap(col: bpy.types.Collection, uv_name: str, objs=None) -> None:
    if objs is None:
        objs = get_meshes_which_require_uvmaps(col)

    if not objs:
        return show_report_popup(f"Uvlayer not found", f"No object has uvlayer with name '{uv_name}'")
    
    for obj in objs:

        addBasematerialAndLightmap(obj)
        uvs = obj.data.uv_layers
        preferred_uv = uvs.get(uv_name)
        
        if preferred_uv:
            preferred_uv.active = True

def addBasematerialAndLightmap(obj: bpy.types.Object) -> None:
    uvs = obj.data.uv_layers
    
    if len(uvs) == 0: uvs.new(do_init=True)
    if len(uvs) == 1: uvs.new(do_init=True)

    # len is now >= 2
    uvs[0].name = UV_LAYER_NAME_BASEMATERIAL
    uvs[1].name = UV_LAYER_NAME_LIGHTMAP


def editUVMap(col: bpy.types.Collection, uv_name: str, objs=None) -> None:
    if objs is None:
        objs = get_meshes_which_require_uvmaps(col)

    if not objs:
        return show_report_popup(f"No object selected", f"Select normal mesh objects... ")
    
    deselect_all_objects()
    for obj in objs:
        select_obj(obj)
    # multi-object edit mode requires an active object that is part of the selection
    bpy.context.view_layer.objects.active = objs[0]

    preferred_workspace_name = "UV Editing"
    workspace = bpy.data.workspaces.get(preferred_workspace_name)
    
    if workspace is not None:
        bpy.context.window.workspace = workspace

    else: # import workspace from blend file and switch to it
        workspace_path = get_addon_assets_blendfiles_path() + "uvedit_workspace.blend"
        bpy.ops.workspace.append_activate(
            idname=preferred_workspace_name, 
            filepath=workspace_path)
    
    showUVMap(col, uv_name, objs)
    editmode()
    select_all_geometry()  # UV editor only shows selected faces


class TM_OT_Items_ShowUVMapV2(Operator):
    bl_idname = "view3d.tm_showuvmap_v2"
    bl_description = f"Show uv map"
    bl_icon = 'ADD'
    bl_label = f"Show uv map"
    
    uv_name: bpy.props.StringProperty()

    def execute(self, context):
        col = get_active_item_collection()
        if col is None:
            return {'CANCELLED'}
        showUVMap(col, self.uv_name)
        return {"FINISHED"}

class TM_OT_Items_EditUVMapV2(Operator):
    bl_idname = "view3d.tm_edituvmap_v2"
    bl_description = f"Edit uv map"
    bl_icon = 'ADD'
    bl_label = f"Edit uv map"
    
    uv_name: bpy.props.StringProperty()

    def execute(self, context):
        col = get_active_item_collection()
        if col is None:
            return {'CANCELLED'}
        objectmode()
        editUVMap(col, self.uv_name, get_item_meshes_which_require_uvmaps(col))
        return {"FINISHED"}


class OT_ITEMS_select_node_objects(bpy.types.Operator):
    bl_idname = "view3d.select_node_objects"
    bl_label = "Select Objects"
    bl_description = "Select objects (Shift: add, Ctrl: toggle)"
    bl_options = {"REGISTER", "UNDO"}

    obj_names: bpy.props.StringProperty()
    extend: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})
    toggle: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.extend = event.shift
        self.toggle = event.ctrl
        return self.execute(context)

    def execute(self, context):
        names = self.obj_names.split("|")
        objects = [
            bpy.data.objects.get(name)
            for name in names
        ]
        objects = [
            obj for obj in objects
            if obj is not None
            and obj.name in context.view_layer.objects
            and obj.visible_get()
        ]

        if not objects:
            return {'CANCELLED'}

        if context.mode != 'OBJECT' and context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        if not self.extend and not self.toggle:
            for obj in context.selected_objects:
                obj.select_set(False)

        for obj in objects:
            if self.toggle and obj.select_get():
                obj.select_set(False)
            else:
                obj.select_set(True)

        context.view_layer.objects.active = objects[-1]
        return {'FINISHED'}

class TM_OT_Items_ObjectManipulations_CopyScaleToHierarchyV2(Operator):
    bl_idname = "tm.copyhierarchyscale"
    bl_description = "Copy scale of selected object to all objects in collections of type 'default'"
    bl_icon = 'ADD'
    bl_label = "Copy scale of selected object to all children in hierarchy"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        coll = get_active_item_collection()
        target_collections = [x for x in get_item_collections_in_hierarchy(coll) if x is not coll]
        for target_col in target_collections:
            setattr(target_col, CollectionProp.SCALE_ITEM, getattr(coll, CollectionProp.SCALE_ITEM))
            setattr(target_col, CollectionProp.SCALE_MODE, getattr(coll, CollectionProp.SCALE_MODE))
            setattr(target_col, CollectionProp.SCALE_FROM, getattr(coll, CollectionProp.SCALE_FROM))
            setattr(target_col, CollectionProp.SCALE_TO, getattr(coll, CollectionProp.SCALE_TO))
            setattr(target_col, CollectionProp.SCALE_FACTOR, getattr(coll, CollectionProp.SCALE_FACTOR))
            items = getattr(target_col, CollectionProp.SCALE_VALUES)
            items.clear()
            for item in getattr(coll, CollectionProp.SCALE_VALUES):
                items.add().value = item.value

            setattr(target_col, CollectionProp.SCALE_SELECTED_VALUE, 0)

            setattr(target_col, CollectionProp.SCALE_PIVOTS, getattr(coll, CollectionProp.SCALE_PIVOTS))
            setattr(target_col, CollectionProp.SCALE_MAGNETS, getattr(coll, CollectionProp.SCALE_MAGNETS))
            setattr(target_col, CollectionProp.SCALE_LIGHT_DISTANCE, getattr(coll, CollectionProp.SCALE_LIGHT_DISTANCE))
            setattr(target_col, CollectionProp.SCALE_ANIMATION_DISTANCE, getattr(coll, CollectionProp.SCALE_ANIMATION_DISTANCE))
            setattr(target_col, CollectionProp.SCALE_ANIMATION_TIME, getattr(coll, CollectionProp.SCALE_ANIMATION_TIME))
            setattr(target_col, CollectionProp.SCALE_LIGHTMAP_SIZE, getattr(coll, CollectionProp.SCALE_LIGHTMAP_SIZE))

        
        return {"FINISHED"}

def getCollectionNameWithoutScaleSuffix(coll:bpy.types.Collection) -> str:
    return coll.name.split("_#SCALE")[0]


def setScaledCollectionName(col:bpy.types.Collection, remove:bool=False) -> None: 
    tm_props        = get_global_props()
    scale_from      = tm_props.NU_objMplScaleFrom
    scale_to        = tm_props.NU_objMplScaleTo
    scale_factor    = tm_props.NU_objMplScaleFactor
    affect_children = tm_props.CB_objMplScaleRecursive

    collections_to_scale = set()
    collections_to_scale.add(col)

    if affect_children:
        for obj in col.all_objects:
            for child_col in obj.users_collection:
                collections_to_scale.add(child_col)


    for col in collections_to_scale:
        col_name_new = col.name

        if "_#SCALE" in col_name_new or remove:
            col_name_new = col.name.split("_#SCALE")[0]
        
        if not remove:
            col_name_new += f"_#SCALE_{scale_from}to{scale_to}_x{scale_factor}"

        col.name = col_name_new
