

import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 



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


# later... lightmap ??
class TM_OT_Items_ObjectManipulationToggleDoublesided(Operator):
    bl_idname = "view3d.tm_toggledoublesided"
    bl_description = f"Toggle {SPECIAL_NAME_SUFFIX_DOUBLESIDED} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_SUFFIX_DOUBLESIDED}"
   
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            toggleNameSpecialSuffix(bpy.context.selected_objects[0], SPECIAL_NAME_SUFFIX_DOUBLESIDED)
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
            toggleNameSpecialPrefix(get_active_collection_of_selected_object(), SPECIAL_NAME_PREFIX_IGNORE)
        return {"FINISHED"}


class TM_OT_Items_ObjectManipulationToggleOrigin(Operator):
    bl_idname = "view3d.tm_toggle_origin"
    bl_description = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN} on selected object"
    bl_icon = 'ADD'
    bl_label = f"Toggle {SPECIAL_NAME_INFIX_ORIGIN}"
   
    def execute(self, context):
        toggle_infix(bpy.context.selected_objects[0], SPECIAL_NAME_INFIX_ORIGIN)
        return {"FINISHED"}



class TM_OT_Items_ObjectManipulationChangeCollectionScale(Operator):
    bl_idname = "wm.tm_changecollectionscale"
    bl_description = "Set custom multi scale for collection"
    bl_icon = 'ADD'
    bl_label = "Set custom multi scale for collection"
   
    remove_scale: bpy.props.BoolProperty(False)

    def execute(self, context):
        col      = get_active_collection_of_selected_object()
        tm_props = get_global_props()

        scale_from     = tm_props.NU_objMplScaleFrom
        scale_to       = tm_props.NU_objMplScaleTo
        scale_step     = tm_props.NU_objMplScaleFactor

        max_step = 1
        steps    = 1 / scale_step
        scales   = scale_from - scale_to
        
        last_step   = max_step - (steps * scales) 
        is_invalid  = last_step <= 0.06 # if scale <= 0, object will be invisible ingame

        if is_invalid:
            show_report_popup("Setting scales failed", [
                f"Invalid values, atleast one scale is lower than 0!",
                f"Last step: {last_step}"
                ])
            return {"FINISHED"}


        if col is not None:
            setScaledCollectionName(col, remove=self.remove_scale)
        else:
            show_report_popup("Renaming failed", ["Select any object to change its collection name"])
        
        return {"FINISHED"}
    


    def invoke(self, context, event):
        if self.remove_scale:
            return self.execute(context)
        else:
            return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = get_global_props()
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
        row.prop(tm_props, "CB_objMplScaleRecursive", text="Affect Child Collections", icon=ICON_RECURSIVE)


        layout.separator(factor=UI_SPACER_FACTOR)

        collection      = get_active_collection_of_selected_object()
        generated_files = []
        scale_from      = tm_props.NU_objMplScaleFrom
        scale_to        = tm_props.NU_objMplScaleTo
        scale_step_raw  = tm_props.NU_objMplScaleFactor
        scale_step      = 1 / scale_step_raw
        current_scale   = 1
        raw_col_name    = getCollectionNameWithoutScaleSuffix(collection)

        row = layout.row()
        row.scale_y = .5
        row.label(text="New name:")
        row = layout.row()
        row.scale_y = .5
        row.label(text=f"{collection.name}_#SCALE_{scale_from}to{scale_to}_x{scale_step_raw}")

        layout.separator(factor=UI_SPACER_FACTOR)


        if not (scale_from > scale_to):
            row = layout.row()
            row.alert = True
            row.label(text="FROM needs to be bigger than TO")
            return
        
        reverse_range = list(reversed(range(scale_to, scale_from+1)))
        for scale in reverse_range:

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


class TM_OT_Items_EditUVMap(Operator):
    bl_idname = "view3d.tm_edituvmap"
    bl_description = f"Edit uv map"
    bl_icon = 'ADD'
    bl_label = f"Edit uv map"
    
    uv_name: bpy.props.StringProperty()

    def execute(self, context):
        col = get_active_collection_of_selected_object()
        editUVMap(col, self.uv_name)
        return {"FINISHED"}


class TM_OT_Items_ShowUVMap(Operator):
    bl_idname = "view3d.tm_showuvmap"
    bl_description = f"Show uv map"
    bl_icon = 'ADD'
    bl_label = f"Show uv map"
    
    uv_name: bpy.props.StringProperty()

    def execute(self, context):
        col = get_active_collection_of_selected_object()
        showUVMap(col, self.uv_name)
        return {"FINISHED"}


class TM_OT_Items_SetItemXMLTemplateOfCollection(Operator):
    bl_idname = "view3d.tm_set_itemxml_template_of_collection"
    bl_description = f"Show uv map"
    bl_icon = 'ADD'
    bl_label = f"Show uv map"

    remove_template: bpy.props.BoolProperty(False)

    def execute(self, context):
        col = get_active_collection_of_selected_object()
        template = get_global_props().LI_xml_item_template_to_add
        template = template if not self.remove_template else ""
        set_itemxml_template_of_collection(col, template)
        return {"FINISHED"}

    def invoke(self, context, event):
        if self.remove_template:
            return self.execute(context)
        else:
            return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = get_global_props()
        layout   = self.layout

        row = layout.row()
        row.prop(tm_props, "LI_xml_item_template_to_add")



class TM_OT_Items_RenameObject(Operator):
    bl_idname = "wm.tm_renameobject"
    bl_description = f"Rename"
    bl_icon = 'ADD'
    bl_label = f"Rename"
    
    obj_name: bpy.props.StringProperty()
    col_name: bpy.props.StringProperty()
    new_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        tm_props = get_global_props()
        layout   = self.layout
        # layout.use_property_split = True
        
        obj_name = self.obj_name if self.obj_name else self.col_name
        obj_type = "collection" if self.col_name else "object"
        obj_icon = ICON_COLLECTION if obj_type == "collection" else ICON_OBJECT

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


def toggle_infix(obj: bpy.types.Object, infix: str) -> None:
    if infix in obj.name:
        obj.name = obj.name.replace(infix, "")
    else:
        prefix = "".join(re.findall(r"^_\w+_", obj.name, re.IGNORECASE ))

        if prefix:
            obj.name = obj.name.replace(prefix, prefix + infix)
        else:
            obj.name = infix + obj.name

        

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
    collection   = get_active_collection_of_selected_object()
    fbx_filepath = ""
    pre_selected_objects = bpy.context.selected_objects.copy()

    if collection is None:
        return
    
    if obj_type == SPECIAL_NAME_PREFIX_TRIGGER:
        fbx_filepath = get_templates_trigger()
    
    elif obj_type == SPECIAL_NAME_PREFIX_SOCKET:
        fbx_filepath = get_templates_car()

    else:
        show_report_popup(f"failed to import a obj of {obj_type=}")
        return

    fbx_filepath = fix_slash(fbx_filepath)
    import_at    = bpy.context.selected_objects[0].location
    collection   = get_active_collection_of_selected_object()

    deselect_all_objects()

    importFBXFile(fbx_filepath)
    imported_objs = bpy.context.selected_objects

    for object in imported_objs:
        # collection.objects.link(object)
        object.location = import_at

    for object in pre_selected_objects:
        object.select_set(True)



def getCollectionNameWithoutScaleSuffix(coll:bpy.types.Collection) -> str:
    return coll.name.split("_#SCALE")[0]


def setScaledCollectionName(col:bpy.types.Collection, remove:bool=False) -> None: 
    tm_props        = get_global_props()
    scale_from      = tm_props.NU_objMplScaleFrom
    scale_to        = tm_props.NU_objMplScaleTo
    scale_factor    = tm_props.NU_objMplScaleFactor
    affect_children = tm_props.CB_objMplScaleRecursive

    collections_to_scale = set()
    collections_to_scale.add(col)

    if affect_children:
        for obj in col.all_objects:
            for child_col in obj.users_collection:
                collections_to_scale.add(child_col)


    for col in collections_to_scale:
        col_name_new = col.name

        if "_#SCALE" in col_name_new or remove:
            col_name_new = col.name.split("_#SCALE")[0]
        
        if not remove:
            col_name_new += f"_#SCALE_{scale_from}to{scale_to}_x{scale_factor}"

        col.name = col_name_new





    

def toggleLightType(obj: bpy.types.Object, type: str) -> None:
    obj.data.type = type


def toggleLightNightOnly(obj: bpy.types.Object, value: bool) -> None:
    obj.data.night_only = value


def renameObject(obj: bpy.types, name: str) -> None:
    obj.name = name



def showUVMap(col: bpy.types.Collection, uv_name: str) -> None:
    objs = get_meshes_which_require_uvmaps(col)

    if not objs:
        return show_report_popup(f"Uvlayer not found", f"No object has uvlayer with name '{uv_name}'")
    
    for obj in objs:

        addBasematerialAndLightmap(obj)
        uvs = obj.data.uv_layers
        preferred_uv = uvs.get(uv_name)
        
        if preferred_uv:
            preferred_uv.active = True



def addBasematerialAndLightmap(obj: bpy.types.Object) -> None:
    uvs = obj.data.uv_layers

    is_lightmap     = lambda uv: uv.name.lower() == UV_LAYER_NAME_LIGHTMAP
    is_basematerial = lambda uv: uv.name.lower() == UV_LAYER_NAME_BASEMATERIAL

    for uvlayer in uvs:
        # uvlayer name is case sensitive, correnct name 
        if is_lightmap(uvlayer):     
            uvlayer.name = UV_LAYER_NAME_LIGHTMAP 
        if is_basematerial(uvlayer): 
            uvlayer.name = UV_LAYER_NAME_BASEMATERIAL 

    
    if len(uvs) == 0: uvs.new(do_init=True)
    if len(uvs) == 1: uvs.new(do_init=True)

    for i, uvlayer in enumerate(uvs):
        if i == 0:
            if not is_basematerial(uvlayer):
                uvlayer.name = UV_LAYER_NAME_BASEMATERIAL
        if i == 1:
            if not is_lightmap(uvlayer):
                uvlayer.name = UV_LAYER_NAME_LIGHTMAP
        if i > 1:
            break




def editUVMap(col: bpy.types.Collection, uv_name: str) -> None:
    objs = get_meshes_which_require_uvmaps(col)

    if not objs:
        return show_report_popup(f"No object selected", f"Select normal mesh objects... ")
    
    deselect_all_objects()
    for obj in objs:
        select_obj(obj)

    preferred_workspace_name = "UV Editing"
    workspace = bpy.data.workspaces.get(preferred_workspace_name)
    
    if workspace is not None:
        bpy.context.window.workspace = workspace

    else: # import workspace from blend file and switch to it
        workspace_path = get_addon_assets_blendfiles_path() + "uvedit_workspace.blend"
        bpy.ops.workspace.append_activate(
            idname=preferred_workspace_name, 
            filepath=workspace_path)
    
    showUVMap(col, uv_name)
    editmode()



def set_itemxml_template_of_collection(col: bpy.types.Collection, template: str) -> None:
    col.tm_itemxml_template = template