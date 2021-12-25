import bpy
import bpy.utils.previews
import bpy_types
from bpy.props import *
from bpy.app.handlers import persistent

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





# register order matters for UI panel ordering
classes = (

    #props (not panel)
    TM_Properties_for_Panels,
    TM_Properties_Generated,
    TM_Properties_Pivots,
    TM_Properties_ConvertingItems,
    TM_Properties_LinkedMaterials,

    #settings
    TM_PT_Settings,
    TM_OT_Settings_AutoFindNadeoIni,
    TM_OT_Settings_OpenDocumentation,
    TM_OT_Settings_OpenGithub,
    TM_OT_Settings_InstallNadeoImporter,
    TM_OT_Settings_InstallGameTextures,
    TM_OT_Settings_DebugALL,

    #export
    TM_PT_Items_Export,
    TM_OT_Items_Export_ExportAndOrConvert,
    TM_OT_Items_Export_OpenConvertReport,
    TM_OT_Items_Export_CloseConvertSubPanel,

    #import
    TM_PT_Items_Import,
    TM_OT_Items_Import,
    TM_OT_Items_ClearMatImportFailList,

    #xml,
    TM_PT_Items_MeshXML,
    TM_PT_Items_ItemXML,
    TM_OT_Items_ItemXML_AddPivot,
    TM_OT_Items_ItemXML_RemovePivot,

    #icons,
    TM_PT_Items_Icon,
    TM_OT_Items_Icon_Test,

    #uvs
    TM_PT_Items_UVmaps_LightMap,
    TM_PT_Items_UVmaps_BaseMaterial_CubeProject,

    #materials
    TM_PT_Materials,
    TM_OT_Materials_Create,
    TM_OT_Materials_Update,
    TM_OT_Materials_ClearBaseMaterial,
    TM_OT_Materials_RevertCustomColor,

    #cars
    TM_OT_Items_Cars_Import,

    #templates
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


    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    
    preview_collections.clear()



@persistent
def on_startup(dummy) -> None:
    """run on blender startup/loadfile"""
    bpy.ops.view3d.tm_closeconvertsubpanel()
    isNadeoIniValid()


bpy.app.handlers.load_post.append(on_startup)

