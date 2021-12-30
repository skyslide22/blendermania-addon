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
                    row.scale_y = .75
                    row.label(text="Spawn object not found!")
                    row = box.row()
                    row.operator("view3d.tm_createsocketitemincollection", text="Add _socket_ to collection", icon="ADD")
                    row = box.row()
                    row.prop(tm_props, "LI_items_cars")
                    
                
                if has_trigger_item is False:
                    box = layout.box()
                    row = box.row()
                    row.alert = True
                    row.scale_y = .75
                    row.label(text="Trigger object not found!")
                    row = box.row()
                    row.operator("view3d.tm_createtriggeritemincollection", text="Add _trigger_ to collection", icon="ADD")


        if isGameTypeTrackmania2020():
            obj      = None
            obj_name = ""
            if bpy.context.selected_objects:
                obj      = bpy.context.selected_objects[0]
                obj_name = obj.name
            
            isEnabled = obj_name.startswith("_skip_")
            row = layout.row()
            row.scale_y = 1
            row.operator(f"view3d.tm_toggleobjectskip", text=f"""{'Use' if isEnabled else 'Ignore'} "{cleanObjNameFromSpecialProps(obj_name)}" during export""")

            isEnabled = obj_name.startswith("_notvisible_")
            row = layout.row()
            row.scale_y = 1
            row.operator("view3d.tm_toggleobjectnotvisible", text=f"""Mark "{cleanObjNameFromSpecialProps(obj_name)}" as {'Visible' if isEnabled else 'Not Visible'}""")

            isEnabled = obj_name.startswith("_notcollidable_")
            row = layout.row()
            row.scale_y = 1
            row.operator("view3d.tm_toggleobjectnotcollidable", text=f"""Mark "{cleanObjNameFromSpecialProps(obj_name)}" as {'Collidable' if isEnabled else 'Not Collidable'}""")

            


def addSocketItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_SOCKET)

def addTriggerItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_TRIGGER)

def cleanObjNameFromSpecialProps(name: str) -> str:
    new_name = ""
    if name is not None:
        new_name = (name
            .replace(SPECIAL_NAME_PREFIX_SKIP, "")
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
        fbx_filepath = ADDON_ITEM_FILEPATH_TRIGGER_32x8
    
    elif obj_type == SPECIAL_NAME_PREFIX_SOCKET:
        envi = getCarType()
        if   envi == "Stadium": fbx_filepath = ADDON_ITEM_FILEPATH_CAR_STADIUM
        elif envi == "Canyon":  fbx_filepath = ADDON_ITEM_FILEPATH_CAR_CANYON
        elif envi == "Valley":  fbx_filepath = ADDON_ITEM_FILEPATH_CAR_VALLEY
        elif envi == "Lagoon":  fbx_filepath = ADDON_ITEM_FILEPATH_CAR_LAGOON
        else:
            makeReportPopup(f"Collection not supported,{envi=}, {obj_type=}")
            return

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