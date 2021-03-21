import bpy
import os.path
import re
import math
import statistics as stats
from bpy.props import EnumProperty
from bpy.types import (
    Panel,
    Operator,
)
from .TM_Functions import *




class TM_OT_Items_Cars_Import(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_importwaypointspawnhelper"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Car Spawns"
    bl_options = {"REGISTER", "UNDO"} #without, ctrl+Z == crash

    cars: EnumProperty(items=[
        ("CAR_StadiumCar_Lowpoly.fbx",  "Stadium Car",  "", "AUTO", 0),
        ("CAR_CanyonCar_Lowpoly.fbx",   "Canyon Car",   "", "AUTO", 1),
        ("CAR_ValleyCar_Lowpoly.fbx",   "Valley Car",   "", "AUTO", 2),
        ("CAR_LagoonCar_Lowpoly.fbx",   "Lagoon Car",   "", "AUTO", 3),
    ])

    def execute(self, context):
        car     = self.properties.cars
        carPath = f"""{getAddonPath()}assets/item_cars/{car}"""
        deselectAll()
        
        bpy.ops.import_scene.fbx(
            filepath=carPath 
        )

        for obj in bpy.context.selected_objects:
            if "_car_" in obj.name.lower():
                obj.location = getCursorLocation()


        return {"FINISHED"}
        


def addMenuPoint_CAR_SPAWN(self, context):
    layout = self.layout
    layout.operator_menu_enum("view3d.tm_importwaypointspawnhelper", "cars", icon="AUTO")
