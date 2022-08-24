import bpy
from bpy.types import (Panel)

from ..utils.Functions      import *

class TM_PT_Items_Export(Panel):
    bl_label   = "Export Items"
    bl_idname  = "TM_PT_Items_Export"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_EXPORT)

    def draw(self, context):

        layout = self.layout
        tm_props = get_global_props()

        enableExportButton      = True
        exportActionIsSelected  = tm_props.LI_exportWhichObjs == "SELECTED"
        exportFolderType        = tm_props.LI_exportFolderType
        exportCustomFolder      = True if str(exportFolderType).lower() == "custom" else False
        exportCustomFolderProp  = "ST_exportFolder_MP" if is_game_maniaplanet() else "ST_exportFolder_TM"
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
                if "/Work/" not in fix_slash( getattr(tm_props, exportCustomFolderProp) ):
                    row_error= layout.row()
                    row_error.alert = True
                    row_error.label(text="Folder has to be in /Work/Items/ ...", icon=ICON_ERROR)
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

            if tm_props.CB_allow_complex_panel_drawing:
                exportable_cols  = get_exportable_collections(objs=objs)
                collection_count = len(exportable_cols)

                plural = "s" if collection_count > 1 else ""

                if exportType == "EXPORT":
                    text=f"Export {collection_count} collection{plural}"

                elif exportType == "EXPORT_CONVERT":
                    text=f"Export & convert {collection_count} collection{plural}"

                if collection_count == 0:
                    enableExportButton = False
            else:
                text = "Export Collections"
                enableExportButton = True

            if exportType == "EXPORT":
                icon=ICON_EXPORT
            elif exportType == "EXPORT_CONVERT":
                icon=ICON_CONVERT

            col = layout.column(align=True)

            row = col.row(align=True)
            row.scale_y = 1.5
            row.enabled = enableExportButton 
            row.alert   = not enableExportButton #red button, 0 selected
            row.operator("view3d.tm_export", text=text,   icon=icon)
            
        
            row = col.row(align=True)
            row.prop(tm_props, "CB_convertMultiThreaded", text="Parallel Convert", icon=ICON_PARALLEL)
            row.prop(tm_props, "CB_notifyPopupWhenDone",  text="Notify Toast",     icon=ICON_INFO)

            if is_game_trackmania2020():
                row = col.row(align=True)
                row.prop(tm_props, "CB_generateMeshAndShapeGBX", text="Create files for meshmodeler import", toggle=True)

            if exportType == "EXPORT_CONVERT" and len(visible_objects) < 500:
                embed_space = 0
                if enableExportButton:
                    for col in exportable_cols:
                        embed_space += get_embedspace_of_collection(col)
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

            exported_cols = [bpy.data.collections[exp_col.name_raw] for exp_col in get_convert_items_props()]
            embed_space   = 0
            for col in exported_cols:
                embed_space += get_embedspace_of_collection(col)
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
            row.prop(tm_props, "CB_stopAllNextConverts", icon_only=True, text="", icon=ICON_CANCEL)

            failed    = str(tm_props.ST_convertedErrorList).split("%%%")
            failed    = [f for f in failed if f!=""]
            

            #buttons OK, REPORT
            row = col.row(align=True)
            row.alert   = atlestOneConvertFailed
            row.scale_y = 1.25
            
            if(failed):
                bcol = row.column(align=True)
                bcol.scale_x = 1.25
                bcol.operator("view3d.tm_open_convert_report", text="Show errors",  icon="HELP")
            
            
            
            
            
            
            
            # TODO make list of last converted collections and only convert those not "selected" or "visible"
            # TODO make list of last converted collections and only convert those not "selected" or "visible"
            # TODO make list of last converted collections and only convert those not "selected" or "visible"
            
            bcol = row.column(align=True)
            bcol.enabled = True # if any([convertDone, stopConverting]) else False
            bcol.operator("view3d.tm_closeconvertsubpanel", text="OK", icon=ICON_SUCCESS)

            bcol = row.column(align=True)
            bcol.enabled = enableExportButton 
            bcol.operator("view3d.tm_export", text="Convert Again", icon=ICON_CONVERT)
            



            #result of fails
            if failed:
                row = layout.row()
                row.alert = True if failed else False
                row.label(text=f"Failed converts: {len(failed)}")


            for item in get_convert_items_props():
                row = layout.row(align=True)
                col = row.column()
                col.alert = item.failed
                col.label(
                    text=f"""{item.convert_duration if item.converted else "??"}s — {item.name}""", 
                    icon=item.icon)








