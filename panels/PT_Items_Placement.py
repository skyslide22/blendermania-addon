
from unittest.mock import patch

import bpy
import re
from bpy.types import (
    Panel,
    Operator,
)
from ..properties.PlacementProperties import PlacementProperties

from ..properties.PlacementPatchProperties import CompatiblePatchGroupProperty, PatchGroupRef

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..properties.Functions import ERROR_ENUM_ID, get_item_config_template_names_enum, is_convert_panel_active
from ..utils.Functions import *
from ..utils.Constants import * 
from ..ui.widgets.lists import *
from ..ui.widgets.foldouts import *


# class TM_PT_Items_ItemPlacement(Panel):
#     # region bl_
#     locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
#     bl_label = ""
#     bl_idname = "TM_PT_Items_Export_ItemPlacement"
#     bl_parent_id = ""
#     # endregion
    
#     @classmethod
#     def poll(cls, context):
#         return not is_convert_panel_active()

#     @classmethod
#     def register_callbacks(cls):
#         register_row_drawer(CompatiblePatchGroupProperty, cls.draw_compatible_group_row)
#         register_row_drawer(PatchGroupRef, cls.draw_valid_for_group_row)
#         from ..properties.PannelsPropertyGroup import PannelsPropertyGroup
#         register_list_hooks(PannelsPropertyGroup, "LI_cfg_patchLayouts", after_add=cls.patch_layout_added)
#         # register_list_hooks(bpy.types.Scene, "tm_props_pivots",
#         #                     after_add=cls.pivot_added)
        
#     @classmethod
#     def unregister_callbacks(cls):
#         unregister_row_drawer(CompatiblePatchGroupProperty)
#         unregister_row_drawer(PatchGroupRef)
#         from ..properties.PannelsPropertyGroup import PannelsPropertyGroup
#         unregister_list_hooks(PannelsPropertyGroup, "LI_cfg_patchLayouts")

#     def draw_header(self, context):
#         layout = self.layout
#         tm_props = get_global_props()
#         row = layout.row()
#         row.enabled = tm_props.CB_xml_overwriteItemXML
#         row.label(text="Placement Configuration")
    
#     def draw_header_preset(self, context):
#         layout = self.layout
#         tm_props = get_global_props()
#         row = layout.row(align=True)

#         # col = row.column(align=True)
#         # col.label(text="", icon=ICON_CHECKED)

#         col = row.column(align=True)
#         col.prop(tm_props, "CB_xml_overwriteItemXML",         text="", icon=ICON_UPDATE,)

#         col = row.column(align=True)
#         op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
#         op.link = ""
#         op.title = "Item XML Infos"
#         op.infos = TM_OT_Settings_OpenMessageBox.get_text(
#             "Here you can configure the generated item xml file",
#             "-> This file is mandatory to convert your object",
#             "-> It is recommended to overwrite it on every export",
#             "",
#             "Simple config",
#             "-> Choose a placement value for X and Y axis in meters",
#             "-> Choose a placement value for the Z axis in meters (one block in-game is 32x32x8 meters)",
#             "-> 'Ghostmode' will allow you to place it inside/ontop other objects",
#             "-> 'Auto Rotation' will auto rotate your object based on the location (grid X, Y & Z needs to be 0/manget)",
#             "",
#             "Advanced config",
#             "-> You can sync the placement settings for X, Y & Z ",
#             "-> Set the placement params for X, Y & Z ",
#             "-> Set the placement offset (0 is recommended from docs) ",
#             "-> 'Ghostmode' will allow you to place it inside/ontop other objects",
#             "-> 'Auto Rotation' will auto rotate your object based on the location (grid X, Y & Z needs to be 0/manget)",
#             "-> 'Not on Item' the item cannot be placed on another item",
#             "-> 'One Axis Rotation' the item can only be roated in the Z axis (! might be wrong)",
#             "-> 'Pivots' are placement variants, aka offsets from the original origin (choose custom positions)",
#             "----> If the switch is activated, you need to manually pivot with the Q/A key",
#             "----> Snap distance will snap other items to this pivot", 
#             # "-> ",
#             # "-> ",
#             # "-> ",
#             # "-> ",
#             # "----> ", 
#             # "----> ", 
#             # "----> ", 
#             # "----> ", 

#         )        
    
#     def draw(self, context):

#         layout = self.layout
#         tm_props        = get_global_props()
#         tm_props_pivots = get_pivot_props()
        
#         if tm_props.CB_showConvertPanel:
#             return
        
#         layout.enabled = tm_props.CB_xml_overwriteItemXML
        
#         # row = layout.row(align=True)
#         # row.prop(tm_props, "CB_xml_overwriteItemXML",   text="Overwrite on export (recommended)")

#         display_type     = tm_props.LI_xml_simpleOrAdvanced
#         display_simple   = display_type.upper() == "SIMPLE"
#         display_advanced = display_type.upper() == "ADVANCED"
#         display_template = display_type.upper() == "TEMPLATE"
        
#         layout.label(text="Placement Parameters:")

#         row = layout.row(align=True)
#         row.prop(tm_props, "LI_xml_simpleOrAdvanced", expand=True)

#         if is_game_maniaplanet():
#             row = layout.row()
#             row.prop(tm_props, "LI_materialCollection", text="Envi")

#         if display_simple:
#             main_col = layout.column(align=True)
            
#             x_row = main_col.row(align=True)
#             x_row.label(text="Grid "+CHAR_HORIZONTAL, )
#             x_row.prop(tm_props, "LI_xml_simpleGridXY", expand=True)
            
#             z_row = main_col.row(align=True)
#             z_row.label(text="Grid "+CHAR_VERTICAL)
#             z_row.prop(tm_props, "LI_xml_simpleGridZ", expand=True)

            
#             row = layout.row(align=True)
            
#             col_ghost = row.column(align=True)
#             col_ghost.prop(tm_props, "CB_xml_ghostMode",   icon=ICON_GHOSTMODE)
            
#             placements_are_0 = tm_props.LI_xml_simpleGridXY == "0" and tm_props.LI_xml_simpleGridZ  == "0"

#             col_autorot = row.column(align=True)
#             col_autorot.enabled = placements_are_0
#             col_autorot.prop(tm_props, "CB_xml_autoRot", icon=ICON_GHOSTMODE)

#             row = layout.row()
#             row.operator("view3d.tm_save_item_placement_template", text="Save as Template", icon=ICON_SAVE)


#         elif display_advanced: # advanced
#             sync = tm_props.CB_xml_syncGridLevi
#             boxCol = layout.column(align=True)
#             row = boxCol.row()
#             row.prop(tm_props, "CB_xml_syncGridLevi", text="Sync Grid & Levitation", icon=ICON_SYNC)
            
#             if sync:
#                 boxRow = boxCol.row(align=True)
#                 boxRow.enabled = True if sync else False
#                 boxRow.prop(tm_props, "NU_xml_gridAndLeviX", text=CHAR_HORIZONTAL+" Place")
#                 boxRow.prop(tm_props, "NU_xml_gridAndLeviY", text=CHAR_VERTICAL+" Place")
#                 boxRow = boxCol.row(align=True)
#                 boxRow.enabled = True if sync else False
#                 boxRow.prop(tm_props, "NU_xml_gridAndLeviOffsetX", text=CHAR_HORIZONTAL+" Offset")
#                 boxRow.prop(tm_props, "NU_xml_gridAndLeviOffsetY", text=CHAR_VERTICAL+" Offset")
            
#             boxCol = layout.column(align=True)
#             boxRow = boxCol.row(align=True)
#             boxRow.enabled = False if sync else True
#             boxRow.label(text="Grid")
#             boxRow.prop(tm_props, "NU_xml_gridX", text=CHAR_HORIZONTAL)
#             boxRow.prop(tm_props, "NU_xml_gridY", text=CHAR_VERTICAL)
#             boxRow = boxCol.row(align=True)
#             boxRow.enabled = False if sync else True
#             boxRow.label(text="Offset")
#             boxRow.prop(tm_props, "NU_xml_gridXoffset", text=CHAR_HORIZONTAL)
#             boxRow.prop(tm_props, "NU_xml_gridYoffset", text=CHAR_VERTICAL)
            
#             boxCol = layout.column(align=True)
#             boxRow = boxCol.row(align=True)
#             boxRow.enabled = False if sync else True
#             boxRow.label(text="Levitation")
#             boxRow.prop(tm_props, "NU_xml_leviX", text=CHAR_HORIZONTAL)
#             boxRow.prop(tm_props, "NU_xml_leviY", text=CHAR_VERTICAL)
#             boxRow = boxCol.row(align=True)
#             boxRow.enabled = False if sync else True
#             boxRow.label(text="Offset")
#             boxRow.prop(tm_props, "NU_xml_leviXoffset", text=CHAR_HORIZONTAL)
#             boxRow.prop(tm_props, "NU_xml_leviYoffset", text=CHAR_VERTICAL)
            
#             boxCol = layout.column(align=True)
#             boxRow = boxCol.row(align=True)
#             boxRow.prop(tm_props, "CB_xml_ghostMode",   icon=ICON_GHOSTMODE)
#             boxRow.prop(tm_props, "CB_xml_autoRot",     icon=ICON_AUTO_ROTATION)
#             boxRow = boxCol.row(align=True)
#             boxRow.prop(tm_props, "CB_xml_oneAxisRot",  icon=ICON_ONE_AXIS_ROTATION)
#             boxRow.prop(tm_props, "CB_xml_notOnItem",   icon=ICON_NOT_ON_ITEM)
            
#             pivot_count = len(tm_props_pivots)
#             pivot_body, pivot_header = foldout_toggle(layout, tm_props, 
#                                         "CB_xml_pivots", 
#                                         label=f"Pivots (Placement Variants) ({pivot_count})",
#                                         indent = UI_FOLDOUT_INDENT)
#             if pivot_body:
#                 row = pivot_body.row(align=True)
#                 list_add_button(row, bpy.context.scene, "tm_props_pivots", text="Add", icon=ICON_ADD)
#                 row.prop(tm_props, "CB_xml_pivotSwitch",    text="Switch", expand=True, icon=ICON_SWITCH)
#                 row.prop(tm_props, "NU_xml_pivotSnapDis",   text="Snap Distance")
                
#                 item_list(pivot_body,
#                           bpy.context.scene, 
#                           "tm_props_pivots", 
#                           draw_item=self.draw_pivot,
#                           add_text="Add Pivot")   # add button lives in the foldout header
                

#             # placement_cube_col = layout.column(align=True)
#             # placement_cube_row=placement_cube_col.row(align=True)
#             # placement_cube_row.prop(tm_props, "CB_cfg_placementCube", text="Placement Cube", icon=ICON_CUBE)

#             placement_cube_body, placement_cube_header = foldout_toggle(layout, tm_props, 
#                                                     "CB_cfg_placementCube", 
#                                                     label="Placement Cube",
#                                                     indent = UI_FOLDOUT_INDENT)
#             if placement_cube_body:
#                 row = placement_cube_body.row(align=True)
#                 row.prop(tm_props, "NU_cfg_cubeSize", text="Cube Size")
#                 row = placement_cube_body.row(align=True)
#                 row.prop(tm_props, "PT_cfg_cubeCenter")
#                 #row.label(text="Cube Center:")
#                 # row.prop(tm_props, "PT_cfg_cubeCenter", index=0, text=CHAR_BOTTOM_LEFT)
#                 # row.prop(tm_props, "PT_cfg_cubeCenter", index=1, text=CHAR_BOTTOM_RIGHT)
#                 # row.prop(tm_props, "PT_cfg_cubeCenter", index=2, text=CHAR_TOP)


#             attachment_body, attachment_header = foldout_toggle(layout, tm_props, 
#                                                                 "CB_cfg_show_attachmentConfiguration", 
#                                                                 label="Attachment Configuration",
#                                                                 indent = UI_FOLDOUT_INDENT,
#                                                                 enable_prop="CB_cfg_attachmentConfiguration")
#             if attachment_body:
#                 row = attachment_body.row(align=True)
#                 size_group_row = row.row(align=True)
#                 size_group_row.enabled = False
#                 size_group_row.prop(tm_props, "ST_cfg_sizeGroup", text="Size Group")
#                 row.prop(tm_props, "CB_cfg_alwaysUp", text="Always Up", toggle=True, icon=ICON_AXIS_Z)
#                 row = attachment_body.row(align=True)
#                 row.prop(tm_props, "CB_cfg_alignToInterior", text="Align to Interior", icon="NONE", toggle=True)
#                 row.prop(tm_props, "CB_cfg_alignToWorldDir", text="Align to World Dir", icon="NONE", toggle=True)
#                 row = attachment_body.row(align=True)
#                 if tm_props.CB_cfg_alignToWorldDir:
#                     row.prop(tm_props, "PT_cfg_worldDir")
#                     # row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirX", text=CHAR_BOTTOM_LEFT)
#                     # row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirY", text=CHAR_BOTTOM_RIGHT)
#                     # row.prop(tm_props.PT_cfg_worldDir, "NU_worldDirZ", text=CHAR_TOP)

#                  # ---- Compatible groups  ----
#                 #row = layout.row(align=True)
#                 #row.prop(tm_props, "CB_cfg_showCompatibleGroups", text=f"Compatible Patch Groups ({len(tm_props.LI_cfg_compatibleGroups)})", emboss=False, icon='TRIA_DOWN' if tm_props.CB_cfg_showCompatibleGroups else 'TRIA_RIGHT')
#                 compat_grp_body, compat_grp_header = foldout_toggle(attachment_body, tm_props, 
#                                                                                 "CB_cfg_showCompatibleGroups", 
#                                                                                 label=f"Compatible Patch Groups ({len(tm_props.LI_cfg_compatibleGroups)})",
#                                                                                 indent = UI_FOLDOUT_INDENT,
#                                                                                 style=FOLDOUT_STYLE_FLAT)
#                 if compat_grp_body:
#                     list_inspector(
#                         compat_grp_body, 
#                         tm_props, 
#                         "LI_cfg_compatibleGroups", 
#                         "NU_cfg_compatibleGroups_index", 
#                         rows=3)

#                 # ---- Patch layouts ----
#                 patch_layout_body, patch_layout_header = foldout_toggle(attachment_body, tm_props, 
#                                                                                 "CB_cfg_showPatchLayouts", 
#                                                                                 label=f"Patch Layouts ({len(tm_props.LI_cfg_patchLayouts)})",
#                                                                                 indent = UI_FOLDOUT_INDENT,
#                                                                                 style=FOLDOUT_STYLE_FLAT)
#                 if patch_layout_body:
#                     list_inspector(patch_layout_body,
#                               tm_props,
#                               "LI_cfg_patchLayouts",
#                               "NU_cfg_patchLayouts_index",
#                               draw_detail=self.draw_patch_layout,
#                               rows = 1)


#                     # row.operator("view3d.tm_add_patch_layout", text="", icon='ADD')
#                     # for p_idx, patch in enumerate(tm_props.LI_cfg_patchLayouts):
#                     #             # gap between layouts

#                     #     patch_box = patch_layout_body.box()

#                     #     # Header in its own sub-box so it looks like a title bar
#                     #     header_box = patch_box.box()
#                     #     header = header_box.row(align=True)
#                     #     header.label(text=f"#{p_idx + 1}", icon='MOD_ARRAY')
#                     #     header.prop(patch, "name", text="")
#                     #     op = header.operator("view3d.tm_remove_patch_layout", text="", icon='X')
#                     #     op.index = p_idx

#                     #     # Indented body
#                     #     split = patch_box.split(factor=0.01)
#                     #     split.label(text="")                         # empty left margin
#                     #     body = split.column(align=True)

#                     #     row = body.row(align=True)
#                     #     row.prop(patch, "autoItemCount", text="", icon='AUTO', toggle=True)   # tooltip still shows the full name
#                     #     count = row.row(align=True)
#                     #     count.enabled = not patch.autoItemCount
#                     #     count.prop(patch, "itemCount", text="Count")
#                     #     row.prop(patch, "itemSpacing", text=CHAR_HORIZONTAL +" Spacing")

#                     #     row = body.row(align=True)
#                     #     row.prop(patch, "fillAlignment", text="Fill Align", toggle=True)
#                     #     align_row = row.row(align=True)
#                     #     align_row.enabled = patch.fillAlignment
#                     #     align_row.prop(patch, "fillDirection", text="Fill Direction", expand=True)

#                     #     row = body.row(align=True)
#                     #     row.prop(patch, "normedPos", text=CHAR_HORIZONTAL +" Norm")
#                     #     row.prop(patch, "altitude", text=CHAR_VERTICAL +" Offset")

#                     #     body.separator()
#                     #     body.label(text="Valid for groups:")
#                     #     for g_idx, ref in enumerate(patch.validForGroups):
#                     #         row = body.row(align=True)
#                     #         row.prop_search(ref, "name", tm_props, "LI_cfg_compatibleGroups", text="")
#                     #         op = row.operator("view3d.tm_remove_patch_group_ref", text="", icon='X')
#                     #         op.patch_index = p_idx
#                     #         op.group_index = g_idx
#                     #     op = body.operator("view3d.tm_add_patch_group_ref", text="Add Group", icon='ADD')
#                     #     op.patch_index = p_idx
                
            

#             row = layout.row()
#             row.operator("view3d.tm_save_item_config_placement_template", text="Save as Template", icon=ICON_SAVE)

            
            
#         elif display_template:
#             selected_template_name = tm_props.LI_cfg_item_template_globally
#             col = layout.column(align=True)
#             row = col.row(align=True)
#             row.prop(tm_props, "LI_cfg_item_template_globally")
#             row.operator("view3d.tm_remove_item_config_placement_template", text=f"", icon=ICON_REMOVE).template_name = selected_template_name
#             #row = layout.row()
#             #row.prop(tm_props, "CB_cfg_ignore_assigned_templates", text=f"Ignore assigned templates (force this)", toggle=True, icon=ICON_OVERWRITE)
            
#             # if selected_template_name != ERROR_ENUM_ID:
#             #     row = col.row()
#             #     row.prop(tm_props, "CB_xml_ignore_assigned_templates", text=f"Force on all collections", toggle=True, icon=ICON_EDIT)
#             #     row = layout.row()
            

#         layout.separator(factor=UI_SPACER_FACTOR)


#     @staticmethod
#     def draw_compatible_group_row(layout, item, index):
#         layout.label(text="", icon='DOT')            # click here to select the row
#         layout.prop(item, "name", text="")

#     @staticmethod
#     def draw_valid_for_group_row(layout, item, index):
#         layout.label(text="", icon='DOT')            # click here to select the row
#         layout.prop(item, "name", text="")

#     def draw_pivot(self, layout, item, index):
#         box = layout.box()
#         col = box.column()
#         pos_row = col.row()
#         pos_row.prop(item, "FV_position",text="Pos")

#         # split.label(text="Pos", translate=False)

#         # values.prop(item, "NU_pivotX", text=CHAR_BOTTOM_LEFT)
#         # values.prop(item, "NU_pivotY", text=CHAR_BOTTOM_RIGHT)
#         # values.prop(item, "NU_pivotZ", text=CHAR_TOP)

#         rot_row = col.row()
#         rot_row.prop(item, "FV_rotation", text="Rot")
#         # values.prop(item, "NU_pivotRotX", text="x")
#         # values.prop(item, "NU_pivotRotY", text="y")
#         # values.prop(item, "NU_pivotRotZ", text="z")

#     def draw_patch_layout(self, layout, item, index):

#         row = layout.row(align=True)
#         row.prop(item, "autoItemCount", text="", icon='AUTO', toggle=True)   # tooltip still shows the full name
#         count = row.row(align=True)
#         count.enabled = not item.autoItemCount
#         count.prop(item, "itemCount", text="Count")
#         row.prop(item, "itemSpacing", text=CHAR_HORIZONTAL +" Spacing")

#         row = layout.row(align=True)
#         row.prop(item, "fillAlignment", text="Fill Align", toggle=True)
#         align_row = row.row(align=True)
#         align_row.enabled = item.fillAlignment
#         align_row.prop(item, "fillDirection", text="Fill Direction", expand=True)
        
#         row = layout.row(align=True)
#         row.prop(item, "normedPos", text=CHAR_HORIZONTAL +" Pos (norm)")
#         row.prop(item, "altitude", text=CHAR_VERTICAL +" Offset")

#         tm_props = get_global_props()

#         valid_group_body, valid_group_header = foldout_toggle(layout, tm_props, 
#                                                               "CB_cfg_showValidForGroups", 
#                                                               label=f"Valid for Groups ({len(item.validForGroups)})",
#                                                               indent = UI_FOLDOUT_INDENT,
#                                                               style=FOLDOUT_STYLE_FLAT)
#         if valid_group_body:
#             list_inspector(valid_group_body,
#                            item,
#                            "validForGroups",
#                            "validForGroups_index",
#                            rows=1)

        
      
#     @staticmethod
#     def patch_layout_added(owner, item, index):
#         if not item.name:
#             item.name = f"Patch Layout {index + 1}"

