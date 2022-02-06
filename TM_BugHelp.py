import os
import bpy
import traceback
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
import os.path
import string
import webbrowser
import addon_utils
from pprint import pprint
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)

from .TM_Functions      import *
from .TM_Items_Convert  import *
from . import bl_info


class TM_OT_ImportSomeFile(Operator):
    """Get all those thicc files in here"""
    bl_idname = "view3d.install_addon"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Install files"

    def execute(self, context):

        #url = https://drive.google.com/file/d/14MH9Do950KlqehUJ_KQsnJ9Eff4NeY5E/view?usp=sharin
        bpy.ops.preferences.addon_install(filepath = getAddonAssetsPath() + 'ninjaripper-blender-import-main.zip', overwrite = True)
        bpy.ops.preferences.addon_enable(module = 'ninjaripper-blender-import-main')
        isNinjaRipperInstalled()
        return {'FINISHED'}



class TM_OT_ImportSomeData(Operator, ImportHelper):
    """Get all those thicc models in here"""
    bl_idname = "view3d.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import File"

    # ImportHelper mixin class uses this
    filename_ext = ".rip"

    filter_glob: StringProperty(
        default="*.rip",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    use_setting: BoolProperty(
        name="Ignore this lol",
        description="This does nothing lol",
        default=True,
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        return read_some_data(context, self.filepath, self.use_setting)



class TM_PT_BugHelper(Panel):
    bl_label = "RIP Importer"
    bl_idname = "TM_PT_BugHelper"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_options = set() # default is closed, open as default

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="GHOST_DISABLED")

    def draw(self, context):
        tm_props = getTmProps()
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        nina_exist = tm_props.CB_ninjarip_isInstalled

        if not nina_exist:
            row = col.row(align=True)
            row.scale_y = 1.5
            row.operator("view3d.install_addon", text=f"Install necessary addon", icon="IMPORT")
            
        else:
            row = col.row(align=True)
            row.scale_y = 1.5
            row.operator("view3d.some_data", text=f"Import RIP files", icon="IMPORT")




def read_some_data(context, filepath, use_some_setting):
    print("Importing files...")
    # put the location to the folder where the objs are located here in this fashion
    # this line will only work on windows ie C:\objects
    pathname = os.path.dirname(os.path.abspath(filepath))
    path_to_obj_dir = os.path.join(pathname)

    print(path_to_obj_dir)
    # get list of all files in directory
    file_list = sorted(os.listdir(path_to_obj_dir))

    # get a list of files ending in 'obj'
    obj_list = [item for item in file_list if item.endswith('.rip')]

    #bpy.ops.import_scene.rip(filepath = os.path.join(path_to_obj_dir, obj_list[0]))
    manual = False

    if(manual):
        i_min = 209
        i_max = 267
    
        for i in range(i_min,i_max+1):
            index = "%04d" % i
            item = "Mesh_"+index+".rip"
            path_to_file = os.path.join(path_to_obj_dir, item)
            try:
                bpy.ops.import_scene.rip(filepath = path_to_file)
            
            except Exception as exc:
                print(traceback.format_exc())
                print(exc)
                pass
            print(item)
    else:
    # loop through the strings in obj_list and add the files to the scene
        for item in obj_list:
            path_to_file = os.path.join(path_to_obj_dir, item)
            try:
                bpy.ops.import_scene.rip(filepath = path_to_file)
            
            except Exception as exc:
                print(traceback.format_exc())
                print(exc)
                pass
        
            print(item)

    return {'FINISHED'}


NINJA_RIPPER_ADDON_NAME = "NinjaRipper RIP Format"

def isNinjaRipperInstalled():
    tm_props = getTmProps()
    exist = False
    for mod in addon_utils.modules():
        if(mod.bl_info.get('name') == NINJA_RIPPER_ADDON_NAME):
            exist = True

    tm_props.CB_ninjarip_isInstalled = exist
    
    return exist