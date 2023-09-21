from ast import main
import bpy
from bpy.types import (Panel)

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

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

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.title = "Export Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here configure the export settings",
            "1. Select your game",
            "2. Select your destination folder (needs to be in Trackmania/Works/Items/<HERE>)",
            "3. Choose your preferred way of the collection which will be exported",
            "4. Enable optional features",
            "----> 'Multi Convert' will convert your exported items all at the same time", 
            "----> 'Notify' will make a popup in windows which informs you that the convert is finished", 
            "5. Export your collection(s)",
            "----> Files for the meshmodeler import can be generated optionally", 
            "",
            "Keep in mind, collections are exported, not individual objects",
            # "-> ",
            # "-> ",
            # "-> ",
            # "-> ",
            # "-> ",
            # "----> ", 
            # "----> ", 
            # "----> ", 
            # "----> ", 

        )

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
            main_row = layout.row(align=True)
            
            left_col  = main_row.column(align=True)
            left_col.scale_x = 0.8
            
            left_col.label(text="Game")
            left_col.label(text="Folder")
            left_col.label(text="Limit by")
            left_col.label(text="Extras")

            right_col = main_row.column(align=True)
            right_col.scale_x = 1

            
            right_col.prop(tm_props, "LI_gameType", text="")
            right_col.prop(tm_props, "LI_exportFolderType", text="")
            right_col.row().prop(tm_props, "LI_exportWhichObjs", expand=True)
            row = right_col.row(align=True)
            col = row.column(align=True)
            col.prop(tm_props, "CB_convertMultiThreaded", text="Multi Convert", icon=ICON_PARALLEL)
            col = row.column(align=True)
            col.scale_x = 0.8
            col.prop(tm_props, "CB_notifyPopupWhenDone",  text="Notify",           icon=ICON_INFO)

            
            if exportCustomFolder:
                row_path = layout.row()

                attr = getattr(tm_props, exportCustomFolderProp)

                if "/work/" not in fix_slash(attr.lower()):
                    row_error= layout.row()
                    row_error.alert = True
                    row_error.label(text="Folder has to be in /Work/Items/ ...", icon=ICON_ERROR)
                    row_path.alert=True

                if ".." in attr:
                    row = layout.row()
                    row.alert = True
                    row.label(text="""Please use an absolute path!""", icon=ICON_ERROR)

                row_path.prop(tm_props, exportCustomFolderProp)


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
            exportable_cols:list[bpy.types.Collection] = None

            if tm_props.CB_allow_complex_panel_drawing:
                exportable_cols  = get_exportable_collections(objs=objs)
                collection_count = len(exportable_cols)

                plural = "s" if collection_count > 1 else ""
                text=f"Export & Convert {collection_count} Collection{plural}"

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
            
        


            if is_game_trackmania2020():
                row = col.row(align=True)
                row.prop(tm_props, "CB_generateMeshAndShapeGBX", text="Create files for meshmodeler import", toggle=True)

            # if tm_props.CB_allow_complex_panel_drawing and collection_count:
            #     embed_space = 0
            #     if enableExportButton:
            #         for col in exportable_cols:
            #             embed_space += get_embedspace_of_collection(col)
            #     row = layout.row()
            #     row.scale_y = 0.5
                
            #     embed_space_1024kb = embed_space < 1.024
            #     if embed_space_1024kb:
            #         embed_space *= 1000

            #     row.label(text=f"Max. embed space: ~ {embed_space:4.2f} {'kB' if embed_space_1024kb else 'mB'}")





        #* show convert panel and hide everything else
        else:
            layout.separator(factor=UI_SPACER_FACTOR)

            box = layout.box()
            box.use_property_split = True

            # exported_cols = [bpy.data.collections[exp_col.name_raw] for exp_col in get_convert_items_props()]
            exported_cols = []
            for exp_col in get_convert_items_props():
                exported_cols.append(bpy.data.collections[exp_col.name_raw])

            embed_space = 0

            for item in get_convert_items_props():
                embed_space += item.embed_size


            row = box.row()
            row.label(text="Embed all:")
            row.label(text=f"{int(embed_space)} kB")

            #progress bar
            convert_duration_since_start = tm_props.NU_convertDurationSinceStart
            prev_convert_time            = tm_props.NU_prevConvertDuration

            # convert time since start
            row = box.row()
            row.scale_y = .5
            row.label(text=f"""Duration:""")
            row.label(text=f"""{convert_duration_since_start}s """) #— {prev_convert_time}s?""")




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
            
            
            
            

            
            bcol = row.column(align=True)
            bcol.enabled = True # if any([convertDone, stopConverting]) else False
            bcol.operator("view3d.tm_closeconvertsubpanel", text="OK", icon=ICON_SUCCESS)

            # bcol = row.column(align=True)
            # bcol.enabled = enableExportButton 
            # bcol.operator("view3d.tm_export", text="Convert Again", icon=ICON_CONVERT)
            



            #result of fails
            if failed:
                row = layout.row()
                row.alert = True if failed else False
                row.label(text=f"Failed converts: {len(failed)}")


            for item in get_convert_items_props():
                
                duration = str(int(item.convert_duration))+"s" if item.converted else "    "
                name = item.name
                embed_size = f"{int(item.embed_size)} kB" if item.embed_size > 0 else ".."

                row = layout.row(align=True)
                col = row.column()
                col.alert = item.failed
                col.label(
                    text=f"""{duration} — {name} — {embed_size}""", 
                    icon=item.icon)








