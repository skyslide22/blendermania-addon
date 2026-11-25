from pathlib import Path
import bpy
from bpy.app.handlers import persistent
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup
from ..properties.PropertyFunctions import enum_items
from ..utils.ItemsExportV2Models import LegacyGameplayId, MaterialId
from ..utils.AssetLibraryFunctions import DEFAULT_REL_BITMAP_DIR, heal_image_paths, image_poll, on_image_changed, on_render_prop_changed, poll_asset
from .PropertyIdentifiers import AssetProp
from ..utils.UvAnimPreview import on_anim_prop_changed


ASSET_TYPES = [
    ("BITMAP", "Bitmap", "Bitmap Asset"),
    ("IMAGE", "Image", "Image Asset"),
    ("TEXTURESET", "TextureSet", "Material for Tree Models"),
    ("CUSTOMMATERIAL", "Custom Material", "Own or game textures on a Nadeo shading model"),
]

# asset types that only reference other assets: no image, no file, nothing to convert
CONTAINER_ASSET_TYPES = {"TEXTURESET", "CUSTOMMATERIAL"}

USAGE_NAMES = [
    "Color", "Light", "Height2DuDv", "Render", "Height2DuDvLumi", "Height2NxNyNz",
    "Height2NxNy", "Depth", "DispH01", "Height2NormPal8b", "NxNyNz", "NxNy",
    "NormPal8b", "NormPal16b", "ColorFloat", "RenderFloat", "Height2DuDv1", "Alpha",
    "LightAlpha", "Height2RxG0BzAy", "NormRxG0BzAy", "TexCoord", "Render16b", "Vertex",
    "Height2BumpTxTy", "BumpTxTy", "Height2R0GyBzAx", "NormR0GyBzAx", "NormXYZ0YZX",
]
# TM2020 usages GBX.NET has no name for (found in the game's Texture.Gbx): list index == game value
_TM2020_USAGE_LABELS = {31: "Normal (TM2020)", 36: "Roughness/Metal (TM2020)"}
USAGE_NAMES += [f"Usage{i}" for i in range(len(USAGE_NAMES), 39)]
USAGE_ITEMS = [(n, _TM2020_USAGE_LABELS.get(i, n), f"game value {i}" if n.startswith("Usage") else "")
               for i, n in enumerate(USAGE_NAMES)]


def usage_to_config(name):
    """enum name for GBX.NET, plain number for usages GBX.NET can't name"""
    return int(name[5:]) if name.startswith("Usage") else name


def usage_from_config(value):
    return USAGE_NAMES[value] if isinstance(value, int) else value


# --------------------------------------------------------------------------
# Property groups
# --------------------------------------------------------------------------

class TM_TexCoordProps(PropertyGroup):
    """Reusable rotate / scale / translate triple (default + grass-id use it)."""
    # note: also fires for grass_uv; harmless, sync_preview only reads default_uv
    rotate: FloatProperty(name="Rotate", default=0.0, description="Unit not verified (radians?)",
                          update=on_render_prop_changed)
    scale: FloatVectorProperty(name="Scale", size=2, default=(1.0, 1.0),
                               update=on_render_prop_changed)
    trans: FloatVectorProperty(name="Translate", size=2, default=(0.0, 0.0),
                               update=on_render_prop_changed)


class TM_FloatItem(PropertyGroup):
    value: FloatProperty(name="Value", default=0.0)


class AssetBitmapProperties(PropertyGroup):
    # --- usage & size ----------------------------------------------------
    usage: EnumProperty(name="Usage", items=USAGE_ITEMS, default="Color",
                        update=on_render_prop_changed)
    render_size_mul: IntProperty(name="Render Size Mul", default=1, min=1)
    render_size_div: IntProperty(name="Render Size Div", default=1, min=1)
    pixel_update: IntProperty(name="Pixel Update", default=0)

    # --- colors (COLOR_GAMMA = raw values, no color-management transform) --
    border_rgb: FloatVectorProperty(
        name="Border", subtype="COLOR_GAMMA", size=3, min=0.0, max=1.0, default=(0.0, 0.0, 0.0))
    clear_color: FloatVectorProperty(
        name="Clear", subtype="COLOR_GAMMA", size=4, min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 0.0))
    default_render_clear_color: FloatVectorProperty(
        name="Default Render Clear", subtype="COLOR_GAMMA", size=4, min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0))  # 4278190080 == 0xFF000000 (opaque black)

    # --- bump / height ---------------------------------------------------
    bump_scale_factor: FloatProperty(name="Bump Scale Factor", default=1.0,
                                     update=on_render_prop_changed)
    bump_scale_mip_level: FloatProperty(name="Bump Scale Mip Level", default=0.5)
    height_in_meters: FloatProperty(name="Height (m)", default=1.0, unit="LENGTH",
                                    update=on_render_prop_changed)

    # --- mipmaps ---------------------------------------------------------
    mip_lod_bias_default: FloatProperty(name="LOD Bias Default", default=0.0)
    mip_lower_alpha: FloatProperty(name="Lower Alpha", default=0.0)
    mip_fade_alphas: CollectionProperty(type=TM_FloatItem)
    mip_fade_alphas_index: IntProperty(default=0)

    # --- texture coordinates ---------------------------------------------
    default_uv: PointerProperty(type=TM_TexCoordProps)

    # --- grass id --------------------------------------------------------
    grass_id: StringProperty(name="Grass ID")
    grass_uv: PointerProperty(type=TM_TexCoordProps)


class AssetImgFileProperties(PropertyGroup):
    pass


class AssetTextureSetProperties(PropertyGroup):
    """Pure container: references other assets, writes no file and needs no conversion."""

    use_gameplay_effect: BoolProperty(name="Use Gameplay Effect", default=False)
    use_surface_material: BoolProperty(name="Use Material Type", default=False)
    gameplay_effect: EnumProperty(name="Gameplay Effect", description="Gameplay effect for this texture set", items=enum_items(LegacyGameplayId), default=LegacyGameplayId.None_.value)
    surface_material: EnumProperty(name="Material Type", description="Type of material", items=enum_items(MaterialId), default=MaterialId.Concrete.value)

    color_image: PointerProperty(type=bpy.types.Material, name="Color Image", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    normal_image: PointerProperty(type=bpy.types.Material, name="Normal Image", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    roughness_image: PointerProperty(type=bpy.types.Material, name="Roughness Image", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    color_texture: PointerProperty(type=bpy.types.Material, name="Color Texture", poll=poll_asset("BITMAP"), update=on_render_prop_changed)
    normal_texture: PointerProperty(type=bpy.types.Material, name="Normal Texture", poll=poll_asset("BITMAP"), update=on_render_prop_changed)
    roughness_texture: PointerProperty(type=bpy.types.Material, name="Roughness Texture", poll=poll_asset("BITMAP"), update=on_render_prop_changed)


# Shading models of Custom materials verified in game (TM_GenericMapping CustomMaterialUtils / ItemConfig.md)

# texture slots (property names) used by each model, in display order
CUSTOM_MATERIAL_MODELS = [
    ("TDSN", "TDSN", "Opaque: Color + Normal"),
    ("TDOSN", "TDOSN", "Alpha test (alpha 0 = hole): Color with alpha + Normal"),
    ("TDOBSN", "TDOBSN", "Alpha blend: Color with alpha + Normal"),
    ("TDSNE", "TDSNE", "Dark by day, energy glow at night: Color + Normal + Energy"),
    ("TDSNI", "TDSNI", "Self-illumination (Self Illum Scale): Color + Normal + Self Illum"),
    ("TDSNI_Night", "TDSNI_Night", "Self-illumination at night only (Self Illum Scale): Color + Normal + Self Illum"),
    ("TIAdd", "TIAdd", "Additive glow (black = invisible, Self Illum Scale): Self Illum only"),
]
CUSTOM_MATERIAL_SLOTS = {
    "TDSN": ("color_image", "normal_image", "roughness_image"),
    "TDOSN": ("color_image", "normal_image", "roughness_image"),
    "TDOBSN": ("color_image", "normal_image", "roughness_image"),
    "TDSNE": ("color_image", "normal_image", "roughness_image", "energy_image"),
    "TDSNI": ("color_image", "normal_image", "roughness_image", "selfillum_image"),
    "TDSNI_Night": ("color_image", "normal_image", "roughness_image", "selfillum_image"),
    "TIAdd": ("selfillum_image",),
}

# models whose UV animations work in game (TM_GenericMapping ItemConfig.md: only TIAdd + layer SelfIllum, static items)
UV_ANIM_MODELS = {"TIAdd"}
# models with the SelfIllumScale constant (glow strength)
SELFILLUM_SCALE_MODELS = {"TDSNI", "TDSNI_Night", "TIAdd"}

TEX_ADDRESS_ITEMS = [
    ("Wrap", "Wrap", "Repeat the texture"),
    ("Clamp", "Clamp", "Stretch the edge pixels outside 0..1"),
    ("Mirror", "Mirror", "Repeat mirrored (not tested in game)"),
]

UV_ANIM_TYPES = [
    ("TransLinear", "Scroll", "Scrolls the texture (Speed U/V per period)"),
    ("TransSubTexture", "Flip-book", "Plays the frames of an atlas (Frame Count, Frames X/Y)"),
]

UV_ANIM_INPUTS = [
    ("GameTime", "Game Time", ""),
    ("RaceTime", "Race Time", ""),
]


class AssetUvAnimProperties(PropertyGroup):
    layer: StringProperty(name="Layer", default="SelfIllum",
                          description="Texture layer to animate (in game only SelfIllum on TIAdd animated)", update=on_anim_prop_changed)
    anim_type: EnumProperty(name="Type", items=UV_ANIM_TYPES, default="TransLinear", update=on_anim_prop_changed)
    period: FloatProperty(name="Period", default=1.0, min=0.001, unit="TIME_ABSOLUTE",
                          description="Seconds per animation cycle", update=on_anim_prop_changed)
    input_val: EnumProperty(name="Time", items=UV_ANIM_INPUTS, default="GameTime")
    speed_u: FloatProperty(name="Speed U", default=0.0, description="Scroll per period along U", update=on_anim_prop_changed)
    speed_v: FloatProperty(name="Speed V", default=0.0, description="Scroll per period along V", update=on_anim_prop_changed)
    frame_count: IntProperty(name="Frame Count", default=0, min=0, update=on_anim_prop_changed)
    frames_x: IntProperty(name="Frames X", default=0, min=0, max=65535, update=on_anim_prop_changed)
    frames_y: IntProperty(name="Frames Y", default=0, min=0, max=65535, update=on_anim_prop_changed)


class AssetCustomMaterialProperties(PropertyGroup):
    """Own or game textures on a Nadeo shading model. Container like a texture set: writes no file."""

    model: EnumProperty(name="Model", items=CUSTOM_MATERIAL_MODELS, default="TDSN", update=on_render_prop_changed)
    # physics and gameplay are always written: the game has no "no physics"
    surface_material: EnumProperty(name="Physics", description="Surface material (physics)",
                                   items=enum_items(MaterialId), default=MaterialId.Concrete.value)
    gameplay_effect: EnumProperty(name="Gameplay", description="Gameplay effect",
                                  items=enum_items(LegacyGameplayId), default=LegacyGameplayId.None_.value)

    color_image: PointerProperty(type=bpy.types.Material, name="Color", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    normal_image: PointerProperty(type=bpy.types.Material, name="Normal", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    roughness_image: PointerProperty(type=bpy.types.Material, name="Roughness", poll=poll_asset("IMAGE"), update=on_render_prop_changed,
                                     description="Written, but showed no visible effect in game")
    selfillum_image: PointerProperty(type=bpy.types.Material, name="Self Illum", poll=poll_asset("IMAGE"), update=on_render_prop_changed)
    energy_image: PointerProperty(type=bpy.types.Material, name="Energy", poll=poll_asset("IMAGE"), update=on_render_prop_changed)

    selfillum_scale: FloatProperty(name="Self Illum Scale", default=1.0, min=0.0, soft_max=10.0,
                                   description="Glow strength (TDSNI, TDSNI_Night, TIAdd)", update=on_render_prop_changed)
    use_tiling: BoolProperty(name="Tiling", default=False, description="Write texture addressing (default: game default)",
                             update=on_render_prop_changed)
    tiling_u: EnumProperty(name="U", items=TEX_ADDRESS_ITEMS, default="Wrap", update=on_render_prop_changed)
    tiling_v: EnumProperty(name="V", items=TEX_ADDRESS_ITEMS, default="Wrap", update=on_render_prop_changed)

    uv_anims: CollectionProperty(type=AssetUvAnimProperties)
    uv_anims_index: IntProperty(default=0)


class AssetImageProperties(PropertyGroup):
    """Record stored on bpy.types.Image as img.tm_image_asset."""
    is_managed: BoolProperty(default=False)
    sha256: StringProperty()
    rel_path: StringProperty(description="Library-root-relative, forward slashes", default="")
    original_name: StringProperty(description="Display only", default="")


class AssetProperties(PropertyGroup):
    is_asset: BoolProperty(name="Is Asset", default=False)
    asset_type: EnumProperty(
        name="Asset Type",
        description="Type of the asset",
        items=ASSET_TYPES,
        default="BITMAP",
    )
    
    image: PointerProperty(type=bpy.types.Image, name="Image",
                           poll=image_poll, update=on_image_changed)


    relative_path: StringProperty(
        name="Target (relative)",
        description="Where the gbx is written, relative to the library. Empty = derived from name",
        default="",
    )

    exported_path: StringProperty(description="Absolute path of the file the asset was last exported/imported to. Empty = not exported yet",)

    bitmap: PointerProperty(type=AssetBitmapProperties)
    imageFile: PointerProperty(type=AssetImgFileProperties)
    texture_set: PointerProperty(type=AssetTextureSetProperties)
    custom_material: PointerProperty(type=AssetCustomMaterialProperties)

    game_path: StringProperty(
        name="Game Path",
        description="Path of this image inside the game data (e.g. Stadium/Media/Texture/Image/RoadIce_D.dds). "
                    "Custom materials reference it there instead of shipping the file",
        default="",
    )


# --------------------------------------------------------------------------
# Config conversion
# --------------------------------------------------------------------------

def bitmap_to_config(bmp):
    from ..utils.Dotnet import DotnetColor, DotnetVec2

    return {
        "Usage": usage_to_config(bmp.usage),
        "RenderSizeMul": bmp.render_size_mul,
        "RenderSizeDiv": bmp.render_size_div,
        "PixelUpdate": bmp.pixel_update,
        "BorderRGB": DotnetColor.from_seq(bmp.border_rgb),
        "ClearColor": DotnetColor.from_seq(bmp.clear_color),
        "DefaultRenderClearColor": DotnetColor.from_seq(bmp.default_render_clear_color),
        "BumpScaleFactor": bmp.bump_scale_factor,
        "BumpScaleMipLevel": bmp.bump_scale_mip_level,
        "HeightInMeters": bmp.height_in_meters,
        "MipMapLodBiasDefault": bmp.mip_lod_bias_default,
        "MipMapLowerAlpha": bmp.mip_lower_alpha,
        "MipMapFadeAlphas": [i.value for i in bmp.mip_fade_alphas],
        "DefaultTexCoordRotate": bmp.default_uv.rotate,
        "DefaultTexCoordScale": DotnetVec2(*bmp.default_uv.scale),
        "DefaultTexCoordTrans": DotnetVec2(*bmp.default_uv.trans),
        "GrassId": bmp.grass_id,
        "GrassIdTexCoordRotate": bmp.grass_uv.rotate,
        "GrassIdTexCoordSize": DotnetVec2(*bmp.grass_uv.scale),
        "GrassIdTexCoordTrans": DotnetVec2(*bmp.grass_uv.trans),
    }


def texture_set_to_config(ts):
    """Asset names of the referenced assets (None where unset)."""
    def n(m):
        return m.name if m else None
    return {
        "ColorImage": n(ts.color_image),
        "NormalImage": n(ts.normal_image),
        "RoughnessImage": n(ts.roughness_image),
        "ColorTexture": n(ts.color_texture),
        "NormalTexture": n(ts.normal_texture),
        "RoughnessTexture": n(ts.roughness_texture),
    }


def _check_constants():
    for name, value in vars(AssetProp).items():
        if not name.startswith("_"):
            assert value in AssetProperties.__annotations__, f"AssetProp.{name} -> '{value}' missing"


# --------------------------------------------------------------------------
# Selecting a preview plane makes its material the active asset
# --------------------------------------------------------------------------

_owner = object()   # msgbus owner token (needed to unsubscribe)


def _on_active_object_changed():
    context = bpy.context
    obj = context.view_layer.objects.active
    if obj is None or "gbx_preview_for" not in obj:
        return  # not a preview plane: keep the current active asset

    mat = obj.active_material          # follows renames, unlike the stored name
    if mat is None or not mat.tm_asset_properties.is_asset:
        return

    scene = context.scene
    if scene.tm_active_material != mat:
        scene.tm_active_material = mat
        # make sure the sidebar panels redraw
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()


def _subscribe():
    bpy.msgbus.clear_by_owner(_owner)
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, "active"),
        owner=_owner,
        args=(),
        notify=_on_active_object_changed,
    )


@persistent
def _on_load_post(_dummy):
    _subscribe()            # msgbus subscriptions are dropped whenever a .blend is loaded
    heal_image_paths()      # re-point managed images after a library folder was copied


def register_active_sync():
    _subscribe()
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)


def unregister_active_sync():
    bpy.msgbus.clear_by_owner(_owner)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------

classes = (
    TM_TexCoordProps,
    TM_FloatItem,
    AssetBitmapProperties,
    AssetImgFileProperties,
    AssetTextureSetProperties,
    AssetUvAnimProperties,
    AssetCustomMaterialProperties,
    AssetImageProperties,
    AssetProperties,
)


def register_asset_properties():
    for cls in classes:
        bpy.utils.register_class(cls)

    _check_constants()
    bpy.types.Material.tm_asset_properties = PointerProperty(type=AssetProperties)
    bpy.types.Scene.tm_new_asset_name = StringProperty(name="Name", default="NewAsset")
    bpy.types.Scene.tm_active_material = PointerProperty(
        type=bpy.types.Material,
        poll=lambda s, m: getattr(m.tm_asset_properties, AssetProp.IS_ASSET, False))
    bpy.types.Image.tm_image_asset = PointerProperty(type=AssetImageProperties)
    bpy.types.Scene.tm_asset_copy_images = BoolProperty(
        name="Copy Images", default=False,
        description="Copy imported images into this library's image store, so they can be changed without touching "
                    "the original (e.g. default assets in Items/_BlenderAssets). Off: images inside the game Items "
                    "folder are referenced in place (no duplicate), other images are copied anyway")

    register_active_sync()


def unregister_asset_properties():
    unregister_active_sync()

    del bpy.types.Scene.tm_asset_copy_images
    del bpy.types.Image.tm_image_asset
    del bpy.types.Scene.tm_active_material
    del bpy.types.Scene.tm_new_asset_name
    del bpy.types.Material.tm_asset_properties

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
