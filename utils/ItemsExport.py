import os
import re
import bpy
from copy import copy
from shutil import copyfile

from .Materials import is_material_exportable, save_mat_props_json

from .Models import ExportedItem
from .NadeoImporter import start_batch_convert
from .ItemsIcon import generate_collection_icon, get_icon_path_from_fbx_path, generate_objects_icon
from .ItemsUVs import generate_base_material_cube_projection, generate_lightmap
from .Constants import (
    NOT_ALLOWED_COLLECTION_NAMES,
    SPECIAL_NAME_PREFIX_ITEM,
    SPECIAL_NAME_PREFIX_SOCKET,
    SPECIAL_NAME_PREFIX_TRIGGER,
    SPECIAL_NAME_PREFIX_IGNORE,
    SPECIAL_NAME_PREFIX_ICON_ONLY,
    SPECIAL_NAME_PREFIX_NOTVISIBLE,
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
    UV_LAYER_NAME_BASEMATERIAL,
    UV_LAYER_NAME_LIGHTMAP,
    WAYPOINT_VALID_NAMES
)
from .Functions import (
    create_folder_if_necessary,
    debug,
    deselect_all_objects,
    get_convert_items_failed_props,
    get_exportable_collection_objects,
    get_global_props,
    get_coll_relative_path,
    get_export_path,
    get_invalid_materials_props,
    get_prefix,
    get_waypointtype_of_collection,
    is_game_maniaplanet,
    safe_name,
    get_object_relative_path,
    get_game_doc_path_items,
    select_obj,
    show_report_popup,
    get_offset_from_item_origin,
)




def _is_real_object(name: str) -> bool:
    name = name.lower()
    return (
        not name.startswith("_") 
        or name.startswith((
            SPECIAL_NAME_PREFIX_NOTVISIBLE, 
            SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
            SPECIAL_NAME_PREFIX_ITEM
        ))
    )




def _is_collection_exportable(coll: bpy.types.Collection)->bool:
    if len(coll.objects) == 0\
    or coll.name.lower() in NOT_ALLOWED_COLLECTION_NAMES:
        return False

    is_exportable = False
    for obj in coll.objects:
        is_exportable = _is_object_exportable(obj)
        if is_exportable: break
    
    return is_exportable




def _is_object_exportable(obj: bpy.types.Object)-> bool:
    if obj.type != "MESH"\
    or obj.visible_get() is False\
    or not _is_real_object(obj.name):
        return False
        
    return True





def _fix_uv_layers_name(objects: list[bpy.types.Object]) -> None:
    for obj in objects:
        if obj.type == "MESH" and not obj.name.startswith((
            SPECIAL_NAME_PREFIX_SOCKET,
            SPECIAL_NAME_PREFIX_TRIGGER,
            SPECIAL_NAME_PREFIX_NOTVISIBLE,
            SPECIAL_NAME_PREFIX_IGNORE,
            SPECIAL_NAME_PREFIX_ICON_ONLY,
        )) and len(obj.material_slots.keys()) > 0:
            has_basematerial = False
            has_lightmap = False

            # fix short names and check if both BaseMaterial & LightMap exists
            for uv in obj.data.uv_layers:
                if uv.name.lower().startswith(("base", "bm")):
                    uv.name = UV_LAYER_NAME_BASEMATERIAL
                elif uv.name.lower().startswith(("light", "lm")):
                    uv.name = UV_LAYER_NAME_LIGHTMAP

                if uv.name == UV_LAYER_NAME_BASEMATERIAL:
                    has_basematerial = True
                elif uv.name == UV_LAYER_NAME_LIGHTMAP:
                    has_lightmap = True

                if uv.name.startswith("UVMap") and not has_basematerial:
                    uv.name = UV_LAYER_NAME_BASEMATERIAL
                    has_basematerial = True

            # create BaseMaterial & LightMap if they don't exist
            if not has_basematerial:
                obj.data.uv_layers.new(name=UV_LAYER_NAME_BASEMATERIAL, do_init=True)
                
            if not has_lightmap:
                obj.data.uv_layers.new(name=UV_LAYER_NAME_LIGHTMAP,     do_init=True)





def _is_physic_hack_required(objects: list[bpy.types.Object]) -> bool:
    if is_game_maniaplanet() is False:
        return False
    
    physic_hack = False
    for obj in objects:
        if obj.type == "MESH":
            for mat in obj.data.materials:
                if mat is None:
                    show_report_popup(title=obj.name, infos=("Material slot has no material, add one!",))
                    raise ValueError(
                        "\n\nMaterial slot has no material assigned, please remove the empty slot or add a (tm_/mp_) material to it!\n\n"
                        + "Object: " + obj.name + "\n"
                        + "Collection: " + ",".join([col.name for col in obj.users_collection])
                        )
                is_linked = mat.baseTexture == ""
                if is_linked:
                    physic_hack = True
                    break
        
    return physic_hack





def _duplicate_scaled(item: ExportedItem) -> list[ExportedItem]:
    pattern   = r"_#SCALE_(\d+)to(\d+)_x(\d+)"
    scale_list = re.findall(pattern, item.name, flags=re.IGNORECASE)

    items = [item]

    if len(scale_list) > 0:
        items.clear()
        scale_from    = int(scale_list[0][0]) 
        scale_to      = int(scale_list[0][1])
        scale_step_raw= int(scale_list[0][2]) 
        scale_step    = 1 / scale_step_raw
        current_scale = 1

        # swap, always lowest to biggest
        if scale_from > scale_to:
            scale_from, scale_to = scale_to, scale_from

        debug(f"{scale_from=}\n{scale_to=}\n{scale_step=}")
        reverse_range = reversed(range(scale_from, scale_to+1))

        for scale in reverse_range:

            if current_scale <= 0:
                raise Exception(f"""
                    Atleast one exported object scale is below 0!
                    try to increase your "_x{scale_step_raw}" to x{scale_step_raw + 1} or
                    x{scale_step_raw+2} in {item.name}
                """)

            new_item = copy(item)
            new_item.scale = current_scale
            new_item.force_scale = True
            new_item.name = re.sub(pattern, f"_#{scale}", item.name)
            new_item.r_path = re.sub(pattern, f"_#{scale}", item.r_path)
            new_item.fbx_path = re.sub(pattern, f"_#{scale}", item.fbx_path)
            new_item.icon_path = re.sub(pattern, f"_#{scale}", item.icon_path)
            new_item.item_path = re.sub(pattern, f"_#{scale}", item.item_path)

            debug(f"create new file: {new_item.fbx_path}")
            os.makedirs(os.path.dirname(new_item.fbx_path), exist_ok=True)
            copyfile(item.fbx_path, new_item.fbx_path)
            try:
                os.makedirs(os.path.dirname(new_item.icon_path), exist_ok=True)
                copyfile(item.icon_path, new_item.icon_path)
            except FileNotFoundError:
                pass

            current_scale -= scale_step

            items.append(new_item)
        
        debug(f"remove original: {item.fbx_path}")
        os.remove(item.fbx_path) # rm original

    return items


def _get_color_variant_settings():
    """Get the color variant settings from the scene, handling missing attribute gracefully."""
    if hasattr(bpy.context.scene, 'tm_props_color_variants'):
        return bpy.context.scene.tm_props_color_variants
    return None


def _duplicate_with_colors(item: ExportedItem) -> list[ExportedItem]:
    """
    Create color variants of an ExportedItem.
    Returns a list of ExportedItems, one for each enabled color variant.
    If multi-color is disabled, returns the original item in a list.
    """
    color_settings = _get_color_variant_settings()

    if color_settings is None or not color_settings.enabled or not color_settings.target_material:
        return [item]

    enabled_variants = [v for v in color_settings.variants if v.enabled]
    if len(enabled_variants) == 0:
        return [item]

    items = []

    for variant in enabled_variants:
        new_item = copy(item)
        # Add color variant info to the item
        new_item.color_variant_name = variant.name
        new_item.color_variant_value = tuple(variant.color)
        new_item.color_variant_material = color_settings.target_material.name

        # Sanitize variant name for file paths
        safe_variant_name = safe_name(variant.name)

        # Update naming: append color variant name
        suffix = f"_{safe_variant_name}"
        new_item.name = item.name + suffix
        new_item.r_path = item.r_path + suffix
        new_item.fbx_path = item.fbx_path.replace(".fbx", f"{suffix}.fbx")
        new_item.icon_path = item.icon_path.replace(".tga", f"{suffix}.tga")
        new_item.item_path = item.item_path.replace(".Item.Gbx", f"{suffix}.Item.Gbx")

        items.append(new_item)

    return items


def _apply_color_variant_to_material(item: ExportedItem) -> dict:
    """
    Temporarily apply a color variant to the target material.
    Returns a dict containing the original values to restore later.
    """
    if not item.color_variant_material or not item.color_variant_value:
        return None

    mat = bpy.data.materials.get(item.color_variant_material)
    if not mat:
        return None

    color = item.color_variant_value
    color_4 = (*color, 1.0)  # Add alpha

    # Store original values
    original_values = {
        'diffuse_color': tuple(mat.diffuse_color),
    }

    if hasattr(mat, 'surfaceColor'):
        original_values['surfaceColor'] = tuple(mat.surfaceColor)

    # Apply new color
    mat.diffuse_color = color_4
    if hasattr(mat, 'surfaceColor'):
        mat.surfaceColor = color[:3]

    # Update shader nodes if present
    if mat.use_nodes and mat.node_tree:
        nodes = mat.node_tree.nodes
        # Try Principled BSDF
        principled = nodes.get("Principled BSDF")
        if principled and "Base Color" in principled.inputs:
            original_values['bsdf_base_color'] = tuple(principled.inputs["Base Color"].default_value)
            principled.inputs["Base Color"].default_value = color_4

        # Try custom color node (some materials use this)
        cus_color = nodes.get("cus_color")
        if cus_color and cus_color.outputs:
            original_values['cus_color'] = tuple(cus_color.outputs[0].default_value)
            cus_color.outputs[0].default_value = color_4

    return original_values


def _restore_material_color(item: ExportedItem, original_values: dict) -> None:
    """
    Restore the original material color after export.
    """
    if not original_values or not item.color_variant_material:
        return

    mat = bpy.data.materials.get(item.color_variant_material)
    if not mat:
        return

    # Restore original values
    if 'diffuse_color' in original_values:
        mat.diffuse_color = original_values['diffuse_color']

    if 'surfaceColor' in original_values and hasattr(mat, 'surfaceColor'):
        mat.surfaceColor = original_values['surfaceColor']

    # Restore shader nodes
    if mat.use_nodes and mat.node_tree:
        nodes = mat.node_tree.nodes
        if 'bsdf_base_color' in original_values:
            principled = nodes.get("Principled BSDF")
            if principled and "Base Color" in principled.inputs:
                principled.inputs["Base Color"].default_value = original_values['bsdf_base_color']

        if 'cus_color' in original_values:
            cus_color = nodes.get("cus_color")
            if cus_color and cus_color.outputs:
                cus_color.outputs[0].default_value = original_values['cus_color']


# takes the first item and return offset from it to "location"
def _move_collection_to(objects: list[bpy.types.Object]) -> list[float]:
    offset = get_offset_from_item_origin(objects)
    
    for obj in objects:
        if obj.parent is not None:
            continue
        obj.location[0] -= offset[0]
        obj.location[1] -= offset[1]
        obj.location[2] -= offset[2]

    return offset





def _move_collection_by(objects: list[bpy.types.Object], offset: list[float] = [0,0,0]):
    for obj in objects:
        if obj.parent is not None:
            continue
        obj.location[0] += offset[0]
        obj.location[1] += offset[1]
        obj.location[2] += offset[2]





def _export_item_FBX(item: ExportedItem) -> None:
    """exports fbx, creates filepath if it does not exist"""
    create_folder_if_necessary(item.fbx_path[:item.fbx_path.rfind("/")]) #deletes all after last slash

    tm_props    = get_global_props()
    # objTypes    = tm_props.LI_exportValidTypes.split("_") 
    # objTypes    = {ot for ot in objTypes} #MESH_LIGHT_EMPTY
    exportArgs  = {
        "filepath":             item.fbx_path,
        # "object_types":         objTypes,
        "use_selection":        True,
        "use_custom_props":     True,
        "apply_unit_scale":     False,
    }

    if is_game_maniaplanet():
        exportArgs["apply_scale_options"] = "FBX_SCALE_UNITS"

    deselect_all_objects()
    for obj in item.objects:
        if not obj.name.lower().startswith((SPECIAL_NAME_PREFIX_IGNORE, SPECIAL_NAME_PREFIX_ICON_ONLY, "delete")) :
            select_obj(obj)

    bpy.ops.export_scene.fbx(**exportArgs) #one argument is optional, so give a modified dict and **unpack

    deselect_all_objects()




def _clean_up_addon_export_settings(total: int):
    tm_props = get_global_props()
    tm_props.NU_convertCount        = total
    tm_props.NU_converted           = 0
    tm_props.NU_convertedRaw        = 0
    tm_props.NU_convertedError      = 0
    tm_props.NU_convertedSuccess    = 0
    tm_props.ST_convertedErrorList  = ""
    tm_props.CB_converting          = True

    tm_props.NU_convertDurationSinceStart = 0
    tm_props.NU_convertStartedAt          = 0
    tm_props.NU_currentConvertDuration    = 0






def _add_empty_socket_hide_existing(coll: bpy.types.Collection) -> None:
    if is_game_maniaplanet():
        return
    
    waypoint = get_waypointtype_of_collection(coll)
    if waypoint not in WAYPOINT_VALID_NAMES:
        return
    
    old_socket:bpy.types.Object = None
    for obj in coll.objects:
        if obj.name.startswith(SPECIAL_NAME_PREFIX_SOCKET):
            old_socket = obj
            break
    else:
        return
    
    new_socket:bpy.types.Object = bpy.data.objects.new(old_socket.name + "_temporary", None)
    new_socket.rotation_euler = old_socket.rotation_euler
    new_socket.location = old_socket.location
    new_socket.name = "_socket_start_"+old_socket.name

    coll.objects.link(new_socket)
    old_socket.hide_set(True) # ignored in export now
    return new_socket





def _remove_empty_socket_unhide_existing(coll:bpy.types.Collection) -> None:
    if is_game_maniaplanet():
        return

    empty_socket:bpy.types.Object = None
    old_socket:bpy.types.Object = None
    
    for obj in coll.all_objects:
        if obj.name.startswith(SPECIAL_NAME_PREFIX_SOCKET):
            if obj.type == "EMPTY":
                empty_socket = obj
            elif obj.type == "MESH":
                old_socket = obj
            
    if empty_socket: bpy.data.objects.remove(empty_socket)
    if old_socket: old_socket.hide_set(False)




def export_collections(colls: list[bpy.types.Collection]):
    current_selection       = bpy.context.selected_objects.copy()
    tm_props                = get_global_props()
    
    use_lightmap_overlapping_check = tm_props.CB_uv_fixLightMap
    overwrite_lightmaps            = tm_props.CB_uv_genLightMap
    
    overwrite_basematerials = tm_props.CB_uv_genBaseMaterialCubeMap
    
    # generate_icons          = tm_props.CB_icon_genIcons
    # overwrite_icon          = tm_props.CB_icon_overwriteIcons
    
    items_to_export:list[ExportedItem]           = []
    processed_materials:list[bpy.types.Material] = []
    
    export_work_path = get_export_path()
    
    if ".." in export_work_path:
        raise ValueError(
            "\n\nExport path must be absolute! (can not start with '/' or '..')"
            + "\nFix: when selecting the export folder in the window that opens, press <N> and uncheck 'Relative Path' (right tab)"
        )


    deselect_all_objects()

    for coll in colls:
        if not _is_collection_exportable(coll):
            continue

        debug(f"Preparing collection <{coll.name}> for export")
        
        objs = get_exportable_collection_objects(coll.objects)

        invalid_mats = get_invalid_materials_props()

        for obj in objs:
            for slot in obj.material_slots:
                mat = slot.material
                if mat is None:
                    continue  # Skip empty material slots
                if mat not in processed_materials:
                    if is_material_exportable(mat):
                        save_mat_props_json(mat)
                        processed_materials.append(mat)
                    else:
                        imat = invalid_mats.add()
                        imat.material = mat
        
        if invalid_mats.items():
            tm_props.CB_showInvalidMatsPanel = True
            debug("Export stopped, found invalid materials")
            return
            

        # fill metadata
        item_to_export = ExportedItem()
        item_to_export.name = safe_name(coll.name)
        item_to_export.name_raw = coll.name
        item_to_export.objects = objs
        item_to_export.color_tag = coll.color_tag
        item_to_export.tm_itemxml_template = coll.tm_itemxml_template
        item_to_export.r_path = get_coll_relative_path(coll)
        item_to_export.fbx_path = f"{export_work_path}{item_to_export.r_path}.fbx"
        item_to_export.icon_path = get_icon_path_from_fbx_path(item_to_export.fbx_path)
        item_to_export.item_path = f"{get_game_doc_path_items()}{item_to_export.r_path}.Item.Gbx"
        item_to_export.physic_hack = _is_physic_hack_required(coll.objects)

        # fix UVs and check lods
        _fix_uv_layers_name(coll.objects)

        has_lod0 = False
        has_lod1 = False
        for obj in coll.objects: 
            if   "_lod0" in obj.name.lower(): has_lod0 = True
            elif "_lod1" in obj.name.lower(): has_lod1 = True

        if (
            not has_lod0 and 
            not has_lod1
        ):
            if overwrite_lightmaps: 
                generate_lightmap(coll, use_lightmap_overlapping_check)
            if overwrite_basematerials: 
                generate_base_material_cube_projection(coll)

        if has_lod1 and not has_lod0:
            show_report_popup("Invalid collections", f"<{coll.name}> has Lod1, but not Lod0, collection skipped")
            return

        # tm2020 socket fix
        tmp_socket = _add_empty_socket_hide_existing(coll)
        if tmp_socket:
            item_to_export.objects.add(tmp_socket)

        # move collection to 0,0,0
        offset = _move_collection_to(coll.objects)

        # Generate color variants (returns list with at least original item)
        color_variants = _duplicate_with_colors(item_to_export)

        for variant_item in color_variants:
            # Apply color variant (if applicable)
            original_colors = _apply_color_variant_to_material(variant_item)

            try:
                # Re-save material props JSON with the modified color so FBX gets the correct color
                if variant_item.color_variant_material:
                    mat = bpy.data.materials.get(variant_item.color_variant_material)
                    if mat:
                        save_mat_props_json(mat)

                # export .fbx with modified material
                _export_item_FBX(variant_item)

                # Create icon directory if needed
                icon_dir = variant_item.icon_path[:variant_item.icon_path.rfind("/")]
                create_folder_if_necessary(icon_dir)

                # generate icon with modified material
                generate_collection_icon(coll, variant_item.icon_path)
            finally:
                # Always restore original colors
                _restore_material_color(variant_item, original_colors)

                # Restore the original material JSON as well
                if variant_item.color_variant_material:
                    mat = bpy.data.materials.get(variant_item.color_variant_material)
                    if mat:
                        save_mat_props_json(mat)

            # Apply multi-scale duplication (this creates the combinations)
            items_to_export += _duplicate_scaled(variant_item)

        # tm2020 socket fix
        if tmp_socket:
            item_to_export.objects.remove(tmp_socket)
        _remove_empty_socket_unhide_existing(coll)

        # move collection back to original position
        _move_collection_by(coll.objects, offset)

    for obj in current_selection:
        try: select_obj(obj)
        except: pass

    clean_failed_converts()

    _clean_up_addon_export_settings(len(items_to_export))
    start_batch_convert(items_to_export)



def export_objects(objects: list[bpy.types.Object]) -> None:
    current_selection                            = bpy.context.selected_objects.copy()
    tm_props                                     = get_global_props()
    items_to_export:list[ExportedItem]           = []
    processed_materials:list[bpy.types.Material] = []
    
    export_work_path = get_export_path()
    
    deselect_all_objects()


    for obj in objects:
        obj:bpy.types.Object = obj
        if not _is_object_exportable(obj):
            continue
        
        debug(f"Preparing object<{obj.name}> for export")

        prefix = get_prefix(obj.name)
        obj.name = obj.name.replace(prefix, "")

        invalid_mats = get_invalid_materials_props()

        for slot in obj.material_slots:
            mat = slot.material
            if mat not in processed_materials: 
                if is_material_exportable(mat):
                    save_mat_props_json(mat)
                    processed_materials.append(mat)
                else:
                    imat = invalid_mats.add()
                    imat.material = mat
        
        if invalid_mats.items():
            tm_props.CB_showInvalidMatsPanel = True
            debug("Export stopped, found invalid materials")
            obj.name = prefix + obj.name
            return

        # fill metadata
        item_to_export = ExportedItem()
        item_to_export.name = safe_name(obj.name)
        item_to_export.name_raw = obj.name
        item_to_export.objects = [obj]
        item_to_export.tm_itemxml_template = obj.users_collection[0].tm_itemxml_template
        item_to_export.r_path = get_object_relative_path(obj)
        item_to_export.fbx_path = f"{export_work_path}{item_to_export.r_path}.fbx"
        item_to_export.icon_path = get_icon_path_from_fbx_path(item_to_export.fbx_path)
        item_to_export.item_path = f"{get_game_doc_path_items()}{item_to_export.r_path}.Item.Gbx"
        item_to_export.physic_hack = _is_physic_hack_required([obj])

        # fix UVs and check lods
        _fix_uv_layers_name([obj])

        old_loc = obj.location.copy()

        # Generate color variants (returns list with at least original item)
        color_variants = _duplicate_with_colors(item_to_export)

        for variant_item in color_variants:
            # Apply color variant (if applicable)
            original_colors = _apply_color_variant_to_material(variant_item)

            try:
                # Re-save material props JSON with the modified color so FBX gets the correct color
                if variant_item.color_variant_material:
                    mat = bpy.data.materials.get(variant_item.color_variant_material)
                    if mat:
                        save_mat_props_json(mat)

                # export .fbx with modified material
                _export_item_FBX(variant_item)

                # Create icon directory if needed
                icon_dir = variant_item.icon_path[:variant_item.icon_path.rfind("/")]
                create_folder_if_necessary(icon_dir)

                # generate icon with modified material
                generate_objects_icon([obj], obj.name, variant_item.icon_path)
            finally:
                # Always restore original colors
                _restore_material_color(variant_item, original_colors)

                # Restore the original material JSON as well
                if variant_item.color_variant_material:
                    mat = bpy.data.materials.get(variant_item.color_variant_material)
                    if mat:
                        save_mat_props_json(mat)

            # Apply multi-scale duplication (this creates the combinations)
            items_to_export += _duplicate_scaled(variant_item)

        obj.location = old_loc

        obj.name = prefix + obj.name

    for obj in current_selection:
        try: select_obj(obj)
        except: pass

    clean_failed_converts()

    _clean_up_addon_export_settings(len(items_to_export))
    start_batch_convert(items_to_export)





def clean_failed_converts() -> None:
    failes = get_convert_items_failed_props()
    failes.objects.clear()
    # failes.collections.clear()









