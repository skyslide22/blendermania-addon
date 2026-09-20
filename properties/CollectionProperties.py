import bpy
from bpy.props import *


def register_collection_properties():
    bpy.types.Collection.tm_itemxml_template = StringProperty(
        name="Item XML Template", 
        default=""
    )
    bpy.types.Collection.tm_waypoint_no_respawn = BoolProperty(
        name="No Respawn",
        description="Indicates if the waypoint should not respawn",
        default=False
    )

def unregister_collection_properties():
    del bpy.types.Collection.tm_itemxml_template
    del bpy.types.Collection.tm_waypoint_no_respawn

