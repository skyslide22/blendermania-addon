import bpy
import gpu
import numpy as np
from gpu_extras.batch import batch_for_shader

from ...properties.AttachmentProperties import (
    AttachmentOptionProperties,
    ATTACHMENT_INT_KEYS,
    ATTACHMENT_KNOWN_KEYS,
    get_podium_slots,
)
from ...properties.PropertyIdentifiers import CollectionProp
from ...utils.Constants import *
from ...utils.Attachments import (
    get_attachment_locators, get_item_attachment_warnings, _empties_source,
    get_attachment_placeholder_kind, get_placeholder_object,
)
from ...utils.FunctionsV2 import get_item_root, is_attachment_collection, is_collection_ignored
from ...ui.widgets.lists import *
from ...ui.widgets.foldouts import *


# callbacks for list items
def _attachment_entry_added(owner, item, index):
    # preselect the first known key which is not used in this option yet
    used = {e.key for e in owner.entries if e != item}
    item.key = next((k for k in ATTACHMENT_KNOWN_KEYS if k not in used), item.key)

def register_attachment_callbacks():
    global _draw_handle
    register_list_hooks(AttachmentOptionProperties, "entries", after_add=_attachment_entry_added)
    if _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_attachment_placeholders, (), 'WINDOW', 'POST_VIEW')

def unregister_attachment_callbacks():
    global _draw_handle
    unregister_list_hooks(AttachmentOptionProperties, "entries")
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None


# viewport preview of the placeholder models (original material colors) at the empties of every attachment,
# nothing is added to the scene/item. Which model is shown depends on the attachment (see PLACEHOLDER_RULES).
# Particle points already show the placeholder as particle render object. Needs the placeholder objects to exist
# (created by the "Show Placeholder" button or the export).
_draw_handle = None
_batch_cache: dict = {}
_LIGHT_DIR = np.array([0.35, 0.45, 0.82], dtype=np.float32) / np.linalg.norm([0.35, 0.45, 0.82])

def _material_image(mat):
    """the color image of the material (image node linked to the base color, else any image node)"""
    tree = getattr(mat, "node_tree", None) if mat else None
    if tree is None:
        return None
    bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    node = None
    if bsdf is not None and "Base Color" in bsdf.inputs and bsdf.inputs["Base Color"].is_linked:
        node = bsdf.inputs["Base Color"].links[0].from_node
    if node is None or node.type != 'TEX_IMAGE':
        node = next((n for n in tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)
    image = getattr(node, "image", None)
    if image is None or not image.size[0] or not image.size[1]:
        return None
    return image

def _material_color(mat) -> tuple[float, float, float, float]:
    """base color of the material (principled bsdf of the fbx import), falls back to the viewport color"""
    if mat is None:
        return (0.8, 0.8, 0.8, 1.0)
    # viewport color is what the solid viewport (and particle instances) show
    viewport = tuple(mat.diffuse_color)
    if any(abs(c - 0.8) > 0.01 for c in viewport[:3]):
        return viewport
    tree = getattr(mat, "node_tree", None)
    if tree is not None:
        bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is not None and "Base Color" in bsdf.inputs:
            base = bsdf.inputs["Base Color"]
            if not base.is_linked:
                return tuple(base.default_value)
            # linked to an image: use its average color
            node = base.links[0].from_node
            image = getattr(node, "image", None)
            if image is not None and image.size[0] and image.size[1]:
                px = np.empty(image.size[0] * image.size[1] * image.channels, dtype=np.float32)
                image.pixels.foreach_get(px)
                avg = px.reshape(-1, image.channels).mean(axis=0)
                return (float(avg[0]), float(avg[1]), float(avg[2]), 1.0)
    return viewport

def _get_placeholder_batch(mesh):
    key = (mesh.name, len(mesh.vertices), len(mesh.polygons), len(mesh.materials))
    batch = _batch_cache.get(key)
    if batch is None:
        mesh.calc_loop_triangles()
        tri_count = len(mesh.loop_triangles)
        verts = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", verts)
        tri_verts = np.empty(tri_count * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get("vertices", tri_verts)
        normals = np.empty(tri_count * 3, dtype=np.float32)
        mesh.loop_triangles.foreach_get("normal", normals)
        mat_index = np.empty(tri_count, dtype=np.int32)
        mesh.loop_triangles.foreach_get("material_index", mat_index)

        palette = np.array([_material_color(m) for m in mesh.materials] or [(0.8, 0.8, 0.8, 1.0)], dtype=np.float32)
        mat_index = np.clip(mat_index, 0, len(palette) - 1)
        # constant material colors are linear -> display
        disp = np.power(np.clip(palette[mat_index][:, :3], 0.0, 1.0), 1.0 / 2.2)

        # textured materials: sample the image at the uv centroid of each triangle
        uv_layer = mesh.uv_layers.active
        if uv_layer is not None:
            uvs = np.empty(len(mesh.loops) * 2, dtype=np.float32)
            uv_layer.uv.foreach_get("vector", uvs)
            uvs = uvs.reshape(-1, 2)
            tri_loops = np.empty(tri_count * 3, dtype=np.int32)
            mesh.loop_triangles.foreach_get("loops", tri_loops)
            centroid = uvs[tri_loops.reshape(-1, 3)].mean(axis=1)
            for index, mat in enumerate(mesh.materials):
                image = _material_image(mat)
                sel = mat_index == index
                if image is None or not sel.any():
                    continue
                w, h, ch = image.size[0], image.size[1], image.channels
                px = np.empty(w * h * ch, dtype=np.float32)
                image.pixels.foreach_get(px)
                px = px.reshape(h, w, ch)[:, :, :3]
                x = np.clip((centroid[sel, 0] % 1.0 * w).astype(np.int32), 0, w - 1)
                y = np.clip((centroid[sel, 1] % 1.0 * h).astype(np.int32), 0, h - 1)
                disp[sel] = np.clip(px[y, x], 0.0, 1.0)

        # simple fixed light so the shape is readable
        shade = 0.45 + 0.55 * np.clip(normals.reshape(-1, 3) @ _LIGHT_DIR, 0.0, 1.0)
        rgb = disp * shade[:, None]
        rgba = np.concatenate([rgb, np.ones((tri_count, 1), dtype=np.float32)], axis=1)

        pos = verts.reshape(-1, 3)[tri_verts]
        col = np.repeat(rgba, 3, axis=0).astype(np.float32)
        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": pos, "color": col})
        _batch_cache.clear() if len(_batch_cache) > 16 else None
        _batch_cache[key] = batch
    return batch

def _draw_attachment_placeholders():
    # placeholder kind -> world matrices of the empties of all attachments showing it
    by_kind: dict[str, list] = {}
    for c in bpy.context.scene.collection.children_recursive:
        if not is_attachment_collection(c) or c.hide_viewport or is_collection_ignored(c) or c.get("tm_placeholder_hidden"):
            continue
        kind = get_attachment_placeholder_kind(getattr(c, CollectionProp.ATTACHMENT, None))
        if kind:
            by_kind.setdefault(kind, []).extend(_empties_source(c))
    if not by_kind:
        return

    shader = gpu.shader.from_builtin('SMOOTH_COLOR')
    gpu.state.depth_test_set('LESS_EQUAL')
    for kind, matrices in by_kind.items():
        obj = get_placeholder_object(kind)
        if obj is None or obj.type != 'MESH' or not matrices:
            continue
        batch = _get_placeholder_batch(obj.data)
        for matrix in matrices:
            gpu.matrix.push()
            gpu.matrix.multiply_matrix(matrix)
            batch.draw(shader)
            gpu.matrix.pop()
    gpu.state.depth_test_set('NONE')


# draw methods
def draw_attachment_entry(layout, item, index):
    row = layout.row(align=True)
    key_row = row.row(align=True)
    key_row.ui_units_x = 6
    key_row.prop(item, "key", text="")
    if item.key in ATTACHMENT_INT_KEYS:
        row.prop(item, "intValue", text="")
    else:
        row.prop(item, "value", text="")

def draw_attachment_option(layout, item, index):
    box = layout.box()
    box.label(text=f"Option {index + 1}")
    item_list(box,
              item,
              "entries",
              draw_item=draw_attachment_entry,
              add=WIDGET_ADD_BUTTON_BOTTOM,
              add_text="Add Key/Value",
              show_move=True,
              inline_buttons=True)

def draw_attachments_collection(layout, collection):
    """settings of the _attachments_ collection itself"""
    col = layout.column(align=True)
    col.label(text="Collections inside define one attachment each.", icon='INFO')
    col.label(text="Nothing inside is exported as fbx.")
    preset_row = layout.row(align=True)
    preset_row.context_pointer_set("tm_attachments_collection", collection)
    preset_row.operator("view3d.tm_load_attachments_preset", text="Insert from Preset...", icon=ICON_IMPORT)
    item = get_item_root(collection, bpy.context.scene)
    if item is not None:
        _draw_warnings(layout, get_item_attachment_warnings(item))

def _draw_warnings(layout, warnings):
    if not warnings:
        return
    warn_box = layout.box()
    warn_box.alert = True   # red
    for warning in warnings:
        warn_box.label(text=warning, icon='ERROR')

def draw_attachment_collection(layout, collection):
    """settings of a collection which defines one attachment"""
    attachment = getattr(collection, CollectionProp.ATTACHMENT)

    row = layout.row(align=True)
    row.prop(attachment, "layout", text="Layout")
    preset_row = layout.row(align=True)
    preset_row.context_pointer_set("tm_attachment", attachment)
    preset_row.operator("view3d.tm_load_attachment_preset", text="Insert from Preset...", icon=ICON_IMPORT)

    # locators: empties, generated particle points, ...
    locator_count = len(get_attachment_locators(collection))
    row = layout.row(align=True)
    row.label(text=f"Attachment points: {locator_count}", icon='EMPTY_AXIS')
    if locator_count == 0:
        layout.label(text="Add empties or objects with particle systems (position/rotation)", icon='INFO')
    ph_row = layout.row(align=True)
    ph_row.context_pointer_set("tm_attachment_collection", collection)
    ph_row.operator("view3d.tm_attachment_particle_placeholder", text="Show Placeholder", icon=ICON_OBJECT)
    ph_row.operator("view3d.tm_attachment_hide_placeholder", text="Hide Placeholder", icon='HIDE_ON')

    option_count = len(attachment.options)
    warnings = []
    if get_podium_slots(attachment) is not None:
        item = get_item_root(collection, bpy.context.scene)
        if item is not None:
            warnings = get_item_attachment_warnings(item)
    _draw_warnings(layout, warnings)
    box = layout.box()
    box.label(text=f"Options ({option_count})", icon='PRESET')
    item_list(box,
              attachment,
              "options",
              draw_item=draw_attachment_option,
              add=WIDGET_ADD_BUTTON_BOTTOM,
              add_text="Add Option",
              show_move=True, show_clipboard=True,
              copy_on_add=WIDGET_NEW_ENTRY_MODE_LAST)
