
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..utils.Functions import *
from ..utils.Constants import * 



class TM_PT_ObjectManipulations(Panel):
    bl_label   = "Object Manipulation"
    bl_idname  = "TM_PT_ObjectManipulations"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="OBJECT_DATA")

    def draw(self, context):

        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        tm_props = get_global_props()
        
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
        row.label(text=current_collection_name.split("_#SCALE")[0] + "")
        row.operator("wm.tm_renameobject", text="", icon="GREASEPENCIL").col_name = current_collection_name

        if current_collection is None:
            return

        ignore = current_collection_name.startswith(SPECIAL_NAME_PREFIX_IGNORE)

        col_list = col_box.column(align=True)
        row = col_list.row(align=True)
        row.prop(tm_props, "LI_xml_waypointtype", text="")
        row.operator(f"view3d.tm_togglecollectionignore", text=f"Ignore Export", icon=ICON_TRUE if ignore else ICON_FALSE)

        
        # helpers if waypoint invalid
        # helpers if waypoint invalid
        # helpers if waypoint invalid
        if get_waypointtype_of_collection(current_collection) != "None":
            has_spawn_item   = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_SOCKET)
            has_trigger_item = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_TRIGGER)
            waypoint_type    = getWaypointTypeOfActiveObjectsCollection()
            
            trigger_missing = has_trigger_item is False
            spawn_missing   = has_spawn_item   is False

            if trigger_missing or spawn_missing:
                err_box = col_box.box()
                err_box.alert = True

                if spawn_missing:
                    row = err_box.row()
                    row.scale_y = .75
                    row.label(text= waypoint_type + " requires a _socket_ object!")
                    row = err_box.row(align=True)
                    row.operator("view3d.tm_createsocketitemincollection", text="Add spawn", icon="ADD")
                    row.prop(tm_props, "LI_items_cars", text="")
                                    
                if has_trigger_item is False:
                    row = err_box.row()
                    row.scale_y = .75
                    row.label(text=waypoint_type + " requires a _trigger_ object!")
                    row = err_box.row()
                    row.scale_y = .75
                    row.label(text="_trigger_ should not have materials and uv maps")
                    row = err_box.row(align=True)
                    row.operator("view3d.tm_createtriggeritemincollection", text="Add trigger", icon="ADD")
                    row.prop(tm_props, "LI_items_triggers", text="")
            
        # col_box.separator(factor=.2)
        active_uvlayer_is_basematerial = True
        objs    = getAllVisibleMeshObjsOfCol(current_collection)
        if len(objs) > 0:
            base_uv = objs[0].data.uv_layers.get(UV_LAYER_NAME_BASEMATERIAL)
            if base_uv:
                active_uvlayer_is_basematerial = base_uv.active is True



        # multi scale export
        # multi scale export
        # multi scale export
        remove_scale = "_#SCALE" in current_collection_name
        multi_scale_icon = ICON_TRUE if remove_scale else ICON_FALSE
        text = ("Remove" if remove_scale else "Add") + " Multi Scale Export"

        row = col_box.row(align=True)
        row.operator("wm.tm_changecollectionscale", text=text, icon=multi_scale_icon).remove_scale = remove_scale
        row.prop(tm_props, "CB_objMplScaleRecursive", text="", icon="FOLDER_REDIRECT")


        # basematerial / lightmap
        # basematerial / lightmap
        # basematerial / lightmap
        icon_basematerial = "HIDE_OFF" if     active_uvlayer_is_basematerial else "HIDE_ON"
        icon_lightmap     = "HIDE_OFF" if not active_uvlayer_is_basematerial else "HIDE_ON"
        col = col_box.column(align=True)
        row = col.row(align=True)
        # row.scale_y = .5
        row = col.row(align=False)
        uv_row = row.column(align=True).row(align=True)
        uv_row.operator("view3d.tm_showuvmap", text="BaseMaterial", icon=icon_basematerial).uv_name = UV_LAYER_NAME_BASEMATERIAL
        uv_row.operator("view3d.tm_edituvmap", text="",             icon="GREASEPENCIL"   ).uv_name = UV_LAYER_NAME_BASEMATERIAL
        uv_row = row.column(align=True).row(align=True)
        uv_row.operator("view3d.tm_showuvmap", text="LightMap",     icon=icon_lightmap ).uv_name = UV_LAYER_NAME_LIGHTMAP
        uv_row.operator("view3d.tm_edituvmap", text="",             icon="GREASEPENCIL").uv_name = UV_LAYER_NAME_LIGHTMAP
        # row = col.row(align=True)
        # row.prop(tm_props, "LI_workspaces", text="")



        
        # object properties
        # object properties
        # object properties
        obj_box = layout.box()

        obj          = None
        obj_name_raw = "Select any object !"
        obj_name     = "Select any object !"

        if bpy.context.selected_objects:
            obj           = bpy.context.selected_objects[0]
            obj_name      = obj.name
            # obj_name_raw  = cleanObjNameFromSpecialProps(obj.name)
            obj_name_raw  = obj_name

        is_light   = (obj.type == "LIGHT") if obj is not None else False 

        doublesided= SPECIAL_NAME_SUFFIX_DOUBLESIDED in obj_name
        ignore     = SPECIAL_NAME_PREFIX_IGNORE in obj_name
        visible    = SPECIAL_NAME_PREFIX_NOTVISIBLE not in obj_name
        collidable = SPECIAL_NAME_PREFIX_NOTCOLLIDABLE not in obj_name 
        trigger    = SPECIAL_NAME_PREFIX_TRIGGER in obj_name
        socket     = SPECIAL_NAME_PREFIX_SOCKET in obj_name
        lod0       = SPECIAL_NAME_SUFFIX_LOD0 in obj_name
        lod1       = SPECIAL_NAME_SUFFIX_LOD1 in obj_name
        is_origin  = SPECIAL_NAME_INFIX_ORIGIN in obj_name

        
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
        row.operator(f"view3d.tm_toggleobjectignore", text=f"Ignore Export", icon=ICON_TRUE if ignore      else ICON_FALSE)
        row.operator(f"view3d.tm_toggle_origin",      text=f"_origin_",  icon=ICON_TRUE if is_origin   else ICON_FALSE)

        if not is_light:


            if current_collection is not None:
                has_lod0_item = check_collection_has_obj_with_fix(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD0)
                has_lod1_item = check_collection_has_obj_with_fix(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD1)

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
            row.operator(f"view3d.tm_toggleobjecttrigger", text=SPECIAL_NAME_PREFIX_TRIGGER, icon=ICON_TRUE if trigger else ICON_FALSE)
            row.operator(f"view3d.tm_toggleobjectsocket",  text=SPECIAL_NAME_PREFIX_SOCKET,  icon=ICON_TRUE if socket  else ICON_FALSE)

            row = col_btns.row(align=True)
            row.operator(f"view3d.tm_toggleobjectlod0",  text=SPECIAL_NAME_SUFFIX_LOD0 + "(high)", icon=ICON_TRUE if lod0  else ICON_FALSE)
            row.operator(f"view3d.tm_toggleobjectlod1",  text=SPECIAL_NAME_SUFFIX_LOD1 + "(low)", icon=ICON_TRUE if lod1  else ICON_FALSE)


            if isGameTypeTrackmania2020():
                row = col_btns.row(align=True)
                # row.enabled = not trigger and not socket
                row.operator("view3d.tm_toggleobjectnotvisible",    text=SPECIAL_NAME_PREFIX_NOTVISIBLE,    icon=ICON_FALSE if visible    else ICON_TRUE)
                row.operator("view3d.tm_toggleobjectnotcollidable", text=SPECIAL_NAME_PREFIX_NOTCOLLIDABLE, icon=ICON_FALSE if collidable else ICON_TRUE)

            # obj_box.separator(factor=UI_SPACER_FACTOR)
            if obj and obj.type == "MESH":
                col = obj_box.column(align=True)
                row = col.row(align=True)
                editmode = obj.mode == "EDIT"
                row.operator("object.shade_smooth" if not editmode else "mesh.faces_shade_smooth")
                row.operator("object.shade_flat"   if not editmode else "mesh.faces_shade_flat")
                row= col.row(align=True)
                innercol = row.column(align=True)
                innercol.scale_x = 1.2
                innercol.prop(obj.data, "use_auto_smooth", toggle=True, icon=ICON_TRUE if obj.data.use_auto_smooth else ICON_FALSE)
                innercol = row.column(align=True)
                innercol.prop(obj.data, "auto_smooth_angle", text="")

        
        

        # lights
        # lights
        # lights
        if is_light:
            light_box = layout.box()

            col      = light_box.column(align=True)

            light_box.enabled = is_light
            
            is_spotlight  = obj.data.type == "SPOT"
            is_pointlight = obj.data.type == "POINT"

            spot_icon  = ICON_TRUE if is_light and is_spotlight  else ICON_FALSE
            point_icon = ICON_TRUE if is_light and is_pointlight else ICON_FALSE
            row = col.row(align=True)
            row.operator("view3d.tm_togglelighttype", text="Spot" , icon=spot_icon ).light_type = "SPOT"
            row.operator("view3d.tm_togglelighttype", text="Point", icon=point_icon).light_type = "POINT"

            use_night_only= is_light and obj.data.night_only
            night_icon    = ICON_TRUE if     use_night_only and is_light else ICON_FALSE
            nightday_icon = ICON_TRUE if not use_night_only and is_light else ICON_FALSE
            row = col.row(align=True)
            row.operator("view3d.tm_togglenightonly", text="Day+Night" , icon=nightday_icon).night_only = False
            row.operator("view3d.tm_togglenightonly", text="Night only", icon=night_icon   ).night_only = True

            row = col.row(align=True)
            row.label(text="Color", icon="COLORSET_13_VEC")
            row.prop(bpy.context.object.data, "color",  text="") 
            
            row = col.row(align=True)
            row.label(text="Power", icon="LIGHT_SUN")
            row.prop(bpy.context.object.data, "energy", text="") 
            
            row = col.row(align=True)
            row.label(text="Radius", icon="LIGHT_POINT")
            row.row().prop(bpy.context.object.data, "shadow_soft_size", text="") 

            if is_spotlight:
                row = col.row(align=True)
                row.label(text="Outer angle", icon="LIGHT_SPOT")
                row.row().prop(bpy.context.object.data, "spot_size", text="") 

                row = col.row(align=True)
                row.label(text="Inner angle", icon="DOT")
                row.row().prop(bpy.context.object.data, "spot_blend", text="", slider=True) 

                col.row().prop(bpy.context.object.data, "show_cone", toggle=True) 



