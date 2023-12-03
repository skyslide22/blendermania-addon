import bpy

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox

from ..utils.Functions import (
    get_global_props
)

from ..utils.Constants import (
    ICON_QUESTION,
    PANEL_CLASS_COMMON_DEFAULT_PROPS
)




class TM_PT_UIEditorTrails(bpy.types.Panel):
    bl_label   = "Editor Trails"
    bl_idname  = "TM_PT_UIEditorTrails"
    bl_context = "objectmode"
    # bl_parent_id = "TM_PT_Map_Manipulate"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="CURVE_DATA")

    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)

        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Editor Trails Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure editor trails settings",
            "-> Data will be received from http://localhost:42069/trails ",
            # "----> ",
        )

    def draw(self, context):
        layout = self.layout
        tm_props = get_global_props()

        row = layout.row(align=True)
        row.prop(tm_props, "CB_etrail_overwriteOnImport", text="Overwrite trails on each import", toggle=False)
        
        row = layout.row(align=True)
        row.enabled = False
        row.prop(tm_props, "NU_etrail_animationProgress", text="Animate Car (WIP)")

        # TODO testing
        # state = layout.progress(text='test', text_ctxt='', translate=True, factor=.5, type='BAR')
