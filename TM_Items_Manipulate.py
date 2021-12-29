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


def addSocketItemToSelectedCollection() -> None:
    addItemToCollection("_socket_")

def addTriggerItemToSelectedCollection() -> None:
    addItemToCollection("_trigger")


def addItemToCollection(obj_type: str) -> None:
    debug(f"add {obj_type=}")