import bpy
from ..widgets.lists import list_inspector, register_row_drawer, unregister_row_drawer
from ...properties.VegetTreeProperties import PositionProperties

from ...properties.PropertyIdentifiers import CollectionProp
from ...utils.FunctionsV2 import get_item_root
from ...utils.TreeModels import get_tree_model_issues
from ..widgets.asset_picker import draw_asset_field
from ..widgets.foldouts import foldout_toggle
from ...utils.Constants import UI_FOLDOUT_INDENT
from ...utils.Functions import get_global_props


def _override_row(layout, tree, override_prop: str, value_prop: str) -> None:
    row = layout.row(align=True)
    row.prop(tree, override_prop, text="")
    sub = row.row(align=True)
    sub.enabled = getattr(tree, override_prop)
    sub.prop(tree, value_prop)


def draw_tree_model_collection(layout, collection: bpy.types.Collection) -> None:
    """settings of a collection of type TreeModel"""
    tree = getattr(collection, CollectionProp.VEGET_TREE)

    layout.prop(tree, "angle_max_rot_xz_deg")
    layout.prop(tree, "enable_random_rotation_y")
    layout.prop(tree, "force_no_collision")
    layout.prop(tree, "impostor_all_planes_visible")
    layout.prop(tree, "lod_dist_at_fov90")
    layout.prop(tree, "propagation_max_random_scale_reduction_per_instance", slider=True)
    layout.prop(tree, "receive_pssm")
    layout.prop(tree, "plane_compute_mode")

    # leaf animation (exported as the tree model's propagation): checkbox in the foldout header, settings inside
    body, _header = foldout_toggle(layout, get_global_props(), "CB_cfg_show_leaf_animation",
                                   label="Leaf Animation", enable_prop="enable_propagation", enable_owner=tree,
                                   indent=UI_FOLDOUT_INDENT)
    if body is not None:
        col = body.column(align=True)
        draw_asset_field(col, tree, "propagation_base_color", "BITMAP", icon="TEXTURE")
        draw_asset_field(col, tree, "propagation_normal", "BITMAP", icon="TEXTURE")
        row = col.row(align=True)
        row.prop(tree, "propagation_atlas_grid")
        col.prop(tree, "propagation_cone_half_angle_degree")
        col.prop(tree, "propagation_emission_spawn_radius")
        col.prop(tree, "propagation_ground_gen_point_count")
        col.prop(tree, "propagation_leaf_per_second")
        col.prop(tree, "propagation_leaf_size")
        col.label(text="Emission Positions")
        list_inspector(col,
                       tree,
                       "propagation_emission_positions", "propagation_emission_position_index",
                       rows=3,
                       show_move=False,
                       # show_clipboard=True,
                       copy_on_add='SELECTED')

        if tree.enable_propagation:
            from ...FX.preview import draw_tree_preview   # viewport overlay of the falling leaves
            draw_tree_preview(body, bpy.context, collection)


    item = get_item_root(collection, bpy.context.scene)
    if item is not None:
        errors = get_tree_model_issues(item)
        if errors:
            box = layout.box()
            box.alert = True
            for message in errors:
                box.label(text=message, icon='CANCEL')

def _draw_position_property_row(layout, item, index):
        layout.label(text="", icon='DOT')            # click here to select the row
        row = layout.row(align=True)
        row.prop(item, "value", text="")

def register():
    register_row_drawer(PositionProperties, _draw_position_property_row)


def unregister():
    unregister_row_drawer(PositionProperties)
    