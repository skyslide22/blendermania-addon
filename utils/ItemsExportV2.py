import bpy
import pprint
from copy import copy

from ..properties.CollectionProperties import sync_collection_properties_with_names

from ..properties.ObjectProperties import sync_object_properties_with_names
from ..properties.PropertyIdentifiers import ObjectProp, CollectionProp
from ..utils.ItemsExportV2Models import *
from ..utils import Constants
from ..utils.Functions import strip_ignore_prefix
from ..utils.FunctionsV2 import get_exportable_collections, get_offset_from_item_origin, get_item_collection_objects, get_invalid_group_children, is_inside_group_collection, EXPLICIT_EXPORT_COLLECTIONS, is_group_collection, get_item_root, get_item_collections_from_collections, name_without_scale
from .Materials import is_material_exportable, save_mat_props_json
from .ItemsIconV2 import generate_collection_icon, get_icon_path_from_fbx_path, generate_objects_icon
from .ItemsUVs import generate_base_material_cube_projection, generate_lightmap
from ..utils.CustomImporter import is_collection_exportable, start_batch_convert, get_convert_items_failed_props
import queue
import json
import math



# def export_collection_to_dotnet(collection) -> bool:
#     if not collection:
#         return False

#     if is_collection_root(collection):
#         show_report_popup("Error", ("The root collection cannot be exported!",))
#         return False

#     cfg = _generate_item_config(collection)
#     cfg_dict = item_config_to_dict(cfg)

#     pprint.pprint(cfg_dict)

#     # write file to desktop
#     with open(f"{Constants.PATH_DESKTOP}/item.info.json", "w") as f:
#         json.dump(cfg_dict, f, indent=4)



#     return True







def export_and_convert(only_failed_ones: bool=False, which: str | None = None, collections: list[bpy.types.Collection] | None = None, plan_only: bool=False):
    """plan_only: export fbx (+ json config) only, no icon, no gbx convert; returns the list of ExportedItem"""
    tm_props = get_global_props()
    failed = get_convert_items_failed_props()

    if collections is not None:
        sync_name_and_properties()
        # explicitly selected collections (and the items of selected groups) override "ignore"
        scene = bpy.context.scene
        EXPLICIT_EXPORT_COLLECTIONS.clear()
        for col in collections:
            EXPLICIT_EXPORT_COLLECTIONS.add(col.name)
            if is_group_collection(col) and (root := get_item_root(col, scene)) is not None:
                EXPLICIT_EXPORT_COLLECTIONS.add(root.name)
        try:
            if colls := get_item_collections_from_collections(collections):
                return export_collections(colls, plan_only=plan_only)
        finally:
            EXPLICIT_EXPORT_COLLECTIONS.clear()
        show_report_popup("Error", ("No exportable item collections found in the selected collections!",))
        return
    
    # explicit scope wins, otherwise fall back to the panel setting
    scope = which or tm_props.LI_exportWhichObjs
    selected_only = scope == "SELECTED"

    objs = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
    objs = [obj.object for obj in failed.objects] if only_failed_ones else objs

    sync_name_and_properties()
    
    # atleast one object whose name startswith _item_ is selected
    # if single_objs := get_exportable_objects(objs):
    #     return export_objects(single_objs)
    
    # export normal way
    if colls := get_exportable_collections(objs):
        return export_collections(colls, plan_only=plan_only)
    
    show_report_popup("Error", ("No objects/collections found to export!",))

    
    
def export_collections(colls: list[bpy.types.Collection], plan_only: bool=False) -> list[ExportedItem] | None:
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
        if not is_collection_exportable(coll):
            continue

        debug(f"Preparing collection <{coll.name}> for export")

        if is_inside_group_collection(coll):
            show_report_popup("Invalid item collection", (
                f"<{coll.name}> skipped: item collections can not be inside a moving group or container.",
            ))
            continue

        invalid_children = get_invalid_group_children(coll)
        if invalid_children:
            show_report_popup("Invalid group", (
                f"<{coll.name}> skipped: moving groups/containers may not contain item collections, but found:",
                *(f"  - {c.name}" for c in invalid_children),
            ))
            continue
        
        objs = get_exportable_collection_objects(get_item_collection_objects(coll))

        invalid_mats = get_invalid_materials_props()

        for obj in objs:
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
            return
            

        # fill metadata
        item_to_export = ExportedItem()
        item_to_export.name = safe_name(strip_ignore_prefix(coll.name))
        item_to_export.name_raw = coll.name
        item_to_export.objects = objs
        item_to_export.collection = coll
        #item_to_export.color_tag = coll.color_tag
        #item_to_export.tm_itemxml_template = coll.tm_itemxml_template
        item_to_export.r_path = get_coll_relative_path(coll)
        item_to_export.fbx_path = f"{export_work_path}{item_to_export.r_path}.fbx"
        item_to_export.icon_path = get_icon_path_from_fbx_path(item_to_export.fbx_path)
        item_to_export.item_path = f"{get_game_doc_path_items()}{item_to_export.r_path}.Item.Gbx"
        #item_to_export.physic_hack = _is_physic_hack_required(coll.objects)

        # fix UVs and check lods
        _fix_uv_layers_name(objs)


        if overwrite_lightmaps: 
            generate_lightmap(coll, use_lightmap_overlapping_check)
        if overwrite_basematerials: 
            generate_base_material_cube_projection(coll)

        # tm2020 socket fix
        # tmp_socket = _add_empty_socket_hide_existing(coll)
        # if tmp_socket:
        #     item_to_export.objects.add(tmp_socket)

        # move collection to 0,0,0
        offset = _move_collection_to(objs)

        scaled_items: list[ExportedItem] = []
        try:
            # export .fbx
            _export_item_FBX(item_to_export)

            # generate icon
            if not plan_only:
                generate_collection_icon(coll, item_to_export.icon_path)
        except (PermissionError, OSError, RuntimeError) as e:
            if isinstance(e, RuntimeError) and "Permission denied" not in str(e) and "Errno 13" not in str(e):
                _move_collection_by(objs, offset)
                raise
            _move_collection_by(objs, offset)
            deselect_all_objects()
            show_report_popup("Export failed", (
                f"<{coll.name}> skipped: permission denied (file may be in use).",
                f"  {e}",
            ))
            continue

        # move collection back to original position
        _move_collection_by(objs, offset)

        try:
            scaled_items = _duplicate_scaled(item_to_export)
        except PermissionError as e:
            show_report_popup("Export failed", (
                f"<{coll.name}> skipped: permission denied (file may be in use).",
                f"  {e}",
            ))
            continue

        items_to_export += scaled_items

    for obj in current_selection:
        try: select_obj(obj)
        except: pass

    if plan_only:
        return items_to_export

    clean_failed_converts()

    _clean_up_addon_export_settings(len(items_to_export))
    start_batch_convert(items_to_export)


def _fix_uv_layers_name(objects: list[bpy.types.Object]) -> None:
    for obj in objects:
        if obj.type == EXPORTABLE_OBJECT_MESH and\
        not getattr(obj, ObjectProp.IGNORE, False) and \
        not getattr(obj, ObjectProp.SOCKET, False) and \
        not getattr(obj, ObjectProp.TRIGGER_EFFECT, False) and \
        not getattr(obj, ObjectProp.TRIGGER_WAYPOINT, False) and \
        not getattr(obj, ObjectProp.INVISIBLE, False) and \
        not getattr(obj, ObjectProp.ICON_ONLY, False) and \
        len(obj.material_slots.keys()) > 0:
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


def sync_name_and_properties():
    sync_object_properties_with_names()
    sync_collection_properties_with_names()

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
        "bake_anim":            False, # required else the active node in multi-export is not exported from 0,0,0. For some reason.
    }

    if is_game_maniaplanet():
        exportArgs["apply_scale_options"] = "FBX_SCALE_UNITS"

    deselect_all_objects()
    for obj in item.objects:
        if not getattr(obj, ObjectProp.IGNORE, False) and not getattr(obj, ObjectProp.ICON_ONLY, False) and \
        not obj.name.lower().startswith("delete"):
            select_obj(obj)

    bpy.ops.export_scene.fbx(**exportArgs) #one argument is optional, so give a modified dict and **unpack

    deselect_all_objects()

_SANITIZED_SCALE_RE = re.compile(
    r"_#SCALE_(?:"
    r"\d+to\d+_x\d+"                    # linear
    r"|_*\d+(?:\.\d+)?(?:_+\d+(?:\.\d+)?)*_*"   # values joined by "_" (tolerates leading/trailing "_")
    r")"
)
def _name_without_scale_sanitized(name):
    """Removes the scale token from an already sanitized collection name."""
    return _SANITIZED_SCALE_RE.sub("", name)

def _duplicate_scaled(item: ExportedItem) -> list[ExportedItem]:

    if getattr(item.collection, CollectionProp.SCALE_ITEM, False) is False:
        return [item]

    items = []
    scale_mode = getattr(item.collection, CollectionProp.SCALE_MODE, False)
    is_linear = scale_mode == "LINEAR"
    is_values = scale_mode == "VALUES"
    name_with_scale_str = item.name
    name_without_scale_str = _name_without_scale_sanitized(item.name)
    scales = []

    if is_linear:
        scale_from = getattr(item.collection, CollectionProp.SCALE_FROM, 1)
        scale_to = getattr(item.collection, CollectionProp.SCALE_TO, 1)
        scale_factor = getattr(item.collection, CollectionProp.SCALE_FACTOR, 1)
        if scale_from > scale_to:
            scale_from, scale_to = scale_to, scale_from
        reverse_range = reversed(range(scale_from, scale_to+1))
        scale_step      = 1 / scale_factor
        current_scale = 1
        for scale in reverse_range:
            scales.append([scale, current_scale])
            current_scale -= scale_step

    if is_values:
        scale_values = getattr(item.collection, CollectionProp.SCALE_VALUES, "1")
        for i, scale in enumerate(reversed(scale_values)):
            scales.append([i + 1, scale.value / 100])

    for scaleT in scales:
        scale = scaleT[1]
        if scale <= 0:
            raise Exception(f"""
                Atleast one exported object scale is below 0!
            """)

        index = scaleT[0]
        new_item = copy(item)
        new_item.scale = scale
        new_item.name = f"{name_without_scale_str}_#{index}"
        new_item.r_path = str.replace(item.r_path, name_with_scale_str, f"{name_without_scale_str}_#{index}")
        new_item.fbx_path = str.replace(item.fbx_path, name_with_scale_str, f"{name_without_scale_str}_#{index}")
        new_item.icon_path = str.replace(item.icon_path, name_with_scale_str, f"{name_without_scale_str}_#{index}")
        new_item.item_path = str.replace(item.item_path, name_with_scale_str, f"{name_without_scale_str}_#{index}")

        debug(f"create new file: {new_item.fbx_path}")
        copyfile(item.fbx_path, new_item.fbx_path)
        try:
            copyfile(item.icon_path, new_item.icon_path)
        except FileNotFoundError:
            pass

        items.append(new_item)
    
    debug(f"remove original: {item.fbx_path}")
    os.remove(item.fbx_path) # rm original

    return items

def clean_failed_converts() -> None:
    failes = get_convert_items_failed_props()
    failes.objects.clear()
    # failes.collections.clear()

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