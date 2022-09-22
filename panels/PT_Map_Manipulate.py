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
from ..utils.Constants import * 
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

    def draw_header_preset(self, context):
        tm_props = get_global_props()
        layout = self.layout
        layout.prop(tm_props, "CB_map_use_grid_helper", text="Grid Helper", icon=ICON_GRID)

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        has_map_file = len(tm_props.ST_map_filepath) != 0
        has_map_coll = tm_props.PT_map_collection is not None

        # info and settings
        # box = layout.box()


        # map collection
        main_col = layout.column(align=True)
        
        # map collection
        if is_game_maniaplanet():
            row = main_col.row(align=True)
            row.prop(tm_props, "LI_DL_TextureEnvi", text="Envi", )#icon=ICON_ENVIRONMENT)
        
        row = main_col.row(align=True)
        row.alert = not has_map_coll
        row.prop(tm_props, "PT_map_collection", text="Map")
        # row = col_right.row(align=True)
        # row.operator(OT_UIValidateMapCollection.bl_idname, text="Validate Map", icon=ICON_UPDATE)
        # row = col_left.row(align=True)
        # row.label(text=" ") # spacer

        # map file path gbx
        row = main_col.row(align=True)
        row.alert = not has_map_file
        row.prop(tm_props, "ST_map_filepath", text="Map File")

        
        


class PT_UIMapExport(bpy.types.Panel):
    bl_label   = "Map Export"
    bl_idname  = "PT_UIMapExport"
    bl_context = "objectmode"
    bl_parent_id = "TM_PT_Map_Manipulate"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw_header_preset(self, context):
        tm_props = get_global_props()
        layout = self.layout
        row = layout.row()
        add_ui_wiki_icon(row, "08.-Map-export")

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        has_map_file = len(tm_props.ST_map_filepath) != 0
        has_map_coll = tm_props.PT_map_collection is not None


        if not is_blendermania_dotnet_installed():
            row = layout.row()
            row.alert = True
            row.label(text="Blendermania dotnet installation required")
            
            row = layout.row()
            row.scale_y = 1.5
            text = f"Install blendermania-dotnet"
            row.operator("view3d.tm_install_blendermania_dotnet", text=text, icon=ICON_UGLYPACKAGE)

            render_donwload_progress_bar(layout)
            return
        
        main_col = layout.column(align=True)
        main_row = main_col.row(align=True)
        col_left = main_row.column(align=True)
        # col_left.scale_x = 0.6
        col_right = main_row.column(align=True)
        
        row = col_left.row()
        row.enabled = not tm_props.CB_map_use_overwrite
        row.label(text="Map Suffix", )#icon=ICON_FILE_NEW)
        row = col_right.row()
        row.enabled = not tm_props.CB_map_use_overwrite
        row.prop(tm_props, "ST_map_suffix", text="")

        row = col_right.row()
        row.enabled = True
        row.prop(tm_props, "CB_map_use_overwrite", text="Overwrite Map", toggle=True, icon=ICON_ERROR)
        row = col_left.row()
        row.label(text=" ")

        
        # col_left.separator(factor=2)
        # col_right.separator(factor=2)
        
        row = col_left.row(align=True)
        row.label(text="Clean", )#icon=ICON_EDIT)
        # row.scale_x = 1.3
        
        row_right = col_right.row(align=True)
        # row_right.scale_x = 0.5
        col_sub_left = row_right.column(align=True)
        col_sub_left.enabled = False
        col_sub_left.prop(tm_props, "CB_map_clean_blocks", text="Blocks", toggle=True)
        
        col_sub_middle = row_right.column(align=True)
        col_sub_middle.enabled = True
        col_sub_middle.prop(tm_props, "CB_map_clean_items", text="Items", toggle=True)
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = has_map_file and has_map_coll
        row.operator(OT_UICollectionToMap.bl_idname, text="Export Map", icon=ICON_EXPORT)

        

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


        if not is_blendermania_dotnet_installed():
            layout.alert = True
            layout.label(text="Blendermania dotnet installation required")
            return
 
        elif not has_map_coll:
            layout.label(text="Select Map collection first")
            return

        elif len(select_objects) > 1 and len(select_map_objects) == 0:
            layout.label(text="To create a new map object select just ONE object")
            return
 
        elif len(select_objects) != 1 and len(select_objects) != len(select_map_objects):
            layout.label(text="Mixed selection: both map objects and other objects selected")
            return
 
        item_action = "Update" if is_update else "Create"
        multi_text = f"s ({len(select_map_objects)})" if len(select_map_objects) > 1 else ""
        layout.label(text=f"{item_action} Item{multi_text} for a Map Collection")

        if is_block:
            row = layout.row()
            row.alert = True
            col = row.column()
            col.scale_y = 0.6
            col.label(text="Blocks are very unstable at the moment")
            col.label(text="probably will be added in the later version")
            #col.label(text="Blocks will be placed on grid")
            #col.label(text="Position will be taken by round(position/32).")
            #col.label(text="Position can not be non-negative")
            #col.label(text="Only rotation on Z axis with 90deg step")
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.enabled = not is_multi
        row.prop(tm_props.PT_map_object, "object_type", text="Type")

        row = col.row(align=True)
        row.enabled = not is_block and not is_multi
        row.prop(tm_props.PT_map_object, "object_item", text="Placeholder")
            
        path_is_valid = tm_props.PT_map_object.object_path.lower().endswith("item.gbx")

        row = col.row(align=True)
        row.enabled = not is_block
        row.alert = not path_is_valid
        path_title = "Name" if is_block else "Item.Gbx"
        row.prop(tm_props.PT_map_object, "object_path", text=f"{path_title}")

        item_gbx_name = (tm_props.PT_map_object.object_path).split("/")[-1].split(".")[0]
        item_btn_icon = ICON_UPDATE if is_update else ICON_ADD
        

        button = layout.row()
        button.scale_y = 1.5
        button.enabled = not is_block and not not not not not not not not not not not not item_gbx_name
        button.operator(
            OT_UICreateUpdateMapItemBlock.bl_idname, 
            text=f"{item_action} Item {item_gbx_name}",
            icon=item_btn_icon)
            

class PT_UIMediatrackerClips(bpy.types.Panel):
    bl_label   = "Mediatracker Clips"
    bl_idname  = "PT_UIMediatrackerClips"
    bl_context = "objectmode"
    bl_parent_id = "TM_PT_Map_Manipulate"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()

        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("view3d.tm_import_mediatracker_clips", text="Import Clips", icon=ICON_IMPORT)
        row.operator("view3d.tm_export_mediatracker_clips", text="Export Clips", icon=ICON_EXPORT)
        
        row = layout.row(align=True)
        row.scale_y = 1.5

        main_col = layout.column(align=True)
        main_row = main_col.row(align=True)
        col_left = main_row.column(align=True)
        col_left.scale_x = 0.6
        col_right = main_row.column(align=True)
        
        row = col_left.row(align=True)
        row.label(text="Clip Name", )
        row = col_right.row(align=True)
        col = col_right.column(align=True)
        row = row.row(align=True)
        row.prop(tm_props, "ST_map_clip_name", text="")
        row.operator("view3d.tm_refresh_mt_clipnames_from_map", text="", icon=ICON_UPDATE)
        row.operator("view3d.tm_select_mt_triggers_by_name",    text="", icon=ICON_SELECT)
        col = col_right.column(align=True)
        col.operator("view3d.tm_change_mt_trigger_clipname", text=f"Assign To Selected ({len(bpy.context.selected_objects)})")

        if not tm_props.CB_allow_complex_panel_drawing:
            return
            
        layout.separator(factor=1.5)
        
        main_col = layout.column(align=True)
        main_row = main_col.row(align=True)
        col_left = main_row.column(align=True)
        col_left.scale_x = 0.6
        col_right = main_row.column(align=True)

        clips = {}
        for obj in bpy.context.selected_objects:
            clip_name = obj.tm_map_clip_name
            if clip_name:
                if clip_name not in clips:
                    clips[clip_name] = 0
                clips[clip_name] += 1 

        row = col_left.row(align=True)
        row.scale_y = 0.6
        row.label(text="Selected:")

        for clip_name, count in clips.items():
            row = col_right.row(align=True)
            row.scale_y = 0.6
            row.label(text=f"({count}) {clip_name}" )

        if len(clips) == 0:
            row = col_right.row(align=True)
            row.scale_y = 0.6
            row.label(text=f"(0) None" )

