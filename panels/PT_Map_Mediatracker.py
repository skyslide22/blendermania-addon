import bpy
from ..utils.Functions import (
    get_global_props,
)
from ..utils.Constants import (
    PANEL_CLASS_COMMON_DEFAULT_PROPS,
    ICON_EXPORT,
)
from ..operators.OT_Map_Mediatracker import (
    OT_UIMapExportMediatrackerTriangle
)

class PT_UIMediatracker(bpy.types.Panel):
    bl_label   = "Mediatracker trinagles"
    bl_idname  = "TM_PT_UIMediatracker"
    bl_context = "objectmode"
    bl_parent_id = "TM_PT_Map_Manipulate"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()
        has_map_file = len(tm_props.ST_map_filepath) != 0
        has_triangle_object = tm_props.PT_map_mt_triangle_object is not None

        if not has_map_file:
            layout.alert = True
            layout.label(text="Select Map file first")
            return

        row = layout.row(align=True)
        row.prop(tm_props, "LI_map_mt_type", text="MT sequence", icon="OUTLINER_OB_CAMERA")

        row = layout.row(align=True)
        row.alert = not has_triangle_object
        row.prop(tm_props, "PT_map_mt_triangle_object", text="Object")

        row = layout.row(align=True)
        row.alert = True
        row.label(text="Object will be triangulated")

        row = layout.row(align=True)
        row.enabled = has_triangle_object
        row.operator(OT_UIMapExportMediatrackerTriangle.bl_idname, text="Export Object as Triangle", icon=ICON_EXPORT)