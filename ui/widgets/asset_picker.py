"""
Asset pointer fields (Bitmap / Image assets) with a search button next to them.

Dragging an asset from the Asset Browser onto an ID field is unreliable (also in plain Blender): the drop
(UI_OT_drop_name -> button_set_string_interactive) types the asset name into the field's fuzzy search box and confirms
the highlighted entry, so with look-alike names (BMP_X_D / _N / _R) and assets only linked during the drop it picks the
wrong asset or nothing. Add-ons can't hook into it. Instead every asset field gets:
- pick button: assigns the asset selected in an Asset Browser (linked if needed)
- search button: assets of the field's type from this file and the default asset library
"""
import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

OWNER_CONTEXT = "tm_pick_owner"

# Blender keeps no reference to enum item strings: they must stay alive while the search popup is open
_items_cache: list = []
_target: dict = {}             # owner + property of the running pick (owner is only in the context during invoke)
_library_names: dict = {}      # default library blend -> (mtime, material names)


def draw_asset_field(layout, owner, prop: str, asset_type: str, **kwargs):
    """layout.prop(owner, prop) + search button; returns the row (for more buttons)"""
    row = layout.row(align=True)
    row.prop(owner, prop, **kwargs)
    sub = row.row(align=True)
    sub.context_pointer_set(OWNER_CONTEXT, owner)
    for idname, icon in ((TM_OT_AssignSelectedAsset.bl_idname, "EYEDROPPER"), (TM_OT_PickAsset.bl_idname, "VIEWZOOM")):
        op = sub.operator(idname, text="", icon=icon)
        op.prop_name = prop
        op.asset_type = asset_type
    return row


def _assign(op, owner, prop: str, mat) -> bool:
    """set the field after checking the asset type (assigning from python bypasses the field's poll)"""
    props = getattr(mat, "tm_asset_properties", None)
    if props is None or not props.is_asset or props.asset_type != op.asset_type:
        label = {"BITMAP": "a Bitmap", "IMAGE": "an Image", "TEXTURESET": "a TextureSet"}
        kind = label.get(props.asset_type, props.asset_type) if props is not None and props.is_asset else "no addon asset"
        op.report({"ERROR"}, f"'{mat.name}' is {kind}, this field needs {label.get(op.asset_type, op.asset_type)}")
        return False
    try:
        setattr(owner, prop, mat)
    except (TypeError, ReferenceError) as e:
        op.report({"ERROR"}, str(e))
        return False
    if getattr(owner, prop, None) != mat:
        op.report({"ERROR"}, f"'{mat.name}' is no {op.asset_type.title()} asset")
        return False
    return True


def _selected_browser_assets(context) -> list:
    """AssetRepresentations selected in the Asset Browsers of all windows (active one first)"""
    found = []
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.ui_type != "ASSETS":
                continue
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region is None:
                continue
            with context.temp_override(window=win, area=area, region=region):
                found += list(getattr(bpy.context, "selected_assets", None) or [])
    return found


def _material_from_asset(asset):
    if asset.id_type != "MATERIAL":
        return None
    if asset.local_id is not None:
        return asset.local_id
    with bpy.data.libraries.load(asset.full_library_path, link=True) as (src, dst):
        dst.materials = [asset.name] if asset.name in src.materials else []
    return dst.materials[0] if dst.materials else None


def _default_library_materials() -> tuple:
    """(blend path, material names) of the default asset library, names cached per file modification"""
    from ...utils.DefaultAssetsLibrary import get_built_default_assets, DEFAULT_ASSETS_BLEND
    root = get_built_default_assets()
    if root is None:
        return None, []
    blend = root / DEFAULT_ASSETS_BLEND
    mtime = blend.stat().st_mtime
    cached = _library_names.get(str(blend))
    if cached is None or cached[0] != mtime:
        with bpy.data.libraries.load(str(blend), link=True) as (src, _dst):
            names = sorted(src.materials, key=str.lower)
        _library_names[str(blend)] = cached = (mtime, names)
    return blend, cached[1]


def _pick_items(self, context):
    from ...utils.DefaultAssetsLibrary import TYPE_PREFIX
    items, seen = [], set()
    for mat in bpy.data.materials:
        props = mat.tm_asset_properties
        if props.is_asset and props.asset_type == self.asset_type:
            source = f"linked from {bpy.path.basename(mat.library.filepath)}" if mat.library else "this file"
            items.append((f"L:{mat.name_full}", mat.name_full, f"{mat.name_full} ({source})",
                          "LINKED" if mat.library else "MATERIAL", len(items)))
            seen.add(mat.name)
    try:
        _blend, names = _default_library_materials()
    except (OSError, RuntimeError):
        names = []
    prefix = TYPE_PREFIX.get(self.asset_type, "")
    for name in names:
        if prefix and name.startswith(prefix) and name not in seen:
            items.append((f"D:{name}", name, f"{name} (default asset library)", "ASSET_MANAGER", len(items)))
    if not items:
        items.append(("NONE", "No assets of this type", "", "INFO", 0))
    _items_cache[:] = items
    return _items_cache


class TM_OT_PickAsset(Operator):
    bl_idname = "tm.pick_asset"
    bl_label = "Pick Asset"
    bl_description = ("Search assets of this type (this file and the default asset library) and assign one. "
                      "More reliable than dragging from the Asset Browser")
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_property = "choice"

    prop_name: StringProperty(options={"HIDDEN"})
    asset_type: StringProperty(options={"HIDDEN"})
    choice: EnumProperty(name="Asset", items=_pick_items)

    def invoke(self, context, event):
        owner = getattr(context, OWNER_CONTEXT, None)
        if owner is None:
            self.report({"ERROR"}, "No asset field")
            return {"CANCELLED"}
        _target.update(owner=owner, prop=self.prop_name)
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        owner = getattr(context, OWNER_CONTEXT, None) or _target.get("owner")
        prop = self.prop_name or _target.get("prop")
        if owner is None or not prop or self.choice == "NONE":
            return {"CANCELLED"}

        kind, _, name = self.choice.partition(":")
        if kind == "L":
            mat = next((m for m in bpy.data.materials if m.name_full == name), None)
        else:
            blend, _names = _default_library_materials()
            if blend is None:
                self.report({"ERROR"}, "Default asset library not installed")
                return {"CANCELLED"}
            with bpy.data.libraries.load(str(blend), link=True) as (_src, dst):
                dst.materials = [name]
            mat = dst.materials[0] if dst.materials else None
        if mat is None:
            self.report({"ERROR"}, f"Asset '{name}' not found")
            return {"CANCELLED"}

        if not _assign(self, owner, prop, mat):
            return {"CANCELLED"}
        _target.clear()
        for area in context.screen.areas if context.screen else []:
            area.tag_redraw()
        return {"FINISHED"}


class TM_OT_AssignSelectedAsset(Operator):
    bl_idname = "tm.assign_selected_asset"
    bl_label = "Use Selected Asset"
    bl_description = ("Assign the asset selected in the Asset Browser (click it there first). "
                      "Replaces drag & drop, which is unreliable for these fields")
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    prop_name: StringProperty(options={"HIDDEN"})
    asset_type: StringProperty(options={"HIDDEN"})

    def execute(self, context):
        owner = getattr(context, OWNER_CONTEXT, None)
        if owner is None:
            return {"CANCELLED"}
        assets = _selected_browser_assets(context)
        if not assets:
            self.report({"WARNING"}, "Select an asset in an Asset Browser first")
            return {"CANCELLED"}
        if len(assets) > 1:
            self.report({"WARNING"}, f"{len(assets)} assets selected, using '{assets[0].name}'")
        mat = _material_from_asset(assets[0])
        if mat is None:
            self.report({"ERROR"}, f"'{assets[0].name}' is no material asset")
            return {"CANCELLED"}
        if not _assign(self, owner, self.prop_name, mat):
            return {"CANCELLED"}
        self.report({"INFO"}, f"Assigned {mat.name}")
        for area in context.screen.areas if context.screen else []:
            area.tag_redraw()
        return {"FINISHED"}


classes = (TM_OT_PickAsset, TM_OT_AssignSelectedAsset)
