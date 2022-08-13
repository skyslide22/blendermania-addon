from typing import List
import bpy
import os.path
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from ..utils.ItemsExport import export_items_collections

from ..utils.Functions      import *
from ..utils.Dotnet         import *
from ..utils.Constants      import * 
from ..operators.OT_Items_Convert  import *
from ..operators.OT_Items_XML      import *
from ..operators.OT_Items_UVMaps   import *
from ..operators.OT_Settings       import *
from ..operators.OT_Items_Icon     import *
from ..operators.OT_Materials      import *

class ExportedItem:
    def __init__(self, name: str, path: str, location: list[float], rotation: list[float] = []):
        self.name = name
        self.path = path
        self.location = location
        self.rotation = rotation

    def to_dotnet_item(self) -> DotnetItem:
        return DotnetItem(
            self.name,
            self.path,
            DotnetVector3(self.location[0],self.location[2], self.location[1]),
        )


class TM_OT_Items_Export_ExportAndOrConvert(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_export"
    bl_description = "Export and convert items"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash
        
    def execute(self, context):

        if saveBlendFile():
            exportAndOrConvert()
        
        else:
            show_report_popup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}
    

class TM_OT_Items_Export_CloseConvertSubPanel(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_closeconvertsubpanel"
    bl_description = "Ok, close this panel"
    bl_icon = 'MATERIAL'
    bl_label = "Close Convert Sub Panel"
        
    def execute(self, context):
        tm_props = get_global_props()
        tm_props.CB_converting            = False
        tm_props.CB_showConvertPanel      = False
        tm_props.CB_stopAllNextConverts   = False
        tm_props.CB_uv_genBaseMaterialCubeMap = False # for stupid mistakes ... :)
        return {"FINISHED"}










def exportAndOrConvert(callback: callable = None)->list[ExportedItem]:
    """ new export
    tm_props = get_global_props()
    
    # take all collections or only selected
    to_export = bpy.data.collections
    if tm_props.LI_exportWhichObjs == "SELECTED":
        to_export = []
        for obj in bpy.context.selected_objects:
            for coll in obj.users_collection:
                if coll not in to_export:
                    to_export.append(coll)
    
    export_items_collections(to_export)
    return
    """


    """export&convert fbx main function, call all other functions on conditions set in UI"""
    tm_props            = get_global_props()
    exported_items      = list[ExportedItem]()
    # validObjTypes       = tm_props.LI_exportValidTypes #mesh, light, empty
    useSelectedOnly     = tm_props.LI_exportWhichObjs == "SELECTED"  #only selected objects?
    action              = tm_props.LI_exportType
    generateIcons       = tm_props.CB_icon_genIcons
    invalidCollections  = []
    embeddedMaterials   = []
    pre_selected_objs   = []

    exportedFBXs: List[ExportFBXModel] = []

    selected_objects = bpy.context.selected_objects
    visible_objects  = bpy.context.visible_objects
    
    objs = selected_objects if useSelectedOnly else visible_objects
    colsToExport = getExportableCollections(objs=objs)

    generateLightmaps                = tm_props.CB_uv_genLightMap
    fixLightmap                      = tm_props.CB_uv_fixLightMap
    generateBaseMaterialCubeProjects = tm_props.CB_uv_genBaseMaterialCubeMap

    export_path_base      = "/"
    export_path_custom    = tm_props.ST_exportFolder_MP if isGameTypeManiaPlanet() else tm_props.ST_exportFolder_TM
    export_path_custom    = fixSlash(get_abs_path(export_path_custom) + "/")
    export_path_is_custom = tm_props.LI_exportFolderType == "Custom"

    if export_path_is_custom:
        export_path_base = export_path_custom
    else:
        export_path_base = get_game_doc_path_work_items()

    fixAllColNames() #[a-zA-Z0-9_-#] only




    if useSelectedOnly:
        pre_selected_objs = bpy.context.selected_objects.copy()
    
    deselect_all_objects()

    for obj in objs:
        
        # rename lazy names (spawn, trigger, notvisible, notcollidable)
        objnameLower = obj.name.lower()

        if objnameLower.startswith("_") is False:
            if "socket" in objnameLower:        obj.name = "_socket_start"
            if "trigger" in objnameLower:       obj.name = "_trigger_"
            if "ignore" in objnameLower:        obj.name = "_ignore_"+obj.name
            if "notvisible" in objnameLower:    obj.name = "_notvisible_"+obj.name
            if "notcollidable" in objnameLower: obj.name = "_notcollidable_"+obj.name


        # save material as json in the exported fbx file (for import? later) 
        for slot in obj.material_slots:
            mat = slot.material
            if mat in embeddedMaterials: continue

            saveMatPropsAsJSONinMat(mat=mat) #only string/bool/num custom props are saved in fbx...
            embeddedMaterials.append(mat)

    debug("-----")
    for col in colsToExport:
        debug(col.name)

    #export each collection ...
    for col in colsToExport:
        deselect_all_objects()

        exportFilePath = f"{export_path_base}{'/'.join( getCollectionHierachy(colname=col.name, hierachystart=[col.name]) )}"
        FBX_exportFilePath = fixSlash(exportFilePath + ".fbx")

    

        fixUvLayerNamesOfObjects(col=col)

        has_lod_0 = False
        has_lod_1 = False
        for obj in col.objects: 
            if   "_lod0" in obj.name.lower(): has_lod_0 = True
            elif "_lod1" in obj.name.lower(): has_lod_1 = True
        

        if  not has_lod_0\
        and not has_lod_1: #if obj uses lods, auto lightmap is not good.
        
            if generateLightmaps:
                generateLightmap(col=col, fix=fixLightmap)

            if generateBaseMaterialCubeProjects:
                generateBaseMaterialCubeProject(col=col)

        if has_lod_1 and not has_lod_0:
            invalidCollections.append(f"<{col.name}> has Lod1, but not Lod0, collection skipped")
            continue
        
        debug()
        debug(f"Start export of collection <{col.name}>")
        
        # all col objs parenting to an empty obj
        # move to center, unparent, export,
        # parent again, back to old origin, unparent
        # avoid it if collection has only one object
        ORIGIN = createExportOriginFixer(col=col) if len(col.objects) != 1 else col.objects[0]
        debug(f"origin for collection <{col.name}> is <{ORIGIN.name}>")

        origin_oldPos    = tuple(ORIGIN.location) #old pos of origin
        ORIGIN.location  = (0,0,0)  #center of world

        # Lod0, Lod1 can't be childrens
        # so unparent and keep all transforms at 0,0,0
        if len(col.objects) != 1: unparentObjsAndKeepTransform(col=col) 

        deselect_all_objects()
        selectAllObjectsInACollection(col=col, only_direct_children=True, exclude_infixes="_ignore, delete")
        debug(f"selected objects: {bpy.context.selected_objects}")

        # export, may be multiple lul
        exportFBX(fbxfilepath=FBX_exportFilePath)
        
        for exportedFBX in getDuplicateScaledExportedFBXFiles(FBX_exportFilePath, col):

            exportedFBXs.append(exportedFBX)

            filename = get_path_filename(exportedFBX.filepath, remove_extension=True)
            debug(f"exported collection <{filename}> (hack physics: {exportedFBX.physic_hack})")

            if generateIcons:
                generateIcon(col, exportedFBX.filepath)




        if len(col.objects) != 1: parentObjsToObj(col=col, obj=ORIGIN)
        ORIGIN.location = origin_oldPos
        exported_items.append(ExportedItem(
            fixSlash("Items/" + FBX_exportFilePath.split("/Work/Items/")[-1]).replace(".fbx", ".Item.Gbx"),
            fixSlash(FBX_exportFilePath.replace("/Work/Items/", "/Items/")).replace(".fbx", ".Item.Gbx"),
            list(origin_oldPos),
        ))

        if len(col.objects) != 1: deleteExportOriginFixer(col=col)
        


    #end for col in colsToExport
    if invalidCollections:
        show_report_popup("Invalid collections", invalidCollections)

    deselect_all_objects()
    if useSelectedOnly:
        for obj in pre_selected_objs:
            try:    select_obj(obj)
            except: pass


    if action == "EXPORT_CONVERT":
        def onExportCallback():
            if callback is not None:
                callback(exported_items)
        
        tm_props.NU_convertCount        = len(exportedFBXs)
        tm_props.NU_converted           = 0
        tm_props.NU_convertedRaw        = 0
        tm_props.NU_convertedError      = 0
        tm_props.NU_convertedSuccess    = 0
        tm_props.ST_convertedErrorList  = ""
        tm_props.CB_converting          = True

        tm_props.NU_convertDurationSinceStart = 0
        tm_props.NU_convertStartedAt          = 0
        tm_props.NU_currentConvertDuration    = 0
        
        #run convert on second thread to avoid blender to freeze
        startBatchConvert(exportedFBXs, onExportCallback)
        return exported_items

    return []






def exportFBX(fbxfilepath) -> None:
    """exports fbx, creates filepath if it does not exist"""
    tm_props    = get_global_props()
    objTypes    = tm_props.LI_exportValidTypes.split("_") 
    objTypes    = {ot for ot in objTypes} #MESH_LIGHT_EMPTY
    exportArgs  = {
        "filepath":             fbxfilepath,
        "object_types":         objTypes,
        "use_selection":        True,
        "use_custom_props":     True,
        "apply_unit_scale":     False,
    }

    if isGameTypeManiaPlanet():
        exportArgs["apply_scale_options"] = "FBX_SCALE_UNITS"

    create_folder_if_necessary(fbxfilepath[:fbxfilepath.rfind("/")]) #deletes all after last slash


    bpy.ops.export_scene.fbx(**exportArgs) #one argument is optional, so give a modified dict and **unpack





