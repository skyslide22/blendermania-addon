import bpy
from ..properties.PropertyIdentifiers import CollectionProp

from ..utils.FunctionsV2 import is_editor_object_mode, get_selected_collections, get_active_item_collection, save_blend_file, show_report_popup
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

        collections = get_selected_collections(context)
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
