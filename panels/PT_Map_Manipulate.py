from bpy.types import (Operator, Panel)

from ..utils.Dotnet         import *
from ..utils.Functions      import *
from ..utils.Constants      import * 
from ..operators.OT_Map_Manipulate  import *



class PT_UIMapManipulation(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_label   = "Manipulate Map Files"
    bl_idname  = "TM_PT_Map_Manipulate"
    bl_context = "objectmode"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    # endregion

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_MAP)

    def draw(self, context):

        layout = self.layout
        tm_props = get_global_props()

        if requireValidNadeoINI(self) is False: return

        row = layout.row()
        row.prop(tm_props, "ST_map_filepath", text="Map file")

        box = layout.box()
        box.operator(OT_UIExportAndCreateMap.bl_idname, text="Export selected collections and place them on a Map")
