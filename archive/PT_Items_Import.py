

import bpy
import os.path
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup,
    OperatorFileListElement
)
from bpy_extras.io_utils import ImportHelper
from bpy.props import CollectionProperty



from ..utils.Functions      import *
from ..utils.Constants      import * 
from ..operators.OT_Settings       import *
from ..operators.OT_Items_Icon     import *
from ..operators.OT_Materials      import *

"""
    ADD TO __init__

    from .panels.PT_Items_Import       import *

    TM_PT_Items_Import,
"""

class TM_PT_Items_Import(Panel):
    bl_label   = "Import FBX"
    bl_idname  = "TM_PT_Items_Import"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_IMPORT)


    def draw(self, context):

        layout = self.layout
        tm_props  = get_global_props()
        action    = tm_props.LI_importType
        recursive = tm_props.CB_importFolderRecursive
        failedMats= tm_props.LI_importMatFailed

        if requireValidNadeoINI(self) is False: return

        row = layout.row(align=True)
        row.prop(tm_props, "LI_importType",            expand=False, text="Type", )
        row.prop(tm_props, "CB_importFolderRecursive", expand=False, text="",    icon=ICON_RECURSIVE)


        btnText = "Import Files" if action == "FILES" else "Import Folder & Subfolders" if recursive else "Import Folder"
        row=layout.row()
        row.scale_y = 1.5
        row.operator("view3d.tm_importfbx", text=btnText, icon=ICON_IMPORT)


        if failedMats:
            layout.separator(factor=UI_SPACER_FACTOR)
            
            row = layout.row()
            row.alert = True
            row.operator("view3d.tm_clearmatimportfails", text="OK, clear list")
            
            layout.label(text="Invalid imported materials:")
            for matName in failedMats.split(";;;"): 
                row=layout.row()
                row.alert = True
                row.label(text=matName)
        
        layout.separator(factor=UI_SPACER_FACTOR)


