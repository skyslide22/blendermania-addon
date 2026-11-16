
from operator import index

from ...properties.AssetProperties import TM_FloatItem

from ..widgets.lists import list_inspector, register_row_drawer, unregister_row_drawer


def _section(layout, idname, label, closed=True):
    header, body = layout.panel(idname, default_closed=closed)
    header.label(text=label)
    return body  # None while collapsed


def _draw_uv(layout, uv):
    layout.prop(uv, "rotate")
    layout.prop(uv, "scale")
    layout.prop(uv, "trans")


def draw_bitmap(layout, bmp):
    if body := _section(layout, "gbx_bmp_usage", "Usage & Size", closed=False):
        body.prop(bmp, "usage")
        col = body.column(align=True)
        col.prop(bmp, "render_size_mul")
        col.prop(bmp, "render_size_div")
        body.prop(bmp, "pixel_update")

    if body := _section(layout, "gbx_bmp_colors", "Colors"):
        body.prop(bmp, "border_rgb")
        body.prop(bmp, "clear_color")
        body.prop(bmp, "default_render_clear_color")

    if body := _section(layout, "gbx_bmp_bump", "Bump / Height"):
        body.prop(bmp, "bump_scale_factor")
        body.prop(bmp, "bump_scale_mip_level")
        body.prop(bmp, "height_in_meters")

    if body := _section(layout, "gbx_bmp_mips", "Mipmaps"):
        body.prop(bmp, "mip_lod_bias_default")
        body.prop(bmp, "mip_lower_alpha")
        body.label(text="Fade Alphas")
        row = body.row()

        list_inspector(body, 
                       bmp, 
                       "mip_fade_alphas",
                       "mip_fade_alphas_index",
                        rows=3,
                        show_move=False, 
                        # show_clipboard=True, 
                        copy_on_add='SELECTED')


    if body := _section(layout, "gbx_bmp_uv", "Default Tex Coords"):
        _draw_uv(body, bmp.default_uv)

    if body := _section(layout, "gbx_bmp_grass", "Grass ID"):
        body.prop(bmp, "grass_id")
        _draw_uv(body, bmp.grass_uv)


def _draw_float_item_row(layout, item, index):
    layout.label(text="", icon='DOT') 
    layout.prop(item, "value", text=f"Mip {index}", emboss=False)


def register():
    register_row_drawer(TM_FloatItem, _draw_float_item_row)

def unregister():
    unregister_row_drawer(TM_FloatItem)