
from email import header
from itertools import count

import bpy
from bpy.types import Panel
from bpy.types import Operator



from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..properties.Functions import ERROR_ENUM_ID
from ..utils.FunctionsV2 import *
from ..utils.Constants import * 
from ..properties.PropertyIdentifiers import ObjectProp, CollectionProp, LightProp
from .UI_widgets import *
from ..panels.PT_Items_Placement import draw_item_placement



class TM_PT_ObjectManipulationsV2(Panel):
    bl_label   = "ManipulationsV2"
    bl_idname  = "TM_PT_ObjectManipulationsV2"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    
    
    @classmethod
    def poll(self, context):
        tm_props = get_global_props()
        return tm_props.CB_blendermaniaV2 and is_selected_nadeoini_file_name_ok()

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

class TM_PT_Items_ObjectManipulationV2(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_ObjectManipulationV2"
    bl_parent_id = "TM_PT_ObjectManipulationsV2"
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

        obj = bpy.context.object
        name = obj.name if obj else "None"

        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).obj_name = name       


    def draw(self, context):
        layout = self.layout
        tm_props        = get_global_props()

        current_item_collection      = get_active_item_collection_of_selected_object()
        current_collection_name = current_item_collection.name if current_item_collection is not None else "Select any object !"

        if current_item_collection is None:
            return

        obj          = None
        obj_name_raw = "Select any object !"
        obj_name     = "Select any object !"

        if bpy.context.selected_objects:
            obj           = bpy.context.selected_objects[0]
            obj_name      = obj.name
            # obj_name_raw  = cleanObjNameFromSpecialProps(obj.name)
            obj_name_raw  = obj_name


        is_Light   = (obj.type == "LIGHT") if obj is not None else False
        is_Mesh    = (obj.type == "MESH")  if obj is not None else False
            
        obj_box = layout
        row = obj_box.row(align=True)
         
        row.prop(obj, ObjectProp.IGNORE, text="No Export", icon_value=get_addon_icon("CANCEL"))

        if is_Mesh:
            col = layout.column()
            col.enabled = not getattr(obj, ObjectProp.IGNORE)

            row = col.row(align=True)
            row.prop(obj, ObjectProp.ORIGIN, text="Origin", icon=ICON_ORIGIN)
            row.prop(obj, ObjectProp.PIVOT, text="Pivot", icon=ICON_PIVOTS)

            row = col.row(align=True)
            row.prop(obj, ObjectProp.INVISIBLE, text="Not Visible", icon=ICON_HIDDEN, toggle=True)
            row.prop(obj, ObjectProp.NON_COLLIDABLE, text="Not Collidable", icon=ICON_GHOSTMODE, toggle=True)

            row = col.row(align=True)
            row.prop(obj, ObjectProp.TRIGGER_EFFECT, text="Trigger Effect", toggle=True)
            row.prop(obj, ObjectProp.TRIGGER_WAYPOINT, text="Trigger Waypoint", toggle=True)

            if getattr(obj, ObjectProp.TRIGGER_EFFECT):
                #col = row.column(align=True)
                row = col.row(align=True)
                row.prop(obj, ObjectProp.TRIGGER_EFFECT_TYPE, text="Effect")
                #row = row.row(align=True)
                row = col.row(align=True)
                row.prop(obj, ObjectProp.GAMEPLAY_MAIN_DIR, text="Gameplay Dir")
                row = col.row(align=True)
                row.label(text="Effect Strength", icon=ICON_FORCE)
                row.prop(obj, ObjectProp.GAMEPLAY_STRENGTH, text="")

            row = col.row(align=True)
            row.prop(obj, ObjectProp.NO_MERGE, text="No Merge", toggle=True)
            row.prop(obj, ObjectProp.SOCKET, text="Spawn", toggle=True)

            row = col.row(align=True)
            row.prop(obj, ObjectProp.ENABLE_LODS, text="LODs", toggle=True)
            if getattr(obj, ObjectProp.ENABLE_LODS):
                item_lods = getattr(current_item_collection, "tm_lods", [])
                lod_count = len(item_lods)
                selected_lods = get_lod_indexes(obj)
                lod_col = col.column(align=True)
                lod_row = None
                for i in range(lod_count + 1):
                    if i % 10 == 0:
                        lod_row = lod_col.row(align=True)
                    op = lod_row.operator("tm.toggle_lod", text=str(i), depress=i in selected_lods)
                    op.index = i
                    start = item_lods[i - 1].distance if i > 0 else 0.0
                    end   = item_lods[i].distance if i < lod_count - 1 else -1
                    op.tip = f"{start:g} → {f'{end:g}' if end >= 0 else '∞'}"


            row = col.row(align=True)
            row.prop(obj, ObjectProp.OVERRIDE_LIGHTMAP_SIZE, text="", icon=ICON_DAYTIME, toggle=True)
            row = row.row(align=True)
            row.enabled = getattr(obj, ObjectProp.OVERRIDE_LIGHTMAP_SIZE)
            row.prop(obj, ObjectProp.LIGHTMAP_SIZE, text="Override Lightmap Size", )

            if obj and obj.type == "MESH":
                    col = obj_box.column(align=True)
                    row = col.row(align=True)
                    editmode = obj.mode == "EDIT"
                    row.operator("object.shade_smooth" if not editmode else "mesh.faces_shade_smooth", icon=ICON_SMOOTH)
                    row.operator("object.shade_flat"   if not editmode else "mesh.faces_shade_flat", icon=ICON_FLAT)
                    
                    if bpy.app.version < (4, 1, 0): # 4.1 changed auto smooth to geo nodes AHHHH
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

        if is_Light:
            light_box = layout.box()
            light_box.enabled = is_Light and not getattr(obj, ObjectProp.IGNORE)
            
            col = light_box.column(align=True)
            is_spotlight  = obj.data.type == "SPOT"
            is_pointlight = obj.data.type == "POINT"
            light = obj.data
            if len(bpy.context.selected_objects) > 1:
                is_spotlight  = all([obj.data.type == "SPOT"  for obj in bpy.context.selected_objects]) or None
                is_pointlight = all([obj.data.type == "POINT" for obj in bpy.context.selected_objects]) or None

            row = col.row(align=True)
            row.operator("view3d.tm_togglelighttype", text="Spot" , icon=ICON_LIGHT_SPOT , depress=(is_spotlight  is True)).light_type = "SPOT"
            row.operator("view3d.tm_togglelighttype", text="Point", icon=ICON_LIGHT_POINT, depress=(is_pointlight is True)).light_type = "POINT"


            light_is_nightonly = obj.data.night_only
            if len(bpy.context.selected_objects) > 1:
                all_false = all([obj.data.night_only is False for obj in bpy.context.selected_objects])
                all_true =  all([obj.data.night_only is True  for obj in bpy.context.selected_objects])
                
                if all_false:
                    light_is_nightonly = False
                elif all_true:
                    light_is_nightonly = True
                else:
                    light_is_nightonly = None


            row = col.row(align=True)
            row.operator("view3d.tm_togglenightonly", text="Day+Night" , icon=ICON_DAYTIME, depress=(light_is_nightonly is False)).night_only = False
            row.operator("view3d.tm_togglenightonly", text="Night Only", icon=ICON_DAYTIME, depress=(light_is_nightonly is True) ).night_only = True

            if len(bpy.context.selected_objects) == 1 or True:
                row = col.row(align=True)
                row.label(text="Color", icon=ICON_LIGHT_COLOR)
                row.prop(light, "color",  text="") 
                
                row = col.row(align=True)
                row.label(text="Power", icon=ICON_LIGHT_POWER)
                row.prop(light, "energy", text="") 
                
                row = col.row(align=True)
                row.label(text="Radius", icon=ICON_LIGHT_RADIUS)
                row.row().prop(light, "shadow_soft_size", text="") 


                if is_spotlight is True:
                    row = col.row(align=True)
                    row.label(text="Outer angle", icon=ICON_LIGHT_RADIUS_OUT)
                    row.row().prop(light, "spot_size", text="") 

                    row = col.row(align=True)
                    row.label(text="Inner angle", icon=ICON_LIGHT_RADIUS_IN)
                    row.row().prop(light, "spot_blend", text="", slider=True) 


                row = col.row(align=True)
                row.label(text="Emitting Radius")
                row.row().prop(light, LightProp.LIGHT_EMITTING_RADIUS, text="")        

                row = col.row(align=True)
                row.label(text="Emitting Length")
                row.row().prop(light, LightProp.LIGHT_EMITTING_LENGTH, text="")
  




        # lights
        # lights
        # lights
       
        layout.separator(factor=1)


class TM_PT_Items_CollectionManipulationV2(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_CollectionManipulationV2"
    bl_parent_id = "TM_PT_ObjectManipulationsV2"
    # endregion

    @classmethod
    def register_callbacks(self):
        register_list_hooks(bpy.types.Collection, CollectionProp.LODS, after_add=self.on_lod_add)

    @classmethod
    def unregister_callbacks(self):
        unregister_list_hooks(bpy.types.Collection, CollectionProp.LODS)

    def draw_header(self, context):
        layout = self.layout
        current_collection      = get_active_collection()
        layout.enabled = current_collection is not None
        

        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row = layout.row()

        col_text = row.column(align=True)
        row = col_text.row(align=True)

        icon = ICON_COLLECTION
        if current_collection and current_collection.color_tag != 'NONE':
            icon = 'COLLECTION_' + current_collection.color_tag 

        row.label(text=current_collection_name.split("_#SCALE")[0], icon=icon)


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
    
        current_collection      = get_active_collection()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).col_name = current_collection_name        
        

    def draw(self, context):
        layout = self.layout
        current_collection      = get_active_collection()
        layout.enabled = current_collection is not None
        tm_props = get_global_props()

        
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        if current_collection is None:
            return

        
        row = layout.row(align=True)
        row.prop(current_collection, CollectionProp.IGNORE, icon_value=get_addon_icon("CANCEL"))

        col = layout.column()
        col.enabled = not getattr(current_collection, CollectionProp.IGNORE)


        can_convert_to_moving_group_collection = can_convert_to_group_collection(current_collection)
        is_moving_group_collection = getattr(current_collection, CollectionProp.MOVING_GROUP, False)

        row = row.row(align=True)
        row.enabled = col.enabled and (can_convert_to_moving_group_collection if not is_moving_group_collection else True)
        row.prop(current_collection, CollectionProp.MOVING_GROUP, icon="NLA_PUSHDOWN")


        if is_moving_group_collection:
            row = col.row(align=True)
            row.prop(current_collection, CollectionProp.MOVING_ANCHOR, text="Anchor", icon=ICON_ORIENTATION_LOCAL)
            op = row.operator("tm.create_anchor", text="", icon='EMPTY_AXIS')
            op.collection_name = current_collection.name

            row = col.row(align=True)
            row.prop(current_collection, CollectionProp.RELATIVE_MOVING_GROUP, text="Parent Group", icon=ICON_CON_CHILDOF)
            row.label(text="", icon='BLANK1')     # same width as an icon button

            row = col.row(align=True)
            row.prop(current_collection, CollectionProp.KINEMATIC_IS_KINEMATIC, text="Is Kinematic", toggle=True)
            row.prop(current_collection, CollectionProp.KINEMATIC_CAST_SHADOW, text="Cast Shadow", toggle=True)

            if False: # disable until we know what it does and where
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_PERIODIC_SC, text="PeriodicSC", toggle=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_PERIODIC_SC_MAX, text="Max", toggle=True)
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_PHASE_01, text="Phase01", toggle=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_PHASE_01_MAX, text="Max", toggle=True)
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_TEXTURE_ID, text="TextureID", toggle=True)

            # translation
            trans_anims = getattr(current_collection, CollectionProp.KINEMATIC_TRANS_ANIMS)
            trans_anim_count = len(trans_anims)
            trans_body, trans_header = foldout_toggle(col,
                                                      tm_props,
                                                      "CB_cfg_show_trans_anims", 
                                                      label=f"Translation Animations ({trans_anim_count}/{MAX_ANIMS})",
                                                      indent = UI_FOLDOUT_INDENT)
            if trans_body:
                row = trans_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_TRANS_AXIS, text="Translation Axis")
                row = trans_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_TRANS_MIN)
                row.prop(current_collection, CollectionProp.KINEMATIC_TRANS_MAX)
                if trans_anim_count == 0:
                    trans_body.label(text="No translation animations", icon='INFO')
                box = trans_body.box()
                item_list(box,
                          current_collection,
                          CollectionProp.KINEMATIC_TRANS_ANIMS,
                          draw_item=self.draw_anim_row,
                          add_text="Add Translation Animation",
                          numbered=True)
                row = box.row(align=True)
                row.enabled = trans_anim_count < MAX_ANIMS
                list_add_button(row,
                                current_collection,
                                CollectionProp.KINEMATIC_TRANS_ANIMS,
                                text="Add Translation Animation",
                                icon=ICON_ADD)

            # rotation
            rot_anims = getattr(current_collection, CollectionProp.KINEMATIC_ROT_ANIMS)
            rot_anim_count = len(rot_anims)
            rot_body, rot_header = foldout_toggle(col,
                                                  tm_props,
                                                  "CB_cfg_show_rot_anims", 
                                                  label=f"Rotation Animations ({rot_anim_count}/{MAX_ANIMS})",
                                                  indent = UI_FOLDOUT_INDENT)
            if rot_body:
                row = rot_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_ROT_AXIS, text="Rotation Axis")
                row = rot_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_ROT_MIN)
                row.prop(current_collection, CollectionProp.KINEMATIC_ROT_MAX)
                if rot_anim_count == 0:
                    rot_body.label(text="No rotation animations", icon='INFO')
                box = rot_body.box()
                item_list(box,
                          current_collection,
                          CollectionProp.KINEMATIC_ROT_ANIMS,
                          draw_item=self.draw_anim_row,
                          add_text="Add Rotation Animation",
                          numbered=True)
                row = box.row(align=True)
                row.enabled = rot_anim_count < MAX_ANIMS
                list_add_button(row,
                                current_collection,
                                CollectionProp.KINEMATIC_ROT_ANIMS,
                                text="Add Rotation Animation",
                                icon=ICON_ADD)


            # tex anims
            tex_body, tex_header = foldout_toggle(col,
                                                  tm_props,
                                                  "CB_objMpl_show_moving_tex_anims",
                                                  enable_prop=CollectionProp.KINEMATIC_HAS_MOVING_TEXTURE,
                                                  enable_owner=current_collection,
                                                  label=f"Moving Texture",
                                                  indent = UI_FOLDOUT_INDENT)
            if tex_body:
                row = tex_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_NUM, text="Num Textures")
                row.prop(current_collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_TOP_TO_BOTTOM, text="Top to Bottom", toggle=True)
                row = tex_body.row(align=True)
                row.prop(current_collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_LINE, text="Textures Per Line")
                row.prop(current_collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_PER_COLUMN, text="Textures Per Column")

                tex_anims = getattr(current_collection, CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS)
                anim_count = len(tex_anims)
                tex_anim_body, tex_anim_header = foldout_toggle(tex_body,
                                                      tm_props,
                                                      "CB_objMpl_show_moving_tex",
                                                      label=f"Moving Texture Animations ({anim_count}/{MAX_TEXTURE_ANIMS})",
                                                      indent = UI_FOLDOUT_INDENT)
                if tex_anim_body:
                    
                    item_list(tex_anim_body,
                            current_collection,
                            CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS,
                            draw_item=self.draw_tex_anim_row,
                            add_text="Add Moving Texture Animation",
                            numbered=True)
                    row = tex_anim_body.row(align=True)
                    row.enabled = anim_count < MAX_TEXTURE_ANIMS
                    list_add_button(row,
                                    current_collection,
                                    CollectionProp.KINEMATIC_MOVING_TEXTURE_ANIMS,
                                    text="Add Moving Texture Animation",
                                    icon=ICON_ADD)
                
    
                

        if not is_moving_group_collection:

            row = col.row(align=True)

            row.prop(current_collection,CollectionProp.WAYPOINT_TYPE, text="Type")
            row = row.row(align=True)
            row.prop(current_collection, CollectionProp.NO_RESPAWN, text="No Respawn", )
            row.enabled = is_waypoint_collection(current_collection)

            if False: # disable until we know what it does and where
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.DEFAULT_GRAVITY_SPAWN)
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.TORQUE_X)
                row = col.row(align=True)
                row.prop(current_collection, CollectionProp.TORQUE_DURATION)

            box = col.box()
            lods = box.column(align=True)
            item_list(lods,
                      owner=current_collection,
                      collection=CollectionProp.LODS,
                      draw_item=self.draw_lod_row,
                      add=WIDGET_ADD_BUTTON_BOTTOM,
                      add_text="Add LOD",
                      draw_footer=self.draw_lod_footer)
    

            active_uvlayer_is_basematerial = True
            objs_with_uvmaps    = get_meshes_which_require_uvmaps(current_collection)
            if len(objs_with_uvmaps) > 0:
                base_uv = objs_with_uvmaps[0].data.uv_layers.get(UV_LAYER_NAME_BASEMATERIAL)
                if base_uv:
                    active_uvlayer_is_basematerial = base_uv.active is True
            depress_basematerial = active_uvlayer_is_basematerial
            depress_lightmap     = not active_uvlayer_is_basematerial
    
            row = col.row(align=True)
            col= row.column(align=True)
            row = col.row()
            row.enabled = len(objs_with_uvmaps) > 0
            uv_row = row.column(align=True).row(align=True)
            uv_row.operator("view3d.tm_showuvmap", text="BaseMaterial", icon=ICON_VISIBLE, depress=depress_basematerial).uv_name = UV_LAYER_NAME_BASEMATERIAL
            uv_row.operator("view3d.tm_edituvmap", text="",             icon=ICON_EDIT).uv_name = UV_LAYER_NAME_BASEMATERIAL
            uv_row = row.column(align=True).row(align=True)
            uv_row.operator("view3d.tm_showuvmap", text="LightMap",     icon=ICON_VISIBLE, depress=depress_lightmap).uv_name = UV_LAYER_NAME_LIGHTMAP
            uv_row.operator("view3d.tm_edituvmap", text="",             icon=ICON_EDIT).uv_name = UV_LAYER_NAME_LIGHTMAP

            row = col.row(align=True)
            draw_item_placement(col, context.scene, current_collection, section=None)
        
        return
        row = layout.row(align=True)

        row.prop(current_collection, CollectionProp.MOVING_GROUP, icon="NLA_PUSHDOWN")

        row = layout.row(align=True)

        row.prop(current_collection,CollectionProp.WAYPOINT_TYPE, text="Type")
        row = row.row(align=True)
        row.prop(current_collection, CollectionProp.NO_RESPAWN, text="No Respawn", )
        row.enabled = is_waypoint_collection(current_collection)

        row = layout.row(align=True)
        row.prop(current_collection, CollectionProp.IGNORE, icon_value=get_addon_icon("CANCEL"))

        row = layout.row(align=True)
        col = context.collection
        box = self.layout.box()
        lods = box.column(align=True)

        for i, lod in enumerate(col.tm_lods):
            row = lods.split(factor=0.25, align=True)
            row.label(text=f"LOD {i}")
            right = row.row(align=True)
            right.prop(lod, "distance", text="")
            op = right.operator("tm.lod_remove", icon="X", text="")
            op.index = i

        # implicit last level, same layout, not editable
        last_start = col.tm_lods[-1].distance if len(col.tm_lods) else 0.0
        row = lods.split(factor=0.25, align=True)
        row.enabled = False
        row.label(text=f"LOD {len(col.tm_lods)}")
        row.label(text=f"{last_start:g} → ∞")

        box.operator("tm.lod_add", icon="ADD", text="Add LOD")






        col_box = layout#.box()
        col_box.label(text="Old")

        row = col_box.row(align=True)
        row.prop(current_collection,CollectionProp.WAYPOINT_TYPE, text="Type")
        row.prop(current_collection, "tm_waypoint_no_respawn", text="No Respawn", )






        # helpers if waypoint invalid
        # helpers if waypoint invalid
        # helpers if waypoint invalid
        if get_waypointtype_of_collection(current_collection) != "None":
            has_spawn_item   = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_SOCKET)
            has_trigger_item = check_collection_has_obj_with_fix(current_collection, prefix=SPECIAL_NAME_PREFIX_TRIGGER)
            waypoint_type    = get_waypoint_of_active_objects_collection()
            
            trigger_missing = has_trigger_item is False and waypoint_type != WAYPOINT_NAME_START
            spawn_missing   = has_spawn_item   is False and waypoint_type != WAYPOINT_NAME_FINISH

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
                                    
                if trigger_missing:
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
        # nice   = current_collection_name.startswith(SPECIAL_NAME_PREFIX_NICE)

        row = col_box.row()
        # row.operator(f"view3d.tm_togglecollectionnice",   text=f"NICE",      icon="ORPHAN_DATA", depress=nice)
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

        coll_itemxml_template = current_collection.tm_itemxml_template
        coll_itemxml_template_404 = False

        if coll_itemxml_template != "":
            if coll_itemxml_template not in bpy.context.scene.tm_props_itemxml_templates:
                coll_itemxml_template_404 = True
                coll_itemxml_template = "NOT FOUND: " + coll_itemxml_template

        
        if coll_itemxml_template:
            row = col_box.row(align=True)
            col = row.column()
            col.label(text="Item XML Template:")
            col = row.column()
            col.enabled = False
            col.alert = coll_itemxml_template_404
            col.label(text=coll_itemxml_template)
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


    def draw_lod_row(self, layout, item, index):
        row = layout.split(factor=0.25, align=True)
        row.label(text=f"LOD {index}")          # clicking here selects the row
        row.prop(item, "distance", text="")     # clicking here edits the value

    @staticmethod
    def on_lod_add(owner, item, index):
        last_distance = getattr(owner, CollectionProp.LODS)[index - 1].distance if index > 0 else 0.0
        item.distance = last_distance + 64.0

    def draw_lod_footer(self, layout, last_item, last_index):
        row = layout.split(factor=0.25, align=True)
        row.enabled = False
        row.label(text=f"LOD {last_index + 1}")          # clicking here selects the row
        last_distance = last_item.distance if last_item is not None else 0.0
        row.label(text=f"{last_distance:g} → ∞")     # clicking here edits the value
    

    def draw_anim_row(self, layout, item, index):
        box = layout.box()
        col = box.column(align=True)
        col.prop(item, "reverse", text="Reverse", toggle=True)
        col.prop(item, "duration", text="Duration Millis")
        col.prop(item, "ease", text="Ease")

    def draw_tex_anim_row(self, layout, item, index):
        row = layout.row(align=True)
        row.prop(item, "duration", text="Duration Millis")
        row.prop(item, "textureIndex", text="Texture Id")
        



class TM_PT_Items_MovingGroupCollectionManipulationV2(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_Items_MovingGroupCollectionManipulationV2"
    bl_parent_id = "TM_PT_ObjectManipulationsV2"
    # endregion


    def draw_header(self, context):
        layout = self.layout
        current_collection      = get_active_group_collection()
        layout.enabled = current_collection is not None
        

        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row = layout.row()

        col_text = row.column(align=True)
        row = col_text.row(align=True)
        row.label(text=""+current_collection_name.split("_#SCALE")[0] + "", icon=ICON_COLLECTION)


    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
    
        current_collection      = get_active_group_collection()
        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        row.operator("wm.tm_renameobject", text="", icon=ICON_EDIT).col_name = current_collection_name        


    def draw(self, context):
        layout = self.layout
        current_collection      = get_active_group_collection()
        layout.enabled = current_collection is not None
        tm_props = get_global_props()
        

        current_collection_name = current_collection.name if current_collection is not None else "Select any object !"

        if current_collection is None:
            return

        row = layout.row(align=True)
        row.prop(current_collection, CollectionProp.MOVING_GROUP)
       

        layout.separator(factor=2)



class TM_PT_DangerousManualManipulationsV2(Panel):
    # region bl_
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_label = ""
    bl_idname = "TM_PT_DangerousManualManipulationsV2"
    bl_parent_id = "TM_PT_ObjectManipulationsV2"
    # endregion

    @classmethod
    def poll(cls, context):
        # Replace `your_boolean_condition` with the actual condition you want to check.
        # For example, it could be a property of the context or a custom property you've defined.
        return bpy.context.scene.tm_props.CB_allow_dangerous_manual_manipulations

    def draw_header(self, context):
        layout = self.layout
        layout.row().label(text="Dangerous Manual Manipulations", icon=ICON_ERROR)     


    def draw(self, context):
        layout = self.layout
        layout.enabled = len(bpy.context.selected_objects) > 0
        tm_props = get_global_props()
        
        row = layout.row()
        row.alert = True
        row.label(text="Edits here can break blendermania", icon=ICON_ERROR)
        
        layout.prop(tm_props, "LI_dangerous_manual_manipulation_types", expand=True)
        mtype = tm_props.LI_dangerous_manual_manipulation_types

        layout.row().separator(factor=1)

        if mtype == DANGEROUS_MANUAL_MANIPULATION_TYPE_MATERIAL:
            draw_dangerous_manual_manipulation_material(self, layout)

        elif mtype == DANGEROUS_MANUAL_MANIPULATION_TYPE_OBJECT:
            draw_dangerous_manual_manipulation_object(self, layout)
        
        elif mtype == DANGEROUS_MANUAL_MANIPULATION_TYPE_TM_PROPS:
            draw_dangerous_manual_manipulation_tm_props(self, layout)


class TM_UL_lods(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.25, align=True)
        row.label(text=f"LOD {index}")          # clicking here selects the row
        row.prop(item, "distance", text="")     # clicking here edits the value

    def draw_filter(self, context, layout):
        pass            


def draw_dangerous_manual_manipulation_material(self, layout):
    tm_props = get_global_props()
    mat = tm_props.LI_dangerous_manual_manipulation_mat
    
    box = layout.box()
    split = box.row(align=True).split(factor=.35)
    left = split.column()
    right = split.column()

    left.label(text="Material")
    right.prop(tm_props, "LI_dangerous_manual_manipulation_mat", text="")

    if not mat:
        layout.label(text="Select/Add a material !")
        return
    
    left.separator(factor=0.8)
    right.separator(factor=0.8)

    left.label(text="Game Type")
    right.prop(mat, "gameType", text="")

    left.label(text="BaseTexture")
    right.prop(mat, "baseTexture", text="")

    left.label(text="Link")
    right.prop(mat, "link", text="")

    left.label(text="PhysicsID")
    right.prop(mat, "physicsId", text="")

    left.label(text="PhysicsID")
    right.prop(mat, "usePhysicsId", text="Use Physics ID")

    left.label(text="GameplayID")
    right.prop(mat, "gameplayId", text="")

    left.label(text="GameplayID")
    right.prop(mat, "useGameplayId", text="Use Gameplay ID")

    left.label(text="Model")
    right.prop(mat, "model", text="")

    left.label(text="Environment")
    right.prop(mat, "environment", text="")

    left.label(text="Surface Color")
    right.prop(mat, "surfaceColor", text="")


def draw_dangerous_manual_manipulation_object(self, layout):
    tm_props = get_global_props()
    obj = bpy.context.object
    if not obj:
        layout.label(text="Select any object !")
        return
    
    if len(bpy.context.selected_objects) > 1:
        layout.label(text="Select only one object !")
        return

    # object
    box = layout.box()
    split = box.row(align=True).split(factor=.35)
    left = split.column()
    right = split.column()

    left.label(text="Name")
    right.prop(obj, "name", text="")

    left.label(text="Item Type")
    right.prop(obj, "tm_map_object_kind", text="")

    left.label(text="Item Path")
    right.prop(obj, "tm_map_object_path", text="")

    left.label(text="AnimPhaseOffset")
    right.prop(obj, "tm_map_object_animphaseoffset", text="")

    left.label(text="DifficultyColor")
    right.prop(obj, "tm_map_object_difficultycolor", text="")

    left.label(text="LightmapQuality")
    right.prop(obj, "tm_map_object_lightmapquality", text="")

    left.label(text="MTClip Name")
    right.prop(obj, "tm_map_clip_name", text="")

    left.label(text="Grid Helper")
    right.prop(obj, "tm_force_grid_helper", text="Force")

    left.label(text="Grid Helper X")
    right.prop(obj, "tm_forced_grid_helper_step_x", text="")

    left.label(text="Grid Helper Y")
    right.prop(obj, "tm_forced_grid_helper_step_y", text="")

    left.label(text="Grid Helper Z")
    right.prop(obj, "tm_forced_grid_helper_step_z", text="") 
    
    is_light = obj.type == "LIGHT"
    lrow = left.row()
    lrow.enabled = is_light
    lrow.label(text="Night Only")
    rrow = right.row()
    rrow.enabled = is_light
    if is_light:
        rrow.prop(obj.data, "night_only", text="Disable in day & sunrise")     
    else:
        rrow.label(text="Only for lights !")
        

def draw_dangerous_manual_manipulation_collection(self, layout):
    ...

def draw_dangerous_manual_manipulation_tm_props(self, layout):
    tm_props = get_global_props()
    tm_prop_names = []

    # Iterate over the properties of the PropertyGroup
    for prop in tm_props.bl_rna.properties:
        # Skip over built-in properties
        if prop.identifier not in {"rna_type", "name"}:
            tm_prop_names.append(prop.identifier)

    box = layout.box()
    split = box.row(align=True).split(factor=.35)
    left = split.column()
    right = split.column()

    for prop in tm_prop_names:
        left.label(text=prop)
        right.prop(tm_props, prop, text="")