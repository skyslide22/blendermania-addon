import bpy
import bpy.utils.previews
import bpy_types
from bpy.props import *
from bpy.app.handlers import persistent

import os
ADDON_ROOT_PATH = os.path.dirname(__file__)

bl_info = {
    "name"          : "Trackmania Export & Convert .fbx > .gbx Addon",
    "author"        : "skyslide & juice",
    "description"   : "Export collections, create icons, generate xml files and convert items",
    "blender"       : (3, 1, 0),
    "version"       : (3, 0, 0),
    "location"      : "View3D",
    "warning"       : "",
    "category"      : "Generic"
}                    

from .utils.Constants     import *
from .utils.Descriptions  import *
from .utils.Dotnet        import *
from .utils.Functions     import *
from .utils.ItemsExport   import *
from .utils.ItemsIcon     import *
from .utils.ItemsImport   import *
from .utils.ItemsUVs      import *
from .utils.Materials     import *
from .utils.Models        import *
from .utils.NadeoImporter import *
from .utils.NadeoXML      import *
from .utils.Properties    import *
from .operators.OT_Map_Manipulate     import *
from .operators.OT_NinjaRipper        import *
from .operators.OT_Settings           import *
from .operators.OT_Items_Export       import *
from .operators.OT_Materials          import *
from .operators.OT_Items_XML          import *
from .operators.OT_Items_Icon         import *
from .operators.OT_Items_Manipulate   import *
from .operators.OT_UV_Manipulate      import *
from .operators.OT_Assets_Library     import *
from .operators.OT_Items_Templates    import * 
from .panels.PT_Map_Manipulate     import *
from .panels.PT_NinjaRipper        import *
from .panels.PT_Settings           import *
from .panels.PT_Items_Export       import *
from .panels.PT_Materials          import *
from .panels.PT_Items_XML          import *
from .panels.PT_Items_UVMaps       import *
from .panels.PT_Items_Icon         import *
from .panels.PT_Items_Manipulate   import *
from .panels.PT_UV_Manipulate      import *




# owner of the object eventlistener
object_eventlistner_owner = object()


# register order matters for UI panel ordering
classes = (
    # map
    OT_UIExportAndCreateMap,
    PT_UIMapManipulation,
    
    # props (not panel)
    TM_Properties_for_Panels,
    TM_Properties_Generated,
    TM_Properties_Pivots,
    TM_Properties_ConvertingItems,
    TM_Properties_LinkedMaterials,

    # settings
    TM_PT_Settings,
    TM_PT_Settings_BlenderRelated,
    TM_PT_Settings_NadeoImporter,
    TM_PT_Settings_Textures,
    TM_OT_Settings_AutoFindNadeoIni,
    TM_OT_Settings_ExecuteHelp,
    TM_OT_Settings_InstallNadeoImporter,
    TM_OT_Settings_InstallGameTextures,
    TM_OT_Settings_InstallGameAssetsLIbrary,
    TM_OT_Settings_UpdateAddon,
    TM_OT_Settings_UpdateAddonResetSettings,
    TM_OT_Settings_UpdateAddonCheckForNewRelease,

    # object manipulation
    TM_PT_ObjectManipulations,
    TM_OT_Items_ObjectManipulationAddSocketItem,
    TM_OT_Items_ObjectManipulationAddTriggerItem,
    TM_OT_Items_ObjectManipulationToggleIgnore,
    TM_OT_Items_CollectionManipulationToggleIgnore,
    TM_OT_Items_ObjectManipulationToggleNotvisible,
    TM_OT_Items_ObjectManipulationToggleNotcollidable,
    TM_OT_Items_ObjectManipulationToggleSocket,
    TM_OT_Items_ObjectManipulationToggleTrigger,
    TM_OT_Items_ObjectManipulationToggleLod0,
    TM_OT_Items_ObjectManipulationToggleLod1,
    TM_OT_Items_ObjectManipulationToggleDoublesided,
    TM_OT_Items_ObjectManipulationToggleOrigin,
    TM_OT_Items_ObjectManipulationChangeCollectionScale,
    TM_OT_Items_ToggleLightType,
    TM_OT_Items_ToggleNightOnly,
    TM_OT_Items_RenameObject,
    TM_OT_Items_EditUVMap,
    TM_OT_Items_ShowUVMap,

    # uv manipulation
    TM_PT_UVManipulations,
    TM_OT_Items_UVManipulationsFollowActiveQuadsForFaceLoop,

    # export
    TM_PT_Items_Export,
    TM_OT_Items_Export_ExportAndOrConvert,
    TM_OT_Items_Export_CloseConvertSubPanel,

    # xml,
    TM_PT_Items_MeshXML,
    TM_PT_Items_ItemXML,
    TM_OT_Items_ItemXML_AddPivot,
    TM_OT_Items_ItemXML_RemovePivot,

    # icons,
    TM_PT_Items_Icon,
    TM_OT_Items_Icon_Test,

    # uvs
    TM_PT_Items_UVmaps_LightMap,
    TM_PT_Items_UVmaps_BaseMaterial_CubeProject,

    # materials
    TM_PT_Materials,
    TM_OT_Materials_Create,
    TM_OT_Materials_Update,
    TM_OT_Materials_Create_Asset_Lib,
    TM_OT_Materials_ClearBaseMaterial,
    TM_OT_Materials_RevertCustomColor,
    
    # ninja
    TM_OT_Ninja17Install,
    TM_PT_NinjaImporter,
    TM_OT_Ninja20Install,

    # templates
    OT_ItemsCarsTemplates,
    OT_ItemsEnviTemplates,
)





# register classes 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tm_props                  = PointerProperty(   type=TM_Properties_for_Panels)
    bpy.types.Scene.tm_props_pivots           = CollectionProperty(type=TM_Properties_Pivots)
    bpy.types.Scene.tm_props_generated        = CollectionProperty(type=TM_Properties_Generated)
    bpy.types.Scene.tm_props_convertingItems  = CollectionProperty(type=TM_Properties_ConvertingItems)
    bpy.types.Scene.tm_props_linkedMaterials  = CollectionProperty(type=TM_Properties_LinkedMaterials)

    bpy.types.DATA_PT_EEVEE_light.append(extend_object_properties_panel_LIGHT)
    bpy.types.Light.night_only          = BoolProperty(default=False)

    bpy.types.VIEW3D_MT_add.prepend(OT_ItemsCarsTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.prepend(OT_ItemsEnviTemplates.add_menu_item)

    bpy.types.Material.gameType         = EnumProperty(         name="Game",                default=0, items=getGameTypes())
    bpy.types.Material.baseTexture      = StringProperty(       name="BaseTexture",         default="")
    bpy.types.Material.link             = StringProperty(       name="Link",                default="")
    bpy.types.Material.physicsId        = StringProperty(       name="PhysicsId",           default="")
    bpy.types.Material.usePhysicsId     = BoolProperty(         name="Use PhysicsId",       default=False)
    bpy.types.Material.gameplayId       = StringProperty(       name="GameplayId",          default="")
    bpy.types.Material.useGameplayId    = BoolProperty(         name="Use GameplayId",      default=False)
    bpy.types.Material.model            = EnumProperty(         name="Model",               default="TDSN",    items=getMaterialModelTypes())
    bpy.types.Material.environment      = EnumProperty(         name="Collection",          default="Stadium", items=getMaterialCollectionTypes())#Material."collection" not allowed
    # the size should be 4 (for BSDF) but to keep backward compability we have to keep it with size=3 (we convert it later in the code)
    bpy.types.Material.surfaceColor     = FloatVectorProperty(  name='Surface Color ',      subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855))

    
    



# delete classes
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tm_props
    del bpy.types.Scene.tm_props_generated
    del bpy.types.Scene.tm_props_pivots
    del bpy.types.Scene.tm_props_convertingItems
    del bpy.types.Scene.tm_props_linkedMaterials

    bpy.types.DATA_PT_EEVEE_light.remove(extend_object_properties_panel_LIGHT)
    bpy.types.VIEW3D_MT_add.remove(OT_ItemsCarsTemplates.add_menu_item)
    bpy.types.VIEW3D_MT_add.remove(OT_ItemsEnviTemplates.add_menu_item)
    
    # icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    
    preview_collections.clear()
            


@persistent
def on_save(what, idontknow) -> None: # on quit?
    """run on blender save"""
    saveDefaultSettingsJSON()

@persistent
def on_startup(dummy) -> None:
    """run on blender startup, load blend file & reload current file"""
    
    # can be opened on save
    try:
        bpy.ops.view3d.tm_closeconvertsubpanel()
        bpy.ops.view3d.tm_resetaddonupdatesettings()

        # so grid_subdivisions is editable
        bpy.context.scene.unit_settings.system = 'NONE'
        
        # ui grid scale


                    
    except AttributeError as error:
        debug(error)
        pass # fails on first startup when open_mainfile used

    loadDefaultSettingsJSON()
    
    @newThread
    def checkUpdate():
        AddonUpdate.checkForNewRelease()
    checkUpdate()

    # external addons
    installUvPackerAddon()

    # remove possible error text
    isNadeoImporterInstalled()
    updateInstalledNadeoImporterVersionInUI()

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
            owner=bpy,
            args=(),
            notify=on_select_obj
        )
    except RuntimeError:
        pass # first try always fails
        # RuntimeError: subscribe_rna, missing bl_rna attribute from 'Scene' instance (may not be registered)



bpy.app.handlers.load_post.append(on_startup)
bpy.app.handlers.save_post.append(on_save)

