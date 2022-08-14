
import bpy
import re

from bpy.types import (Operator)

from ..utils.Materials import create_material_nodes
from ..utils.Functions  import *
from ..utils.Properties import *
from ..utils.Constants  import * 

class TM_OT_Materials_Create(Operator):
    bl_idname = "view3d.tm_creatematerial"
    bl_label = "create materials"
    bl_description = "create material"
   
    def execute(self, context):
        _create_or_ipdate_material("CREATE")
        context.region.tag_redraw()
        return {"FINISHED"}
    
class TM_OT_Materials_Update(Operator):
    bl_idname = "view3d.tm_updatematerial"
    bl_label = "update materials"
    bl_description = "update material"
   
    def execute(self, context):
        _create_or_ipdate_material("UPDATE")
        context.region.tag_redraw()
        return {"FINISHED"}

class TM_OT_Materials_ClearBaseMaterial(Operator):
    bl_idname = "view3d.tm_clearbasetexture"
    bl_label = "clear basematerial"
    bl_description = "clear basematerial"
   
    def execute(self, context):
        get_global_props()["ST_materialBaseTexture"] = ""
        context.region.tag_redraw()
        return {"FINISHED"}

class TM_OT_Materials_RevertCustomColor(Operator):
    bl_idname = "view3d.tm_revertcustomcolor"
    bl_label = "reset custom color"
    bl_description = "reset custom color"
   
    def execute(self, context):
        revertMaterialCustomColorLiveChanges()
        context.region.tag_redraw()
        return {"FINISHED"}

def _create_or_ipdate_material(action)->None:
    """create a export/convert ready material for TM and MP"""
    tm_props = get_global_props()
    
    TM_PREFIX = "TM_"
    MP_PREFIX = "MP_"

    matName          = tm_props.ST_selectedExistingMaterial
    matNameNew       = safe_name( tm_props.ST_materialAddName )
    matGameType      = tm_props.LI_gameType
    matCollection    = tm_props.LI_materialCollection
    matPhysicsId     = tm_props.LI_materialPhysicsId
    matUsePhysicsId  = tm_props.CB_materialUsePhysicsId
    matGameplayId    = tm_props.LI_materialGameplayId
    matUseGameplayId = tm_props.CB_materialUseGameplayId
    matModel         = tm_props.LI_materialModel
    matLink          = tm_props.ST_selectedLinkedMat
    matBaseTexture   = tm_props.ST_materialBaseTexture
    matColor         = tm_props.NU_materialCustomColor
    MAT              = None

    matTexSourceIsCustom = tm_props.LI_materialChooseSource == "CUSTOM"

    if isGameTypeTrackmania2020():
        if not matNameNew.startswith(TM_PREFIX):
            matNameNew = TM_PREFIX + matNameNew.replace(MP_PREFIX, "") 

    if isGameTypeManiaPlanet():
        if not matNameNew.startswith(MP_PREFIX):
            matNameNew = MP_PREFIX + matNameNew.replace(TM_PREFIX, "") 


    if action == "CREATE" and matNameNew in bpy.data.materials:
        show_report_popup(
            title="Material with this name already exists", 
            infos=["Creation failed"], 
            icon=ICON_ERROR)
        debug(f"Material {matNameNew} creation failed")
        return

    if action == "CREATE":
        MAT = bpy.data.materials.new(name=matNameNew)
    else:
        MAT = bpy.data.materials[matName]

    MAT.gameType      = matGameType
    MAT.environment   = matCollection
    MAT.usePhysicsId  = matUsePhysicsId
    MAT.physicsId     = matPhysicsId
    MAT.useGameplayId = matUseGameplayId
    MAT.gameplayId    = matGameplayId
    MAT.model         = matModel
    MAT.link          = matLink
    MAT.baseTexture   = matBaseTexture if matTexSourceIsCustom          else ""
    MAT.name          = matNameNew
    MAT.surfaceColor  = matColor[:3]

    if action == "CREATE":
        show_report_popup(
            title=f"Material {matNameNew} successfully created!",
            icon ="CHECKMARK"
        )
        debug(f"Material {matNameNew} created")
    else: #UPDATE
        show_report_popup(
            title=f"Material {matName} sucessfully updated", 
            icon=ICON_SUCCESS
        )
        debug(f"Material {matName} updated")

    create_material_nodes(MAT)
    applyMaterialLiveChanges()