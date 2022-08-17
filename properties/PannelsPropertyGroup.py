
import bpy
import bpy.utils.previews
from bpy.props import *

from ..utils.Descriptions   import *
from .Functions             import *
from .MapObjectProperties   import *



# def get_itemxml_template_names(self, context) -> list:#
#     return context.scene.tm_props_itemxml_templates.templates_ui.to_list() or ERROR_ENUM_PROPS




#? CB = CheckBox => BoolProperty
#? LI = List     => EnumProperty
#? NU = Number   => IntProperty, FloatProperty
#? ST = String   => StringProperty

class PannelsPropertyGroup(bpy.types.PropertyGroup):
    """general trackmania properties"""
    LI_gameType                 : EnumProperty(  name="Game",    items=getGameTypes(),   update=gameTypeGotUpdated)
    ST_nadeoIniFile_MP          : StringProperty(name="",        subtype="FILE_PATH",    update=lambda s, c: updateINI("ST_nadeoIniFile_MP"), default=defaultINI("ST_nadeoIniFile_MP"))
    ST_nadeoIniFile_TM          : StringProperty(name="",        subtype="FILE_PATH",    update=lambda s, c: updateINI("ST_nadeoIniFile_TM"), default=defaultINI("ST_nadeoIniFile_TM"))
    ST_author                   : StringProperty(name="Author",  default="")
    CB_nadeoImporterIsInstalled : BoolProperty(  name="NadeoImporter installed", default=False)
    NU_nadeoImporterDLProgress  : FloatProperty( min=0, max=100, default=0, subtype="PERCENTAGE", update=redraw_panels)
    CB_nadeoImporterDLRunning   : BoolProperty(  default=False,  update=redraw_panels)
    ST_nadeoImporterDLError     : StringProperty(name="Status",  default="", update=redraw_panels)
    CB_nadeoImporterDLshow      : BoolProperty(  default=False,  update=redraw_panels)
    LI_nadeoImporters_MP        : EnumProperty(items=getNadeoImportersManiaplanet(), name="Select NadeoImporter Version")
    ST_nadeoImporter_MP_current : StringProperty("None found")
    LI_nadeoImporters_TM        : EnumProperty(items=getNadeoImportersTrackmania2020(), name="Select NadeoImporter Version")
    ST_nadeoImporter_TM_current : StringProperty("None found")
    CB_NadeoLibParseFailed      : BoolProperty("NadeoMatLib.txt parse attempt", default=False)
    LI_blenderGridSize          : EnumProperty(items=getGridSizes(),         default=3, update=apply_custom_blender_grid_size)
    LI_blenderGridSizeDivision  : EnumProperty(items=getGridDivisionSizes(), default=3, update=apply_custom_blender_grid_size)
    
    #performance
    CB_allow_complex_panel_drawing: BoolProperty(default=True)
    CB_compress_blendfile:          BoolProperty(default=True)

    CB_addonUpdateDLRunning   : BoolProperty(       default=False,  update=redraw_panels)
    NU_addonUpdateDLProgress  : FloatProperty(      min=0, max=100, default=0, subtype="PERCENTAGE", update=redraw_panels)
    ST_addonUpdateDLmsg       : StringProperty(     name="Status",  default="", update=redraw_panels)
    CB_addonUpdateDLshow      : BoolProperty(       default=False,  update=redraw_panels)
    CB_addonUpdateAvailable   : BoolProperty(       default=False,  update=redraw_panels)

    #map manipulation
    ST_map_filepath           : StringProperty(name="Map file", default="",   subtype="FILE_PATH")
    PT_map_collection         : bpy.props.PointerProperty(type=bpy.types.Collection)
    PT_map_object             : bpy.props.PointerProperty(type=MapObjectProperties)

    #object manipulation
    NU_objMplScaleFrom      : IntProperty(default=7, min=1, max=20)
    NU_objMplScaleTo        : IntProperty(default=4, min=1, max=20)
    NU_objMplScaleFactor    : IntProperty(default=4, min=1, max=20)
    CB_objMplScaleRecursive : BoolProperty(default=True, description="Affect child collections")

    #export
    LI_exportType               : EnumProperty(items=getExportTypes(),        name="Action", default=1)
    LI_exportFolderType         : EnumProperty(items=getExportFolderTypes,    name="Folder", default=0)
    ST_exportFolder_MP          : StringProperty(name="Folder", default="",   subtype="DIR_PATH") #update=lambda self, context: makeItemsPathRelative("ST_exportFolder")
    ST_exportFolder_TM          : StringProperty(name="Folder", default="",   subtype="DIR_PATH") #update=lambda self, context: makeItemsPathRelative("ST_exportFolder")
    LI_exportWhichObjs          : EnumProperty(items=getExportWhichObjects(), name="Export by?")
    LI_exportValidTypes         : EnumProperty(name="Export",      items=getExportWhichObjTypes())
    NU_exportObjScale           : FloatProperty(name="Scale", min=0, soft_max=16)
    NU_multiScaleExportFactor   : FloatProperty(name="Steps", min=0, soft_max=8, default=0.25)
    CB_useMultiScaleExport      : BoolProperty(default=True, name="Scale exports", description=DESC_MULTI_SCALE_EXPORT)
    CB_overwriteMultiScaleFactor: BoolProperty(default=False, name="Step factor" , description=DESC_MULTI_SCALE_EXPORT)
    
    #convert
    NU_convertCount              : IntProperty(min=0,               default=0, update=redraw_panels)
    NU_convertedRaw              : IntProperty(min=0,               default=0, update=redraw_panels)
    NU_converted                 : IntProperty(min=0, max=100,      default=0, subtype="PERCENTAGE", update=redraw_panels) 
    NU_convertedSuccess          : IntProperty(min=0,               default=0, update=redraw_panels)
    NU_convertedError            : IntProperty(min=0,               default=0, update=redraw_panels)
    ST_convertedErrorList        : StringProperty(default="",       update=redraw_panels)
    CB_showConvertPanel          : BoolProperty(default=False,      update=redraw_panels)
    CB_stopAllNextConverts       : BoolProperty(default=False,      update=redraw_panels, name="Stop all next converts")
    CB_converting                : BoolProperty(default=False,      update=redraw_panels)
    CB_convertMultiThreaded      : BoolProperty(default=False,      update=redraw_panels, description="Don't convert all at the same time (converts can be cancelled")
    CB_notifyPopupWhenDone       : BoolProperty(default=True,       name="Notify toast when done")
    NU_convertDurationSinceStart : IntProperty(min=-1,              default=-1,   update=redraw_panels)
    NU_convertStartedAt          : IntProperty(min=-1,              default=-1,   update=redraw_panels)
    NU_currentConvertDuration    : IntProperty(min=0,               default=0,    update=redraw_panels)
    NU_prevConvertDuration       : IntProperty(min=0,               default=0,    update=redraw_panels)
    CB_generateMeshAndShapeGBX   : BoolProperty(default=True,       update=redraw_panels, description="To import your item in meshmodeler, those 2 additional files are required")

    #import
    LI_importMatFailed        : StringProperty()
    LI_importType             : EnumProperty(items=getImportTypes())
    CB_importFolderRecursive  : BoolProperty(name="Recursive", default=False)

    #icons
    CB_icon_genIcons        : BoolProperty(name="Generate Icons",         default=True, update=redraw_panels)
    CB_icon_overwriteIcons  : BoolProperty(name="Overwrite Icons",        default=True, update=redraw_panels)
    LI_icon_perspective     : EnumProperty(items=getIconPerspectives(),   name="Perspective")
    LI_icon_pxDimension     : EnumProperty(items=getIconPXdimensions(),   name="Size")
    NU_icon_padding         : IntProperty(min=0, max=100,     default=80, subtype="PERCENTAGE", update=redraw_panels) 
    NU_icon_bgColor         : FloatVectorProperty(name='BG Color',        subtype='COLOR', min=0, max=1, size=4, default=(1,1,1,1), update=updateWorldBG)

    #uvmaps
    CB_uv_genLightMap               : BoolProperty(name="Generate LightMap",                        default=True,       update=redraw_panels)
    CB_uv_fixLightMap               : BoolProperty(name="Only if LM has overlaps",                  default=True,       update=redraw_panels)
    NU_uv_angleLimitLM              : FloatProperty(name="Angle Limit",                             default=r(89.0),    min=0, max=r(89.0), subtype="ANGLE")
    NU_uv_islandMarginLM            : FloatProperty(name="Island Margin",                           default=0.1,        min=0, max=1)
    NU_uv_areaWeightLM              : FloatProperty(name="Area Weight",                             default=0.0,        min=0, max=1)
    CB_uv_correctAspectLM           : BoolProperty(name="Correct Aspect",                           default=True,       update=redraw_panels)
    CB_uv_scaleToBoundsLM           : BoolProperty(name="Scale To Bounds",                          default=False,      update=redraw_panels)
    CB_uv_genBaseMaterialCubeMap    : BoolProperty(name="Generate BaseMaterial with Cube Project",  default=False,      update=redraw_panels)
    NU_uv_cubeProjectSize           : FloatProperty(name="Cube Project",                            default=0.2,        min=0, max=100)
    
    #workspaces
    LI_workspaces : EnumProperty(items=getWorkspaceNames, name="Workspace", default=3)

    #xml
    LI_xml_simpleOrAdvanced : EnumProperty(items=get_itemxml_display_menu())
    LI_xml_simpleGridXY     : EnumProperty(items=getSimpleGridParams())
    LI_xml_simpleGridZ      : EnumProperty(items=getSimpleGridParams())
    CB_xml_syncGridLevi     : BoolProperty(name="Sync Grid & Levi steps",   default=True)
    CB_xml_overwriteMeshXML : BoolProperty(name="Overwrite Mesh XML",       default=True, update=redraw_panels)
    CB_xml_overwriteItemXML : BoolProperty(name="Overwrite Item XML",       default=True, update=redraw_panels)
    CB_xml_genItemXML       : BoolProperty(name="Generate Item XML",        default=True, update=redraw_panels)
    CB_xml_genMeshXML       : BoolProperty(name="Generate Mesh XML",        default=True, update=redraw_panels)
    LI_xml_meshtype         : EnumProperty( name="Type",                    items=getMeshXMLType())
    NU_xml_scale            : FloatProperty(name="Objscales",               default=1.0, min=0, max=256, step=100)
    CB_xml_scale            : BoolProperty( name="Obj Scale",               default=False)
    CB_xml_lightPower       : BoolProperty( name="Lightpower",              default=False)
    NU_xml_lightPower       : FloatProperty(name="Lightpower",              default=1.0, min=0, max=256, step=1)
    CB_xml_lightGlobColor   : BoolProperty(name="Lightcolor",               default=False)
    NU_xml_lightGlobColor   : FloatVectorProperty(name='Lightcolor',        subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855))
    CB_xml_lightGlobDistance: BoolProperty(name="Lightdistance",            default=False)
    NU_xml_lightGlobDistance: FloatProperty(name="Lightdistance",           default=32.0, min=0, max=256, step=1)
    LI_xml_itemtype         : EnumProperty( name="Type",            items=getItemXMLType())
    LI_xml_waypointtype     : EnumProperty( name="Waypoint",        items=getWayPointVariations(), update=onWaypointUpdate)
    LI_xml_enviType         : EnumProperty( name="Envi",            items=getItemXMLCollections())
    NU_xml_gridAndLeviX     : FloatProperty(name="Sync X",          default=8.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridAndLeviY     : FloatProperty(name="Synx Y",          default=8.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridX            : FloatProperty(name="X Grid",          default=8.0, min=0, max=256, step=100)
    NU_xml_gridXoffset      : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_gridY            : FloatProperty(name="Y Grid",          default=8.0,  min=0, max=256, step=100)
    NU_xml_gridYoffset      : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviX            : FloatProperty(name="X Levitation",    default=8.0,  min=0, max=256, step=100)
    NU_xml_leviXoffset      : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviY            : FloatProperty(name="Y Levitation",    default=8.0,  min=0, max=256, step=100)
    NU_xml_leviYoffset      : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    CB_xml_ghostMode        : BoolProperty(name="Ghostmode",        default=True)
    CB_xml_autoRot          : BoolProperty(name="Auto rotation",    default=False, description="Grid needs to be set to 0")
    CB_xml_oneAxisRot       : BoolProperty(name="OneAxisRot",       default=False)
    CB_xml_notOnItem        : BoolProperty(name="Not on Item",      default=True)
    CB_xml_pivots           : BoolProperty(name="Pivots (ingame Q Key)",default=False)
    CB_xml_pivotSwitch      : BoolProperty(name="Pivot switch",     default=False)
    NU_xml_pivotSnapDis     : FloatProperty(name="Pivot snap distance", default=0.0,  min=0, max=256, step=100)

    LI_xml_item_template_globally   : EnumProperty(name="Template", items=get_itemxml_template_names_enum)
    LI_xml_item_template_to_add     : EnumProperty(name="Template", items=get_itemxml_template_names_enum) 
    ST_xml_item_template_add_name   : StringProperty(default="defaut_template_name")
    CB_xml_ignore_assigned_templates: BoolProperty(default=False)

    #materials          
    ST_selectedExistingMaterial : StringProperty(name="Material",                 update=updateMaterialSettings)
    #LI_materials                : EnumProperty(name="Material",                   items=getMaterials, update=updateMaterialSettings)
    LI_materialAction           : EnumProperty(name="Material Action",            default=0, items=getMaterialActions())
    ST_materialAddName          : StringProperty(name="Name",                     default="Matname...")
    LI_materialCollection       : EnumProperty(name="Collection",                 items=getMaterialCollectionTypes(), update=gameTypeGotUpdated)
    CB_materialUsePhysicsId     : BoolProperty(name="Use PhysicsId",              default=False)
    LI_materialPhysicsId        : EnumProperty(name="PhysicId",                   items=getMaterialPhysicIds)
    CB_materialUseGameplayId    : BoolProperty(name="Use GameplayId",             default=False)
    LI_materialGameplayId       : EnumProperty(name="GameplayId",                 items=getMaterialGameplayIds)
    LI_materialModel            : EnumProperty(name="Model",                      items=getMaterialModelTypes())
    #LI_materialLink             : EnumProperty(name="Link",                       items=getMaterialLinks)
    NU_materialCustomColorOld   : FloatVectorProperty(name='OldLightcolor',       subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855, 1.0), size=4,) # as backup, when BELOW changes(live preview)
    NU_materialCustomColor      : FloatVectorProperty(name='Lightcolor',          subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855, 1.0), size=4, update=setMaterialCustomColorLiveChanges)
    ST_materialBaseTexture      : StringProperty(name="BaseTexture",              default="", subtype="FILE_PATH", description="Custom texture located in Documents / Items / <Folders?> / <YouTexturename_D.dds>")
    LI_materialChooseSource     : EnumProperty(name="Custom Texture or Link",     items=getMaterialTextureSourceOptions())
    ST_selectedLinkedMat        : StringProperty(name="Linked mat", default="")

    #textures
    LI_DL_TextureEnvi      : EnumProperty(items=getGameTextureZipFileNames(), update=redraw_panels)
    CB_DL_TexturesRunning  : BoolProperty(name="Downloading...",              default=False, update=redraw_panels)
    NU_DL_Textures         : FloatProperty(min=0, max=100,                    default=0, subtype="PERCENTAGE", update=redraw_panels)
    ST_DL_TexturesErrors   : StringProperty(name="Status",                    default="")
    CB_DL_TexturesShow     : BoolProperty(default=False,                      update=redraw_panels)

    # cars
    LI_items_cars     : EnumProperty(name="Car",     items=get_car_names())
    LI_items_triggers : EnumProperty(name="Trigger", items=getTriggerNames())