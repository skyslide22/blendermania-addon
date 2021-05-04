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
    bl_description = "Execute Order 66"
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
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Open convert report"
        
    def execute(self, context):
        openHelp("convertreport")
        return {"FINISHED"}


class TM_OT_Items_Export_CloseConvertSubPanel(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_closeconvertsubpanel"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Close Convert Sub Panel"
        
    def execute(self, context):
        context.scene.tm_props.CB_showConvertPanel      = False
        context.scene.tm_props.CB_stopAllNextConverts   = False
        return {"FINISHED"}


class TM_PT_Items_Export(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label = "Export & Convert FBX"
    bl_idname = "TM_PT_Items_Export"
    locals().update( panelClassDefaultProps )

    # endregion
    def draw(self, context):

        layout = self.layout
        tm_props = context.scene.tm_props

        if requireValidNadeoINI(self) is False: return

        enableExportButton      = True
        exportSelectedOrVisible = tm_props.LI_exportWhichObjs
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

            if bpy.context.selected_objects == [] and exportSelectedOrVisible == "SELECTED":
                enableExportButton = False
        
        if exportTypeIsConvertOnly:
            row=layout.row()
            row.alert=True
            row.label(text="work in progress, soon ...")
            return

        layout.separator(factor=UI_SPACER_FACTOR)
        
        if showConvertPanel is False:
            row = layout.row()
            row.scale_y = 1.5
            row.enabled = enableExportButton
            row.alert   = not enableExportButton #red button, 0 selected

            text = exportType
            icon = "EXPORT"

            if exportType == "EXPORT":            
                icon="EXPORT";          
                text=f"Export {exportSelectedOrVisible.lower()}"

            elif exportType == "EXPORT_CONVERT":    
                icon="CON_FOLLOWPATH";  
                text=f"Export {exportSelectedOrVisible.lower()} & convert"

            elif exportType == "CONVERT":           
                icon="FILE_REFRESH";    
                text=f"Convert folder..."
                
            elif exportType == "ICON":              
                icon="FILE_IMAGE";      
                text=f"Create icons for {exportSelectedOrVisible.lower()}"
            
            row.operator("view3d.tm_export", text=text, icon=icon)


        #*show panel
        else:

            #progress bar
            row=layout.row(align=True)
            # row.enabled = not (stopConverting or convertDone)
            row.alert   = atlestOneConvertFailed
            row.prop(tm_props, "NU_converted", text=f"{converted} of {convertCount}")
            row.prop(tm_props, "CB_stopAllNextConverts", icon_only=True, text="", icon="CANCEL")
            # row.prop(tm_props, "CB_notifyPopupWhenDone", icon_only=True, text="", icon="INFO")

            failed    = str(tm_props.ST_convertedErrorList).split("%%%")
            failed    = [f for f in failed if f!=""]
            
            #buttons OK, REPORT
            row = layout.row(align=True)
            row.alert = atlestOneConvertFailed
            row.enabled = True if any([convertDone, stopConverting]) else False
            row.operator("view3d.tm_closeconvertsubpanel", text="OK",           icon="CHECKMARK")
            row.operator("view3d.tm_openconvertreport",    text="Open Report",  icon="HELP")    

            #label convert status
            row = layout.row()
            row.alert = atlestOneConvertFailed or stopConverting
            row.label(text="Convert status: " + ("converting" if converting else "done" if not stopConverting else "stopped") )
            
            #result of fails
            row = layout.row()
            row.alert = True if failed else False
            row.label(text=f"Failed converts: {len(failed)}")

            for i, fail in enumerate(failed):
                row = layout.row()
                row.alert=True
                row.label(text=f"{i+1}. {fail}")

        # layout.separator(factor=spacerFac)










def exportAndOrConvert()->None:
    """export&convert fbx main function, call all other functions on conditions set in UI"""
    tm_props            = bpy.context.scene.tm_props
    # validObjTypes       = tm_props.LI_exportValidTypes #mesh, light, empty
    useSelectedOnly     = tm_props.LI_exportWhichObjs == "SELECTED"  #only selected objects?
    allObjs             = bpy.context.scene.collection.all_objects
    action              = tm_props.LI_exportType
    generateLightmaps   = tm_props.CB_uv_genLightMap
    fixLightmap         = tm_props.CB_uv_fixLightMap
    generateIcons       = tm_props.CB_icon_genIcons
    colsToExport        = []
    exportedFBXs        = []
    invalidCollections  = []
    embeddedMaterials   = []

    exportFilePathBase  = ""
    exportPathType      = tm_props.LI_exportFolderType
    exportPathCustom    = tm_props.ST_exportFolder_MP if isGameTypeManiaPlanet() else tm_props.ST_exportFolder_TM

    if str(exportPathType).lower() != "custom":
        envi = exportPathType if str(exportPathType).lower() != "base" else ""
        exportFilePathBase = getDocPathWorkItems() + envi
    
    elif str(exportPathType).lower() == "custom":
        exportFilePathBase = exportPathCustom

    exportFilePathBase += "/"
    fixAllColNames() #[a-zA-Z0-9_-#] only


    if action == "EXPORT" \
    or action == "EXPORT_CONVERT"\
    or action == "ICON":
        
        #generate list of collections to export
        for obj in allObjs:
            
            if useSelectedOnly:
                if not obj.select_get(): continue

            debug(f"try action <{action}> for <{obj.name}>")

            selectObj(obj)
            objnameLower = obj.name.lower()

            if "socket" in objnameLower\
            and objnameLower.startswith("_") is False:
                obj.name = "_socket_"
            
            if "trigger" in objnameLower\
            and objnameLower.startswith("_") is False:
                obj.name = "_trigger_"


            #run through collections, select and add to exportlist if visible(=selectable)
            for col in obj.users_collection:
                if col.name.lower() not in notAllowedColnames:
                    if col not in colsToExport:
                        colsToExport.append( col )
        
        #remove doubles
        colsToExportSet = set(colsToExport)
        colsToExport = [] #sort collections which are not disabled
        
        for col in colsToExportSet:
            if not isCollectionExcluded(col):
                for obj in col.all_objects:
                    if obj.type == "MESH":
                        if selectObj(obj):
                            for slot in obj.material_slots:
                                mat = slot.material
                                if not mat in embeddedMaterials:
                                    saveMatPropsAsJSONinMat(mat=mat) #only string/bool/num custom props are saved in fbx...
                                    embeddedMaterials.append(mat)
                            colsToExport.append(col)
                        
        #export each collection ...


        for col in set(colsToExport):

            if isCollectionExcluded(col):
                continue #col is disabled by user in outliner


            deselectAll()

            exportFilePath = f"{exportFilePathBase}{'/'.join( getCollectionHierachy(colname=col.name, hierachystart=[col.name]) )}"
            FBX_exportFilePath = fixSlash(exportFilePath + ".fbx")

            if not action == "ICON":

                fixUvLayerNamesOfObjects(col=col)

                has_lod_0 = False
                has_lod_1 = False
                for obj in col.all_objects: 
                    if   "_lod0" in obj.name.lower(): has_lod_0 = True
                    elif "_lod1" in obj.name.lower(): has_lod_1 = True
                
                if  not has_lod_0\
                and not has_lod_1: #if obj uses lods, auto lightmap is not good.
                    if generateLightmaps:
                        generateLightmap(col=col, fix=fixLightmap)

                if has_lod_1 and not has_lod_0:
                    invalidCollections.append(f"<{col.name}> has Lod1, but not Lod0, collection skipped")
                    continue
                
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

                deselectAll()
                selectAllObjectsInACollection(col=col, exclude_infixes="_ignore, delete")
                debug(f"selected objects: {bpy.context.selected_objects}")

                exportFBX(fbxfilepath=FBX_exportFilePath)
                exportedFBXs.append(    (FBX_exportFilePath, col)  )
                debug(f"exported collection <{col.name}>")

                parentObjsToObj(col=col, obj=ORIGIN)
                ORIGIN.location = origin_oldPos

                deleteExportOriginFixer(col=col)
            
            if generateIcons\
            or action == "ICON":
                generateIcon(col=col, filepath=FBX_exportFilePath)

        #end for col in colsToExport
        if invalidCollections:
            makeReportPopup("Invalid collections", invalidCollections)
    




    if action == "EXPORT_CONVERT":
        
        tm_props.NU_convertCount        = len(exportedFBXs)
        tm_props.NU_converted           = 0
        tm_props.NU_convertedRaw        = 0
        tm_props.NU_convertedError      = 0
        tm_props.NU_convertedSuccess    = 0
        tm_props.ST_convertedErrorList  = ""
        tm_props.CB_converting          = True
        
        #run convert on second thread to avoid blender to freeze
        convert = Thread(target=startBatchConvert, args=[exportedFBXs]) 
        convert.start()
    

    # generate xmls
    for fbxinfo in exportedFBXs:
        genItemXML = tm_props.CB_xml_genItemXML
        genMeshXML = tm_props.CB_xml_genMeshXML
        genIcon    = tm_props.CB_icon_genIcons


        fbx, col = fbxinfo

        if genItemXML: generateItemXML(fbxfilepath=fbx, col=col)
        if genMeshXML: generateMeshXML(fbxfilepath=fbx, col=col)
        # if genIcon:    generateIcon(col=col)








def exportFBX(fbxfilepath) -> None:
    """exports fbx, creates filepath if it does not exist"""
    tm_props    = bpy.context.scene.tm_props
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





