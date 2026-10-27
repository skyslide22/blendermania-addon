import bpy
import bmesh
from bpy.props import StringProperty
from ..utils.Constants import UV_LAYER_NAME_LIGHTMAP
from ..properties.PropertyIdentifiers import CollectionProp

from ..utils.FunctionsV2 import is_editor_object_mode, get_item_collections_from_selected, get_active_item_collection, save_blend_file, show_report_popup
from ..utils.ItemsExportV2 import export_and_convert
from ..utils.CustomImporter import plan_item


class OT_ITEMS_analyze_groups(bpy.types.Operator):
    bl_idname = "view3d.analyze_groups"
    bl_label = "Analyze Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_editor_object_mode()

    def execute(self, context):
        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
            return {"CANCELLED"}

        collections = get_item_collections_from_selected(context)
        if not collections:
            show_report_popup("Nothing to analyze", ["Select a collection first"], "ERROR")
            return {"CANCELLED"}

        # exports fbx only (no icon, no gbx)
        items = export_and_convert(collections=collections, plan_only=True)
        if not items:
            return {"CANCELLED"}

        for item in items:
            plan = plan_item(item)
            if plan is None:
                show_report_popup("Plan failed", [f"<{item.name}> could not be analyzed"], "ERROR")
                continue
            apply_plan(context.scene, item.name_raw, plan, item.collection)

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        return {"FINISHED"}


def _get(d: dict, key: str, default=None):
    """json from dotnet may be PascalCase or camelCase"""
    return d.get(key, d.get(key[:1].lower() + key[1:], default))


def apply_plan(scene, item_name: str, plan: dict, collection: bpy.types.Collection) -> None:
    # FbxGbxPlanReport { Version, Groups: [ { Key, Type, OriginalGroupId, LodDistances, Nodes: [ { Name, LodIndices } ] } ] }
    plan_prop = getattr(collection, CollectionProp.ANALYZED_FBXGBX_PLAN)
    plan_prop.groups.clear()


    for group in _get(plan, "Groups", []):
        group_prop = plan_prop.groups.add()
        group_prop.key = _get(group, "Key", "")
        group_prop.group_type = _get(group, "Type", "")
        #group_prop.original_group_id = _get(group, "OriginalGroupId", "")
        lods = _get(group, "LodDistances", [])
        if isinstance(lods, list):
            group_prop.lod_distances = ",".join(str(d) for d in lods)

        group_prop.nodes.clear()
        for node in _get(group, "Nodes", []):
            node_prop = group_prop.nodes.add()
            node_prop.name = _get(node, "Name", "")
            node_prop.obj = scene.objects.get(node_prop.name)
            lod_distances = _get(node, "LodDistances", [])
            if isinstance(lod_distances, list):
                node_prop.lod_indices = ",".join(str(d) for d in lod_distances)


    plan_prop.is_valid = True
    plan_prop.is_stale = False


        # nodes = [_get(n, "Name") for n in _get(group, "Nodes", [])]
        # print(f"[plan] {item_name}: group={_get(group, 'Key')} type={_get(group, 'Type')} lods={_get(group, 'LodDistances')} nodes={nodes}")
        # # TODO: map nodes to blender objects/collections and write properties

class OT_ITEMS_analyze_uv_overlaps(bpy.types.Operator):
    bl_idname = "view3d.analyze_uv_overlaps"
    bl_label = "Analyze UV Overlaps"
    bl_options = {"REGISTER", "UNDO"}

    collection_name: bpy.props.StringProperty(name="Collection Name", default="")
    group_index: bpy.props.IntProperty(name="Group Index", default=-1)

    def execute(self, context):
        from ..utils.UV_Overlap import find_uv_overlaps

        if not save_blend_file():
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")
            return {"CANCELLED"}

        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            self.report({'ERROR'}, "Collection not found")
            return {'CANCELLED'}

        plan_prop = getattr(coll, CollectionProp.ANALYZED_FBXGBX_PLAN)
        if self.group_index < 0:
            groups = plan_prop.groups
        else:
            groups = [plan_prop.groups[self.group_index]] if self.group_index < len(plan_prop.groups) else []

        if len(groups) == 0:
            self.report({'ERROR'}, "No groups found in the plan")
            return {'CANCELLED'}
        
        for group_prop in groups:
            objs = [node.obj for node in group_prop.nodes if node.obj is not None and node.obj.type == 'MESH']
            
            overlaps, skipped = find_uv_overlaps(objs, layer_name=UV_LAYER_NAME_LIGHTMAP)
            if skipped:
                show_report_popup("UV check", [f"No UVs on: {', '.join(skipped)}"], "WARNING")
            overlap_count = len(overlaps)

            setattr(group_prop, "has_uv_overlap", overlap_count > 0)
            setattr(group_prop, "num_uv_overlap_faces", overlap_count)
                
            overlapping_objects = {
                obj_name
                for overlap in overlaps
                for obj_name, face_idx in overlap
            }
            for node in group_prop.nodes:
                node.has_uv_overlap = node.obj is not None and node.obj.name in overlapping_objects

            if overlap_count > 0 and self.group_index >= 0:
                self.select_overlapping_faces(context, overlaps)

        return {"FINISHED"}

    def select_overlapping_faces(self, context, overlaps):
        # Map object names to face indices
        face_map = {}
        for (obj_a, face_a), (obj_b, face_b) in overlaps:
            face_map.setdefault(obj_a, set()).add(face_a)
            face_map.setdefault(obj_b, set()).add(face_b)

        # Switch to Object Mode first
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')

        selected_objects = []
        for obj_name, indices in face_map.items():
            obj = bpy.data.objects.get(obj_name)
            if not obj or obj.type != 'MESH':
                continue

            obj.select_set(True)
            selected_objects.append(obj)

            # Select faces using mesh polygon indices
            for poly in obj.data.polygons:
                poly.select = poly.index in indices

        if not selected_objects:
            return

        context.view_layer.objects.active = selected_objects[0]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')



class TM_OT_select_all_uvs(bpy.types.Operator):
    bl_idname = "tm.select_all_uvs"
    bl_label = "Select All UVs"
    bl_description = ("Select all faces/UVs of the node on the chosen UV layer. "
                      "Other nodes of the group stay visible in the UV editor but unselected")
    bl_options = {'REGISTER', 'UNDO'}

    node_name: StringProperty(name="Node", default="")
    layer_name: StringProperty(name="UV Layer", default="")
    keep_visible: StringProperty(name="Keep Visible", default="")

    def execute(self, context):
        target = bpy.data.objects.get(self.node_name) if self.node_name else context.active_object
        if target is None or target.type != 'MESH':
            self.report({'ERROR'}, "Node is not a mesh")
            return {'CANCELLED'}

        # objects in the edit session: target + the ones that should stay visible
        names = [n.strip() for n in self.keep_visible.split(",") if n.strip()]
        objs = [target]
        for n in names:
            o = bpy.data.objects.get(n)
            if o is not None and o.type == 'MESH' and o not in objs and o.visible_get():
                objs.append(o)

        # 1) leave whatever mode we are in, so selection can change cleanly
        if context.object is not None and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 2) select exactly these objects, the target is active
        for o in context.view_layer.objects:
            o.select_set(False)
        for o in objs:
            o.select_set(True)
        context.view_layer.objects.active = target

        # 3) UV layer: the target must have it, the others get it if they do
        if self.layer_name:
            if target.data.uv_layers.get(self.layer_name) is None:
                self.report({'WARNING'}, f"<{target.name}> has no UV layer '{self.layer_name}'")
                return {'CANCELLED'}
            for o in objs:
                layer = o.data.uv_layers.get(self.layer_name)
                if layer is not None:
                    o.data.uv_layers.active = layer
        elif target.data.uv_layers.active is None:
            self.report({'WARNING'}, f"<{target.name}> has no UV layer")
            return {'CANCELLED'}

        # 4) multi-object edit mode, face select, UV sync on:
        #    unselected faces of the other nodes stay visible in the UV editor
        bpy.ops.object.mode_set(mode='EDIT')
        ts = context.tool_settings
        ts.mesh_select_mode = (False, False, True)
        if hasattr(ts, "use_uv_select_sync"):
            ts.use_uv_select_sync = True
        else:
            self.report({'INFO'}, "Enable UV Sync Selection in the UV editor to see the other nodes")

        # 5) select all faces of the target only
        for o in objs:
            me = o.data
            bm = bmesh.from_edit_mesh(me)             # live edit data, do NOT free
            select = (o == target)
            for f in bm.faces:
                f.select_set(select and not f.hide)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {'IMAGE_EDITOR', 'VIEW_3D'}:
                    area.tag_redraw()
        return {'FINISHED'}
    