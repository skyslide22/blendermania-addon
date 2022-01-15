import bpy
from bpy.types import Panel
from bpy.types import Operator

from .TM_Functions import *




class TM_OT_Items_ObjectManipulationAddSocketItem(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_createsocketitemincollection"
    bl_description = "Create a _socket_ item"
    bl_icon = 'ADD'
    bl_label = "Create _socket_"
        
    def execute(self, context):
        addSocketItemToSelectedCollection()
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationAddTriggerItem(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_createtriggeritemincollection"
    bl_description = "Create a _trigger_ item"
    bl_icon = 'ADD'
    bl_label = "Create _trigger_"
        
    def execute(self, context):
        addTriggerItemToSelectedCollection()
        return {"FINISHED"}

class TM_OT_Items_ObjectManipulationToggleIgnore(Operator):
    bl_idname = "view3d.tm_toggleobjectsignore"
    bl_description = "Toggle _ignore_ on selected object"
    bl_icon = 'ADD'
    bl_label = "Toggle _ignore_"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            isEnabled = obj.name.startswith("_ignore_")

            obj.name = obj.name.replace("_notvisible_", "").replace("_notcollidable_", "")

            if isEnabled:
                obj.name = obj.name.replace("_ignore_", "")
            else:
                obj.name = "_ignore_"+obj.name
        
        return {"FINISHED"}


class TM_OT_Items_CollectionManipulationToggleIgnore(Operator):
    bl_idname = "view3d.tm_togglecollectionignore"
    bl_description = "Toggle _ignore_ on selected collection"
    bl_icon = 'ADD'
    bl_label = "Toggle _ignore_"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            col = obj.users_collection[0]
            isEnabled = col.name.startswith("_ignore_")

            if isEnabled:
                col.name = col.name.replace("_ignore_", "")
            else:
                col.name = "_ignore_"+col.name
        
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleNotvisible(Operator):
    bl_idname = "view3d.tm_toggleobjectnotvisible"
    bl_description = "Toggle _notvisible_ on selected object"
    bl_icon = 'ADD'
    bl_label = "Toggle _notvisible_"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            isEnabled = obj.name.startswith("_notvisible_")

            obj.name = obj.name.replace("_ignore_", "").replace("_notcollidable_", "")

            if isEnabled:
                obj.name = obj.name.replace("_notvisible_", "")
            else:
                obj.name = "_notvisible_"+obj.name
        
        return {"FINISHED"}

class TM_OT_Items_ObjectManipulationToggleNotcollidable(Operator):
    bl_idname = "view3d.tm_toggleobjectnotcollidable"
    bl_description = "Toggle _notcollidable_ on selected object"
    bl_icon = 'ADD'
    bl_label = "Toggle _notcollidable_"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            isEnabled = obj.name.startswith("_notcollidable_")

            obj.name = obj.name.replace("_ignore_", "").replace("_notvisible_", "")

            if isEnabled:
                obj.name = obj.name.replace("_notcollidable_", "")
            else:
                obj.name = "_notcollidable_"+obj.name

        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationChangeCollectionScale(Operator):
    bl_idname = "wm.tm_changecollectionscale"
    bl_description = "Set custom multi scale for collection"
    bl_icon = 'ADD'
    bl_label = "Set custom multi scale for collection"
   
    def execute(self, context):
        setScaledCollectionName()
        return {"FINISHED"}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = getTmProps()
        layout   = self.layout
        
        row = layout.row()
        row.prop(tm_props, "ST_objMplScaleFrom", text="From")
        row = layout.row()
        row.prop(tm_props, "ST_objMplScaleTo",   text="To")
        row = layout.row()
        row.prop(tm_props, "ST_objMplScaleFactor", text="Factor")



class TM_PT_ObjectManipulations(Panel):
    bl_label = "Object Manipulation"
    bl_idname = "TM_PT_ObjectManipulations"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="OBJECT_DATA")

    def draw(self, context):

        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        tm_props = getTmProps()
        
        current_collection      = getActiveCollectionOfSelectedObject()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"
        
        # collection box
        col_box = layout.box()
        col = col_box.column(align=True)
        row = col.row()
        row.alignment = "CENTER"
        row.label(text=current_collection_name)

        row = col.row()
        row.prop(tm_props, "LI_xml_waypointtype", text="")
        

        
        # check if collection is a waypoint
        if current_collection is not None:
            if getWaypointTypeOfCollection(current_collection) != "None":
                has_spawn_item   = checkIfCollectionHasObjectWithName(current_collection, "_socket_")
                has_trigger_item = checkIfCollectionHasObjectWithName(current_collection, "_trigger_")
                

                if has_spawn_item is False:
                    row = col_box.row()
                    row.alert = True
                    row.scale_y = .75
                    row.alignment = "CENTER"
                    row.label(text="Spawn object not found!")
                    row = col_box.row(align=True)
                    row.operator("view3d.tm_createsocketitemincollection", text="Add spawn", icon="ADD")
                    row.prop(tm_props, "LI_items_cars", text="")
                    
                
                if has_trigger_item is False:
                    row = col_box.row()
                    row.alert = True
                    row.scale_y = .75
                    row.alignment = "CENTER"
                    row.label(text="Trigger object not found!")
                    row = col_box.row(align=True)
                    row.operator("view3d.tm_createtriggeritemincollection", text="Add trigger", icon="ADD")
                    row.prop(tm_props, "LI_items_triggers", text="")


        # layout.separator(factor=UI_SPACER_FACTOR)
        
        # object box
        obj_box = layout.box()

        obj                 = None
        obj_name_raw        = "Select any object !"
        obj_name_with_prefix= "Select any object !"
        if bpy.context.selected_objects:
            obj                 = bpy.context.selected_objects[0]
            obj_name_with_prefix= obj.name
            obj_name_raw        = cleanObjNameFromSpecialProps(obj.name)

        col = obj_box.column(align=True)
        row = col.row()
        row.alignment = "CENTER"
        row.label(text=f"{obj_name_raw}")

        row = col.row(align=True)
        
        isEnabled = obj_name_with_prefix.startswith("_ignore_")
        row.operator(f"view3d.tm_toggleobjectsignore", text=f"ignore", icon="CHECKMARK" if isEnabled else "CHECKBOX_DEHLT")


        if isGameTypeTrackmania2020():
            isEnabled = obj_name_with_prefix.startswith("_notvisible_")
            row.operator("view3d.tm_toggleobjectnotvisible", text=f"notvisible", icon="CHECKMARK" if isEnabled else "CHECKBOX_DEHLT")

            isEnabled = obj_name_with_prefix.startswith("_notcollidable_")
            row.operator("view3d.tm_toggleobjectnotcollidable", text=f"notcollidable", icon="CHECKMARK" if isEnabled else "CHECKBOX_DEHLT")


        layout.separator(factor=UI_SPACER_FACTOR)
        
        layout.operator("wm.tm_changecollectionscale", text="set scaleee")

        layout.separator(factor=UI_SPACER_FACTOR)

            


def addSocketItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_SOCKET)

def addTriggerItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_TRIGGER)

def cleanObjNameFromSpecialProps(name: str) -> str:
    new_name = ""
    if name is not None:
        new_name = (name
            .replace(SPECIAL_NAME_PREFIX_IGNORE, "")
            .replace(SPECIAL_NAME_PREFIX_NOTVISIBLE, "")
            .replace(SPECIAL_NAME_PREFIX_NOTCOLLIDABLE, "")
            )
    return new_name


def importWaypointHelperAndAddToActiveCollection(obj_type: str) -> None:
    collection   = getActiveCollectionOfSelectedObject()
    fbx_filepath = ""
    pre_selected_objects = bpy.context.selected_objects.copy()

    if collection is None:
        return
    
    if obj_type == SPECIAL_NAME_PREFIX_TRIGGER:
        fbx_filepath = getTriggerName()
    
    elif obj_type == SPECIAL_NAME_PREFIX_SOCKET:
        fbx_filepath = getCarType()

    else:
        makeReportPopup(f"failed to import a obj of {obj_type=}")
        return

    fbx_filepath = fixSlash(fbx_filepath)
    import_at    = bpy.context.selected_objects[0].location
    collection   = getActiveCollectionOfSelectedObject()

    deselectAllObjects()

    importFBXFile(fbx_filepath)
    imported_objs = bpy.context.selected_objects

    for object in imported_objs:
        # collection.objects.link(object)
        object.location = import_at

    for object in pre_selected_objects:
        object.select_set(True)



def setScaledCollectionName(col) -> None: ...
