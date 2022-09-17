import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from ..utils.Constants import ICON_AUTO, ICON_GHOSTMODE, ICON_OBJECT

from ..utils.ItemsImport import import_item_FBXs

from ..utils.Functions import deselect_all_objects, get_addon_path, get_cursor_location, get_global_props
from ..properties.Functions import EnumProps, get_car_names

class OT_ItemsCarsTemplates(Operator):
    """import a dummy car for checkpoint spawn use..."""
    bl_idname = "view3d.tm_importwaypointspawnhelper"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Car Spawns"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    cars: EnumProperty(items=get_car_names())

    def execute(self, context):
        carpath = self.properties.cars
        deselect_all_objects()
        
        bpy.ops.import_scene.fbx(filepath=carpath)

        for obj in bpy.context.selected_objects:
            if "_car_" in obj.name.lower():
                obj.location = get_cursor_location()


        return {"FINISHED"}
        

    @staticmethod
    def add_menu_item(self, context):
        layout = self.layout
        layout.operator_menu_enum("view3d.tm_importwaypointspawnhelper", "cars", icon=ICON_AUTO)

class OT_ItemsEnviTemplates(Operator):
    """import a template for an environment, for example a StadiumPlatform object with proper materials"""
    bl_idname = "view3d.tm_importenvitemplate"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Envi Templates"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    envi_templates: EnumProperty(items=[
        ("VANILLA_Platform_Stadium",  "Platform: Stadium", "", "CUBE", 0),
        ("VANILLA_Platform_Canyon",   "Platform: Canyon",  "", "CUBE", 1),
        ("VANILLA_Platform_Valley",   "Platform: Valley",  "", "CUBE", 2),
        ("VANILLA_Platform_Lagoon",   "Platform: Lagoon",  "", "CUBE", 3),
    ])

    def execute(self, context):
        envi = self.properties.envi_templates
        import_item_FBXs([f"""{get_addon_path()}assets/item_vanilla_platforms/{envi}.fbx"""])
        return {"FINISHED"}
        

    @staticmethod
    def add_menu_item(self, context):
        layout = self.layout
        layout.operator_menu_enum("view3d.tm_importenvitemplate", "envi_templates", icon=ICON_OBJECT)

class OT_MediaTrackerClipTriggerTemplates(Operator):
    """import a template for an environment, for example a StadiumPlatform object with proper materials"""
    bl_idname = "view3d.tm_import_mt_clip_trigger"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Mediatracker Trigger"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    mt_trigger_templates: EnumProperty(items=EnumProps().add(
        "MT_TRIGGER_10_66x8.fbx", "Stadium Trigger", icon=ICON_GHOSTMODE
    ).to_list())

    def execute(self, context):
        tm_props = get_global_props()
        template = self.properties.mt_trigger_templates
        
        deselect_all_objects()
        bpy.ops.import_scene.fbx(filepath=f"{get_addon_path()}assets/item_mt_triggers/{template}")
        
        obj      = bpy.context.selected_objects[-1]
        coll     = bpy.context.collection
        map_coll = tm_props.PT_map_collection

        if map_coll:
            coll.objects.unlink(obj)
            map_coll.objects.link(obj)

        trigger_clip_step_xy = 32/3
        trigger_clip_step_z  = 8

        obj.tm_force_grid_helper         = True
        obj.tm_forced_grid_helper_step_x = trigger_clip_step_xy
        obj.tm_forced_grid_helper_step_y = trigger_clip_step_xy
        obj.tm_forced_grid_helper_step_z = trigger_clip_step_z

        return {"FINISHED"}
        

    @staticmethod
    def add_menu_item(self, context):
        layout = self.layout
        layout.operator_menu_enum("view3d.tm_import_mt_clip_trigger", "mt_trigger_templates", icon=ICON_GHOSTMODE)