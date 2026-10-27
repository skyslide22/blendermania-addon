from bpy.types import (Panel)
from ..ui.widgets.panels import ViewPanelMixin
from ..utils.Functions import get_global_props
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS

class TM_PT_Animation_Preview(ViewPanelMixin, Panel):
    view_id = "animation_preview"
    view_label = "Animation Preview"

    bl_label   = "Moving Animation Preview"
    bl_idname  = "TM_PT_Animation_Preview"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_order = 12

    @classmethod
    def view_poll(self, context):
        #tm_props = get_global_props()
        return True

    def draw_header(self, ctx):
        self.layout.label(icon='ANIM')

    def draw(self, ctx):
        s, l = ctx.scene, self.layout
        l.prop(s, "tm_preview_enabled", toggle=True, icon='PLAY')
        col = l.column()
        col.enabled = s.tm_preview_enabled
        # col.prop(s, "tm_preview_use_timeline")   # hidden for now, functionality kept
        if not s.tm_preview_use_timeline:
            col.prop(s, "tm_preview_time")
            r = col.row(align=True)
            r.prop(s, "tm_preview_playing", toggle=True)
            r.prop(s, "tm_preview_speed")
        if s.tm_preview_enabled:
            box = l.box()
            box.label(text="Changes while preview is active may produce errors", icon='ERROR')
