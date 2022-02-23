from cgitb import text
from os import remove
from socket import socket
import bpy
from bpy.types import Panel
from bpy.types import Operator

from .TM_Functions import *




class TM_OT_Items_ObjectManipulationAddSocketItem(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_createsocketitemincollection"
    bl_description = f"Create a {SPECIAL_NAME_PREFIX_SOCKET} item"
    bl_icon = 'ADD'
    bl_label = f"Create {SPECIAL_NAME_PREFIX_SOCKET}"
        
    def execute(self, context):
        addSocketItemToSelectedCollection()
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationAddTriggerItem(Operator):
    """open convert report"""
    bl_idname = "view3d.tm_createtriggeritemincollection"
    bl_description = f"Create a {SPECIAL_NAME_PREFIX_TRIGGER} item"
    bl_icon = 'ADD'
    bl_label = f"Create {SPECIAL_NAME_PREFIX_TRIGGER}"
        
    def execute(self, context):
        addTriggerItemToSelectedCollection()
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleLod1(Operator):
    bl_idname = "view3d.tm_toggleobjectlod1"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD1}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialSuffix(bpy.context.selected_objects[0], SPECIAL_NAME_SUFFIX_LOD1)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleLod0(Operator):
    bl_idname = "view3d.tm_toggleobjectlod0"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_LOD0}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialSuffix(bpy.context.selected_objects[0], SPECIAL_NAME_SUFFIX_LOD0)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleIgnore(Operator):
    bl_idname = "view3d.tm_toggleobjectignore"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(bpy.context.selected_objects[0], SPECIAL_NAME_PREFIX_IGNORE)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleSocket(Operator):
    bl_idname = "view3d.tm_toggleobjectsocket"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_SOCKET}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(bpy.context.selected_objects[0], SPECIAL_NAME_PREFIX_SOCKET)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleTrigger(Operator):
    bl_idname = "view3d.tm_toggleobjecttrigger"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_TRIGGER}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(bpy.context.selected_objects[0], SPECIAL_NAME_PREFIX_TRIGGER)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleNotvisible(Operator):
    bl_idname = "view3d.tm_toggleobjectnotvisible"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTVISIBLE}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(bpy.context.selected_objects[0], SPECIAL_NAME_PREFIX_NOTVISIBLE)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleNotcollidable(Operator):
    bl_idname = "view3d.tm_toggleobjectnotcollidable"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_NOTCOLLIDABLE}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(bpy.context.selected_objects[0], SPECIAL_NAME_PREFIX_NOTCOLLIDABLE)
        return {"FINISHED"}


class TM_OT_Items_CollectionManipulationToggleIgnore(Operator):
    bl_idname = "view3d.tm_togglecollectionignore"
    bl_description = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE} on selected collection"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_PREFIX_IGNORE}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialPrefix(getActiveCollectionOfSelectedObject(), SPECIAL_NAME_PREFIX_IGNORE)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationRemoveCollectionScale(Operator):
    bl_idname = "view3d.tm_removecollectionscale"
    bl_description = "Remove custom multi scale for collection"
    bl_icon = 'REMOVE'
    bl_label = "Remove custom multi scale for collection"
   
    def execute(self, context):
        tm_props        = getTmProps()
        affect_children = tm_props.CB_objMplScaleRecursive
        col             = getActiveCollectionOfSelectedObject()

        if col is not None:    
            child_cols = set()
            child_cols.add(col)
            
            if affect_children:
                for obj in col.all_objects:
                    for child_col in obj.users_collection:
                        child_cols.add(child_col)
            
            for child_col in child_cols:
                setScaledCollectionName(col=child_col, remove=True)
        

        else:
            makeReportPopup("Renaming failed", ["Select any object to change its collection name"])
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationChangeCollectionScale(Operator):
    bl_idname = "wm.tm_changecollectionscale"
    bl_description = "Set custom multi scale for collection"
    bl_icon = 'ADD'
    bl_label = "Set custom multi scale for collection"
   
    def execute(self, context):
        col      = getActiveCollectionOfSelectedObject()
        tm_props = getTmProps()

        affect_children = tm_props.CB_objMplScaleRecursive

        scale_from     = tm_props.NU_objMplScaleFrom
        scale_to       = tm_props.NU_objMplScaleTo
        scale_step     = tm_props.NU_objMplScaleFactor

        max_step = 1
        steps    = 1 / scale_step
        scales   = scale_from - scale_to
        
        last_step   = max_step - (steps * scales) 
        is_invalid  = last_step <= 0.06 # if scale <= 0, object will be invisible ingame

        if is_invalid:
            makeReportPopup("Setting scales failed", [
                f"Invalid values, atleast one scale is lower than 0!",
                f"Last step: {last_step}"
                ])
            return {"FINISHED"}


        if col is not None:
            
            child_cols = set()
            child_cols.add(col)
            
            if affect_children:
                for obj in col.all_objects:
                    for child_col in obj.users_collection:
                        child_cols.add(child_col)
            
            for child_col in child_cols:
                setScaledCollectionName(col=child_col)
        

        else:
            makeReportPopup("Renaming failed", ["Select any object to change its collection name"])
        
        return {"FINISHED"}
    


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = getTmProps()
        layout   = self.layout
        # layout.use_property_split = True
        
        main_row = layout.row(align=True) 
        
        col = main_row.column(align=True)
        row = col.row()
        row.alignment = "CENTER"
        row.label(text="From")
        row = col.row()
        row.prop(tm_props, "NU_objMplScaleFrom", text="")
       
        col = main_row.column(align=True)
        row = col.row()
        row.alignment = "CENTER"
        row.label(text="To")
        row = col.row()
        row.prop(tm_props, "NU_objMplScaleTo", text="")
       
        col = main_row.column(align=True)
        row = col.row()
        row.alignment = "CENTER"
        row.label(text="Factor")
        row = col.row()
        row.prop(tm_props, "NU_objMplScaleFactor", text="")
        
        row = layout.row(align=True)
        row.prop(tm_props, "CB_objMplScaleRecursive", text="Affect child collections", icon="FOLDER_REDIRECT")


        layout.separator(factor=UI_SPACER_FACTOR)

        collection_name = getActiveCollectionOfSelectedObject().name

        row = layout.row()
        row.scale_y = .5
        row.label(text="New name:")
        row = layout.row()
        row.scale_y = .5
        row.label(text=f"{collection_name}_#SCALE_7to4_x4")

        layout.separator(factor=UI_SPACER_FACTOR)

        generated_files = []
        scale_from     = tm_props.NU_objMplScaleFrom
        scale_to       = tm_props.NU_objMplScaleTo
        scale_step_raw = tm_props.NU_objMplScaleFactor
        scale_step     = 1 / scale_step_raw
        current_scale  = 1

        if not (scale_from > scale_to):
            row = layout.row()
            row.alert = True
            row.label(text="FROM needs to be bigger than TO")
            return
        
        reverse_range = list(reversed(range(scale_to, scale_from+1)))
        for scale in reverse_range:

            raw_col_name = getCollectionNameWithoutScaleSuffix(collection_name)
            generated_files.append([
                f"{raw_col_name}_#{scale}.fbx    %.2f%%" % (current_scale * 100),
                current_scale
            ])
            current_scale -= scale_step

        row = layout.row()
        row.scale_y = .5
        row.label(text="Exported files like:")
        for file in generated_files:
            text, scale = file
            
            is_invalid = scale <= 0.06 # 0.0 == 0 is False for some reason
            text       = text if not is_invalid else text + " - increase factor?"
            
            row = layout.row()
            row.scale_y = .5
            row.alert = is_invalid
            row.label(text=text)


class TM_OT_Items_ToggleLightType(Operator):
    bl_idname = "view3d.tm_togglelighttype"
    bl_description = f"Toggle light type"
    bl_icon = 'ADD'
    bl_label = f"Toggle light type"
    
    light_type: bpy.props.StringProperty()

    def execute(self, context):
        toggleLightType(bpy.context.object, self.light_type)
        return {"FINISHED"}

class TM_OT_Items_ToggleNightOnly(Operator):
    bl_idname = "view3d.tm_togglenightonly"
    bl_description = f"Toggle night only"
    bl_icon = 'ADD'
    bl_label = f"Toggle night only"
    
    night_only: bpy.props.BoolProperty()

    def execute(self, context):
        toggleLightNightOnly(bpy.context.object, self.night_only)
        return {"FINISHED"}

class TM_OT_Items_RenameObject(Operator):
    bl_idname = "wm.tm_renameobject"
    bl_description = f"Rename object"
    bl_icon = 'ADD'
    bl_label = f"Rename object"
    
    obj_name: bpy.props.StringProperty()
    col_name: bpy.props.StringProperty()
    new_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = getTmProps()
        layout   = self.layout
        # layout.use_property_split = True
        
        obj_name = self.obj_name if self.obj_name else self.col_name
        obj_type = "collection" if self.col_name else "object"
        obj_icon = "OUTLINER_COLLECTION" if obj_type == "collection" else "MESH_CUBE"

        row = layout.row()
        row.label(text=f"Rename {obj_type} {obj_name}", icon=obj_icon)
        
        row = layout.row()
        row.prop(self, "new_name", text="Name")


    def execute(self, context):
        if self.obj_name:
            obj = bpy.data.objects[self.obj_name]
            renameObject(obj, self.new_name)
        if self.col_name:
            col = bpy.data.collections[self.col_name]
            renameObject(col, self.new_name)
        return {"FINISHED"}


class TM_PT_ObjectManipulations(Panel):
    bl_label   = "Object Manipulation"
    bl_idname  = "TM_PT_ObjectManipulations"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="OBJECT_DATA")

    def draw(self, context):

        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        tm_props = getTmProps()

        true_icon  = "CHECKMARK"
        false_icon = "CHECKBOX_DEHLT"
        
        current_collection      = getActiveCollectionOfSelectedObject()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"
        
        
        
        # collection properties
        # collection properties
        # collection properties
        col_box = layout.box()

        row = col_box.row()
        col_icon = row.column(align=True)
        col_icon.label(text="", icon="OUTLINER_COLLECTION")
        
        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=f"{current_collection_name}")
        row.operator("wm.tm_renameobject", text="", icon="GREASEPENCIL").col_name = current_collection.name

        col_list = col_box.column(align=True)
        row = col_list.row(align=True)
        row.prop(tm_props, "LI_xml_waypointtype", text="")

        ignore = current_collection.name.startswith(SPECIAL_NAME_PREFIX_IGNORE) if current_collection is not None else False
        row = col_list.row(align=True)
        row.operator(f"view3d.tm_togglecollectionignore", text=f"ignore collection during export", icon=true_icon if ignore else false_icon)
        

        
        # check if collection is a waypoint
        if current_collection is not None:
            if getWaypointTypeOfCollection(current_collection) != "None":
                has_spawn_item   = checkIfCollectionHasObjectWithName(current_collection, prefix=SPECIAL_NAME_PREFIX_SOCKET)
                has_trigger_item = checkIfCollectionHasObjectWithName(current_collection, prefix=SPECIAL_NAME_PREFIX_TRIGGER)

                if has_spawn_item is False:
                    row = col_box.row()
                    row.alert = True
                    row.scale_y = .75
                    row.alignment = "CENTER"
                    row.label(text="Spawn(_socket_) object not found!")
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
                


        
        # object properties
        # object properties
        # object properties
        obj_box = layout.box()

        obj          = None
        obj_name_raw = "Select any object !"
        obj_name= "Select any object !"

        if bpy.context.selected_objects:
            obj           = bpy.context.selected_objects[0]
            obj_name      = obj.name
            # obj_name_raw  = cleanObjNameFromSpecialProps(obj.name)
            obj_name_raw  = obj_name

        ignore     = SPECIAL_NAME_PREFIX_IGNORE in obj_name
        visible    = SPECIAL_NAME_PREFIX_NOTVISIBLE not in obj_name
        collidable = SPECIAL_NAME_PREFIX_NOTCOLLIDABLE not in obj_name 
        trigger    = SPECIAL_NAME_PREFIX_TRIGGER in obj_name
        socket     = SPECIAL_NAME_PREFIX_SOCKET in obj_name
        lod0       = SPECIAL_NAME_SUFFIX_LOD0 in obj_name
        lod1       = SPECIAL_NAME_SUFFIX_LOD1 in obj_name

        
        row = obj_box.row(align=True)
        
        col_icon = row.column(align=True)
        col_icon.label(text="", icon="MESH_CUBE")
        
        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=f"  {obj_name_raw}")
        row.operator("wm.tm_renameobject", text="", icon="GREASEPENCIL").obj_name = obj_name

        col_btns = obj_box.column(align=True)
        
        # ignore
        row = col_btns.row(align=True)
        row.operator(f"view3d.tm_toggleobjectignore", text=f"ignore object during export", icon=true_icon if ignore else false_icon)

        row = col_btns.row(align=True)
        row.operator(f"view3d.tm_toggleobjectlod0",  text=SPECIAL_NAME_SUFFIX_LOD0 + "(high)", icon=true_icon if lod0  else false_icon)
        row.operator(f"view3d.tm_toggleobjectlod1",  text=SPECIAL_NAME_SUFFIX_LOD1 + "(low)", icon=true_icon if lod1  else false_icon)

        if current_collection is not None:
            has_lod0_item = checkIfCollectionHasObjectWithName(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD0)
            has_lod1_item = checkIfCollectionHasObjectWithName(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD1)

            lod0_missing = has_lod0_item and not has_lod1_item
            lod1_missing = has_lod1_item and not has_lod0_item

            if lod1_missing or lod0_missing:
                missing_lod_name = "Lod1" if lod1_missing else "Lod0"
                found_lod_name   = "Lod1" if lod0_missing else "Lod0"
                text             = f"{found_lod_name} also requires {missing_lod_name}"
                row = col_btns.row(align=True)
                row.alert = True
                row.scale_y = .75
                row.alignment = "CENTER"
                row.label(text=text)

        row = col_btns.row(align=True)
        row.operator(f"view3d.tm_toggleobjecttrigger", text=SPECIAL_NAME_PREFIX_TRIGGER, icon=true_icon if trigger else false_icon)
        row.operator(f"view3d.tm_toggleobjectsocket",  text=SPECIAL_NAME_PREFIX_SOCKET,  icon=true_icon if socket  else false_icon)

        if isGameTypeTrackmania2020():
            row = col_btns.row(align=True)
            # row.enabled = not trigger and not socket
            row.operator("view3d.tm_toggleobjectnotvisible",    text=SPECIAL_NAME_PREFIX_NOTVISIBLE,    icon=false_icon if visible    else true_icon)
            row.operator("view3d.tm_toggleobjectnotcollidable", text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE, icon=false_icon if collidable else true_icon)

        

        # lights
        # lights
        # lights
        light_box = layout.box()
        obj = bpy.context.object
        # light_box.label(text="Light properties", icon="OUTLINER_OB_LIGHT")

        col      = light_box.column(align=True)
        is_light = (obj.type == "LIGHT") if obj is not None else False 
        light_box.enabled = is_light
        
        spot_icon  = true_icon if is_light and obj.data.type == "SPOT"  else false_icon
        point_icon = true_icon if is_light and obj.data.type == "POINT" else false_icon
        row = col.row(align=True)
        row.operator("view3d.tm_togglelighttype", text="Spot" , icon=spot_icon ).light_type = "SPOT"
        row.operator("view3d.tm_togglelighttype", text="Point", icon=point_icon).light_type = "POINT"

        use_night_only = (obj.type == "LIGHT") and obj.data.night_only if obj is not None else False
        night_icon    = true_icon if     use_night_only and is_light else false_icon
        nightday_icon = true_icon if not use_night_only and is_light else false_icon
        row = col.row(align=True)
        row.operator("view3d.tm_togglenightonly", text="Day+Night" , icon=nightday_icon).night_only = False
        row.operator("view3d.tm_togglenightonly", text="Night only", icon=night_icon   ).night_only = True

        row = col.row(align=True)
        row.label(text="Color", icon="COLORSET_13_VEC")
        row.prop(bpy.context.object.data, "color",  text="") if is_light else row.label(text="NOT A LIGHT")
        
        row = col.row(align=True)
        row.label(text="Power", icon="LIGHT_SUN")
        row.prop(bpy.context.object.data, "energy", text="") if is_light else row.label(text="NOT A LIGHT")
        
        row = col.row(align=True)
        row.label(text="Radius", icon="LIGHT_POINT")
        row.row().prop(bpy.context.object.data, "shadow_soft_size", text="") if is_light else row.label(text="NOT A LIGHT")


        # multi scale export
        # multi scale export
        # multi scale export
        scale_box = layout.box()
        row = scale_box.row(align=True)
        row.scale_y = .75
        row.label(text="Multi scale export", icon="CON_SIZELIKE")
        row = scale_box.row(align=True)
        col = row.column(align=True)
        col.scale_x = .8
        col.operator("wm.tm_changecollectionscale", text="Add", icon="ADD")
        col = row.column(align=True)
        col.scale_x = 1
        row = col.row(align=True)
        row.operator("view3d.tm_removecollectionscale", text="Remove", icon="REMOVE")
        row.prop(tm_props, "CB_objMplScaleRecursive", text="", icon="FOLDER_REDIRECT")

            


def addSocketItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_SOCKET)

def addTriggerItemToSelectedCollection() -> None:
    importWaypointHelperAndAddToActiveCollection(SPECIAL_NAME_PREFIX_TRIGGER)

def cleanObjNameFromSpecialProps(name: str) -> str:
    new_name = ""
    if name is not None:
        new_name = name
        for prefix in SPECIAL_NAME_PREFIXES:
            if name.lower().startswith(prefix):
                new_name = new_name.replace(prefix, "")
    return new_name


def toggleNameSpecialPrefix(obj:object, prefix:str) -> None:
    """switch prefix if bpy.types (collection, object, etc) .name"""
    name = obj.name
    had_prefix = False

    for special_prefix in SPECIAL_NAME_PREFIXES:
        if name.startswith(prefix):
            had_prefix = True
        name = name.replace(special_prefix, "")
    
    new_name = name
    if not had_prefix:
        new_name = prefix+name

    obj.name = new_name


def toggleNameSpecialSuffix(obj:object, suffix:str) -> None:
    """switch prefix if bpy.types (collection, object, etc) .name"""
    name = obj.name
    had_suffix = False

    for special_suffix in SPECIAL_NAME_SUFFIXES:
        if name.endswith(suffix):
            had_suffix = True
        name = name.replace(special_suffix, "")
    
    new_name = name
    if not had_suffix:
        new_name = name+suffix

    obj.name = new_name


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



def getCollectionNameWithoutScaleSuffix(col_name:str) -> str:
    return col_name.split("_#SCALE")[0]


def setScaledCollectionName(col:bpy.types.Collection, remove:bool=False) -> None: 
    tm_props     = getTmProps()
    scale_from   = tm_props.NU_objMplScaleFrom
    scale_to     = tm_props.NU_objMplScaleTo
    scale_factor = tm_props.NU_objMplScaleFactor

    col_name_new = col.name

    if "_#SCALE" in col_name_new or remove:
        col_name_new = getCollectionNameWithoutScaleSuffix(col.name)
    
    if not remove:
        col_name_new += f"_#SCALE_{scale_from}to{scale_to}_x{scale_factor}"

    col.name = col_name_new

    

def toggleLightType(obj: bpy.types.Object, type: str) -> None:
    obj.data.type = type


def toggleLightNightOnly(obj: bpy.types.Object, value: bool) -> None:
    obj.data.night_only = value


def renameObject(obj: bpy.types, name: str) -> None:
    obj.name = name