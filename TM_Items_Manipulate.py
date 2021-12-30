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

class TM_OT_Items_ObjectManipulationToggleSkip(Operator):
    bl_idname = "view3d.tm_toggleobjectskip"
    bl_description = "Toggle _skip_ on selected object"
    bl_icon = 'ADD'
    bl_label = "Toggle _skip_"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            isEnabled = obj.name.startswith("_skip_")

            obj.name = obj.name.replace("_notvisible_", "").replace("_notcollidable_", "")

            if isEnabled:
                obj.name = obj.name.replace("_skip_", "")
            else:
                obj.name = "_skip_"+obj.name
        
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

            obj.name = obj.name.replace("_skip_", "").replace("_notcollidable_", "")

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

            obj.name = obj.name.replace("_skip_", "").replace("_notvisible_", "")

            if isEnabled:
                obj.name = obj.name.replace("_notcollidable_", "")
            else:
                obj.name = "_notcollidable_"+obj.name

        return {"FINISHED"}



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
        
        collection      = getActiveCollectionOfSelectedObject()
        collection_name = collection.name if collection is not None else "Select any object !"

        # layout.separator(factor=UI_SPACER_FACTOR)

        # row = layout.row()
        # row.scale_y = .5
        # # row.alignment = "CENTER"
        # row.label(text="Collection to manipulate:")
        
        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text=collection_name)

        # layout.separator(factor=UI_SPACER_FACTOR)

        row = layout.row()
        col = row.column()
        col.label(text="Waypoint")
        col = row.column()
        col.scale_x = 1.5
        col.prop(tm_props, "LI_xml_waypointtype", text="")

        current_collection = getActiveCollectionOfSelectedObject()

        # check if collection is a waypoint
        if current_collection is not None:
            if getWaypointTypeOfCollection(current_collection) != "None":
                has_spawn_item   = checkIfCollectionHasObjectWithName(current_collection, "_socket_")
                has_trigger_item = checkIfCollectionHasObjectWithName(current_collection, "_trigger_")
                

                if has_spawn_item is False:
                    box = layout.box()
                    row = box.row()
                    row.alert = True
                    row.label(text="Spawn object not found!")
                    row = box.row()
                    row.operator("view3d.tm_createsocketitemincollection", text="Add _socket_ to collection", icon="ADD")
                    
                
                if has_trigger_item is False:
                    box = layout.box()
                    row = box.row()
                    row.alert = True
                    row.label(text="Trigger object not found!")
                    row = box.row()
                    row.operator("view3d.tm_createtriggeritemincollection", text="Add _trigger_ to collection", icon="ADD")

        if len(bpy.context.selected_objects) == 1:
            obj = bpy.context.selected_objects[0]
            
            isEnabled = obj.name.startswith("_skip_")
            row = layout.row()
            row.scale_y = 1
            row.operator("view3d.tm_toggleobjectskip", text=f"{'Use' if isEnabled else 'Ignore'} \"{cleanObjNameFromSpecialProps(obj.name)}\" during export")

            isEnabled = obj.name.startswith("_notvisible_")
            row = layout.row()
            row.scale_y = 1
            row.operator("view3d.tm_toggleobjectnotvisible", text=f"Mark \"{cleanObjNameFromSpecialProps(obj.name)}\" as {'Visible' if isEnabled else 'Not Visible'}")

            isEnabled = obj.name.startswith("_notcollidable_")
            row = layout.row()
            row.scale_y = 1
            row.operator("view3d.tm_toggleobjectnotcollidable", text=f"Mark \"{cleanObjNameFromSpecialProps(obj.name)}\" as {'Collidable' if isEnabled else 'Not Collidable'}")

            


def addSocketItemToSelectedCollection() -> None:
    addItemToCollection("_socket_")

def addTriggerItemToSelectedCollection() -> None:
    addItemToCollection("_trigger")


def addItemToCollection(obj_type: str) -> None:
    debug(f"add {obj_type=}")

def cleanObjNameFromSpecialProps(name: str) -> str:
    return name.replace("_skip_", "").replace("_notvisible_", "").replace("_notcollidable_", "")