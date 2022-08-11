from typing import List
import bpy
import os.path
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)


from .TM_Functions      import *
from .TM_Items_Convert  import *
from .TM_Items_XML      import *
from .TM_Items_UVMaps   import *
from .TM_Settings       import *
from .TM_Items_Icon     import *
from .TM_Materials      import *


class TM_OT_Map_SaveCollectionAsMap(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.tm_save_col_as_map"
    bl_description = "Save collection as map gbx"
    bl_label = "Save as map"
        
    def execute(self, context):

        if saveBlendFile():
            save_col_as_map_gbx()
        
        else:
            makeReportPopup("FILE NOT SAVED!", ["Save your blend file!"], "ERROR")

        return {"FINISHED"}
    



class TM_PT_Map_Manipulate(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Manipulate Map Files"
    bl_idname  = "TM_PT_Map_Manipulate"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    # endregion
    def draw(self, context):

        layout = self.layout
        tm_props = getTmProps()

        if requireValidNadeoINI(self) is False: return

        # map
        row = layout.row()
        row.prop(tm_props, "ST_map_filepath", text="Map file")

        col = getActiveCollectionOfSelectedObject()
        col_name = col.name if col else ""

        box = layout.box()
        box.enabled = col is not None
        box.label(text=f"""Name: {col_name or 'Select any object'}""", icon="OUTLINER_COLLECTION")
        box.operator(TM_OT_Map_SaveCollectionAsMap.bl_idname, text="Save as Map")







def is_block(map_obj: dict) -> bool:
    return map_obj["type"] == "block"

def is_item(map_obj: dict) -> bool:
    return map_obj["type"] == "item"


def obj_to_map_json(obj: bpy.types.Object) -> dict:
    map_obj = {
        "name": obj.name,        
        "pos": [int(pos) for pos in obj.location],
        "rot": [rot for rot in obj.rotation_euler],
        "type": "block",
    }
    return map_obj
    

def objs_to_map_json(col: bpy.types.Collection) -> string:
    objs = [obj for obj in col.all_objects if obj.type == "MESH"]
    obj_map_dict = {
        "blocks": [],
        "items": [], 
        "mapname": getTmProps().ST_map_filepath
    }
    for obj in objs:
        map_obj = obj_to_map_json(obj)
        if is_block(map_obj):
            obj_map_dict["blocks"].append(map_obj)
        if is_item(map_obj):
            obj_map_dict["items"].append(map_obj)

    return json.dumps(obj_map_dict)


def save_col_as_map_gbx() -> None:
    # tm_props = getTmProps()
    col      = getActiveCollectionOfSelectedObject()
    
    objs_map_json = objs_to_map_json(col)

    proc = subprocess.Popen(
        args=[
            "C:/Users/User/source/repos/MapGbxManipulator/MapGbxManipulator/bin/Debug/net6.0/MapGbxManipulator.exe",
            objs_map_json,
        ]
    )
    proc.stdout = subprocess.PIPE
    proc.wait()

    debug("returncode: ", proc.returncode)


