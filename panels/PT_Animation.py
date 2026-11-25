
import bpy
from bpy.types import (Panel, Operator)
from ..ui.widgets.panels import ViewPanelMixin, is_hidden
from ..utils.Constants import PANEL_CLASS_COMMON_DEFAULT_PROPS

HEADER_VIEW_ID = "preview_header"
PLAY_SHORTCUT = "Shift Alt Space"


class MY_OT_reset_value(Operator):
    bl_idname = "tm.reset_animation_time"
    bl_label = "Reset"
    bl_description = "Set the preview time back to 0"

    def execute(self, context):
        scene = context.scene
        if scene.tm_preview_use_timeline:
            scene.frame_set(scene.frame_start)
        else:
            scene.tm_preview_time = 0
        return {'FINISHED'}


class TM_OT_PreviewTogglePlay(Operator):
    bl_idname = "tm.preview_toggle_play"
    bl_label = "Play / Pause Preview"
    bl_description = (f"Play or pause the Blendermania preview ({PLAY_SHORTCUT}). "
                      "Turns the moving parts preview on if no preview is active")

    def execute(self, context):
        from ..utils.Animations import any_preview_active
        scene = context.scene
        if not any_preview_active(scene):
            scene.tm_preview_enabled = True
            self.report({'INFO'}, "Moving parts preview on")
        if scene.tm_preview_use_timeline:
            bpy.ops.screen.animation_play()
        else:
            scene.tm_preview_playing = not scene.tm_preview_playing
        return {'FINISHED'}


def draw_auto_keying_warning(layout, context) -> bool:
    """Blender's Auto Keying turns every move into a keyframe; keyframes make objects jump back on frame
    changes and are ignored by Trackmania. Returns True when the warning was drawn."""
    ts = context.scene.tool_settings
    if not ts.use_keyframe_insert_auto:
        return False
    box = layout.box()
    col = box.column(align=True)
    col.alert = True
    col.label(text="Auto Keying is on", icon='ERROR')
    col.label(text="Moving objects creates keyframes")
    col.label(text="-> objects jump back on frame change")
    col.label(text="-> Trackmania ignores them")
    row = box.row()
    row.prop(ts, "use_keyframe_insert_auto", text="Turn Auto Keying off", toggle=True, icon='REC')
    return True


def _is_playing(scene, context) -> bool:
    if scene.tm_preview_use_timeline:
        return bool(context.screen and context.screen.is_animation_playing)
    return scene.tm_preview_playing


def draw_preview(l, ctx):
    """full preview controls, used by the sidebar panel and the viewport header popover"""
    s = ctx.scene
    fx = getattr(s, "tm_fx_preview", None)

    row = l.row(align=True)
    row.prop(s, "tm_preview_enabled", text="Moving", toggle=True, icon='ANIM')
    if fx is not None:
        row.prop(fx, "show", text="Particles", toggle=True, icon='PARTICLES')
        row.prop(fx, "show_trees", text="Leaves", toggle=True, icon='OUTLINER_OB_FORCE_FIELD')
    if hasattr(s, "tm_preview_uv_anims"):
        row.prop(s, "tm_preview_uv_anims", text="UV", toggle=True, icon='UV')

    col = l.column(align=True)
    playing = _is_playing(s, ctx)
    r = col.row(align=True)
    r.scale_y = 1.2
    r.operator(TM_OT_PreviewTogglePlay.bl_idname, text="Pause" if playing else "Play",
               icon='PAUSE' if playing else 'PLAY', depress=playing)
    r = col.row(align=True)
    if s.tm_preview_use_timeline:
        r.label(text=f"Timeline: frame {s.frame_current}", icon='TIME')
    else:
        r.prop(s, "tm_preview_time")
    r.operator("tm.reset_animation_time", text="", icon='LOOP_BACK')
    if not s.tm_preview_use_timeline:
        col.prop(s, "tm_preview_speed")
    l.prop(s, "tm_preview_use_timeline")
    l.label(text=f"Play/Pause: {PLAY_SHORTCUT}", icon='INFO')

    draw_auto_keying_warning(l, ctx)

    if s.tm_preview_enabled:
        box = l.box().column(align=True)
        box.label(text="Objects are moved while active,", icon='INFO')
        box.label(text="edit while paused or off")


class TM_PT_Animation_Preview(ViewPanelMixin, Panel):
    """one preview clock for moving parts, particle fx and tree propagation"""
    view_id = "animation_preview"
    view_label = "Preview"

    bl_label   = "Preview"
    bl_idname  = "TM_PT_Animation_Preview"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )
    bl_order = 10  # Blendermania tab: settings 0, preview 10, manipulations 20, export 30, map 40, materials 50, asset library 60, textures 65, editor trails 70, NICE 80, imports 90

    @classmethod
    def view_poll(self, context):
        return True

    def draw_header(self, ctx):
        self.layout.label(icon='PLAY')

    def draw_header_preset(self, ctx):
        from .LibraryInstallUI import draw_info_button
        draw_info_button(self.layout, "Preview", (
            "One clock for all previews: moving parts, particle effects and tree leaves",
            "",
            "Moving Parts: moves the objects of moving groups while active,",
            "-> they are restored when switched off and before every export",
            "Particles / Tree Leaves: viewport overlays only, nothing is added to the scene",
            "-> their settings are in the particle fx / tree model panels",
            "",
            f"Quick access: viewport header (play, time, ▾ for all settings), {PLAY_SHORTCUT}",
            "-> the header controls can be hidden in Settings > Views",
            "",
            "The own clock never changes the Blender frame, so no keyframes are evaluated",
            "-> 'Sync with Timeline' uses the Blender timeline instead (Space plays)",
            "Trackmania ignores Blender keyframes: keep Auto Keying off",
        ))

    def draw(self, ctx):
        draw_preview(self.layout, ctx)


class TM_PT_Preview_Header(ViewPanelMixin, Panel):
    """popover of the viewport header controls; its view toggle also hides the header controls"""
    view_id = HEADER_VIEW_ID
    view_label = "Preview (viewport header)"

    bl_label = "Blendermania Preview"
    bl_idname = "TM_PT_Preview_Header"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_ui_units_x = 12

    def draw(self, ctx):
        self.layout.label(text="Blendermania Preview", icon='PLAY')
        draw_preview(self.layout, ctx)


def draw_header_controls(self, context):
    """compact preview controls in the 3D viewport header: play/pause, time, popover with everything else"""
    try:
        if is_hidden(HEADER_VIEW_ID, context):
            return
    except KeyError:   # addon preferences missing (imported, not enabled)
        pass
    from ..utils.Animations import any_preview_active
    s = context.scene
    if not hasattr(s, "tm_preview_enabled"):
        return
    active = any_preview_active(s)
    playing = _is_playing(s, context)

    row = self.layout.row(align=True)
    row.operator(TM_OT_PreviewTogglePlay.bl_idname, text="", icon='PAUSE' if playing else 'PLAY', depress=playing)
    if active and not s.tm_preview_use_timeline:
        sub = row.row(align=True)
        sub.ui_units_x = 4.5
        sub.prop(s, "tm_preview_time", text="")
    row.popover(panel=TM_PT_Preview_Header.bl_idname, text="" if active else "Preview")


_keymaps = []


def register_preview_header():
    bpy.utils.register_class(TM_OT_PreviewTogglePlay)
    bpy.types.VIEW3D_HT_header.append(draw_header_controls)
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new(TM_OT_PreviewTogglePlay.bl_idname, "SPACE", "PRESS", shift=True, alt=True)
        _keymaps.append((km, kmi))


def unregister_preview_header():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    bpy.types.VIEW3D_HT_header.remove(draw_header_controls)
    bpy.utils.unregister_class(TM_OT_PreviewTogglePlay)
