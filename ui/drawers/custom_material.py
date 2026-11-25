"""
Settings of the non-disk material assets (Texture Set, Custom Material).

Drawn by the TM Asset tab (asset library) and by Materials V2 (local materials of the project .blend), both edit the
same data (mat.tm_asset_properties.texture_set / .custom_material).
"""
import bpy

from ..widgets.asset_picker import draw_asset_field
from ..widgets.lists import list_inspector, register_row_drawer, unregister_row_drawer
from ...properties.AssetProperties import (AssetUvAnimProperties, CUSTOM_MATERIAL_SLOTS,
                                           SELFILLUM_SCALE_MODELS,
                                           UV_ANIM_MODELS, UV_ANIM_TYPES)


def _split_row(layout, text: str, factor: float = 0.3):
    split = layout.split(factor=factor, align=True)
    split.label(text=text)
    return split.row(align=True)


def draw_texture_set(layout, ts) -> None:
    """texture set (tree model material): optional physics/gameplay, images, optional bitmaps"""
    col = layout.column()
    row = col.row(align=True)
    row.prop(ts, "use_gameplay_effect", toggle=True)
    sub = row.row(align=True)
    sub.enabled = ts.use_gameplay_effect
    sub.prop(ts, "gameplay_effect", text="")
    row = col.row(align=True)
    row.prop(ts, "use_surface_material", toggle=True)
    sub = row.row(align=True)
    sub.enabled = ts.use_surface_material
    sub.prop(ts, "surface_material", text="")
    col.label(text="Images")
    for prop in ("color_image", "normal_image", "roughness_image"):
        draw_asset_field(col, ts, prop, "IMAGE", icon="IMAGE_DATA")
    col.label(text="Textures (optional)")
    for prop in ("color_texture", "normal_texture", "roughness_texture"):
        draw_asset_field(col, ts, prop, "BITMAP", icon="TEXTURE")


def _image_note(asset_mat) -> str:
    """how the image reaches the game: by its game path (nothing shipped) or as a dds file below Items"""
    if asset_mat is None:
        return ""
    from ...utils.ItemConfigBuilder import image_game_path
    return "game texture" if image_game_path(asset_mat) else "own file"


def draw_custom_material(layout, cm) -> None:
    """custom material: model, physics + gameplay (always written), texture slots of the model, glow, tiling, uv anims"""
    col = layout.column()
    _split_row(col, "Model").prop(cm, "model", text="")
    _split_row(col, "Physics").prop(cm, "surface_material", text="")
    _split_row(col, "Gameplay").prop(cm, "gameplay_effect", text="")

    col.separator()
    col.label(text="Textures (Image assets)")
    for prop in CUSTOM_MATERIAL_SLOTS.get(cm.model, ()):
        kwargs = {"text": "Glow (Self Illum)"} if cm.model == "TIAdd" else {}
        row = draw_asset_field(col, cm, prop, "IMAGE", icon="IMAGE_DATA", **kwargs)
        note = _image_note(getattr(cm, prop))
        if note:
            sub = row.row(align=True)
            sub.enabled = False
            sub.label(text="", icon="WORLD" if note == "game texture" else "FILE")
    if "roughness_image" in CUSTOM_MATERIAL_SLOTS.get(cm.model, ()) and cm.roughness_image:
        col.label(text="Roughness showed no visible effect in game", icon="INFO")

    if cm.model == "TIAdd":
        col.label(text="TIAdd has no color/normal: the glow texture is added", icon="INFO")
        col.label(text="to what's behind it (black = invisible)", icon="BLANK1")
    if cm.model in SELFILLUM_SCALE_MODELS:
        col.prop(cm, "selfillum_scale")

    col.separator()
    row = col.row(align=True)
    row.prop(cm, "use_tiling", toggle=True)
    sub = row.row(align=True)
    sub.enabled = cm.use_tiling
    sub.prop(cm, "tiling_u")
    sub.prop(cm, "tiling_v")

    col.separator()
    if cm.model not in UV_ANIM_MODELS:
        row = col.row()
        row.enabled = False
        row.label(text=f"UV Animations: only {', '.join(sorted(UV_ANIM_MODELS))} (in game)", icon="UV")
        if len(cm.uv_anims):
            col.label(text=f"{len(cm.uv_anims)} animation(s) kept but not exported", icon="INFO")
    else:
        col.label(text="UV Animations")
        list_inspector(col, cm, "uv_anims", "uv_anims_index", rows=2, draw_detail=_draw_uv_anim_detail)
        _draw_uv_anim_preview(col)
    if len(cm.uv_anims) and cm.model in UV_ANIM_MODELS:
        if any(a.layer != "SelfIllum" for a in cm.uv_anims):
            col.label(text="In game only layer SelfIllum animated", icon="ERROR")
        if len(cm.uv_anims) > 2:
            col.label(text="Only the first 2 animations are used", icon="ERROR")
        col.label(text="Static items only (moving items don't animate)", icon="INFO")


def _draw_uv_anim_preview(layout) -> None:
    """same switches as the Preview panel (shared clock)"""
    scene = bpy.context.scene
    if not hasattr(scene, "tm_preview_uv_anims"):
        return
    row = layout.row(align=True)
    row.prop(scene, "tm_preview_uv_anims", text="Preview", toggle=True, icon="UV")
    playing = (bpy.context.screen.is_animation_playing if scene.tm_preview_use_timeline and bpy.context.screen
               else scene.tm_preview_playing)
    row.operator("tm.preview_toggle_play", text="", icon="PAUSE" if playing else "PLAY", depress=playing)
    row.operator("tm.reset_animation_time", text="", icon="LOOP_BACK")
    if scene.tm_preview_uv_anims:
        shading = getattr(bpy.context.space_data, "shading", None)
        if shading is not None and shading.type in {"SOLID", "WIREFRAME"}:
            layout.label(text="Visible in Material Preview / Rendered shading", icon="INFO")


def _draw_uv_anim_detail(layout, anim, index) -> None:
    col = layout.column(align=True)
    col.prop(anim, "layer")
    col.prop(anim, "anim_type")
    col.prop(anim, "period")
    col.prop(anim, "input_val")
    if anim.anim_type == "TransSubTexture":
        col.prop(anim, "frame_count")
        row = col.row(align=True)
        row.prop(anim, "frames_x")
        row.prop(anim, "frames_y")
    else:
        row = col.row(align=True)
        row.prop(anim, "speed_u")
        row.prop(anim, "speed_v")


def _draw_uv_anim_row(layout, item, index) -> None:
    label = next((name for ident, name, _ in UV_ANIM_TYPES if ident == item.anim_type), item.anim_type)
    layout.label(text=f"{label} ({item.layer}, {item.period:g} s)", icon="UV")


def register():
    register_row_drawer(AssetUvAnimProperties, _draw_uv_anim_row)


def unregister():
    unregister_row_drawer(AssetUvAnimProperties)
