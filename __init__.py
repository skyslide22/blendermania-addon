import bpy
import bpy.utils.previews
import bpy_types
from bpy.props import *
from bpy.app.handlers import persistent


bl_info = {
    "name"          : "Trackmania Export & Convert .fbx > .gbx Addon",
    "author"        : "skyslide",
    "description"   : "Export collections, create icons, generate xml files and convert items",
    "blender"       : (3, 0, 0),
    "version"       : (2, 0, 0),
    "location"      : "View3D",
    "warning"       : "",
    "category"      : "Generic"
}                    


from .TM_Functions          import *
from .TM_Settings           import *
from .TM_Properties         import *
from .TM_Items_Export       import *
from .TM_Items_Import       import * 
from .TM_Materials          import *
from .TM_Items_XML          import *
from .TM_Items_UVMaps       import *
from .TM_Items_Icon         import *
from .TM_Items_Templates    import *
from .TM_Items_Manipulate   import *
from .TM_Assets_Library     import *



# owner of the object eventlistener
object_eventlistner_owner = object()


# register order matters for UI panel ordering
classes = (

    # props (not panel)
    TM_Properties_for_Panels,
    TM_Properties_Generated,
    TM_Properties_Pivots,
    TM_Properties_ConvertingItems,
    TM_Properties_LinkedMaterials,

    # settings
    TM_PT_Settings,
    TM_OT_Settings_AutoFindNadeoIni,
    TM_OT_Settings_OpenDocumentation,
    TM_OT_Settings_OpenGithub,
    TM_OT_Settings_InstallNadeoImporter,
    TM_OT_Settings_InstallGameTextures,
    TM_OT_Settings_InstallGameAssetsLIbrary,
    TM_OT_Settings_DebugALL,
    TM_OT_Settings_UpdateAddon,
    TM_OT_Settings_UpdateAddonResetSettings,
    TM_OT_Settings_UpdateAddonOpenChangelog,
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
    TM_OT_Items_ObjectManipulationChangeCollectionScale,
    TM_OT_Items_ObjectManipulationRemoveCollectionScale,

    # export
    TM_PT_Items_Export,
    TM_OT_Items_Export_ExportAndOrConvert,
    TM_OT_Items_Export_OpenConvertReport,
    TM_OT_Items_Export_CloseConvertSubPanel,

    # import
    TM_PT_Items_Import,
    TM_OT_Items_Import,
    TM_OT_Items_ClearMatImportFailList,

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

    # cars
    TM_OT_Items_Cars_Import,

    # templates
    TM_OT_Items_Envi_Template_Import,
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

    bpy.types.DATA_PT_EEVEE_light.append(extendObjectPropertiesPanel_LIGHT)
    bpy.types.Light.night_only          = BoolProperty(default=False)

    bpy.types.VIEW3D_MT_add.prepend(TM_OT_Items_Envi_Template_Import.addMenuPoint_ENVI_TEMPLATE)
    bpy.types.VIEW3D_MT_add.prepend(TM_OT_Items_Cars_Import.addMenuPoint_CAR_SPAWN)


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

    bpy.types.DATA_PT_EEVEE_light.remove(extendObjectPropertiesPanel_LIGHT)

    bpy.types.VIEW3D_MT_add.remove(TM_OT_Items_Cars_Import.addMenuPoint_CAR_SPAWN)
    bpy.types.VIEW3D_MT_add.remove(TM_OT_Items_Envi_Template_Import.addMenuPoint_ENVI_TEMPLATE)

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
    except AttributeError as error:
        pass # fails on first startup when open_mainfile used

    loadDefaultSettingsJSON()

    AddonUpdate.checkForNewRelease()
    
    # remove possible error text
    isNadeoImporterInstalled()

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
            notify=onSelectObject
        )
    except RuntimeError:
        pass # first try always fails
        # RuntimeError: subscribe_rna, missing bl_rna attribute from 'Scene' instance (may not be registered)



bpy.app.handlers.load_post.append(on_startup)
bpy.app.handlers.save_post.append(on_save)

