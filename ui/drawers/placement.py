from ...properties.PlacementProperties import PlacementProperties

from ...properties.PlacementPatchProperties import CompatiblePatchGroupProperty, PatchGroupRef

from ...utils.Functions import *
from ...utils.Constants import * 
from ...ui.widgets.lists import *
from ...ui.widgets.foldouts import *

# callbacks for list items
def _draw_compatible_group_row(layout, item, index):
        layout.label(text="", icon='DOT')            # click here to select the row
        layout.prop(item, "name", text="")


def _draw_valid_for_group_row(layout, item, index):
    layout.label(text="", icon='DOT')            # click here to select the row
    layout.prop(item, "name", text="")

def _patch_layout_added(owner, item, index):
    if not item.name:
        item.name = f"Patch Layout {index + 1}"

# register method for ui
def register_placement_callbacks():
    register_row_drawer(CompatiblePatchGroupProperty, _draw_compatible_group_row)
    register_row_drawer(PatchGroupRef, _draw_valid_for_group_row)
    register_list_hooks(PlacementProperties, "LI_patchLayouts", after_add=_patch_layout_added)

def unregister_placement_callbacks():
    unregister_row_drawer(CompatiblePatchGroupProperty)
    unregister_row_drawer(PatchGroupRef)
    unregister_list_hooks(PlacementProperties, "LI_patchLayouts")



# draw methods for placement
def draw_pivot(layout, item, index):
    box = layout.box()
    col = box.column()
    pos_row = col.row()
    pos_row.prop(item, "FV_position",text="Pos")

    rot_row = col.row()
    rot_row.prop(item, "FV_rotation", text="Rot")

def draw_patch_layout(layout, item, index):
    tm_props = get_global_props()

    row = layout.row(align=True)
    row.prop(item, "autoItemCount", text="", icon='AUTO', toggle=True)   # tooltip still shows the full name
    count = row.row(align=True)
    count.enabled = not item.autoItemCount
    count.prop(item, "itemCount", text="Count")
    row.prop(item, "itemSpacing", text=CHAR_HORIZONTAL +" Spacing")

    row = layout.row(align=True)
    row.prop(item, "fillAlignment", text="Fill Align", toggle=True)
    align_row = row.row(align=True)
    align_row.enabled = item.fillAlignment
    align_row.prop(item, "fillDirection", text="Fill Direction", expand=True)
    
    row = layout.row(align=True)
    row.prop(item, "normedPos", text=CHAR_HORIZONTAL +" Pos (norm)")
    row.prop(item, "altitude", text=CHAR_VERTICAL +" Offset")

  

    valid_group_body, valid_group_header = foldout_toggle(layout, tm_props, 
                                                            "CB_cfg_showValidForGroups", 
                                                            label=f"Valid for Groups ({len(item.validForGroups)})",
                                                            indent = UI_FOLDOUT_INDENT,
                                                            style=FOLDOUT_STYLE_FLAT)
    if valid_group_body:
        list_inspector(valid_group_body,
                        item,
                        "validForGroups",
                        "validForGroups_index",
                        rows=1)


def draw_item_placement_editor(layout, context, placement, section):
    #todo: load template into custom
    tm_props = get_global_props()
    row = layout.row(align=True)
    row.label(text="Custom Placement Parameters:")

    row = layout.row(align=True)
    row.label(text="Load Template")
    row.context_pointer_set("tm_placement", placement)
    row.prop(context.scene, "tm_props_cfg_placement_template_ui", text="")
    op = row.operator("view3d.tm_load_item_config_placement_template", text="", icon=ICON_IMPORT)
    op.template_name =  context.scene.tm_props_cfg_placement_template_ui

    row = layout.row(align=True)
    row.prop(placement, "LI_simpleOrAdvanced", expand=True)
    display_simple = placement.LI_simpleOrAdvanced == 'SIMPLE'

    if display_simple:
        main_col = layout.column(align=True)
        
        x_row = main_col.row(align=True)
        x_row.label(text="Grid "+CHAR_HORIZONTAL, )
        x_row.prop(placement, "LI_simpleGridXY", expand=True)
        
        z_row = main_col.row(align=True)
        z_row.label(text="Grid "+CHAR_VERTICAL)
        z_row.prop(placement, "LI_simpleGridZ", expand=True)

        
        row = layout.row(align=True)
        
        col_ghost = row.column(align=True)
        col_ghost.prop(placement, "CB_ghostMode",   icon=ICON_GHOSTMODE)
        
        placements_are_0 = placement.LI_simpleGridXY == "0" and placement.LI_simpleGridZ  == "0"

        col_autorot = row.column(align=True)
        col_autorot.enabled = placements_are_0
        col_autorot.prop(placement, "CB_autoRot", icon=ICON_GHOSTMODE)

    else: # advanced
        sync = placement.CB_syncGridLevi
        boxCol = layout.column(align=True)
        row = boxCol.row()
        row.prop(placement, "CB_syncGridLevi", text="Sync Grid & Levitation", icon=ICON_SYNC)
        
        if sync:
            boxRow = boxCol.row(align=True)
            boxRow.enabled = True if sync else False
            boxRow.prop(placement, "NU_gridAndLeviX", text=CHAR_HORIZONTAL+" Place")
            boxRow.prop(placement, "NU_gridAndLeviY", text=CHAR_VERTICAL+" Place")
            boxRow = boxCol.row(align=True)
            boxRow.enabled = True if sync else False
            boxRow.prop(placement, "NU_gridAndLeviOffsetX", text=CHAR_HORIZONTAL+" Offset")
            boxRow.prop(placement, "NU_gridAndLeviOffsetY", text=CHAR_VERTICAL+" Offset")
        
        boxCol = layout.column(align=True)
        boxRow = boxCol.row(align=True)
        boxRow.enabled = False if sync else True
        boxRow.label(text="Grid")
        boxRow.prop(placement, "NU_gridX", text=CHAR_HORIZONTAL)
        boxRow.prop(placement, "NU_gridY", text=CHAR_VERTICAL)
        boxRow = boxCol.row(align=True)
        boxRow.enabled = False if sync else True
        boxRow.label(text="Offset")
        boxRow.prop(placement, "NU_gridXoffset", text=CHAR_HORIZONTAL)
        boxRow.prop(placement, "NU_gridYoffset", text=CHAR_VERTICAL)
        
        boxCol = layout.column(align=True)
        boxRow = boxCol.row(align=True)
        boxRow.enabled = False if sync else True
        boxRow.label(text="Levitation")
        boxRow.prop(placement, "NU_leviX", text=CHAR_HORIZONTAL)
        boxRow.prop(placement, "NU_leviY", text=CHAR_VERTICAL)
        boxRow = boxCol.row(align=True)
        boxRow.enabled = False if sync else True
        boxRow.label(text="Offset")
        boxRow.prop(placement, "NU_leviXoffset", text=CHAR_HORIZONTAL)
        boxRow.prop(placement, "NU_leviYoffset", text=CHAR_VERTICAL)
        
        boxCol = layout.column(align=True)
        boxRow = boxCol.row(align=True)
        boxRow.prop(placement, "CB_ghostMode",   icon=ICON_GHOSTMODE)
        boxRow.prop(placement, "CB_autoRot",     icon=ICON_AUTO_ROTATION)
        boxRow = boxCol.row(align=True)
        boxRow.prop(placement, "CB_oneAxisRot",  icon=ICON_ONE_AXIS_ROTATION)
        boxRow.prop(placement, "CB_notOnItem",   icon=ICON_NOT_ON_ITEM)
        
        pivot_count = len(placement.LI_pivots)
        pivot_body, pivot_header = foldout_toggle(layout, tm_props, 
                                    "CB_xml_pivots", 
                                    label=f"Pivots (Placement Variants) ({pivot_count})",
                                    indent = UI_FOLDOUT_INDENT)
        if pivot_body:
            row = pivot_body.row(align=True)
            list_add_button(row, placement, "LI_pivots", text="Add", icon=ICON_ADD)
            row.prop(placement, "CB_pivotSwitch",    text="Switch", expand=True, icon=ICON_SWITCH)
            row.prop(placement, "NU_pivotSnapDis",   text="Snap Distance")
            
            item_list(pivot_body,
                        placement, 
                        "LI_pivots", 
                        draw_item=draw_pivot,
                        add_text="Add Pivot")   # add button lives in the foldout header

        placement_cube_body, placement_cube_header = foldout_toggle(layout, placement, 
                                                "CB_placementCube", 
                                                label="Placement Cube",
                                                indent = UI_FOLDOUT_INDENT)
        if placement_cube_body:
            row = placement_cube_body.row(align=True)
            row.prop(placement, "NU_cubeSize", text="Cube Size")
            row = placement_cube_body.row(align=True)
            row.prop(placement, "PT_cubeCenter")

        attachment_body, attachment_header = foldout_toggle(layout, tm_props, 
                                                            "CB_cfg_show_attachmentConfiguration", 
                                                            label="Attachment Configuration",
                                                            indent = UI_FOLDOUT_INDENT,
                                                            enable_owner=placement,
                                                            enable_prop="CB_attachmentConfiguration")
        if attachment_body:
            row = attachment_body.row(align=True)
            size_group_row = row.row(align=True)
            size_group_row.enabled = False
            size_group_row.prop(placement, "ST_sizeGroup", text="Size Group")
            row.prop(placement, "CB_alwaysUp", text="Always Up", toggle=True, icon=ICON_AXIS_Z)
            row = attachment_body.row(align=True)
            row.prop(placement, "CB_alignToInterior", text="Align to Interior", icon="NONE", toggle=True)
            row.prop(placement, "CB_alignToWorldDir", text="Align to World Dir", icon="NONE", toggle=True)
            row = attachment_body.row(align=True)
            if placement.CB_alignToWorldDir:
                row.prop(placement, "PT_worldDir")

        # ---- Compatible groups  ----
            compat_grp_body, compat_grp_header = foldout_toggle(attachment_body, tm_props, 
                                                                            "CB_cfg_showCompatibleGroups", 
                                                                            label=f"Compatible Patch Groups ({len(placement.LI_compatibleGroups)})",
                                                                            indent = UI_FOLDOUT_INDENT,
                                                                            style=FOLDOUT_STYLE_FLAT)
            if compat_grp_body:
                list_inspector(
                    compat_grp_body, 
                    placement, 
                    "LI_compatibleGroups", 
                    "NU_compatibleGroups_index", 
                    rows=3)

            # ---- Patch layouts ----
            patch_layout_body, patch_layout_header = foldout_toggle(attachment_body, tm_props, 
                                                                            "CB_cfg_showPatchLayouts", 
                                                                            label=f"Patch Layouts ({len(placement.LI_patchLayouts)})",
                                                                            indent = UI_FOLDOUT_INDENT,
                                                                            style=FOLDOUT_STYLE_FLAT)
            if patch_layout_body:
                list_inspector(patch_layout_body,
                            placement,
                            "LI_patchLayouts",
                            "NU_patchLayouts_index",
                            draw_detail=draw_patch_layout,
                            rows = 1)

    row = layout.row()
    row.context_pointer_set("tm_placement", placement)
    op = row.operator("view3d.tm_save_item_config_placement_template", text="Save as Template", icon=ICON_SAVE)

def draw_item_placement_template_selection(layout, context, placement_ref, section):
    tm_props = get_global_props()

    selected_template_name = placement_ref.template

    row = layout.row(align=True)
    row.label(text="Placement Template:")
    row.prop(placement_ref, "template", text="")
    row.operator("view3d.tm_remove_item_config_placement_template", text=f"", icon=ICON_REMOVE).template_name = selected_template_name

