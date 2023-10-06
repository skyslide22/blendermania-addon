
import bpy
from bpy.types import Panel
from bpy.types import Operator

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..properties.Functions import ERROR_ENUM_ID
from ..utils.Functions import *
from ..utils.Constants import * 



class TM_PT_ObjectManipulations(Panel):
    bl_label   = "Manipulations"
    bl_idname  = "TM_PT_ObjectManipulations"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    
    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="TOOL_SETTINGS")


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Manipulation Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can manipulate the behavior of collections and objects",
            "",
            "Collections:",
            "-> f.e. checkpoint(blue icon) or another waypoint type",
            "-> 'NICE', <! TODO !> aka NadeoImporterCommunityEdition will allow you to use non official features like gates",
            "-> 'No Export', the collection will not be exported",
            "-> Multi-Scale, export in different sizes, child collections optionally too",
            "-> Use a Item-XML template(add in export panel), those are the placement settings in the editor",
            "-> Display specific uv layers for the entire collection, or edit them for all",
            "",
            "Objects:",
            "-> 'No Export', the object will not be exported, but other objects will!",
            "-> 'Item', the object can be exported by itself, a collection is not required",
            "-> 'Icon Dummy', the object will be used for icon only",
            "-> 'Origin', the object will be the origin of the collection",
            "----> If none is set, the first object found in the collection will be the origin",
            "-> waypoint related object",
            "----> 'Trigger' should be a mesh without materials and uv maps (drive through = checkpoint triggered)",
            "----> 'Spawnpoint' can be anything, its location and rotation data will be used for respawns",
            "-> 'Not Visible' will make your object invisible, it will still have a hitbox!",
            "-> 'Not Collidable' will make your object act like a ghost, no collisions",
            "-> 'Highpoly' or 'Lowpoly'",
            "----> Need to be used together on 2 different objects in the collection",
            "----> Highpoly object will be rendered when you are in front of it",
            "----> Lowpoly object will be rendered when you are far away, (low quality version of you object)",
            "-> 'Shade Smooth' will make your object look smooth between angles",
            "-> 'Shade Flat' will make your object look flat, sharp corners",
            "-> 'Auto Smooth' will make your object look smooth but limits it to an angle",
            "-> 'X Y Z' Lock the movement, rotation and scale of your object (only in blender)",
        )


    def draw(self, context):
        pass



            


class TM_PT_Items_ObjectManipulation(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_ObjectManipulation"
    bl_parent_id = "TM_PT_ObjectManipulations"
    # endregion


    def draw_header(self, context):
        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        
        objs = bpy.context.selected_objects
        obj_name = objs[0].name if len(objs) > 0 else "Select any object !"

        row = layout.row()

        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=obj_name, icon=ICON_OBJECT)


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
    
        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).obj_name = bpy.context.object.name        


    def draw(self, context):
        layout = self.layout
        tm_props        = get_global_props()

        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        if current_collection is None:
            return

        obj          = None
        obj_name_raw = "Select any object !"
        obj_name     = "Select any object !"

        if bpy.context.selected_objects:
            obj           = bpy.context.selected_objects[0]
            obj_name      = obj.name
            # obj_name_raw  = cleanObjNameFromSpecialProps(obj.name)
            obj_name_raw  = obj_name

        is_light   = (obj.type == "LIGHT") if obj is not None else False 

        doublesided     = SPECIAL_NAME_SUFFIX_DOUBLESIDED in obj_name
        is_item         = SPECIAL_NAME_PREFIX_ITEM in obj_name
        is_ignored      = SPECIAL_NAME_PREFIX_IGNORE in obj_name
        is_icon_only    = SPECIAL_NAME_PREFIX_ICON_ONLY in obj_name
        is_notvisible   = SPECIAL_NAME_PREFIX_NOTVISIBLE in obj_name
        is_notcollidable= SPECIAL_NAME_PREFIX_NOTCOLLIDABLE in obj_name 
        is_trigger      = SPECIAL_NAME_PREFIX_TRIGGER in obj_name
        is_socket       = SPECIAL_NAME_PREFIX_SOCKET in obj_name
        is_gate         = SPECIAL_NAME_PREFIX_GATE in obj_name
        is_lod0         = SPECIAL_NAME_SUFFIX_LOD0 in obj_name
        is_lod1         = SPECIAL_NAME_SUFFIX_LOD1 in obj_name
        is_origin       = SPECIAL_NAME_INFIX_ORIGIN in obj_name
        is_pivot        = SPECIAL_NAME_INFIX_PIVOT in obj_name

        
    
        obj_box = layout#.box()
    

        row = obj_box.row(align=True)
        row.operator(f"view3d.tm_toggleobjectignore",   
                     text=f"No Export",   
                     icon_value=get_addon_icon("CANCEL"), 
                     depress=is_ignored)
        row.operator(f"view3d.tm_toggleobjectitem",   
                     text=f"Item",   
                     icon=ICON_EXPORT, 
                     depress=is_item)
        row.operator(f"view3d.tm_toggleobjecticononly", 
                     text=f"Icon Dummy",  
                     icon=ICON_IMAGE_DATA, 
                     depress=is_icon_only)
        
        row = obj_box.row(align=True)
        row.operator(f"view3d.tm_toggle_origin",        
                     text=f"Origin",   
                     icon=ICON_ORIGIN, 
                     depress=is_origin)
        row.operator(f"view3d.tm_toggle_pivot",         
                     text=f"Pivot",    
                     icon=ICON_PIVOTS, 
                     depress=is_pivot)
        

        if not is_light:

            row = obj_box.row(align=True)

            if is_game_trackmania2020():
                row.operator(f"view3d.tm_toggle_gate",  
                            text="Gate",  
                            icon="OUTLINER_OB_FORCE_FIELD", 
                            depress=is_gate)
                
            row.operator(f"view3d.tm_toggleobjecttrigger", 
                        text="Trigger", 
                        icon_value=get_addon_icon("CAR_TRIGGER"), 
                        depress=is_trigger)
            row.operator(f"view3d.tm_toggleobjectsocket",  
                        text="Spawn",  
                        icon_value=get_addon_icon("CAR_SPAWN"), 
                        depress=is_socket)
            
                
                
            

            # warn if waypoint is default and trigger, socket are used
            if tm_props.CB_allow_complex_panel_drawing:
                if is_trigger or is_socket:
                    waypoint = get_waypointtype_of_collection(current_collection)
                    if waypoint not in WAYPOINT_VALID_NAMES:
                        row = obj_box.row(align=True)
                        row.alert = True
                        row.alignment = "CENTER"
                        row.label(text="Since this collection is not a waypoint,")
                        row = obj_box.row(align=True)
                        row.alert = True
                        row.alignment = "CENTER"
                        row.label(text="triggers (_trigger_) & spawns (_socket_)")
                        row = obj_box.row(align=True)
                        row.alert = True
                        row.alignment = "CENTER"
                        row.label(text="will have no effect")


            if is_game_trackmania2020():
                row = obj_box.row(align=True)
                # row.enabled = not trigger and not socket
                row.operator("view3d.tm_toggleobjectnotvisible",    text="Not Visible",    icon=ICON_HIDDEN, depress=is_notvisible)
                row.operator("view3d.tm_toggleobjectnotcollidable", text="Not Collidable", icon=ICON_IGNORE, depress=is_notcollidable)

            col = obj_box.column(align=True)
            row = col.row(align=True)
            row.operator(f"view3d.tm_toggleobjectlod0",  text="Highpoly", icon_value=get_addon_icon("LOD_HIGHPOLY") , depress=is_lod0)
            row.operator(f"view3d.tm_toggleobjectlod1",  text="Lowpoly",  icon_value=get_addon_icon("LOD_LOWPOLY")  , depress=is_lod1)

            if current_collection is not None:
                has_lod0_item = check_collection_has_obj_with_fix(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD0)
                has_lod1_item = check_collection_has_obj_with_fix(current_collection, suffix=SPECIAL_NAME_SUFFIX_LOD1)

                lod0_missing = has_lod1_item and not has_lod0_item
                lod1_missing = has_lod0_item and not has_lod1_item

                if lod1_missing or lod0_missing:
                    missing_lod_name = "Lowpoly (_Lod1)" if lod1_missing else "Highpoly (_Lod0)"
                    found_lod_name   = "Lowpoly (_Lod1)" if lod0_missing else "Highpoly (_Lod0)"
                    row = col.row(align=True)
                    row.alert = True
                    # row.scale_y = .75
                    row.alignment = "CENTER"
                    row.label(text=f"{found_lod_name} wont work until you")
                    row = col.row(align=True)
                    row.alert = True
                    # row.scale_y = .75
                    row.alignment = "CENTER"
                    row.label(text=f"mark another object as {missing_lod_name}")
                    row = col.row(align=True)
                    row.alignment = "CENTER"
                    row.label(text="Using _Lod(s) is optional!")

            # obj_box.separator(factor=UI_SPACER_FACTOR)
            if obj and obj.type == "MESH":
                col = obj_box.column(align=True)
                row = col.row(align=True)
                editmode = obj.mode == "EDIT"
                row.operator("object.shade_smooth" if not editmode else "mesh.faces_shade_smooth", icon=ICON_SMOOTH)
                row.operator("object.shade_flat"   if not editmode else "mesh.faces_shade_flat", icon=ICON_FLAT)
                row= col.row(align=True)
                innercol = row.column(align=True)
                innercol.scale_x = 1.2
                innercol.prop(obj.data, "use_auto_smooth", toggle=True, icon=ICON_FLAT_SMOOTH)
                innercol = row.column(align=True)
                innercol.prop(obj.data, "auto_smooth_angle", text="")

        
        
            col = obj_box.column(align=False)
            row = col.row(align=True)

            split = row.split(factor=0.25, align=True)

            text_row = split.row(align=True)
            text_row.alignment = "CENTER"
            text_row.label()

            text_row = split.row(align=True)
            text_row.alignment = "CENTER"
            text_row.label(text="X", icon=ICON_AXIS_X)

            text_row = split.row(align=True)
            text_row.alignment = "CENTER"
            text_row.label(text="Y", icon=ICON_AXIS_Y)
            
            text_row = split.row(align=True)
            text_row.alignment = "CENTER"
            text_row.label(text="Z", icon=ICON_AXIS_Z)

            row = col.row(align=False)
            row.prop(obj, "lock_location", text="Location")
            row = col.row(align=False)
            row.prop(obj, "lock_rotation", text="Rotation")
            row = col.row(align=False)
            row.prop(obj, "lock_scale", text="Scale")

        # lights
        # lights
        # lights
        if is_light:
            light_box = layout.box()
            light_box.enabled = is_light
            
            col = light_box.column(align=True)
            is_spotlight  = obj.data.type == "SPOT"
            is_pointlight = obj.data.type == "POINT"


            row = col.row(align=True)
            row.operator("view3d.tm_togglelighttype", text="Spot" , icon=ICON_LIGHT_SPOT , depress=is_spotlight).light_type = "SPOT"
            row.operator("view3d.tm_togglelighttype", text="Point", icon=ICON_LIGHT_POINT, depress=is_pointlight).light_type = "POINT"



            row = col.row(align=True)
            row.operator("view3d.tm_togglenightonly", text="Day+Night" , icon=ICON_DAYTIME).night_only = False
            row.operator("view3d.tm_togglenightonly", text="Night only", icon=ICON_DAYTIME).night_only = True

            row = col.row(align=True)
            row.label(text="Color", icon=ICON_LIGHT_COLOR)
            row.prop(bpy.context.object.data, "color",  text="") 
            
            row = col.row(align=True)
            row.label(text="Power", icon=ICON_LIGHT_POWER)
            row.prop(bpy.context.object.data, "energy", text="") 
            
            row = col.row(align=True)
            row.label(text="Radius", icon=ICON_LIGHT_RADIUS)
            row.row().prop(bpy.context.object.data, "shadow_soft_size", text="") 

            if is_spotlight:
                row = col.row(align=True)
                row.label(text="Outer angle", icon=ICON_LIGHT_RADIUS_OUT)
                row.row().prop(bpy.context.object.data, "spot_size", text="") 

                row = col.row(align=True)
                row.label(text="Inner angle", icon=ICON_LIGHT_RADIUS_IN)
                row.row().prop(bpy.context.object.data, "spot_blend", text="", slider=True) 

                col.row().prop(bpy.context.object.data, "show_cone", toggle=True) 
        
        layout.separator(factor=2)



class TM_PT_Items_CollectionManipulation(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_CollectionManipulation"
    bl_parent_id = "TM_PT_ObjectManipulations"
    # endregion


    def draw_header(self, context):
        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row = layout.row()

        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=""+current_collection_name.split("_#SCALE")[0] + "", icon=ICON_COLLECTION)


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
    
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).col_name = current_collection_name        


    def draw(self, context):
        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        tm_props = get_global_props()
        
        current_collection      = get_active_collection_of_selected_object()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        if current_collection is None:
            return

        col_box = layout#.box()

        row = col_box.row(align=True)
        row.prop(tm_props, "LI_xml_waypointtype", text="Type")

        
        # helpers if waypoint invalid
        # helpers if waypoint invalid
        # helpers if waypoint invalid
        if get_waypointtype_of_collection(current_collection) != "None":
            has_spawn_item   = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_SOCKET)
            has_trigger_item = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_TRIGGER)
            waypoint_type    = get_waypoint_of_active_objects_collection()
            
            trigger_missing = has_trigger_item is False
            spawn_missing   = has_spawn_item   is False

            if trigger_missing or spawn_missing:
                err_box = col_box.box()
                err_box.alert = True

                if spawn_missing:
                    row = err_box.row()
                    row.scale_y = .75
                    row.label(text= waypoint_type + " requires a spawnpoint (_socket_)!")
                    row = err_box.row(align=True)
                    row.operator("view3d.tm_createsocketitemincollection", text="Add spawn", icon=ICON_ADD)
                    row.prop(tm_props, "LI_items_cars", text="")
                                    
                if has_trigger_item is False:
                    row = err_box.row()
                    row.scale_y = .5
                    row.label(text=waypoint_type + " requires a trigger (_trigger_)!")
                    row = err_box.row()
                    row.scale_y = .5
                    row.label(text="_trigger_ must not have materials")
                    row = err_box.row()
                    row.scale_y = .5
                    row.label(text="_trigger_ must not have uv maps")
                    row = err_box.row()
                    row.scale_y = .5
                    row.label(text="_trigger_ must be a mesh object")
                    row = err_box.row(align=True)
                    row.operator("view3d.tm_createtriggeritemincollection", text="Add trigger", icon=ICON_ADD)
                    row.prop(tm_props, "LI_items_triggers", text="")
            
        # col_box.separator(factor=.2)
        active_uvlayer_is_basematerial = True
        objs_with_uvmaps    = get_meshes_which_require_uvmaps(current_collection)
        if len(objs_with_uvmaps) > 0:
            base_uv = objs_with_uvmaps[0].data.uv_layers.get(UV_LAYER_NAME_BASEMATERIAL)
            if base_uv:
                active_uvlayer_is_basematerial = base_uv.active is True




        # ignore & nice
        # ignore & nice
        # ignore & nice
        ignore = current_collection_name.startswith(SPECIAL_NAME_PREFIX_IGNORE)
        nice   = current_collection_name.startswith(SPECIAL_NAME_PREFIX_NICE)

        row = col_box.row()
        row.operator(f"view3d.tm_togglecollectionnice",   text=f"NICE",      icon="ORPHAN_DATA", depress=nice)
        row.operator(f"view3d.tm_togglecollectionignore", text=f"No Export", icon_value=get_addon_icon("CANCEL"), depress=ignore)





        # multi scale export
        # multi scale export
        # multi scale export
        remove_scale = "_#SCALE" in current_collection_name
        multi_scale_icon = ICON_CHECKED if remove_scale else ICON_UNCHECKED
        # text = ("Remove" if remove_scale else "Add") + " Multi Scale Export"
        text = "Multi Scale Exporting"

        row = col_box.row(align=True)
        row.operator("wm.tm_changecollectionscale", text=text, icon=ICON_SCALE, depress=remove_scale).remove_scale = remove_scale
        row.prop(tm_props, "CB_objMplScaleRecursive", text="", icon=ICON_RECURSIVE)

        # col_itemxml_template = tm_props.LI_xml_item_template_to_add

        col_itemxml_template = current_collection.tm_itemxml_template
        if col_itemxml_template:
            row = col_box.row(align=True)
            col = row.column()
            col.label(text="Item XML Template:")
            col = row.column()
            col.enabled = False
            col.label(text=col_itemxml_template)
            col = row.column()
            col.operator("view3d.tm_set_itemxml_template_of_collection", text="", icon=ICON_REMOVE).remove_template = True
        else:
            row = col_box.row()
            row.enabled = tm_props.LI_xml_item_template_globally != ERROR_ENUM_ID
            row.operator("view3d.tm_set_itemxml_template_of_collection", text="Add Item XML Template").remove_template = False
            
        


        # basematerial / lightmap
        # basematerial / lightmap
        # basematerial / lightmap
        # icon_basematerial = "HIDE_OFF" if     active_uvlayer_is_basematerial else "HIDE_ON"
        # icon_lightmap     = "HIDE_OFF" if not active_uvlayer_is_basematerial else "HIDE_ON"

        depress_basematerial = active_uvlayer_is_basematerial
        depress_lightmap     = not active_uvlayer_is_basematerial

        row = col_box.row(align=True)
        col= row.column(align=True)
        row = col.row()
        row.enabled = len(objs_with_uvmaps) > 0
        uv_row = row.column(align=True).row(align=True)
        uv_row.operator("view3d.tm_showuvmap", text="BaseMaterial", icon=ICON_VISIBLE, depress=depress_basematerial).uv_name = UV_LAYER_NAME_BASEMATERIAL
        uv_row.operator("view3d.tm_edituvmap", text="",             icon=ICON_EDIT).uv_name = UV_LAYER_NAME_BASEMATERIAL
        uv_row = row.column(align=True).row(align=True)
        uv_row.operator("view3d.tm_showuvmap", text="LightMap",     icon=ICON_VISIBLE, depress=depress_lightmap).uv_name = UV_LAYER_NAME_LIGHTMAP
        uv_row.operator("view3d.tm_edituvmap", text="",             icon=ICON_EDIT).uv_name = UV_LAYER_NAME_LIGHTMAP
        # row = col.row(align=True)
        # row.prop(tm_props, "LI_workspaces", text="")


        layout.separator(factor=2)

