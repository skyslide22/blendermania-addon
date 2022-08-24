from email.policy import default
import bpy

from .PT_DownloadProgress import render_donwload_progress_bar
from ..utils.MapObjects import get_selected_map_objects
from ..operators.OT_Map_Manipulate import (
    OT_UICollectionToMap,
    OT_UIValidateMapCollection,
    OT_UICreateUpdateMapItemBlock,
)
from ..utils.Functions import (
    draw_nadeoini_required_message,
    get_global_props,
    is_blendermania_dotnet_installed,
    is_game_maniaplanet,
    is_selected_nadeoini_file_name_ok,
)
from ..utils.Constants import (
    ICON_COLLECTION,
    ICON_UPDATE,
    MAP_OBJECT_BLOCK,
    PANEL_CLASS_COMMON_DEFAULT_PROPS,
    ICON_MAP,
    ICON_UGLYPACKAGE,
    ICON_ENVIRONMENT,
)
from ..operators.OT_WikiLink import add_ui_wiki_icon



class PT_UIMapManipulation(bpy.types.Panel):
    bl_label   = "Map"
    bl_idname  = "TM_PT_Map_Manipulate"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_MAP)

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        has_map_file = len(tm_props.ST_map_filepath) != 0
        has_map_coll = tm_props.PT_map_collection is not None

        # info and settings
        box = layout.box()
        row = box.row()
        row.label(text="Export collection as Map.Gbx", icon=ICON_COLLECTION)
        add_ui_wiki_icon(row, "08.-Map-export")

        if not is_blendermania_dotnet_installed():
            row = box.row()
            row.alert = True
            row.label(text="Blendermania dotnet installation required")
            
            row = box.row()
            row.scale_y = 1.5
            text = f"Install blendermania-dotnet"
            row.operator("view3d.tm_install_blendermania_dotnet", text=text, icon=ICON_UGLYPACKAGE)

            render_donwload_progress_bar(layout)
            return

        # map collection
        if is_game_maniaplanet():
            row = box.row()
            row.prop(tm_props, "LI_DL_TextureEnvi", text="Envi", icon=ICON_ENVIRONMENT)

        row = box.row()
        row.alert = not has_map_coll
        row.prop(tm_props, "PT_map_collection", text="Map collection")

        row = box.row()
        row.alert = not has_map_file
        row.prop(tm_props, "ST_map_filepath", text="Map file")
        
        if not tm_props.CB_map_use_overwrite:
            row = box.row()
            row.prop(tm_props, "ST_map_suffix", text="New map suffix")

            if len(tm_props.ST_map_suffix) == 0:
                row = box.row()
                row.alert = True
                row.label(text='empty suffix: "_modified" will be added')

        row = box.row()
        row.prop(tm_props, "CB_map_use_overwrite")
        if tm_props.CB_map_use_overwrite:
            row = box.row()
            row.alert = True
            row.label(text='this operation CAN NOT be undone')

        row = layout.row()
        row.scale_y = 1
        row.enabled = has_map_file and has_map_coll
        row.operator(OT_UIValidateMapCollection.bl_idname)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.5
        row.enabled = has_map_file and has_map_coll
        row.operator(OT_UICollectionToMap.bl_idname)

        row = col.row(align=True)
        col = row.column(align=True)
        col.enabled = False
        col.prop(tm_props, "CB_map_clean_blocks", icon=ICON_UPDATE)
        row.column(align=True).prop(tm_props, "CB_map_clean_items", icon=ICON_UPDATE)


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
        obj:bpy.types.Object = tm_props.PT_map_object.object_item
        is_update = obj and "tm_map_object_kind" in obj
        is_block = tm_props.PT_map_object.object_type == MAP_OBJECT_BLOCK
        select_objects = bpy.context.selected_objects
        select_map_objects = get_selected_map_objects()
        is_multi = len(select_map_objects) > 1

        box = layout.box()

        if not is_blendermania_dotnet_installed():
            box.alert = True
            box.label(text="Blendermania dotnet installation required")
            return
        elif not has_map_coll:
            box.label(text="Select Map collection first")
        elif len(select_objects) > 1 and len(select_map_objects) == 0:
            box.label(text="To create a new map object select just ONE object")
        elif len(select_objects) != 1 and len(select_objects) != len(select_map_objects):
            box.label(text="Mixed selection: both map objects and other objects selected")
        else:
            title = "Update" if is_update else "Create"
            multi_text = f"s ({len(select_map_objects)})" if len(select_map_objects) > 1 else ""
            box.label(text=f"{title} Map Item{multi_text}")

            if is_block:
                row = box.row()
                row.alert = True
                col = row.column()
                col.scale_y = 0.6
                col.label(text="Blocks are very unstable at the moment")
                col.label(text="probably will be added in the later version")
                #col.label(text="Blocks will be palced on grid")
                #col.label(text="Position will be taken by round(position/32).")
                #col.label(text="Position can not be non-negative")
                #col.label(text="Only rotation on Z axis with 90deg step")
            
            
            row = box.row()
            row.enabled = not is_multi
            row.prop(tm_props.PT_map_object, "object_type", text="Object type")

            row = box.row()
            row.enabled = not is_block and not is_multi
            row.prop(tm_props.PT_map_object, "object_item", text="Object placeholder")
                
            row = box.row()
            row.enabled = not is_block
            path_title = "Name" if is_block else "Name/Path"
            row.prop(tm_props.PT_map_object, "object_path", text=f"{path_title} of {tm_props.PT_map_object.object_type}")

            button = layout.row()
            button.scale_y = 1.5
            button.enabled = not is_block
            button.operator(OT_UICreateUpdateMapItemBlock.bl_idname, text=title)
            