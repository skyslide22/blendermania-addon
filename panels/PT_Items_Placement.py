
from unittest.mock import patch

import bpy
import re
from bpy.types import (
    Panel,
    Operator,
)

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..properties.Functions import ERROR_ENUM_ID, is_convert_panel_active
from ..utils.Functions import *
from ..utils.Constants import * 



class TM_PT_Items_ItemPlacement(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_Export_ItemPlacement"
    bl_parent_id = "TM_PT_Items_ExportV2"
    # endregion
    
    @classmethod
    def poll(cls, context):
        return not is_convert_panel_active()

    def draw_header(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row()
        row.enabled = tm_props.CB_xml_overwriteItemXML
        row.label(text="Placement Configuration")
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        # col = row.column(align=True)
        # col.label(text="", icon=ICON_CHECKED)

        col = row.column(align=True)
        col.prop(tm_props, "CB_xml_overwriteItemXML",         text="", icon=ICON_UPDATE,)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Item XML Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure the generated item xml file",
            "-> This file is mandatory to convert your object",
            "-> It is recommended to overwrite it on every export",
            "",
            "Simple config",
            "-> Choose a placement value for X and Y axis in meters",
            "-> Choose a placement value for the Z axis in meters (one block in-game is 32x32x8 meters)",
            "-> 'Ghostmode' will allow you to place it inside/ontop other objects",
            "-> 'Auto Rotation' will auto rotate your object based on the location (grid X, Y & Z needs to be 0/manget)",
            "",
            "Advanced config",
            "-> You can sync the placement settings for X, Y & Z ",
            "-> Set the placement params for X, Y & Z ",
            "-> Set the placement offset (0 is recommended from docs) ",
            "-> 'Ghostmode' will allow you to place it inside/ontop other objects",
            "-> 'Auto Rotation' will auto rotate your object based on the location (grid X, Y & Z needs to be 0/manget)",
            "-> 'Not on Item' the item cannot be placed on another item",
            "-> 'One Axis Rotation' the item can only be roated in the Z axis (! might be wrong)",
            "-> 'Pivots' are placement variants, aka offsets from the original origin (choose custom positions)",
            "----> If the switch is activated, you need to manually pivot with the Q/A key",
            "----> Snap distance will snap other items to this pivot", 
            # "-> ",
            # "-> ",
            # "-> ",
            # "-> ",
            # "----> ", 
            # "----> ", 
            # "----> ", 
            # "----> ", 

        )        
    
    def draw(self, context):

        layout = self.layout
        tm_props        = get_global_props()
        tm_props_pivots = get_pivot_props()
        
        if tm_props.CB_showConvertPanel:
            return
        
        layout.enabled = tm_props.CB_xml_overwriteItemXML
        
        # row = layout.row(align=True)
        # row.prop(tm_props, "CB_xml_overwriteItemXML",   text="Overwrite on export (recommended)")

        display_type     = tm_props.LI_xml_simpleOrAdvanced
        display_simple   = display_type.upper() == "SIMPLE"
        display_advanced = display_type.upper() == "ADVANCED"
        display_template = display_type.upper() == "TEMPLATE"
        
        layout.label(text="Placement Parameters:")

        row = layout.row(align=True)
        row.prop(tm_props, "LI_xml_simpleOrAdvanced", expand=True)

        if is_game_maniaplanet():
            row = layout.row()
            row.prop(tm_props, "LI_materialCollection", text="Envi")

        if display_simple:
            main_col = layout.column(align=True)
            
            x_row = main_col.row(align=True)
            x_row.label(text="Grid "+CHAR_HORIZONTAL, )
            x_row.prop(tm_props, "LI_xml_simpleGridXY", expand=True)
            
            z_row = main_col.row(align=True)
            z_row.label(text="Grid "+CHAR_VERTICAL)
            z_row.prop(tm_props, "LI_xml_simpleGridZ", expand=True)

            
            row = layout.row(align=True)
            
            col_ghost = row.column(align=True)
            col_ghost.prop(tm_props, "CB_xml_ghostMode",   icon=ICON_GHOSTMODE)
            
            placements_are_0 = tm_props.LI_xml_simpleGridXY == "0" and tm_props.LI_xml_simpleGridZ  == "0"

            col_autorot = row.column(align=True)
            col_autorot.enabled = placements_are_0
            col_autorot.prop(tm_props, "CB_xml_autoRot", icon=ICON_GHOSTMODE)

            row = layout.row()
            row.operator("view3d.tm_save_item_placement_template", text="Save as Template", icon=ICON_SAVE)


        elif display_advanced: # advanced
            sync = tm_props.CB_xml_syncGridLevi
            boxCol = layout.column(align=True)
            row = boxCol.row()
            row.prop(tm_props, "CB_xml_syncGridLevi", text="Sync Grid & Levitation", icon=ICON_SYNC)
            
            if sync:
                boxRow = boxCol.row(align=True)
                boxRow.enabled = True if sync else False
                boxRow.prop(tm_props, "NU_xml_gridAndLeviX", text=CHAR_HORIZONTAL+" Place")
                boxRow.prop(tm_props, "NU_xml_gridAndLeviY", text=CHAR_VERTICAL+" Place")
                boxRow = boxCol.row(align=True)
                boxRow.enabled = True if sync else False
                boxRow.prop(tm_props, "NU_xml_gridAndLeviOffsetX", text=CHAR_HORIZONTAL+" Offset")
                boxRow.prop(tm_props, "NU_xml_gridAndLeviOffsetY", text=CHAR_VERTICAL+" Offset")
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.label(text="Grid")
            boxRow.prop(tm_props, "NU_xml_gridX", text=CHAR_HORIZONTAL)
            boxRow.prop(tm_props, "NU_xml_gridY", text=CHAR_VERTICAL)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.label(text="Offset")
            boxRow.prop(tm_props, "NU_xml_gridXoffset", text=CHAR_HORIZONTAL)
            boxRow.prop(tm_props, "NU_xml_gridYoffset", text=CHAR_VERTICAL)
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.label(text="Levitation")
            boxRow.prop(tm_props, "NU_xml_leviX", text=CHAR_HORIZONTAL)
            boxRow.prop(tm_props, "NU_xml_leviY", text=CHAR_VERTICAL)
            boxRow = boxCol.row(align=True)
            boxRow.enabled = False if sync else True
            boxRow.label(text="Offset")
            boxRow.prop(tm_props, "NU_xml_leviXoffset", text=CHAR_HORIZONTAL)
            boxRow.prop(tm_props, "NU_xml_leviYoffset", text=CHAR_VERTICAL)
            
            boxCol = layout.column(align=True)
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_ghostMode",   icon=ICON_GHOSTMODE)
            boxRow.prop(tm_props, "CB_xml_autoRot",     icon=ICON_AUTO_ROTATION)
            boxRow = boxCol.row(align=True)
            boxRow.prop(tm_props, "CB_xml_oneAxisRot",  icon=ICON_ONE_AXIS_ROTATION)
            boxRow.prop(tm_props, "CB_xml_notOnItem",   icon=ICON_NOT_ON_ITEM)
            
            pivot_col = layout.column(align=True)
            pivot_row=pivot_col.row(align=True)
            pivot_row.prop(tm_props, "CB_xml_pivots", text="Pivots (Placement Variants)", icon=ICON_PIVOTS)
            
            if tm_props.CB_xml_pivots is True:
                row = pivot_col.row(align=True)
                row.operator("view3d.tm_addpivot", text="Add", icon=ICON_ADD)
                row.prop(tm_props, "CB_xml_pivotSwitch",    text="Switch", expand=True, icon=ICON_SWITCH)
                row.prop(tm_props, "NU_xml_pivotSnapDis",   text="Snap Distance")
                
                
                if len(tm_props_pivots):
                    pivot_box = layout.box()
                    for i, pivot in enumerate(tm_props_pivots):
                        pivot_row = pivot_box.row(align=True)

                        # Left: Pos + Rot
                        values = pivot_row.column(align=True)

                        pos_row = values.row(align=True)
                        pos_row.label(text="Pos", translate=False)
                        pos_row.prop(pivot, "NU_pivotX", text=CHAR_BOTTOM_LEFT)
                        pos_row.prop(pivot, "NU_pivotY", text=CHAR_BOTTOM_RIGHT)
                        pos_row.prop(pivot, "NU_pivotZ", text=CHAR_TOP)

                        rot_row = values.row(align=True)
                        rot_row.label(text="Rot", translate=False)
                        rot_row.prop(pivot, "NU_pivotRotX", text="x")
                        rot_row.prop(pivot, "NU_pivotRotY", text="y")
                        rot_row.prop(pivot, "NU_pivotRotZ", text="z")

                        # Right: one button spanning both rows
                        remove_col = pivot_row.column(align=True)
                        remove_col.operator(
                            "view3d.tm_removepivot",
                            text="",
                            icon=ICON_REMOVE
                        ).pivot_index = i

            placement_cube_col = layout.column(align=True)
            placement_cube_row=placement_cube_col.row(align=True)
            placement_cube_row.prop(tm_props, "CB_cfg_placementCube", text="Placement Cube", icon=ICON_CUBE)
            if tm_props.CB_cfg_placementCube is True:
                row = placement_cube_col.row(align=True)
                row.prop(tm_props, "NU_cfg_cubeSize", text="Cube Size")
                row = placement_cube_col.row(align=True)
                row.prop(tm_props.PT_cfg_cubeCenter, "NU_centerX", text=CHAR_BOTTOM_LEFT)
                row.prop(tm_props.PT_cfg_cubeCenter, "NU_centerY", text=CHAR_BOTTOM_RIGHT)
                row.prop(tm_props.PT_cfg_cubeCenter, "NU_centerZ", text=CHAR_TOP)

            attachment_pattern_col = layout.column(align=True)
            attachment_pattern_row=attachment_pattern_col.row(align=True)
            attachment_pattern_row.prop(tm_props, "CB_cfg_attachmentConfiguration", text="Attachment Configuration", icon=ICON_LINKED, toggle=True)
            if tm_props.CB_cfg_attachmentConfiguration is True:
                row = attachment_pattern_col.row(align=True)
                size_group_row = row.row(align=True)
                size_group_row.enabled = False
                size_group_row.prop(tm_props, "ST_cfg_sizeGroup", text="Size Group")
                row.prop(tm_props, "CB_cfg_alwaysUp", text="Always Up", toggle=True, icon=ICON_AXIS_Z)
                row = attachment_pattern_col.row(align=True)
                row.prop(tm_props, "CB_cfg_alignToInterior", text="Align to Interior", icon="NONE", toggle=True)
                row.prop(tm_props, "CB_cfg_alignToWorldDir", text="Align to World Dir", icon="NONE", toggle=True)
                row = attachment_pattern_col.row(align=True)
                if tm_props.CB_cfg_alignToWorldDir:
                    row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirX", text=CHAR_BOTTOM_LEFT)
                    row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirY", text=CHAR_BOTTOM_RIGHT)
                    row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirZ", text=CHAR_TOP)

                 # ---- Compatible groups  ----
                row = layout.row(align=True)
                row.prop(tm_props, "CB_cfg_showCompatibleGroups", text=f"Compatible Patch Groups ({len(tm_props.LI_cfg_compatibleGroups)})", emboss=False, icon='TRIA_DOWN' if tm_props.CB_cfg_showCompatibleGroups else 'TRIA_RIGHT')
                if tm_props.CB_cfg_showCompatibleGroups:
                    group_box = layout.box()
                    for i, group in enumerate(tm_props.LI_cfg_compatibleGroups):
                        row = group_box.row(align=True)
                        row.prop(group, "name", text="")
                        op = row.operator("view3d.tm_remove_compatible_patch_group", text="", icon='X')
                        op.index = i

                    group_box.operator("view3d.tm_add_compatible_patch_group", text="Add", icon=ICON_ADD)
                # ---- Patch layouts ----
                row = layout.row(align=True)
                row.prop(tm_props, "CB_cfg_showPatchLayouts", text=f"Patch Layouts ({len(tm_props.LI_cfg_patchLayouts)})", emboss=False, icon='TRIA_DOWN' if tm_props.CB_cfg_showPatchLayouts else 'TRIA_RIGHT')

                if tm_props.CB_cfg_showPatchLayouts:
                    row.operator("view3d.tm_add_patch_layout", text="", icon='ADD')
                    for p_idx, patch in enumerate(tm_props.LI_cfg_patchLayouts):
                                # gap between layouts

                        patch_box = layout.box()

                        # Header in its own sub-box so it looks like a title bar
                        header_box = patch_box.box()
                        header = header_box.row(align=True)
                        header.label(text=f"#{p_idx + 1}", icon='MOD_ARRAY')
                        header.prop(patch, "name", text="")
                        op = header.operator("view3d.tm_remove_patch_layout", text="", icon='X')
                        op.index = p_idx

                        # Indented body
                        split = patch_box.split(factor=0.01)
                        split.label(text="")                         # empty left margin
                        body = split.column(align=True)

                        row = body.row(align=True)
                        row.prop(patch, "autoItemCount", text="", icon='AUTO', toggle=True)   # tooltip still shows the full name
                        count = row.row(align=True)
                        count.enabled = not patch.autoItemCount
                        count.prop(patch, "itemCount", text="Count")
                        row.prop(patch, "itemSpacing", text=CHAR_HORIZONTAL +" Spacing")

                        row = body.row(align=True)
                        row.prop(patch, "fillAlignment", text="Fill Align", toggle=True)
                        align_row = row.row(align=True)
                        align_row.enabled = patch.fillAlignment
                        align_row.prop(patch, "fillDirection", text="Fill Direction", expand=True)

                        row = body.row(align=True)
                        row.prop(patch, "normedPos", text=CHAR_HORIZONTAL +" Norm")
                        row.prop(patch, "altitude", text=CHAR_VERTICAL +" Offset")

                        body.separator()
                        body.label(text="Valid for groups:")
                        for g_idx, ref in enumerate(patch.validForGroups):
                            row = body.row(align=True)
                            row.prop_search(ref, "name", tm_props, "LI_cfg_compatibleGroups", text="")
                            op = row.operator("view3d.tm_remove_patch_group_ref", text="", icon='X')
                            op.patch_index = p_idx
                            op.group_index = g_idx
                        op = body.operator("view3d.tm_add_patch_group_ref", text="Add Group", icon='ADD')
                        op.patch_index = p_idx
                
            

            row = layout.row()
            row.operator("view3d.tm_save_item_config_placement_template", text="Save as Template", icon=ICON_SAVE)

            
            
        elif display_template:
            selected_template_name = tm_props.LI_cfg_item_template_globally
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(tm_props, "LI_cfg_item_template_globally")
            row.operator("view3d.tm_remove_item_config_placement_template", text=f"", icon=ICON_REMOVE).template_name = selected_template_name
            #row = layout.row()
            #row.prop(tm_props, "CB_cfg_ignore_assigned_templates", text=f"Ignore assigned templates (force this)", toggle=True, icon=ICON_OVERWRITE)
            
            # if selected_template_name != ERROR_ENUM_ID:
            #     row = col.row()
            #     row.prop(tm_props, "CB_xml_ignore_assigned_templates", text=f"Force on all collections", toggle=True, icon=ICON_EDIT)
            #     row = layout.row()
            

            
        layout.separator(factor=UI_SPACER_FACTOR)


    