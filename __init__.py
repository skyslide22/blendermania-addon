import bpy
import bpy.utils.previews
from bpy.props import *
from bpy.app.handlers import persistent

import os















ADDON_ROOT_PATH = os.path.dirname(__file__)


bl_info = {
    "name"          : "Blendermania",
    "author"        : "skyslide22, juice & schadocalex",
    "description"   : "Makes creating objects for Trackmania more easy and fun!",
    "blender"       : (5, 2, 3),
    "version"       : (4, 4, 4),
    "location"      : "View3D",
    "warning"       : "",
    "category"      : "Generic",
}


from .utils.Constants      import *
from .utils.Descriptions   import *
from .utils.Dotnet         import *
from .utils.Functions      import *
from .utils.ItemsExport    import *
from .utils.ItemsIcon      import *
from .utils.ItemsIconV2    import *
from .utils.ItemsImport    import *
from .utils.ItemsUVs       import *
from .utils.Materials      import *
from .utils.Models         import *
from .utils.NadeoImporter  import *
from .utils.NadeoXML       import *
from .utils.BlenderObjects import *
from .utils.ItemsExportV2Models       import *
from .utils.OutlinerMenus import *
from .utils.HeaderMenus import *

from .utils.KeyMappings import *

from .utils.Server import run_server

from .properties.Functions                  import *
from .properties.ConvertingItemsProperties  import *
from .properties.GeneratedProperties        import *
from .properties.ItemXMLTemplatesProperties import *
from .properties.LinkedMaterialsProperties  import *
from .properties.MapObjectProperties        import *
from .properties.PannelsPropertyGroup       import *
from .properties.PlacementProperties        import *
from .properties.CollectionProperties       import *
from .properties.ObjectProperties           import *
from .properties.PlacementPatchProperties   import *
from .properties.LightProperties            import *
from .properties.ItemConfigProperties       import *
from .properties.ItemPlanProperties       import *

from .operators.OT_Map_Manipulate          import *
from .operators.OT_NinjaRipper             import *
from .operators.OT_Settings                import *
from .operators.OT_Items_Export            import *
from .operators.OT_Materials               import *
from .operators.OT_Items_XML               import *
from .operators.OT_Items_Icon              import *
from .operators.OT_Items_Manipulate        import *
from .operators.OT_Items_ManipulateV2      import *
from .operators.OT_UV_Manipulate           import *
from .operators.OT_Assets_Library          import *
from .operators.OT_Items_Templates         import * 
from .operators.OT_WikiLink                import * 
from .operators.OT_Textures                import * 
from .operators.OT_Imports                 import * 
from .operators.OT_VisibilitySelection     import *
from .operators.OT_Items_Placement          import *
from .operators.OT_Items_ExportV2           import *
from .operators.OT_Items_IconV2             import *
from .operators.OT_Items_AnalyzeGroups import *


from .panels.PT_Map_Manipulate          import *
from .panels.PT_Imports                 import *
from .panels.PT_Settings                import *
from .panels.PT_Items_Export            import *
from .panels.PT_Items_ExportV2          import *
from .panels.PT_Materials               import *
from .panels.PT_Items_XML               import *
from .panels.PT_Items_UVMaps            import *
from .panels.PT_Items_Icon              import *
from .panels.PT_Items_IconV2            import *
from .panels.PT_Items_Manipulate        import *
from .panels.PT_Items_ManipulateV2      import *
from .panels.PT_UV_Manipulate           import *
from .panels.PT_Textures                import *
from .panels.PT_VisibilitySelection     import *
from .panels.PT_EditorTrails            import *
from .panels.PT_Items_Placement         import *
from .panels.PT_Animation               import *

from .utils.Placement import register_placement_templates, unregister_placement_templates


from .ui.widgets.lists import *
from .ui.widgets.foldouts import *
from .ui.drawers.placement import register_placement_callbacks, unregister_placement_callbacks
from .ui.widgets.panels import register_panel_widgets, unregister_panel_widgets

from .NICE.nice import NICE_register, NICE_unregister


# owner of the object eventlistener
object_eventlistner_owner = object()


# register order matters for UI panel ordering
classes = (
    MapObjectProperties,
    #CubeCenterProperties,

    CompatiblePatchGroupProperty,
    PatchGroupRef,
    PlacementPatchProperties,
    #WorldDirProperties,
    PivotsProperties,
    FBXPlanNodeProperties,
    FbxGbxPlanGroupProperties,
    FbxGbxPlanProperties,
    PlacementProperties,
    PlacementPropertiesRef,
    ItemConfigProperties,
    PannelsPropertyGroup,
    GeneratedProperties,

    TM_LodDistanceProperties,
    TM_TextureAnimProperties,
    TM_SubAnimProperties,
    TM_LodIndex,
    ConvertingItemsProperties,
    LinkedMaterialsProperties,
    ItemXMLTemplate,
    ItemPlacementTemplate,
    InvalidMaterial,
    FailedConvertObject,
    FailedConvertCollection,
    FailedConverts,

    # settings
    TM_PT_Settings,
    TM_PT_Settings_BlenderRelated,
    TM_PT_Settings_NadeoImporter,
    TM_PT_Settings_Performance,
    TM_PT_Settings_Materials,
    TM_OT_Settings_AutoFindNadeoIni,
    TM_OT_Settings_InstallNadeoImporter,
    TM_OT_Settings_InstallGameTextures,
    TM_OT_Settings_InstallGameAssetsLIbrary,
    TM_OT_Settings_InstallBlendermaniaDotnet,
    TM_OT_Settings_UpdateAddon,
    TM_OT_Settings_UpdateAddonResetSettings,
    TM_OT_Settings_UpdateAddonCheckForNewRelease,
    TM_OT_Settings_OpenUrl,
    TM_OT_Settings_OpenFolder,
    TM_OT_Settings_DebugAll,
    TM_OT_Settings_OpenConvertReport,
    TM_PT_Settings_Experimentals,
    TM_PT_Settings_Views,
    
    # object manipulation
    TM_PT_ObjectManipulations,
    TM_PT_Items_CollectionManipulation,
    TM_PT_Items_ObjectManipulation,
    #TM_PT_ObjectManipulationsV2,
    TM_PT_Items_DefaultCollectionManipulationV2,
    TM_PT_ItemCollection_Lightmap,
    TM_PT_ItemCollection_Placement,

    TM_PT_Items_SpecialCollectionManipulationV2,
    TM_PT_Items_ObjectManipulationV2,
    TM_OT_Items_ObjectManipulationAddSocketItem,
    TM_OT_Items_ObjectManipulationAddTriggerItem,
    TM_OT_Items_ObjectManipulationToggleIgnore,
    TM_OT_Items_ObjectManipulationToggleItem,
    TM_OT_Items_ObjectManipulationToggleIconOnly,
    TM_OT_Items_CollectionManipulationToggleIgnore,
    TM_OT_Items_ObjectManipulationToggleNotvisible,
    TM_OT_Items_ObjectManipulationToggleNotcollidable,
    TM_OT_Items_ObjectManipulationToggleSocket,
    TM_OT_Items_ObjectManipulationToggleTrigger,
    TM_OT_Items_ObjectManipulationToggleLod0,
    TM_OT_Items_ObjectManipulationToggleLod1,
    TM_OT_Items_ObjectManipulationToggleDoublesided,
    TM_OT_Items_ObjectManipulationToggleOrigin,
    TM_OT_Items_ObjectManipulationTogglePivot,
    TM_OT_Items_ObjectManipulationChangeCollectionScale,
    TM_OT_Items_SetItemXMLTemplateOfCollection,
    TM_OT_Items_ToggleLightType,
    TM_OT_Items_ToggleNightOnly,
    TM_OT_Items_RenameObject,
    TM_OT_Items_EditUVMap,
    TM_OT_Items_EditUVMapV2,
    TM_OT_Items_EditGroupLightmap,
    TM_OT_Items_ShowUVMap,
    TM_OT_Items_ShowUVMapV2,
    TM_OT_Items_ShowGroupLightmap,
    TM_OT_Items_CollectionManipulationToggleNICE,
    TM_OT_Items_ObjectManipulationToggleGate,


    # object visibility and selection controls
    TM_PT_VisibilitySelection,
    TM_OT_VisibilitySelection_Toggle,

    # uv manipulation
    TM_PT_UVManipulations,
    TM_OT_Items_UVManipulationsFollowActiveQuadsForFaceLoop,

    # export
    TM_PT_Items_Export,
    TM_OT_Items_Export_ExportAndOrConvert,
    TM_OT_Items_Export_CloseConvertSubPanel,
    TM_OT_Items_Export_ExportAndOrConverFailedOnes,

    #TM_PT_Items_ExportV2,
    TM_PT_ExportV2_Placement,
    TM_OT_Items_ExportV2,
    TM_OT_Items_Export_ExportAndOrConverFailedOnesV2,


    # xml,
    TM_PT_Items_MeshXML,
    TM_PT_Items_ItemXML,
    TM_OT_Items_ItemXML_AddPivot,
    TM_OT_Items_ItemXML_RemovePivot,
    TM_OT_Items_ItemXML_SaveItemPlacementTemplate,
    TM_OT_Items_ItemXML_RemoveItemPlacementTemplate,

    # cfg
    TM_OT_Items_Config_AddCompatiblePatchGroup,
    TM_OT_Items_Config_RemoveCompatiblePatchGroup,
    TM_OT_Items_Config_AddPatchLayoutGroup,
    TM_OT_Items_Config_RemovePatchLayoutGroup,
    TM_OT_Items_Config_AddPatchLayout,
    TM_OT_Items_Config_RemovePatchLayout,
    TM_OT_Items_ItemConfig_SaveItemPlacementTemplate,
    TM_OT_Items_ItemConfig_RemoveItemPlacementTemplate,
    TM_OT_Items_ItemConfig_CopyPlacementTemplateToLocal,
    TM_OT_Items_ItemConfig_LoadPlacementTemplate,

    TM_OT_Items_ItemConfig_LoadPlacementClassTemplate,

    # Export Options V2
    # TM_PT_Items_ItemPlacement,

    # manipulation v2
    TM_OT_Lod_Add,
    TM_OT_Lod_Remove,
    TM_OT_Toggle_Lod,
    TM_OT_Create_Anchor,

    TM_OT_Texture_Anim_Add,
    TM_OT_Texture_Anim_Remove,
    TM_OT_Trans_Anim_Add,
    TM_OT_Trans_Anim_Remove,
    TM_OT_Rot_Anim_Add,
    TM_OT_Rot_Anim_Remove,

    # icons,
    TM_PT_Items_Icon,
    TM_OT_Items_Icon_Test,


    TM_PT_Items_IconV2,
    TM_OT_Items_Icon_TestV2,

    # uvs
    TM_PT_Items_UVmaps_LightMap,
    TM_PT_Items_UVmaps_BaseMaterial_CubeProject,


    OT_ITEMS_analyze_groups,
    OT_ITEMS_analyze_uv_overlaps,
    TM_OT_select_all_uvs,
    #anim
    #TM_PT_Animation_Preview,


    # materials
    TM_PT_Materials,
    #TM_PT_Materials_Library,
    TM_OT_Materials_Create,
    TM_OT_Materials_Update,
    TM_OT_Materials_Create_Asset_Lib,
    TM_OT_Materials_ClearBaseMaterial,
    TM_OT_Materials_RevertCustomColor,
    TM_OT_Materials_CloseInvalidPanel,
    

    # textures
    #TM_PT_Textures,
    TM_PT_Textures_Install,
    TM_OT_Textures_ToggleModwork,
    TM_OT_Textures_UpdateTextureSource,
    
    # ninja
    TM_OT_Ninja17Install,
    TM_OT_Ninja20Install,

    # imports
    TM_OT_ImportItem,
    #TM_PT_Imports,

    # templates
    OT_ItemsCarsTemplates,
    OT_ItemsEnviTemplates,
    OT_MediaTrackerClipTriggerTemplates,

    # map
    OT_UICollectionToMap,
    OT_UIValidateMapCollection,
    #PT_UIMapManipulation,
    PT_UIMapExport,
    PT_UIMapObjectsManipulation,
    OT_UICreateUpdateMapItemBlock,
    OT_UIImportMediatrackerClips,
    OT_UIExportMediatrackerClips,
    PT_UIMediatrackerClips,
    OT_UIChangeMediatrackerTriggerClipName,
    OT_UIRefreshMediatrackerTriggerClipNamesFromMap,
    OT_UISelectMediatrackerTriggersByName,
    PT_UIMapHelpers,
    
    # editor trails
    #TM_PT_UIEditorTrails,

    # util
    OT_UIWikiLink,
    TM_OT_Settings_OpenMessageBox,

    # experimental/dangerous
    TM_PT_DangerousManualManipulations,

    # items manipulate v2
    TM_UL_lods,

    # widgets
    TM_OT_List_Add,
    TM_OT_List_Remove,
    TM_OT_List_Move,
    TM_OT_List_Clipboard,
    TM_MT_List_Clipboard,
    TM_UL_Generic,
    
)



from collections import Counter

# register classes 
def register():

    register_panel_widgets()

    for cls in classes:
        print(f"Registering: {cls!r}, type: {type(cls)}")
        bpy.utils.register_class(cls)

    
    bpy.types.Scene.tm_props                  = PointerProperty(   type=PannelsPropertyGroup)
    bpy.types.Scene.tm_props_pivots           = CollectionProperty(type=PivotsProperties)
    bpy.types.Scene.tm_props_pivots_index           = IntProperty(default=-1)

    bpy.types.Scene.tm_props_generated        = CollectionProperty(type=GeneratedProperties)
    bpy.types.Scene.tm_props_convertingItems  = CollectionProperty(type=ConvertingItemsProperties)
    bpy.types.Scene.tm_props_linkedMaterials  = CollectionProperty(type=LinkedMaterialsProperties)
    bpy.types.Scene.tm_props_linkedMaterialsLibrary = CollectionProperty(type=LinkedMaterialsProperties)
    bpy.types.Scene.tm_props_invalidMaterials = CollectionProperty(type=InvalidMaterial)
    bpy.types.Scene.tm_props_failed_converts  = PointerProperty(type=FailedConverts)
    # bpy.types.Scene.tm_props_itemxml_templates= CollectionProperty(type=ItemXMLTemplatesProperties)
    bpy.types.Scene.tm_props_itemxml_templates_ui     = EnumProperty(items=get_itemxml_template_names_enum)
    bpy.types.Scene.tm_props_itemxml_templates        = CollectionProperty(type=ItemXMLTemplate)
    bpy.types.Scene.tm_props_cfg_placement_templates     = CollectionProperty(type=ItemPlacementTemplate)
    bpy.types.Scene.tm_props_cfg_placement_template_ui  = EnumProperty(items=get_item_config_template_names_enum)
    # local templates (settings.json), runtime only: not saved into the blend file
    bpy.types.WindowManager.tm_local_placement_templates = CollectionProperty(type=ItemPlacementTemplate)
    bpy.types.DATA_PT_EEVEE_light.append(draw_nightonly_option)

    bpy.types.VIEW3D_MT_add.prepend(OT_MediaTrackerClipTriggerTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.prepend(OT_ItemsCarsTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.prepend(OT_ItemsEnviTemplates.add_menu_item)

    # object extra props
    bpy.types.Object.tm_map_object_kind             = StringProperty(name="Item (soon Block)", default="Item")
    bpy.types.Object.tm_map_object_path             = StringProperty(name="Name/Path of Item or Block", default="")
    bpy.types.Object.tm_map_object_animphaseoffset  = EnumProperty(name="Animation Phase Offset", items=get_animphaseoffset_values())
    bpy.types.Object.tm_map_object_difficultycolor  = EnumProperty(name="Difficulty Color", items=get_difficultycolor_values())
    bpy.types.Object.tm_map_object_lightmapquality  = EnumProperty(name="Lightmap Quality", items=get_lightmapquality_values())
    bpy.types.Object.tm_map_clip_name               = StringProperty(name="Name of mediatracker clip", default="")
    bpy.types.Object.tm_force_grid_helper         = BoolProperty(default=False)
    bpy.types.Object.tm_forced_grid_helper_step_x = FloatProperty(default=0.0)
    bpy.types.Object.tm_forced_grid_helper_step_y = FloatProperty(default=0.0)
    bpy.types.Object.tm_forced_grid_helper_step_z = FloatProperty(default=0.0)

    # collections callbacks
    register_collection_properties()
    register_object_properties()
    register_light_properties()
    register_placement_callbacks()
    register_animation_preview()

    # templates
    register_placement_templates()


    # material extra props
    bpy.types.Material.gameType         = EnumProperty(         name="Game",                default=0, items=getGameTypes())
    bpy.types.Material.baseTexture      = StringProperty(       name="BaseTexture",         default="")
    bpy.types.Material.link             = StringProperty(       name="Link",                default="")
    bpy.types.Material.physicsId        = StringProperty(       name="PhysicsId",           default="")
    bpy.types.Material.usePhysicsId     = BoolProperty(         name="Use PhysicsId",       default=False)
    bpy.types.Material.gameplayId       = StringProperty(       name="GameplayId",          default="")
    bpy.types.Material.useGameplayId    = BoolProperty(         name="Use GameplayId",      default=False)
    bpy.types.Material.useColor         = BoolProperty(         name="Use Color",           default=False)
    bpy.types.Material.isLibraryMaterial = BoolProperty(        name="Created with materiallib (V2)", default=False)
    bpy.types.Material.libraryEnvironment = StringProperty(     name="Materiallib collection (V2)", default="")
    bpy.types.Material.model            = EnumProperty(         name="Model",               default="TDSN",    items=getMaterialModelTypes())
    bpy.types.Material.environment      = EnumProperty(         name="Collection",          default="Stadium", items=getMaterialCollectionTypes())#Material."collection" not allowed
    # the size should be 4 (for BSDF) but to keep backward compability we have to keep it with size=3 (we convert it later in the code)
    bpy.types.Material.surfaceColor     = FloatVectorProperty(  name='Surface Color ',      subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855))

    # object listeners
    from .utils.MapObjects import listen_object_move
    
    try:
        bpy.app.handlers.depsgraph_update_post.remove(listen_object_move)
    except:
        pass
    
    bpy.app.handlers.depsgraph_update_post.append(listen_object_move)
    bpy.types.Object.location_before = FloatVectorProperty(name="old pos", subtype="TRANSLATION")


    TM_PT_Items_DefaultCollectionManipulationV2.register_callbacks()

    from .ui.drawers.gameplay_dir import register_gameplay_dir
    register_gameplay_dir()
    
    NICE_register()

    register_keymaps()
    register_outliner_menus()
    register_header_menus()

    # addon enabled in a running session: load_post did not run yet
    try:
        from .operators.OT_Settings import reload_local_placement_templates
        reload_local_placement_templates()
    except Exception as e:
        debug(f"loading local placement templates failed: {e}")
    



# delete classes
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tm_props
    del bpy.types.Scene.tm_props_generated
    del bpy.types.Scene.tm_props_pivots
    del bpy.types.Scene.tm_props_convertingItems
    del bpy.types.Scene.tm_props_linkedMaterials
    del bpy.types.Scene.tm_props_linkedMaterialsLibrary
    del bpy.types.Scene.tm_props_itemxml_templates_ui
    del bpy.types.Scene.tm_props_itemxml_templates

    del bpy.types.Scene.tm_props_cfg_placement_templates
    del bpy.types.Scene.tm_props_cfg_placement_template_ui
    del bpy.types.WindowManager.tm_local_placement_templates
    # del bpy.types.Scene.tm_props_itemxml_templates
    del bpy.types.Object.location_before 

    unregister_panel_widgets()

    unregister_collection_properties()
    unregister_object_properties()

    unregister_placement_callbacks()
    register_animation_preview()

    unregister_placement_templates()

    bpy.types.DATA_PT_EEVEE_light.remove(draw_nightonly_option)
    bpy.types.VIEW3D_MT_add.remove(OT_ItemsCarsTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.remove(OT_ItemsEnviTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.remove(OT_MediaTrackerClipTriggerTemplates.add_menu_item)
    
    # icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    
    preview_collections.clear()
    
    from .utils.MapObjects import listen_object_move
    try:
        bpy.app.handlers.depsgraph_update_post.remove(listen_object_move)
    except:
        pass


    TM_PT_Items_DefaultCollectionManipulationV2.unregister_callbacks()

    from .ui.drawers.gameplay_dir import unregister_gameplay_dir
    unregister_gameplay_dir()

    NICE_unregister()
    unregister_keymaps()
    unregister_outliner_menus()
    unregister_header_menus()

@persistent
def on_save_pre(what, idontknow) -> None:
    """embed the local placement templates into the blend file"""
    try:
        from .utils.ItemsExportV2Models import embed_local_placement_templates
        embed_local_placement_templates()
    except Exception as e:
        debug(f"embedding placement templates failed: {e}")

@persistent
def on_save(what, idontknow) -> None: # on quit?
    """run on blender save"""
    saveDefaultSettingsJSON()

# TODO runs 10 times on new blend file ??
@persistent
def on_startup(dummy) -> None:
    """run on blender startup, load blend file & reload current file"""
    
    # can be opened on save
    try:
        bpy.ops.view3d.tm_closeconvertsubpanel()
        bpy.ops.view3d.tm_resetaddonupdatesettings()

        tm_props = get_global_props()
        tm_props.CB_DL_ProgressRunning  = False
        tm_props.NU_DL_Progress         = 0
        tm_props.ST_DL_ProgressErrors   = ""
        tm_props.CB_DL_ProgressShow     = False


        # so grid_subdivisions is editable
        bpy.context.scene.unit_settings.system = 'NONE'
                    
    except AttributeError as error:
        debug(error)
        pass # fails on first startup when open_mainfile used

    loadDefaultSettingsJSON()
    
    @in_new_thread
    def checkUpdate():
        AddonUpdate.check_for_new_release()
    checkUpdate()

    # external addons
    installUvPackerAddon()

    # remove possible error text
    is_nadeoimporter_installed()
    update_installed_nadeoimporter_version_ui()

    # modwork
    check_modwork_folders_enabled()
    
    from .utils.MapObjects import delete_map_grid_helper_and_cleanup
    delete_map_grid_helper_and_cleanup()

    # this mat is auto created by blender, remove due appearance in mat list 
    stroke_mat = bpy.data.materials.get("Dots Stroke", None)
    if stroke_mat is not None:
        bpy.data.materials.remove(stroke_mat)


    # clear before add to avoid multi register
    bpy.msgbus.clear_by_owner(object_eventlistner_owner)

    # eventlistner when a object gets selected
    try:
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.LayerObjects, 'active'),
            owner=object_eventlistner_owner,
            args=(),
            notify=on_select_obj
        )
    except RuntimeError:
        pass # first try always fails
        # RuntimeError: subscribe_rna, missing bl_rna attribute from 'Scene' instance (may not be registered)

    try:
        run_server()
    except:
        print("server died hm..")


# drop stale handlers from previous addon (re)loads, otherwise they run multiple times
for _handlers, _fn in ((bpy.app.handlers.load_post, on_startup), (bpy.app.handlers.save_post, on_save), (bpy.app.handlers.save_pre, on_save_pre)):
    for _h in list(_handlers):
        if getattr(_h, "__name__", None) == _fn.__name__ and getattr(_h, "__module__", "") == _fn.__module__:
            _handlers.remove(_h)
    _handlers.append(_fn)

