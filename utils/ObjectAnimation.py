"""Blender keyframes/drivers on item objects.

Trackmania ignores Blender animation (moving parts use the moving group settings). Transform keyframes are
still harmful: the export moves the item to 0,0,0 by changing `location`, but the evaluated object (what the
FBX exporter writes) takes the keyed value -> the item would be exported at the wrong place. They usually come
from Blender's Auto Keying. The export therefore mutes them temporarily and warns about them.
"""

from contextlib import contextmanager

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

TRANSFORM_PATHS = {
    "location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale",
    "delta_location", "delta_rotation_euler", "delta_rotation_quaternion", "delta_scale",
    "matrix_world", "matrix_basis", "matrix_local", "matrix_parent_inverse",
}


def _is_transform(fcurve) -> bool:
    return fcurve.data_path in TRANSFORM_PATHS


def _action_fcurves(anim_data):
    """fcurves of the object's active action (slotted actions of Blender 4.4+ and legacy actions)"""
    action = anim_data.action
    if action is None:
        return []
    slot = getattr(anim_data, "action_slot", None)
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        if slot is not None:
            bag = action_get_channelbag_for_slot(action, slot)
            return list(bag.fcurves) if bag else []
    except ImportError:
        pass
    legacy = getattr(action, "fcurves", None)
    return list(legacy) if legacy is not None else []


def _transform_curves(obj):
    """(action fcurves, drivers, nla tracks) that animate the transform of obj"""
    ad = obj.animation_data
    if ad is None:
        return [], [], []
    fcurves = [fc for fc in _action_fcurves(ad) if _is_transform(fc)]
    drivers = [fc for fc in ad.drivers if _is_transform(fc)]
    tracks = [t for t in ad.nla_tracks if len(t.strips)] if ad.use_nla else []
    return fcurves, drivers, tracks


def get_animated_objects(objs) -> list[bpy.types.Object]:
    """objects whose transform is driven by keyframes, drivers or NLA strips"""
    result = []
    for obj in objs:
        fcurves, drivers, tracks = _transform_curves(obj)
        if any(not fc.mute for fc in fcurves + drivers) or any(not t.mute for t in tracks):
            result.append(obj)
    return result


@contextmanager
def muted_transform_animation(objs):
    """mute transform keyframes/drivers/NLA of objs for the export, restore the mute flags afterwards"""
    changed = []   # (owner, previous mute)
    for obj in objs:
        fcurves, drivers, tracks = _transform_curves(obj)
        for owner in fcurves + drivers + tracks:
            if not owner.mute:
                changed.append(owner)
                owner.mute = True
    if changed:
        bpy.context.view_layer.update()
    try:
        yield
    finally:
        for owner in changed:
            try:
                owner.mute = False
            except ReferenceError:
                pass
        if changed:
            bpy.context.view_layer.update()


def show_animated_objects_popup(collection_name: str, objs) -> None:
    names = [o.name for o in objs]

    def draw(self, context):
        lay = self.layout
        lay.label(text=f"<{collection_name}>: {len(names)} object(s) have keyframes/drivers on their transform:")
        for n in names[:12]:
            lay.label(text=f"  - {n}", icon="OBJECT_DATA")
        if len(names) > 12:
            lay.label(text=f"  ... and {len(names) - 12} more")
        lay.label(text="Trackmania ignores Blender animation, they were muted for this export.")
        lay.label(text="They usually come from Auto Keying and make objects jump on frame changes.")
        lay.label(text="For moving parts use moving groups instead.")
        op = lay.operator(TM_OT_ClearTransformAnimation.bl_idname, icon="KEY_DEHLT")
        op.object_names = "\n".join(names)

    bpy.context.window_manager.popup_menu(draw, title="Keyframes found", icon="ERROR")


class TM_OT_ClearTransformAnimation(Operator):
    bl_idname = "tm.clear_transform_animation"
    bl_label = "Remove keyframes"
    bl_description = ("Remove the transform keyframes, drivers and NLA tracks of these objects "
                      "(keeps their current position)")
    bl_options = {"REGISTER", "UNDO"}

    object_names: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    def execute(self, context):
        count = 0
        for name in filter(None, self.object_names.split("\n")):
            obj = bpy.data.objects.get(name)
            if obj is None or obj.animation_data is None:
                continue
            m = obj.matrix_world.copy()   # current (evaluated) placement stays
            fcurves, drivers, tracks = _transform_curves(obj)
            ad = obj.animation_data
            for fc in drivers:
                ad.drivers.remove(fc)
            for t in tracks:
                ad.nla_tracks.remove(t)
            if fcurves:
                remaining = [fc for fc in _action_fcurves(ad) if not _is_transform(fc)]
                if not remaining or ad.action.users > 1:
                    ad.action = None   # shared actions are only unassigned, never edited for other users
                else:
                    _remove_fcurves(ad, fcurves)
            if ad.action is None and not len(ad.drivers) and not len(ad.nla_tracks):
                obj.animation_data_clear()
            obj.matrix_world = m
            count += 1
        self.report({"INFO"}, f"Removed transform animation of {count} object(s)")
        return {"FINISHED"}


def _remove_fcurves(anim_data, fcurves) -> None:
    action = anim_data.action
    slot = getattr(anim_data, "action_slot", None)
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        bag = action_get_channelbag_for_slot(action, slot) if slot is not None else None
        if bag is not None:
            for fc in fcurves:
                bag.fcurves.remove(fc)
            return
    except ImportError:
        pass
    for fc in fcurves:
        action.fcurves.remove(fc)


def register():
    bpy.utils.register_class(TM_OT_ClearTransformAnimation)


def unregister():
    bpy.utils.unregister_class(TM_OT_ClearTransformAnimation)
