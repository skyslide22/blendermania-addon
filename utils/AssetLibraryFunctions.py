import hashlib
import os
import re
import shutil
from pathlib import Path
import uuid

import bpy

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

IMAGE_NODE_NAME = "GBX_Image"
PREVIEW_SPACING = 3.0       # distance between preview planes
PREVIEW_Y = -20.0
PREVIEW_COLLECTION = "GBX_Previews"

DEFAULT_REL_BITMAP_DIR = "Texture"
DEFAULT_REL_IMAGE_DIR = "Texture/Image"     # managed image store (relative to library root)

# VERIFY these extensions. IMAGE is a guess.
GBX_EXT = {"BITMAP": ".Texture.Gbx"}
# Prefix that turns a library-relative path into the path stored in gbx files.
GAME_PREFIX = ""

# usage -> preview mode
USAGE_MODE = {}
for _n in ("Color", "ColorFloat", "Render", "RenderFloat", "Render16b", "Light", "LightAlpha"):
    USAGE_MODE[_n] = "COLOR"
for _n in ("Alpha", "Depth", "Vertex", "TexCoord"):
    USAGE_MODE[_n] = "DATA"           # non-color data, shown as plain image
for _n in ("NxNyNz", "NxNy", "NormPal8b", "NormPal16b", "NormRxG0BzAy",
           "NormR0GyBzAx", "NormXYZ0YZX", "BumpTxTy"):
    USAGE_MODE[_n] = "NORMAL"         # image is already a normal-ish map
for _n in ("Height2DuDv", "Height2DuDvLumi", "Height2NxNyNz", "Height2NxNy",
           "Height2NormPal8b", "Height2DuDv1", "Height2RxG0BzAy",
           "Height2BumpTxTy", "Height2R0GyBzAx", "DispH01"):
    USAGE_MODE[_n] = "HEIGHT"         # source image is a height map (converted on import)
USAGE_MODE["Usage31"] = "NORMAL"      # TM2020 normal maps (_N)
USAGE_MODE["Usage36"] = "DATA"        # TM2020 roughness/metal maps (_R)


# --------------------------------------------------------------------------
# Basic accessors
# --------------------------------------------------------------------------

def active_asset(context):
    return context.scene.tm_active_material


def all_assets():
    return [m for m in bpy.data.materials if m.tm_asset_properties.is_asset]


# --------------------------------------------------------------------------
# Paths / hashing
# --------------------------------------------------------------------------

def resolve_abs(path, id_block=None):
    """Absolute path of a '//'-style Blender path, resolved against the library for linked data."""
    return bpy.path.abspath(path, library=getattr(id_block, "library", None))


def blend_dir(id_block=None):
    """Folder of the .blend that owns this datablock (library file for linked data)."""
    lib = getattr(id_block, "library", None)
    fp = bpy.path.abspath(lib.filepath) if lib else bpy.data.filepath
    if not fp:
        raise RuntimeError("Save the .blend first (the image store lives next to it)")
    return Path(os.path.normpath(fp)).parent


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_image_file(img):
    """Absolute file for a record. rel_path is library-root-relative (no '//' prefix)."""
    return blend_dir(img) / img.tm_image_asset.rel_path


def _relative_inside(root, path):
    """Library-relative posix path if `path` is inside `root` (case-insensitive on Windows)."""
    # compare AND relativize the resolved paths: Documents/Trackmania is often a link to another drive,
    # relpath of the unresolved pair raises "path is on mount 'H:', start on mount 'C:'"
    real_path, real_root = os.path.realpath(path), os.path.realpath(root)
    if os.path.normcase(real_path).startswith(os.path.normcase(real_root) + os.sep):
        return Path(os.path.relpath(real_path, real_root)).as_posix()
    return None


def _store_path(root, original_name, sha):
    """Target file in the store; adds a short hash only if the name is taken by different content."""
    name = re.sub(r"[^\w.\-]", "_", original_name)
    store = root / DEFAULT_REL_IMAGE_DIR
    store.mkdir(parents=True, exist_ok=True)
    cand = store / name
    if cand.exists() and sha256_file(cand) != sha:
        cand = store / f"{cand.stem}_{sha[:8]}{cand.suffix}"
    return cand


def gbx_rel_path(mat):
    """Library-relative path of the gbx this asset writes."""
    p = mat.tm_asset_properties
    if p.asset_type not in GBX_EXT:
        return ""
    rel = p.relative_path.strip().replace("\\", "/").lstrip("/")
    if not rel:
        safe = re.sub(r"[^\w.\-]", "_", mat.name)
        rel = f"{DEFAULT_REL_BITMAP_DIR}/{safe}{GBX_EXT[p.asset_type]}"
    if ".." in Path(rel).parts:
        raise ValueError(f"'{mat.name}': path must not contain '..': {rel}")
    return rel


# --------------------------------------------------------------------------
# Preview material
# --------------------------------------------------------------------------

def _node(nt, idname, name, loc):
    n = nt.nodes.get(name)
    if n is None:
        n = nt.nodes.new(idname)
        n.name = name
        n.location = loc
    return n


def _channel_image(image_asset, texture_asset):
    """Image for one TextureSet channel: the Image asset wins, else the Bitmap asset's image."""
    for m in (image_asset, texture_asset):
        if m is not None and m.tm_asset_properties.image is not None:
            return m.tm_asset_properties.image
    return None


def _private_image(mat, channel, src, colorspace):
    """Per-material copy of src, so its color space never changes the shared image
    (and thereby other assets' previews)."""
    key = f"GBX_TS_{mat.name}_{channel}"
    img = bpy.data.images.get(key)
    if src is None:
        if img is not None and img.users == 0:
            bpy.data.images.remove(img)
        return None
    if img is not None and img.filepath != src.filepath:
        bpy.data.images.remove(img)
        img = None
    if img is None:
        img = src.copy()
        img.name = key
        img.tm_image_asset.is_managed = False     # not a store record
        img.use_fake_user = False
    try:
        img.colorspace_settings.name = colorspace
    except (TypeError, RuntimeError):
        pass
    return img


def _setup_alpha(mat):
    """texture alpha visible in Eevee (viewport + render) and Cycles: dithered (alpha clip like the game),
    transparent shadows. Both settings are ignored by Cycles, which uses the BSDF Alpha directly."""
    for attr, value in (("surface_render_method", "DITHERED"), ("use_transparent_shadow", True),
                        ("blend_method", "HASHED"), ("shadow_method", "HASHED")):   # last two: pre-4.2 names
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, value)
            except (TypeError, AttributeError):
                pass


def _sync_textureset_preview(mat):
    nt = mat.node_tree
    if "GBX_TS_BSDF" not in nt.nodes:
        nt.nodes.clear()
    ts = mat.tm_asset_properties.texture_set

    coord = _node(nt, "ShaderNodeTexCoord", "GBX_TS_TexCoord", (-900, 0))
    bsdf = _node(nt, "ShaderNodeBsdfPrincipled", "GBX_TS_BSDF", (150, 0))
    out = _node(nt, "ShaderNodeOutputMaterial", "GBX_TS_Output", (450, 0))
    nmap = _node(nt, "ShaderNodeNormalMap", "GBX_TS_NormalMap", (-150, -450))

    L = nt.links
    L.clear()
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    _setup_alpha(mat)

    channels = (
        ("Color", ts.color_image, ts.color_texture, "sRGB", 200),
        ("Normal", ts.normal_image, ts.normal_texture, "Non-Color", -100),
        ("Roughness", ts.roughness_image, ts.roughness_texture, "Non-Color", -400),
    )
    for name, image_asset, texture_asset, cs, y in channels:
        tex = _node(nt, "ShaderNodeTexImage", f"GBX_TS_{name}", (-450, y))
        img = _private_image(mat, name, _channel_image(image_asset, texture_asset), cs)
        tex.image = img
        if img is None:
            continue
        L.new(coord.outputs["UV"], tex.inputs["Vector"])
        if name == "Color":
            L.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            L.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])     # leaf cutouts
        elif name == "Normal":
            L.new(tex.outputs["Color"], nmap.inputs["Color"])
            L.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            L.new(tex.outputs["Color"], bsdf.inputs["Roughness"])


def sync_preview(mat):
    """Idempotent: (re)builds the preview node tree from mat.tm_asset_properties.
    The builder is chosen by asset type in PREVIEW_BUILDERS (below)."""
    if mat is None:
        return
    if mat.node_tree is None:          # Blender 5.x materials normally have one already
        mat.use_nodes = True
    PREVIEW_BUILDERS.get(mat.tm_asset_properties.asset_type, _sync_image_preview)(mat)


def _sync_image_preview(mat):
    """Preview for BITMAP / IMAGE: one image texture, shaded according to the bitmap usage."""
    nt = mat.node_tree
    if IMAGE_NODE_NAME not in nt.nodes:
        nt.nodes.clear()               # first build: drop the default nodes

    coord = _node(nt, "ShaderNodeTexCoord", "GBX_TexCoord", (-900, 0))
    mapping = _node(nt, "ShaderNodeMapping", "GBX_Mapping", (-700, 0))
    tex = _node(nt, "ShaderNodeTexImage", IMAGE_NODE_NAME, (-450, 0))
    bump = _node(nt, "ShaderNodeBump", "GBX_Bump", (-150, -250))
    nmap = _node(nt, "ShaderNodeNormalMap", "GBX_NormalMap", (-150, -450))
    bsdf = _node(nt, "ShaderNodeBsdfPrincipled", "GBX_BSDF", (150, 0))
    out = _node(nt, "ShaderNodeOutputMaterial", "GBX_Output", (450, 0))

    props = mat.tm_asset_properties
    bmp = props.bitmap if props.asset_type == "BITMAP" else None
    mode = USAGE_MODE.get(bmp.usage, "COLOR") if bmp else "COLOR"

    # image color space
    if tex.image:
        try:
            tex.image.colorspace_settings.name = "sRGB" if mode == "COLOR" else "Non-Color"
        except (TypeError, RuntimeError):
            pass

    # mapping node <- default tex coords
    if bmp:
        uv = bmp.default_uv
        mapping.inputs["Location"].default_value = (uv.trans[0], uv.trans[1], 0.0)
        mapping.inputs["Rotation"].default_value = (0.0, 0.0, uv.rotate)  # assumes radians
        mapping.inputs["Scale"].default_value = (uv.scale[0], uv.scale[1], 1.0)

        nmap.inputs["Strength"].default_value = max(bmp.bump_scale_factor, 0.0)
        bump.inputs["Strength"].default_value = min(max(bmp.bump_scale_factor, 0.0), 1.0)
        bump.inputs["Distance"].default_value = bmp.height_in_meters

    # wiring (the tree is fully ours, so rebuild all links)
    L = nt.links
    L.clear()
    L.new(coord.outputs["UV"], mapping.inputs["Vector"])
    L.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    if mode in ("COLOR", "DATA", "HEIGHT"):
        L.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if mode == "NORMAL":
        L.new(tex.outputs["Color"], nmap.inputs["Color"])
        L.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    elif mode == "HEIGHT":
        L.new(tex.outputs["Color"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


# asset type -> preview builder(mat). Add new asset types here; unknown types use the image preview.
PREVIEW_BUILDERS = {
    "BITMAP": _sync_image_preview,
    "IMAGE": _sync_image_preview,
    "TEXTURESET": _sync_textureset_preview,
}


def assign_image(mat, img):
    """Show the record in the preview node and re-sync the material."""
    sync_preview(mat)                       # makes sure the nodes exist
    tex = mat.node_tree.nodes.get(IMAGE_NODE_NAME)
    if tex is not None:
        tex.image = img                     # None clears it
    sync_preview(mat)                       # applies color space etc.


def on_render_prop_changed(self, context):
    """update= callback. self is the PropertyGroup; id_data is the owning Material."""
    mat = self.id_data
    if isinstance(mat, bpy.types.Material):
        sync_preview(mat)


def on_image_changed(self, context):
    """update= callback for AssetProperties.image (self is the AssetProperties group)."""
    mat = self.id_data
    if isinstance(mat, bpy.types.Material):
        assign_image(mat, self.image)


# --------------------------------------------------------------------------
# Preview plane
# --------------------------------------------------------------------------

def get_preview_collection(scene):
    coll = bpy.data.collections.get(PREVIEW_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(PREVIEW_COLLECTION)
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def find_free_location(scene):
    """First slot along the preview row that has no object near it."""
    half = PREVIEW_SPACING * 0.5
    for i in range(10000):
        x = i * PREVIEW_SPACING
        taken = any(
            abs(o.location.x - x) < half and abs(o.location.y - PREVIEW_Y) < half
            for o in scene.objects
        )
        if not taken:
            return (x, PREVIEW_Y, 0.0)
    return (0.0, PREVIEW_Y, 0.0)


def spawn_preview_plane(context, mat):
    scene = context.scene
    mesh = bpy.data.meshes.new(f"{mat.name}_mesh")
    verts = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()

    uv = mesh.uv_layers.new(name="UVMap")
    for loop, co in zip(mesh.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = co

    mesh.materials.append(mat)

    obj = bpy.data.objects.new(f"Preview_{mat.name}", mesh)
    obj.location = find_free_location(scene)
    obj["gbx_preview_for"] = mat.name
    get_preview_collection(scene).objects.link(obj)
    return obj      # found again via get_preview_object(mat)


def get_preview_object(mat):
    """Preview plane of a local asset. Looked up by name instead of an ID pointer: a pointer
    makes drag/drop from the asset browser drag the object (and its mesh) along, which
    duplicates the library."""
    return next((o for o in bpy.data.objects
                 if o.library is None and o.get("gbx_preview_for") == mat.name), None)


# --------------------------------------------------------------------------
# Image store (records live on bpy.types.Image as img.tm_image_asset)
# --------------------------------------------------------------------------

def local_records():
    """Records of THIS file only (linked ones belong to another library's store)."""
    return [i for i in bpy.data.images if i.library is None and i.tm_image_asset.is_managed]


def is_reference_record(img):
    """record pointing at a file outside this library (e.g. shared default assets in Items/_BlenderAssets):
    used in place, never copied into or deleted from the store"""
    rel = img.tm_image_asset.rel_path
    return rel.startswith("../") or Path(rel).is_absolute()


def find_record_by_sha(sha, copies_only=False):
    return next((i for i in local_records()
                 if i.tm_image_asset.sha256 == sha and not (copies_only and is_reference_record(i))), None)


def _blender_path(rel):
    """datablock path of a record: '//'-relative, absolute for references on another drive"""
    return rel if Path(rel).is_absolute() else "//" + rel


def _game_items_dir():
    """Documents/Trackmania/Items (None if the game folder is unknown): files there can be referenced by gbx files"""
    try:
        from .Functions import get_game_doc_path_items
        path = Path(get_game_doc_path_items())
    except Exception:
        return None
    return path if path.is_absolute() and path.is_dir() else None


def _reference_rel_path(root, src):
    """rel_path of a referenced file: relative to the library ('../..'), absolute if on another drive"""
    try:   # resolved paths: a linked Items folder must not turn a same-drive reference absolute
        return Path(os.path.relpath(os.path.realpath(src), os.path.realpath(root))).as_posix()
    except ValueError:
        return Path(os.path.realpath(src)).as_posix()


def _make_record(dst, rel, sha, original_name):
    try:
        img = bpy.data.images.load(str(dst), check_existing=True)
        img.filepath = _blender_path(rel)             # keep the datablock path relative
    except RuntimeError:                              # Blender can't read this DDS variant
        img = bpy.data.images.new(dst.name, 8, 8)     # placeholder, record still valid
    img.use_fake_user = True
    rec = img.tm_image_asset
    rec.is_managed = True
    rec.sha256 = sha
    rec.rel_path = rel
    rec.original_name = original_name
    return img


def import_image_file(filepath, copy=True):
    """
    Register an image in the store and return (record_image, created_new).
    copy=True:  copied into the store (once), so it can be edited without touching the original.
    copy=False: images inside the game Items folder (e.g. shared default assets in _BlenderAssets) are
                referenced in place, no duplicate. Other images are still copied: gbx files can only
                reference files inside Items.
    """
    src = Path(filepath)
    if not src.is_file():
        raise FileNotFoundError(src)
    root = blend_dir()
    sha = sha256_file(src)

    existing = find_record_by_sha(sha, copies_only=copy)
    if existing:                                      # dedupe: same content already registered
        dst = root / existing.tm_image_asset.rel_path
        if not dst.is_file():                         # file was deleted from the store -> restore
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return existing, False

    rel = _relative_inside(root, src)
    items = _game_items_dir()
    if rel:                                           # already inside the library: register, don't copy
        dst = src
    elif not copy and items is not None and _relative_inside(items, src):
        dst = src                                     # reference in place (shared asset inside Items)
        rel = _reference_rel_path(root, src)
    else:
        dst = _store_path(root, src.name, sha)
        if not dst.exists():
            shutil.copy2(src, dst)
        rel = dst.relative_to(root).as_posix()

    return _make_record(dst, rel, sha, src.name), True


def heal_image_paths():
    """After a library was copied elsewhere: re-point record images at their relative path."""
    if not bpy.data.filepath:
        return
    root = blend_dir()
    for img in local_records():
        rel = img.tm_image_asset.rel_path
        want = os.path.normcase(os.path.normpath(str(root / rel)))
        have = os.path.normcase(os.path.normpath(bpy.path.abspath(img.filepath)))
        if want != have:
            img.filepath = _blender_path(rel)
            try:
                img.reload()
            except RuntimeError:
                pass


def users_of(img):
    return [m for m in bpy.data.materials
            if m.tm_asset_properties.is_asset and m.tm_asset_properties.image == img]


def purge_unused_images(delete_files=False):
    removed = 0
    for img in local_records():
        if users_of(img):
            continue
        if delete_files and bpy.data.filepath and not is_reference_record(img):  # never delete shared originals
            f = resolve_image_file(img)
            if f.is_file():
                f.unlink()
        bpy.data.images.remove(img)
        removed += 1
    return removed


def image_poll(self, img):
    return img.tm_image_asset.is_managed

# for property polling
def poll_asset(asset_type=None):
    def poll(self, mat):
        p = mat.tm_asset_properties
        return p.is_asset and (asset_type is None or p.asset_type == asset_type)
    return poll

# --------------------------------------------------------------------------
# Asset removal (call from your remove operator)
# --------------------------------------------------------------------------

def remove_asset_data(mat, delete_files=False):
    """
    Removes preview plane + mesh, the material, and any image no longer used.
    Set scene.tm_active_material = None in the operator before calling this.
    Returns the number of purged image records.
    """
    p = mat.tm_asset_properties
    obj = get_preview_object(mat)
    if obj:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    if mat.asset_data:
        mat.asset_clear()
    bpy.data.materials.remove(mat)
    return purge_unused_images(delete_files)


# --------------------------------------------------------------------------
# Export data: unique images once, assets reference them by image_id
# --------------------------------------------------------------------------

def collect_export_data(assets, config_fns, verify=True):
    """
    config_fns maps asset type -> callable(props) -> dict, passed in by the caller so this
    file never imports the properties file (circular):
        {"BITMAP": lambda p: bitmap_to_config(p.bitmap), "IMAGE": lambda p: {}}
    """
    images, out_assets, problems, seen = {}, [], [], {}

    for mat in assets:
        p = mat.tm_asset_properties
        if p.asset_type == "TEXTURESET":          # container only: no image, no files
            fn = config_fns.get(p.asset_type)
            out_assets.append({"name": mat.name, "type": p.asset_type, "image_id": "",
                               "gbx_out": "", "gbx_game_path": "",
                               "config": fn(p) if fn else {}})
            continue

        img = p.image
        if img is None or not img.tm_image_asset.is_managed:
            problems.append(f"'{mat.name}': no image assigned")
            continue

        rec = img.tm_image_asset
        try:
            file = resolve_image_file(img)
            gbx_rel = gbx_rel_path(mat)
            gbx_abs = blend_dir(mat) / gbx_rel if gbx_rel else None
        except (RuntimeError, ValueError) as e:
            problems.append(str(e))
            continue

        if not file.is_file():
            problems.append(f"'{mat.name}': image file missing: {file}")
            continue
        if verify and sha256_file(file) != rec.sha256:
            problems.append(f"'{mat.name}': image changed on disk since import: {file}")

        if gbx_rel:     # IMAGE assets write no gbx (empty path), so they can't collide
            key = os.path.normcase(gbx_rel)
            if key in seen:
                problems.append(f"'{mat.name}' and '{seen[key]}' write the same file: {gbx_rel}")
                continue
            seen[key] = mat.name

        image_id = rec.sha256[:16]
        images.setdefault(image_id, {
            "id": image_id,
            "file": str(file),                         # absolute, for copying/reading
            "game_path": GAME_PREFIX + rec.rel_path,   # what gbx files reference
        })

        fn = config_fns.get(p.asset_type)
        out_assets.append({
            "name": mat.name,
            "type": p.asset_type,
            "image_id": image_id,
            "gbx_out": str(gbx_abs) if gbx_abs else "",
            "gbx_game_path": GAME_PREFIX + gbx_rel if gbx_rel else "",
            "config": fn(p) if fn else {},
        })

    return {"images": list(images.values()), "assets": out_assets, "problems": problems}


def copy_images_once(data, dest_root):
    """Optional: copy each UNIQUE image to an export folder, mirroring game_path."""
    for im in data["images"]:
        dst = Path(dest_root) / im["game_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or sha256_file(dst) != sha256_file(im["file"]):
            shutil.copy2(im["file"], dst)


#   ---
#   Catalogue
#   ---


# fixed namespace: never change it, or all catalog IDs change
CATALOG_NS = uuid.UUID("6f1c2a7e-3b54-4d0e-9a47-5d2f8a1c9e10")

# asset_type -> catalog path ("/" makes a hierarchy in the asset browser)
CATALOGS = {
    "BITMAP": "Textures/Bitmaps",
    "IMAGE": "Textures/Images",
    "TEXTURESET": "Textures/TextureSets",
}

HEADER = (
    "# This is an Asset Catalog Definition file for Blender.\n"
    "#\n"
    "# Empty lines and lines starting with `#` will be ignored.\n"
    "# The first non-ignored line should be the version indicator.\n"
    '# Other lines are of the format "UUID:catalog/path/for/assets:simple catalog name"\n'
    "\n"
    "VERSION 1\n"
    "\n"
)


def catalog_uuid(path):
    return str(uuid.uuid5(CATALOG_NS, path))


def ensure_catalogs(library_root):
    """Append missing catalog definitions; never touches existing lines."""
    f = Path(library_root) / "blender_assets.cats.txt"
    text = f.read_text(encoding="utf-8") if f.is_file() else HEADER
    if not text.endswith("\n"):
        text += "\n"

    added = False
    for path in CATALOGS.values():
        u = catalog_uuid(path)
        if u not in text:
            text += f"{u}:{path}:{path.replace('/', '-')}\n"
            added = True

    if added:
        f.write_text(text, encoding="utf-8")
    return added


def assign_catalog(mat, add_tag=True):
    """Put the asset into its type's catalog and tag it (tags allow cross-catalog filtering)."""
    data = mat.asset_data
    if data is None:
        return
    path = CATALOGS.get(mat.tm_asset_properties.asset_type)
    if path is None:
        return

    data.catalog_id = catalog_uuid(path)

    if add_tag:
        tag = path.split("/")[-1]
        if tag not in [t.name for t in data.tags]:
            data.tags.new(tag, skip_if_exists=True)


def assign_all_catalogs():
    for mat in bpy.data.materials:
        if mat.library is None and mat.tm_asset_properties.is_asset:
            assign_catalog(mat)


def sync_all_catalogs(library_root):
    ensure_catalogs(library_root)
    assign_all_catalogs()


