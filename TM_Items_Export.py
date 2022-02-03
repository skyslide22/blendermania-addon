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
    
    
class TM_OT_Items_Export_OpenConvertReport(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_openconvertreport"
    bl_description = "Open the error report in browser"
    bl_icon = 'MATERIAL'
    bl_label = "Open convert report"
        
    def execute(self, context):
        openHelp("convertreport")
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
        tm_props.NU_lastConvertDuration   = tm_props.NU_currentConvertDuration
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
            collection_count = len(getExportableCollections(objs=objs))

            plural = "s" if collection_count > 1 else ""

            if exportType == "EXPORT":
                icon="EXPORT"; 
                text=f"Export {collection_count} collection{plural}"

            elif exportType == "EXPORT_CONVERT":
                icon="CON_FOLLOWPATH";  
                text=f"Export & convert {collection_count} collection{plural}"

            if collection_count == 0:
                enableExportButton = False

            col = layout.column(align=True)

            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = enableExportButton 
            row.alert   = not enableExportButton #red button, 0 selected
            row.operator("view3d.tm_export", text=text, icon=icon)
            row.prop(tm_props, "CB_notifyPopupWhenDone", icon_only=True, icon="INFO")

            if isGameTypeTrackmania2020():
                row = col.row(align=True)
                row.prop(tm_props, "CB_generateMeshAndShapeGBX", text="Create files for meshmodeler import", toggle=True)




        #* show convert panel and hide everything else
        else:

            #progress bar
            convert_duration_since_start = tm_props.NU_convertDurationSinceStart
            last_convert_time            = tm_props.NU_lastConvertDuration
            is_not_first_convert         = last_convert_time != -1
            remaining_time               = tm_props.NU_remainingConvertTime

            # convert time since start
            layout.row().label(text=f"""Current convert duration: {convert_duration_since_start}s""")

            # last & remaining
            if is_not_first_convert and converting:
                row = layout.row()
                row.scale_y = 0.2
                row.label(text=f"""Like previous convert?: {remaining_time}s""")


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
            row.alert = atlestOneConvertFailed
            row.enabled = True if any([convertDone, stopConverting]) else False
            row.operator("view3d.tm_closeconvertsubpanel", text="OK",           icon="NONE")
            if(failed):
                row.operator("view3d.tm_openconvertreport",    text="Open Report",  icon="HELP")    
            

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











def exportAndOrConvert()->None:
    """export&convert fbx main function, call all other functions on conditions set in UI"""
    tm_props            = getTmProps()
    # validObjTypes       = tm_props.LI_exportValidTypes #mesh, light, empty
    useSelectedOnly     = tm_props.LI_exportWhichObjs == "SELECTED"  #only selected objects?
    allObjs             = bpy.context.scene.collection.all_objects
    action              = tm_props.LI_exportType
    generateIcons       = tm_props.CB_icon_genIcons
    exportedFBXs        = []
    invalidCollections  = []
    embeddedMaterials   = []
    pre_selected_objs   = []

    selected_objects = bpy.context.selected_objects
    visible_objects  = bpy.context.visible_objects
    
    objs = selected_objects if useSelectedOnly else visible_objects
    colsToExport = getExportableCollections(objs=objs)

    generateLightmaps                = tm_props.CB_uv_genLightMap
    fixLightmap                      = tm_props.CB_uv_fixLightMap
    generateBaseMaterialCubeProjects = tm_props.CB_uv_genBaseMaterialCubeMap

    exportFilePathBase  = ""
    exportPathType      = tm_props.LI_exportFolderType
    exportPathCustom    = tm_props.ST_exportFolder_MP if isGameTypeManiaPlanet() else tm_props.ST_exportFolder_TM
    exportPathCustom    = fixSlash(getAbspath(exportPathCustom)) # ../../myproject=> C:/Users.../Work/Items/myproject
    
    if str(exportPathType).lower() != "custom":
        envi = exportPathType if str(exportPathType).lower() != "base" else ""
        exportFilePathBase = getDocPathWorkItems() + envi
    
    elif str(exportPathType).lower() == "custom":
        exportFilePathBase = exportPathCustom

    exportFilePathBase += "/"
    fixAllColNames() #[a-zA-Z0-9_-#] only




    if useSelectedOnly:
        pre_selected_objs = bpy.context.selected_objects.copy()
    
    deselectAllObjects()

    for obj in allObjs:
        
        # rename lazy names (spawn, trigger, notvisible, notcollidable)
        objnameLower = obj.name.lower()

        if "socket" in objnameLower\
        and objnameLower.startswith("_") is False:
            obj.name = "_socket_start"
        
        if "trigger" in objnameLower\
        and objnameLower.startswith("_") is False:
            obj.name = "_trigger_"

        if "ignore" in objnameLower\
        and objnameLower.startswith("_") is False:
            obj.name = "_ignore_"+obj.name

        if "notvisible" in objnameLower\
        and objnameLower.startswith("_") is False:
            obj.name = "_notvisible_"+obj.name

        if "notcollidable" in objnameLower\
        and objnameLower.startswith("_") is False:
            obj.name = "_notcollidable_"+obj.name


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

        exportFilePath = f"{exportFilePathBase}{'/'.join( getCollectionHierachy(colname=col.name, hierachystart=[col.name]) )}"
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
        ORIGIN = createExportOriginFixer(col=col)
        debug(f"origin for collection <{col.name}> is <{ORIGIN.name}>")

        origin_oldPos    = tuple(ORIGIN.location) #old pos of origin
        ORIGIN.location  = (0,0,0)  #center of world

        # Lod0, Lod1 can't be childrens
        # so unparent and keep all transforms at 0,0,0
        unparentObjsAndKeepTransform(col=col) 

        deselectAllObjects()
        selectAllObjectsInACollection(col=col, only_direct_children=True, exclude_infixes="_ignore, delete")
        debug(f"selected objects: {bpy.context.selected_objects}")



        # export, may be multiple lul
        exportFBX(fbxfilepath=FBX_exportFilePath)
        
        for exportedFBX in getDuplicateScaledExportedFBXFiles(FBX_exportFilePath, col):

            exportedFBXs.append(exportedFBX)
            debug(f"exported collection <{getFilenameOfPath(exportedFBX.filepath, remove_extension=True)}>")

            if generateIcons:
                generateIcon(col, exportedFBX.filepath)




        parentObjsToObj(col=col, obj=ORIGIN)
        ORIGIN.location = origin_oldPos

        deleteExportOriginFixer(col=col)
        


    #end for col in colsToExport
    if invalidCollections:
        makeReportPopup("Invalid collections", invalidCollections)

    deselectAllObjects()
    if useSelectedOnly:
        for obj in pre_selected_objs:
            try:    selectObj(obj)
            except: pass


    if action == "EXPORT_CONVERT":
        
        tm_props.NU_convertCount        = len(exportedFBXs)
        tm_props.NU_converted           = 0
        tm_props.NU_convertedRaw        = 0
        tm_props.NU_convertedError      = 0
        tm_props.NU_convertedSuccess    = 0
        tm_props.ST_convertedErrorList  = ""
        tm_props.CB_converting          = True
        
        #run convert on second thread to avoid blender to freeze
        startBatchConvert(exportedFBXs) 


    # generate xmls
    for exportedFBX in exportedFBXs:
        genItemXML = tm_props.CB_xml_genItemXML
        genMeshXML = tm_props.CB_xml_genMeshXML
        genIcon    = tm_props.CB_icon_genIcons

        if genItemXML: generateItemXML(exportedFBX)
        if genMeshXML: generateMeshXML(exportedFBX)
        # if genIcon:    generateIcon(col=col)






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





