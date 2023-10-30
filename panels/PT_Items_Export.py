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
        op.link = ""
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
            "-> If you want to export objecs only, mark them as _item_",
            "",
            "Embed size means the item file size, the total map maximums embed size are:",
            f"-> {MAX_EMBED_SIZE_TRACKMANIA2020} kilobytes for trackmania2020",
            f"-> {MAX_EMBED_SIZE_MANIAPLANET} kilobytes for maniaplanet",
        )

    def draw(self, context):
        tm_props = get_global_props()
        show_convert_panel = tm_props.CB_showConvertPanel
        show_invalid_materials_panel = tm_props.CB_showInvalidMatsPanel

        if show_invalid_materials_panel:
            draw_invalid_materials_panel(self)

        elif show_convert_panel:
            draw_convert_panel(self)

        else:
            draw_export_panel(self)
        
        


def draw_invalid_materials_panel(self:Panel) -> None:
    layout = self.layout
    tm_props = get_global_props()
    mats = get_invalid_materials_props()
    SPACER_FACTOR = 1

    invalid_count = len(mats)

    row = layout.row()
    row.alert = True
    row.label(text=f"""Export failed, {invalid_count} invalid material{"s" if invalid_count > 1 else ""} found!""")

    row = layout.row()
    row.operator("view3d.tm_closeinvalidmaterialpanel", text="Ok")

    op = row.operator("view3d.tm_open_messagebox", text="How to fix", icon=ICON_QUESTION)
    op.link = ""
    op.title = "How to fix"
    op.infos = TM_OT_Settings_OpenMessageBox.get_text(
        "Check the following:",
        f"""-> Link{" or BaseTexture" if is_game_maniaplanet() else ""} should not be None""",
        "-> PhysicsId should not be None when enabled",
        "----> If you use Physicsid, you can disable it here, then the default will be used", 
        "-> GameplayId should not be None when enabled",
        "----> If you use GameplayId, you can disable it here, then the default will be used", 
        "----> Most materials do not support GameplayId!", 
        "-> Update the material in the materials tab and export again",
        "----> Materials need some extra information to be exportable", 
        "----> You can add/update them(Link, PhysicId, etc..) with the addon", 
    )
    
    is_tm2020 = is_game_trackmania2020()
    is_maniaplanet = is_game_maniaplanet()

    for prop in mats:
        mat = prop.material

        box = layout.box()

        row = box.row()
        row.label(text=mat.name, icon=ICON_MATERIAL)

        row = box.row()
        col1 = row.column(align=True)
        col1.scale_x = 0.8
        col1.scale_y = 0.8
        col2 = row.column(align=True)
        col2.scale_y = 0.8

        # col1.label(text="Name")
        # col2.label(text=mat.name)

        # col1.separator(factor=SPACER_FACTOR)
        # col2.separator(factor=SPACER_FACTOR)
        
        col1.label(text="Link")
        valid_link = mat.link != ""
        col2.alert = not valid_link
        col2.label(text=(mat.link if valid_link else "None"))
        col2.alert = False

        if is_maniaplanet:
            col1.label(text="BaseTexture")
            valid_btex = mat.baseTexture != ""
            col2.label(text=(mat.baseTexture if valid_btex else "None"))

        col1.separator(factor=SPACER_FACTOR)
        col2.separator(factor=SPACER_FACTOR)

        col1.label(text="PhysicsId")
        valid_physicsId = mat.physicsId != ""
        use_physicsId   = mat.usePhysicsId
        col2.alert = use_physicsId and not valid_physicsId
        col2.label(text=(mat.physicsId if valid_physicsId else "None"))
        col2.alert = False

        col1.label(text="Use PhysicsId")
        col2.prop(mat, "usePhysicsId", text="")

        col1.separator(factor=SPACER_FACTOR)
        col2.separator(factor=SPACER_FACTOR)

        col1.label(text="GameplayId")
        valid_gameplayId = mat.gameplayId != ""
        use_gameplayId   = mat.useGameplayId
        col2.alert = use_gameplayId and not valid_gameplayId
        col2.label(text=(mat.gameplayId if valid_gameplayId else "None"))
        col2.alert = False

        col1.label(text="Use GameplayId")
        col2.prop(mat, "useGameplayId", text="")

        # col2.prop(prop, "material", text="")
        


def draw_export_panel(self:Panel) -> None:
    layout = self.layout
    tm_props = get_global_props()

    enableExportButton      = True
    exportActionIsSelected  = tm_props.LI_exportWhichObjs == "SELECTED"
    exportFolderType        = tm_props.LI_exportFolderType
    exportCustomFolder      = True if str(exportFolderType).lower() == "custom" else False
    exportCustomFolderProp  = "ST_exportFolder_MP" if is_game_maniaplanet() else "ST_exportFolder_TM"
    exportType              = tm_props.LI_exportType


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

    if is_game_trackmania2020():
        right_col.prop(tm_props, "CB_generateMeshAndShapeGBX", text="Meshmodeler importable", toggle=True, icon=ICON_IMPORT)

    
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



    layout.separator(factor=UI_SPACER_FACTOR)

    text = exportType
    icon = "EXPORT"

    # get number of collections which can be exported
    selected_objects = bpy.context.selected_objects
    visible_objects  = bpy.context.visible_objects
    
    objs = selected_objects if exportActionIsSelected else visible_objects
    exportable_cols:list[bpy.types.Collection] = None

    item_prefix_detected = False
    for obj in objs: 
        item_prefix_detected = obj.name.startswith(SPECIAL_NAME_PREFIX_ITEM)
        if item_prefix_detected:
            break

    if tm_props.CB_allow_complex_panel_drawing:
        exportable_cols  = get_exportable_collections(objs=objs)
        exportable_objs  = get_exportable_objects(objs=objs)
        collection_count = len(exportable_cols)
        objects_count    = len(exportable_objs)

        type = ""

        if objects_count > 0:
            type = "Object"
            if objects_count > 1:
                type += "s"
        
        elif collection_count > 0:
            type = "Collection"
            if collection_count > 1:
                type += "s"
        
        else:
            enableExportButton = False
        
        text = f"Export & Convert {type}"


    else:
        type = "Objects" if item_prefix_detected else "Collections"
        type = type if enableExportButton else ""
        text = f"Export {type}"
        # enableExportButton = True


    col = layout.column(align=True)

    row = col.row(align=True)
    row.scale_y = 1.5
    row.enabled = enableExportButton 
    row.alert   = not enableExportButton #red button, 0 selected
    row.operator("view3d.tm_export", text=text,   icon=ICON_CONVERT)

    # row = col.row()
    # row.label(text=f"expobjs={[obj.name for obj in exportable_objs]}")
    



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





def draw_convert_panel(self:Panel) -> None:
    layout = self.layout
    tm_props = get_global_props()

    atlest_1_convert_failed  = tm_props.NU_convertedError > 0
    converted                = tm_props.NU_convertedRaw
    convert_count            = tm_props.NU_convertCount
    convert_failed_count     = tm_props.NU_convertedError

    layout.separator(factor=UI_SPACER_FACTOR)

    box = layout.box()
    box.use_property_split = True

    embed_space = 0

    for item in get_convert_items_props():
        embed_space += item.embed_size

    MAX_EMBED_SIZE = MAX_EMBED_SIZE_TRACKMANIA2020 if is_game_trackmania2020() else MAX_EMBED_SIZE_MANIAPLANET

    embed_space = int(embed_space)
    embed_space_in_percent = int(embed_space / MAX_EMBED_SIZE * 100)

    row = box.row()
    row.scale_y = .7
    row.label(text="Embed all:")
    row.label(text=f"{embed_space} kB ({embed_space_in_percent}%)")

    #progress bar
    convert_duration_since_start = tm_props.NU_convertDurationSinceStart
    prev_convert_time            = tm_props.NU_prevConvertDuration

    # convert time since start
    row = box.row()
    row.scale_y = .7
    row.label(text=f"""Duration:""")
    row.label(text=f"""{convert_duration_since_start}s """) #— {prev_convert_time}s?""")
    
    if atlest_1_convert_failed:
        row = box.row()
        row.scale_y = .7
        row.alert = True
        row.label(text=f"""Failed:""")
        row.label(text=f"""{convert_failed_count} of {convert_count}""")


    col = layout.column(align=True)
    row = col.row(align=True)
    # row.alert   = atlest_1_convert_failed
    row.prop(tm_props, "NU_converted", text=f"{converted} of {convert_count}")
    row.prop(tm_props, "CB_stopAllNextConverts", icon_only=True, text="", icon=ICON_CANCEL)


    

    row = col.row(align=True)
    # row.alert   = atlest_1_convert_failed
    row.scale_y = 1.25
    
    # SHOW ERROR BUTTON
    if(atlest_1_convert_failed):
        bcol = row.column(align=True)
        bcol.scale_x = 1.25
        bcol.operator("view3d.tm_open_convert_report", text="Show errors",  icon="HELP")
 

    # OK BUTTON
    bcol = row.column(align=True)
    bcol.enabled = True # if any([convertDone, stopConverting]) else False
    bcol.operator("view3d.tm_closeconvertsubpanel", text="OK", icon=ICON_SUCCESS)

    # CONVERT AGAIN BUTTON
    if atlest_1_convert_failed:
        row = layout.row()
        row.scale_y = 1.5
        row.alert = True
        row.operator("view3d.tm_export_failed_ones", text="Convert failed ones again", icon=ICON_CONVERT)


    # split = layout.row(align=True).split(factor=.6)
    split = layout.row(align=True).split(factor=.75)
    left = split.column()
    right = split.column()

    row = left.row()
    row.enabled = False
    col = row.column().label(text="", icon="BLANK1")
    col = row.column().label(text=f"""Name""")
    col = row.column()
    col.alignment = "RIGHT"
    col.label(text=f"""Time""")
    
    row = right.row()
    row.enabled = False
    rsplit = row.split(factor=1)
    # rsplit = row.split(factor=.6)
    col = rsplit.column()
    col.alignment = "RIGHT"
    col.label(text=f"""Embed""")
    # col = rsplit.column()
    # col.alignment = "RIGHT"
    # col.label(text=f"""%""")

    for item in get_convert_items_props():
        
        duration = str(int(item.convert_duration))+"s" if item.converted and not item.failed else ".."
        name = item.name 
        embed_size = f"{int(item.embed_size)}" if item.embed_size > 0 else ".."
        embed_size_percent = f" {int(item.embed_size / MAX_EMBED_SIZE * 100)}" if item.embed_size > 0 else ".."

        row = left.row()
        row.alert = item.failed

        # state RUNNING | SUCCESS | FAILURE
        col = row.column()
        col.label(text=f"", icon=item.icon)
        
        col = row.column()
        col.label(text=f"""{name}""")

        # convert duration in seconds
        col = row.column()
        # col.scale_x = 0.3
        col.alignment = "RIGHT"
        col.label(text=f"""{duration}""")
        
        # # split = right.split(factor=.6)

        row = right.row()
        row.alert = item.failed

        # rsplit = row.split(factor=.6)
        rsplit = row.split(factor=1)
        
        col = rsplit.column()
        col.alignment = "RIGHT"
        col.label(text=f"""{embed_size} kB""")

        # col = rsplit.column()
        # col.alignment = "RIGHT"
        # col.label(text=f"""{embed_size_percent}""")





