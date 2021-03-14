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
            makeReportPopup("FILE NOT SAVED!", "Save your blend file!", "ERROR")

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

        enableExportButton      = True
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

        if not isNadeoIniValid():
            row = layout.row()
            row.alert = True
            row.label(text=errorMsg_NADEOINI)
            return

        if not showConvertPanel:
            layout.row().prop(tm_props, "LI_exportType")
        
        if not exportTypeIsConvertOnly and not showConvertPanel:
            layout.row().prop(tm_props, "LI_gameType")
            layout.row().prop(tm_props, "LI_exportFolderType")
            layout.row().prop(tm_props, exportCustomFolderProp) if exportCustomFolder else None
            layout.row().prop(tm_props, "LI_exportValidTypes",)
            layout.row().prop(tm_props, "LI_exportWhichObjs", expand=True)

            if bpy.context.selected_objects == [] and tm_props.LI_exportWhichObjs == "SELECTED":
                enableExportButton = False
        
        if exportTypeIsConvertOnly:
            row=layout.row()
            row.alert=True
            row.label(text="work in progress, soon ...")
            return

        layout.separator(factor=spacerFac)
        
        if not showConvertPanel:
            row = layout.row()
            row.scale_y = 1.5
            row.enabled = enableExportButton
            row.alert   = not enableExportButton #red button, 0 selected
            row.operator("view3d.tm_export", text=exportType if enableExportButton else "0 objects selected")

        else:
            row=layout.row(align=True)
            row.enabled = not (stopConverting or convertDone)
            row.alert   = atlestOneConvertFailed
            row.prop(tm_props, "NU_converted", text=f"{converted} of {convertCount}")
            row.prop(tm_props, "CB_stopAllNextConverts", icon_only=True, text="", icon="CANCEL")

            # print( dir (row ))
            
            row = layout.row()
            row.alert = atlestOneConvertFailed or stopConverting
            row.label(text="Convert status: " + ("converting" if converting else "done" if not stopConverting else "stopped") )
            

            failed    = str(tm_props.ST_convertedErrorList).split("%%%")
            failed    = [f for f in failed if f!=""]
            
            row = layout.row(align=True)
            row.alert = atlestOneConvertFailed
            row.enabled = True if any([convertDone, stopConverting]) else False
            row.operator("view3d.tm_closeconvertsubpanel", text="OK",           icon="CHECKMARK")
            row.operator("view3d.tm_openconvertreport",    text="Open Report",  icon="HELP")

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
    validObjTypes       = tm_props.LI_exportValidTypes #mesh, light, empty
    useSelectedOnly     = tm_props.LI_exportWhichObjs == "SELECTED"  #only selected objects?
    allObjs             = bpy.context.scene.collection.all_objects
    cols                = bpy.context.scene.collection.children
    action              = tm_props.LI_exportType
    generateLightmaps   = tm_props.CB_uv_genLightMap
    generateIcons       = tm_props.CB_icon_genIcons
    colsToExport        = []
    exportedFBXs        = []

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

            selectObj(obj)
            objnameLower = obj.name.lower()

            if "socket" in objnameLower:
                if "_socket_" not in objnameLower:
                    obj.name = objnameLower
                    obj.name = obj.name.replace("socket", "_socket_")
            
            if "trigger" in objnameLower:
                if "_trigger_" not in objnameLower:
                    obj.name = objnameLower
                    obj.name = obj.name.replace("trigger", "_trigger_")

            if obj.type == "MESH" \
                and not "trigger" in obj.name \
                and not "socket"  in obj.name:
                    fixUvLayerNamesOfObject(obj)


            #run through collections, select and add to exportlist if visible(=selectable)
            for col in obj.users_collection:

                col["waypoint"]  = None
                CHECKPOINT_COLOR = "COLOR_05" 
                START_COLOR      = "COLOR_04" 
                FINISH_COLOR     = "COLOR_01" 
                STARTFINISH_COLOR= "COLOR_03" 
                
                if      col.color_tag == CHECKPOINT_COLOR:   col["WAYPOINT"] = "Checkpoint"
                elif    col.color_tag == START_COLOR:        col["WAYPOINT"] = "Start"
                elif    col.color_tag == FINISH_COLOR:       col["WAYPOINT"] = "Finish"
                elif    col.color_tag == STARTFINISH_COLOR:  col["WAYPOINT"] = "StartFinish"

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
                            colsToExport.append(col)
                            break
                        
        #export each collection ...

        


        for col in colsToExport:

            if isCollectionExcluded(col):
                continue #col is disabled by user in outliner


            deselectAll()

            exportFilePath = f"{exportFilePathBase}{'/'.join( getCollectionHierachy(colname=col.name, hierachystart=[col.name]) )}.fbx"
            exportFilePath = fixSlash(exportFilePath)

            if not action == "ICON":
                newOrigin           = createOriginFixer(col=col)
                newOrigin_oldPos    = tuple(newOrigin.location)     #old pos of origin
                newOrigin.location  = (0,0,0)  #center of world

                selectAllObjectsInACollection(col=col)

                debug(exportFilePath)
                exportFBX(fbxfilepath=exportFilePath)
                exportedFBXs.append(    (exportFilePath, col)  )

                newOrigin.location = newOrigin_oldPos
                deleteOriginFixer(col=col)

                if generateLightmaps:
                    generateLightmap(col=col)
            
            if generateIcons or action == "ICON":
                generateIcon(col=col, filepath=exportFilePath)


    




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
