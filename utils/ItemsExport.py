import os
import re
import bpy
from copy import copy
from shutil import copyfile

from .Materials import save_mat_props_json

from .Models import ExportedItem
from .NadeoImporter import start_batch_convert
from .ItemsIcon import generate_collection_icon, get_icon_path_from_fbx_path, generate_objects_icon
from .ItemsUVs import generate_base_material_cube_projection, generate_lightmap
from .Constants import (
    NOT_ALLOWED_COLLECTION_NAMES,
    SPECIAL_NAME_PREFIX_SOCKET,
    SPECIAL_NAME_PREFIX_TRIGGER,
    SPECIAL_NAME_PREFIX_IGNORE,
    SPECIAL_NAME_PREFIX_ICON_ONLY,
    SPECIAL_NAME_PREFIX_NOTVISIBLE,
    SPECIAL_NAME_PREFIX_NOTCOLLIDABLE,
    WAYPOINT_VALID_NAMES
)
from .Functions import (
    create_folder_if_necessary,
    debug,
    deselect_all_objects,
    get_global_props,
    get_coll_relative_path,
    get_export_path,
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
    return not name.startswith("_") or name.startswith((SPECIAL_NAME_PREFIX_NOTVISIBLE, SPECIAL_NAME_PREFIX_NOTCOLLIDABLE))

def _is_collection_exportable(coll: bpy.types.Collection)->bool:
    if len(coll.objects) == 0\
    or coll.name.lower() in NOT_ALLOWED_COLLECTION_NAMES:
        return False

    is_exportable = False
    for obj in coll.objects:
        is_exportable = _is_object_exportable(obj)
    
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
            has_bm = False
            has_lm = False

            # fix short names and check if both BaseMaterial & LightMap exists
            for uv in obj.data.uv_layers:
                if uv.name.lower().startswith(("base", "bm")):
                    uv.name = "BaseMaterial"
                elif uv.name.lower().startswith(("light", "lm")):
                    uv.name = "LightMap"

                if uv.name == "BaseMaterial":
                    has_bm = True
                elif uv.name == "LightMap":
                    has_lm = True

            # create BaseMaterial & LightMap if they don't exist
            if not has_bm:
                obj.data.uv_layers.new(name="BaseMaterial", do_init=True)
                
            if not has_lm:
                obj.data.uv_layers.new(name="LightMap",     do_init=True)

def _is_physic_hack_required(objects: list[bpy.types.Object]) -> bool:
    physic_hack = False
    if is_game_maniaplanet():
        for obj in objects:
            if obj.type == "MESH":
                for mat in obj.data.materials:
                    is_linked = mat.baseTexture == ""
                    if is_linked:
                        physic_hack = True
                        break
        
    return physic_hack

def _duplicate_scaled(item: ExportedItem) -> list[ExportedItem]:
    pattern   = r"_#SCALE_(\d)+to(\d)+_x(\d)+"
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
            new_item.name = re.sub(pattern, f"_#{scale}", item.name)
            new_item.r_path = re.sub(pattern, f"_#{scale}", item.r_path)
            new_item.fbx_path = re.sub(pattern, f"_#{scale}", item.fbx_path)
            new_item.icon_path = re.sub(pattern, f"_#{scale}", item.icon_path)
            new_item.item_path = re.sub(pattern, f"_#{scale}", item.item_path)

            debug(f"create new file: {new_item.fbx_path}")
            copyfile(item.fbx_path, new_item.fbx_path)
            try:
                copyfile(item.icon_path, new_item.icon_path)
            except FileNotFoundError:
                pass

            current_scale -= scale_step

            items.append(new_item)
        
        debug(f"remove original: {item.fbx_path}")
        os.remove(item.fbx_path) # rm original

    return items

# takes the first item and return offset from it to "location"
def _move_collection_to(objects: list[bpy.types.Object]) -> list[float]:
    offset = get_offset_from_item_origin(objects)
    
    for obj in objects:
        obj.location[0] -= offset[0]
        obj.location[1] -= offset[1]
        obj.location[2] -= offset[2]

    return offset

def _move_collection_by(objects: list[bpy.types.Object], offset: list[float] = [0,0,0]):
    for obj in objects:
        obj.location[0] += offset[0]
        obj.location[1] += offset[1]
        obj.location[2] += offset[2]

def _export_item_FBX(item: ExportedItem) -> None:
    """exports fbx, creates filepath if it does not exist"""
    create_folder_if_necessary(item.fbx_path[:item.fbx_path.rfind("/")]) #deletes all after last slash

    tm_props    = get_global_props()
    objTypes    = tm_props.LI_exportValidTypes.split("_") 
    objTypes    = {ot for ot in objTypes} #MESH_LIGHT_EMPTY
    exportArgs  = {
        "filepath":             item.fbx_path,
        "object_types":         objTypes,
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

def export_collections(colls: list[bpy.types.Collection])->list[ExportedItem]:
    current_selection                            = bpy.context.selected_objects.copy()
    tm_props                                     = get_global_props()
    fix_lightmap                                 = tm_props.CB_uv_fixLightMap
    generate_lightmaps                           = tm_props.CB_uv_genLightMap
    generate_base_materials                      = tm_props.CB_uv_genBaseMaterialCubeMap
    generate_icons                               = tm_props.CB_icon_genIcons
    items_to_export:list[ExportedItem]           = []
    processed_materials:list[bpy.types.Material] = []
    
    export_work_path = get_export_path()
    
    deselect_all_objects()

    for coll in colls:
        if not _is_collection_exportable(coll):
            continue

        debug(f"Preparing <{coll.name}> for export")
        # clean up lazy names
        for obj in coll.objects:
            objname_lower = obj.name.lower()
            if objname_lower.startswith("_") is False:
                if "socket" in objname_lower:  obj.name = "_socket_start"
                if "trigger" in objname_lower: obj.name = "_trigger_"

            for slot in obj.material_slots:
                mat = slot.material
                if mat in processed_materials: continue
                save_mat_props_json(mat)
                processed_materials.append(mat)
        
        # fill metadata
        item_to_export = ExportedItem()
        item_to_export.name = safe_name(coll.name)
        item_to_export.name_raw = coll.name
        item_to_export.objects = coll.objects
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

        if not has_lod0 and not has_lod1:
            if generate_lightmaps: generate_lightmap(coll, fix_lightmap)
            if generate_base_materials: generate_base_material_cube_projection(coll)

        if has_lod1 and not has_lod0:
            show_report_popup("Invalid collections", f"<{coll.name}> has Lod1, but not Lod0, collection skipped")
            return

        # tm2020 socket fix
        _add_empty_socket_hide_existing(coll)

        # move collection to 0,0,0
        offset = _move_collection_to(coll.objects)

        # export .fbx
        _export_item_FBX(item_to_export)
        
        # tm2020 socket fix
        _remove_empty_socket_unhide_existing(coll)

        # generate icon
        if generate_icons:
            generate_collection_icon(coll, item_to_export.icon_path)
        
        # move collection back to original position
        _move_collection_by(coll.objects, offset)

        items_to_export += _duplicate_scaled(item_to_export)

    for obj in current_selection:
        try: select_obj(obj)
        except: pass

    _clean_up_addon_export_settings(len(items_to_export))
    start_batch_convert(items_to_export)

def export_objects(objects: list[bpy.types.Object])->list[ExportedItem]:
    current_selection                            = bpy.context.selected_objects.copy()
    tm_props                                     = get_global_props()
    generate_icons                               = tm_props.CB_icon_genIcons
    items_to_export:list[ExportedItem]           = []
    processed_materials:list[bpy.types.Material] = []
    
    export_work_path = get_export_path()
    
    deselect_all_objects()

    for obj in objects:
        obj:bpy.types.Object = obj
        if not _is_object_exportable(obj):
            continue
        
        debug(f"Preparing <{obj.name}> for export")

        for slot in obj.material_slots:
            mat = slot.material
            if mat in processed_materials: continue
            save_mat_props_json(mat)
            processed_materials.append(mat)

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

        # move collection to 0,0,0
        offset = _move_collection_to([obj])

        # export .fbx
        _export_item_FBX(item_to_export)

        # generate icon
        if generate_icons:
            generate_objects_icon([obj], obj.name, item_to_export.icon_path)
        
        # move collection back to original position
        _move_collection_by([obj], offset)

        items_to_export += _duplicate_scaled(item_to_export)

    for obj in current_selection:
        try: select_obj(obj)
        except: pass

    _clean_up_addon_export_settings(len(items_to_export))
    start_batch_convert(items_to_export)