from email.policy import default
import bpy

from ..operators.OT_Map_Manipulate import (
    OT_UICollectionToMap,
    OT_UIValidateMapCollection,
    OT_UICreateUpdateMapItemBlock,
)
from ..utils.Functions import get_global_props, requireValidNadeoINI
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS, ICON_MAP, ICON_CUBE
from ..operators.OT_WikiLink import add_ui_wiki_icon



class PT_UIMapManipulation(bpy.types.Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Map export WIP"
    bl_idname  = "TM_PT_Map_Manipulate"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    # endregion

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_MAP)

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        has_map_file = len(tm_props.ST_map_filepath) != 0
        has_map_coll = tm_props.PT_map_collection is not None

        if requireValidNadeoINI(self) is False: return

        # info and settings
        box = layout.box()
        row = box.row()
        row.label(text="Export collection as a map")
        add_ui_wiki_icon(row, "08.-Map-export")

        # map collection
        row = box.row()
        row.alert = not has_map_coll
        row.prop(tm_props, "PT_map_collection", text="Map collection")

        row = box.row()
        row.alert = not has_map_file
        row.prop(tm_props, "ST_map_filepath", text="Map file")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1
        row.enabled = has_map_file and has_map_coll
        row.operator(OT_UIValidateMapCollection.bl_idname)

        row = col.row(align=True)
        row.scale_y = 1.5
        row.enabled = has_map_file and has_map_coll
        row.operator(OT_UICollectionToMap.bl_idname)


class PT_UIMapObjectsManipulation(bpy.types.Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Map Blocks & Items"
    bl_idname  = "TM_PT_Map_Export_Items_Blcoks"
    bl_context = "objectmode"
    bl_parent_id = "TM_PT_Map_Manipulate"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()

        has_map_coll = tm_props.PT_map_collection is not None
        obj = bpy.context.selected_objects[0] if len(bpy.context.selected_objects) > 0 else None

        box = layout.box()

        if not has_map_coll:
            box.label(text="Select Map collection first")
        elif obj and "tm_map_object_kind" in obj:
            box.label(text=f"Update Map Item")
        else:
            box.label(text=f"Create Map Item")
            row = box.row()
            row.prop(tm_props.PT_map_object, "object_type", text="Object type")

            row = box.row()
            row.prop(tm_props.PT_map_object, "object_item", text="Object placeholder")
            
            row = box.row()
            row.prop(tm_props.PT_map_object, "object_path", text=f"Name/Path of {tm_props.PT_map_object.object_type}")

            button = layout.row()
            button.scale_y = 1.5
            button.operator(OT_UICreateUpdateMapItemBlock.bl_idname, text="Create")
            