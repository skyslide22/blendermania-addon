from typing import List
import bpy
import os.path
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from .TM_Functions      import *
from .TM_Items_Convert  import *
from .TM_Items_XML      import *
from .TM_Items_UVMaps   import *
from .TM_Settings       import *
from .TM_Items_Icon     import *
from .TM_Materials      import *
from .TM_Dotnet         import *
from .TM_UI_Map_Export  import *

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
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}
    

class TM_OT_Items_Export_CloseConvertSubPanel(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_closeconvertsubpanel"
    bl_description = "Ok, close this panel"
    bl_icon = 'MATERIAL'
    bl_label = "Close Convert Sub Panel"
        
    def execute(self, context):
        tm_props = getTmProps()
        tm_props.CB_converting            = False
        tm_props.CB_showConvertPanel      = False
        tm_props.CB_stopAllNextConverts   = False
        tm_props.CB_uv_genBaseMaterialCubeMap = False # for stupid mistakes ... :)
        return {"FINISHED"}


class TM_PT_Items_Export(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Export & Convert FBX"
    bl_idname  = "TM_PT_Items_Export"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="EXPORT")

    # endregion
    def draw(self, context):

        layout = self.layout
        tm_props = getTmProps()

        if requireValidNadeoINI(self) is False: return

        enableExportButton      = True
        exportActionIsSelected  = tm_props.LI_exportWhichObjs == "SELECTED"
        exportFolderType        = tm_props.LI_exportFolderType
        exportCustomFolder      = True if str(exportFolderType).lower() == "custom" else False
        exportCustomFolderProp  = "ST_exportFolder_MP" if isGameTypeManiaPlanet() else "ST_exportFolder_TM"
        exportType              = tm_props.LI_exportType
        showConvertPanel        = tm_props.CB_showConvertPanel
        atlestOneConvertFailed  = tm_props.NU_convertedError > 0
        converted               = tm_props.NU_convertedRaw
        convertCount            = tm_props.NU_convertCount
        converting              = tm_props.CB_converting
        convertDone             = not converting
        stopConverting          = tm_props.CB_stopAllNextConverts
        exportTypeIsConvertOnly = str(exportType).lower() == "convert"


        if not showConvertPanel:
            layout.row().prop(tm_props, "LI_exportType")
        
        if not exportTypeIsConvertOnly and not showConvertPanel:
            layout.row().prop(tm_props, "LI_gameType")
            layout.row().prop(tm_props, "LI_exportFolderType")
            
            if exportCustomFolder:
                row_path = layout.row()
                if "/Work/" not in fixSlash( getattr(tm_props, exportCustomFolderProp) ):
                    row_error= layout.row()
                    row_error.alert = True
                    row_error.label(text="Folder has to be in /Work/Items/ ...", icon="ERROR")
                    row_path.alert=True
                row_path.prop(tm_props, exportCustomFolderProp)


            # layout.row().prop(tm_props, "LI_exportValidTypes",)
            layout.row().prop(tm_props, "LI_exportWhichObjs", expand=True)

            if bpy.context.selected_objects == [] and exportActionIsSelected:
                enableExportButton = False
        
        # if exportTypeIsConvertOnly:
        #     row=layout.row()
        #     row.alert=True
        #     row.label(text="work in progress, soon ...")
        #     return

        
        if not showConvertPanel:
            layout.separator(factor=UI_SPACER_FACTOR)

            text = exportType
            icon = "EXPORT"

            # get number of collections which can be exported
            selected_objects = bpy.context.selected_objects
            visible_objects  = bpy.context.visible_objects
            objs = selected_objects if exportActionIsSelected else visible_objects

            if len(visible_objects) < 500:
                exportable_cols  = getExportableCollections(objs=objs)
                collection_count = len(exportable_cols)

                plural = "s" if collection_count > 1 else ""

                if exportType == "EXPORT":
                    text=f"Export {collection_count} collection{plural}"

                elif exportType == "EXPORT_CONVERT":
                    text=f"Export & convert {collection_count} collection{plural}"

                if collection_count == 0:
                    enableExportButton = False
            else:
                text = "Export collections"
                enableExportButton = True

            if exportType == "EXPORT":
                icon="EXPORT"
            elif exportType == "EXPORT_CONVERT":
                 icon="CON_FOLLOWPATH"

            col = layout.column(align=True)

            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = enableExportButton 
            row.alert   = not enableExportButton #red button, 0 selected
            row.operator("view3d.tm_export", text=text,   icon=icon)
            row.prop(tm_props, "CB_convertMultiThreaded", icon_only=True, icon="SORTTIME", invert_checkbox=True)
            row.prop(tm_props, "CB_notifyPopupWhenDone",  icon_only=True, icon="INFO")

            if isGameTypeTrackmania2020():
                row = col.row(align=True)
                row.prop(tm_props, "CB_generateMeshAndShapeGBX", text="Create files for meshmodeler import", toggle=True)

            if exportType == "EXPORT_CONVERT" and len(visible_objects) < 500:
                embed_space = 0
                if enableExportButton:
                    for col in exportable_cols:
                        embed_space += getEmbedSpaceOfCollection(col)
                row = layout.row()
                
                embed_space_1024kb = embed_space < 1.024
                if embed_space_1024kb:
                    embed_space *= 1000

                row.label(text=f"Max. embed space: ~ {embed_space:4.2f} {'kB' if embed_space_1024kb else 'mB'}")





        #* show convert panel and hide everything else
        else:
            layout.separator(factor=UI_SPACER_FACTOR)

            box = layout.box()
            box.use_property_split = True

            exported_cols = [bpy.data.collections[exp_col.name_raw] for exp_col in getTmConvertingItemsProp()]
            embed_space   = 0
            for col in exported_cols:
                embed_space += getEmbedSpaceOfCollection(col)
            row = box.row()
            row.scale_y = .5
            embed_space_1024kb = embed_space < 1.024
            if embed_space_1024kb:
                embed_space *= 1000
            row.label(text="Max. embedding")
            row.label(text=f"~ {embed_space:4.2f} {'kB' if embed_space_1024kb else 'mB'}")

            #progress bar
            convert_duration_since_start = tm_props.NU_convertDurationSinceStart
            prev_convert_time            = tm_props.NU_prevConvertDuration

            # convert time since start
            row = box.row()
            row.scale_y = .5
            row.label(text=f"""Duration:""")
            row.label(text=f"""{convert_duration_since_start}s — {prev_convert_time}s?""")




            col = layout.column(align=True)
            row = col.row(align=True)
            row.alert   = atlestOneConvertFailed
            row.prop(tm_props, "NU_converted", text=f"{converted} of {convertCount}")
            row.prop(tm_props, "CB_stopAllNextConverts", icon_only=True, text="", icon="CANCEL")
            # row.prop(tm_props, "CB_notifyPopupWhenDone", icon_only=True, text="", icon="INFO")

            failed    = str(tm_props.ST_convertedErrorList).split("%%%")
            failed    = [f for f in failed if f!=""]
            

            #buttons OK, REPORT
            row = col.row(align=True)
            row.alert   = atlestOneConvertFailed
            row.scale_y = 1.25
            
            if(failed):
                bcol = row.column(align=True)
                bcol.scale_x = 1.25
                bcol.operator("view3d.tm_execute_help", text="Show errors",  icon="HELP").command = "open_convertreport"    
            
            bcol = row.column(align=True)
            bcol.enabled = True # if any([convertDone, stopConverting]) else False
            bcol.operator("view3d.tm_closeconvertsubpanel", text="OK",           icon="NONE")

            bcol = row.column(align=True)
            bcol.enabled = enableExportButton 
            bcol.operator("view3d.tm_export", text="", icon="FILE_REFRESH")
            


            #result of fails
            if failed:
                row = layout.row()
                row.alert = True if failed else False
                row.label(text=f"Failed converts: {len(failed)}")


            for item in getTmConvertingItemsProp():
                row = layout.row(align=True)
                col = row.column()
                col.alert = item.failed
                col.label(
                    text=f"""{item.convert_duration if item.converted else "??"}s — {item.name}""", 
                    icon=item.icon)











def exportAndOrConvert(callback: callable = None)->list[ExportedItem]:
    """export&convert fbx main function, call all other functions on conditions set in UI"""
    tm_props            = getTmProps()
    exported_items      = list[ExportedItem]()
    # validObjTypes       = tm_props.LI_exportValidTypes #mesh, light, empty
    useSelectedOnly     = tm_props.LI_exportWhichObjs == "SELECTED"  #only selected objects?
    action              = tm_props.LI_exportType
    generateIcons       = tm_props.CB_icon_genIcons
    invalidCollections  = []
    embeddedMaterials   = []
    pre_selected_objs   = []

    exportedFBXs: List[exportFBXModel] = []

    selected_objects = bpy.context.selected_objects
    visible_objects  = bpy.context.visible_objects
    
    objs = selected_objects if useSelectedOnly else visible_objects
    colsToExport = getExportableCollections(objs=objs)

    generateLightmaps                = tm_props.CB_uv_genLightMap
    fixLightmap                      = tm_props.CB_uv_fixLightMap
    generateBaseMaterialCubeProjects = tm_props.CB_uv_genBaseMaterialCubeMap

    export_path_base      = "/"
    export_path_custom    = tm_props.ST_exportFolder_MP if isGameTypeManiaPlanet() else tm_props.ST_exportFolder_TM
    export_path_custom    = fixSlash(getAbspath(export_path_custom) + "/")
    export_path_is_custom = tm_props.LI_exportFolderType == "Custom"

    if export_path_is_custom:
        export_path_base = export_path_custom
    else:
        export_path_base = getGameDocPathWorkItems()

    fixAllColNames() #[a-zA-Z0-9_-#] only




    if useSelectedOnly:
        pre_selected_objs = bpy.context.selected_objects.copy()
    
    deselectAllObjects()

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
        deselectAllObjects()

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

        deselectAllObjects()
        selectAllObjectsInACollection(col=col, only_direct_children=True, exclude_infixes="_ignore, delete")
        debug(f"selected objects: {bpy.context.selected_objects}")

        # export, may be multiple lul
        exportFBX(fbxfilepath=FBX_exportFilePath)
        
        for exportedFBX in getDuplicateScaledExportedFBXFiles(FBX_exportFilePath, col):

            exportedFBXs.append(exportedFBX)

            filename = getFilenameOfPath(exportedFBX.filepath, remove_extension=True)
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
        makeReportPopup("Invalid collections", invalidCollections)

    deselectAllObjects()
    if useSelectedOnly:
        for obj in pre_selected_objs:
            try:    selectObj(obj)
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
    tm_props    = getTmProps()
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

    createFolderIfNecessary(fbxfilepath[:fbxfilepath.rfind("/")]) #deletes all after last slash


    bpy.ops.export_scene.fbx(**exportArgs) #one argument is optional, so give a modified dict and **unpack





