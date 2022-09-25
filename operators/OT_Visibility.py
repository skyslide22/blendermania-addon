
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 

class TM_OT_Visibility_ViewLayerToggleSocket(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitysocket"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_SOCKET)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleTrigger(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitytrigger"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_TRIGGER)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleIgnore(Operator):
    bl_idname = "view3d.tm_viewlayervisibilityignore"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_IGNORE)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleNotVisible(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitynotvisible"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_NOTVISIBLE)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleNotCollidable(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitynotcollidable"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_NOTCOLLIDABLE)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleMTTrigger(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitymttrigger"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_MTTRIGGER} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_MTTRIGGER}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_PREFIX_MTTRIGGER)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleOrigin(Operator):
    bl_idname = "view3d.tm_viewlayervisibilityorigin"
    bl_description = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_INFIX_ORIGIN)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerTogglePivot(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitypivot"
    bl_description = f"Toggle {SPECIAL_NAME_INFIX_PIVOT} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_INFIX_PIVOT}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_INFIX_PIVOT)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleLod0(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitylod0"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_SUFFIX_LOD0)
        return {"FINISHED"}

class TM_OT_Visibility_ViewLayerToggleLod1(Operator):
    bl_idname = "view3d.tm_viewlayervisibilitylod1"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1} visibility in the ViewLayer"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1}"
    
    def execute(self, context):
        toggleNameVisibilityInViewLayer(SPECIAL_NAME_SUFFIX_LOD1)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleSocket(Operator):
    bl_idname = "view3d.tm_collectionvisibilitysocket"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_SOCKET)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleTrigger(Operator):
    bl_idname = "view3d.tm_collectionvisibilitytrigger"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_TRIGGER)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleIgnore(Operator):
    bl_idname = "view3d.tm_collectionvisibilityignore"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_IGNORE)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleNotVisible(Operator):
    bl_idname = "view3d.tm_collectionvisibilitynotvisible"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_NOTVISIBLE)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleNotCollidable(Operator):
    bl_idname = "view3d.tm_collectionvisibilitynotcollidable"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_NOTCOLLIDABLE)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleMTTrigger(Operator):
    bl_idname = "view3d.tm_collectionvisibilitymttrigger"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_MTTRIGGER} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_MTTRIGGER}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_PREFIX_MTTRIGGER)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleOrigin(Operator):
    bl_idname = "view3d.tm_collectionvisibilityorigin"
    bl_description = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_INFIX_ORIGIN)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionTogglePivot(Operator):
    bl_idname = "view3d.tm_collectionvisibilitypivot"
    bl_description = f"Toggle {SPECIAL_NAME_INFIX_PIVOT} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_INFIX_PIVOT}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_INFIX_PIVOT)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleLod0(Operator):
    bl_idname = "view3d.tm_collectionvisibilitylod0"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_SUFFIX_LOD0)
        return {"FINISHED"}

class TM_OT_Visibility_CollectionToggleLod1(Operator):
    bl_idname = "view3d.tm_collectionvisibilitylod1"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1} visibility in the Collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1}"
    
    def execute(self, context):
        toggleNameVisibilityInCollection(SPECIAL_NAME_SUFFIX_LOD1)
        return {"FINISHED"}

def toggleNameVisibilityInViewLayer(subname: str):
    if is_name_visible_in_viewlayer(subname):
        for obj in bpy.context.scene.objects:
            if subname in obj.name.lower():
                obj.hide_set(True)
    else:
        for obj in bpy.context.scene.objects:
            if subname in obj.name.lower():
                obj.hide_set(False)

def toggleNameVisibilityInCollection(subname: str):
    coll = get_active_collection_of_selected_object()
    if is_name_visible_in_collection(coll,subname):
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.hide_set(True)
    else:
        for obj in coll.objects:
            if subname in obj.name.lower():
                obj.hide_set(False)