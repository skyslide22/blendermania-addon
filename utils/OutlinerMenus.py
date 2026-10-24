import bpy


_MENUS = (
    bpy.types.OUTLINER_MT_object,               # right-click an object in the Outliner
    bpy.types.OUTLINER_MT_collection,           # right-click a collection in the Outliner
    bpy.types.VIEW3D_MT_object_context_menu,    # right-click in the 3D viewport
)

# collection based export (Outliner selection, or active collection in the 3D viewport)
_COLLECTION_MENUS = (
    bpy.types.OUTLINER_MT_collection,
    bpy.types.VIEW3D_MT_object_context_menu,
)

def _draw_export_entry(self, context):
    self.layout.separator()
    row = self.layout.row()
    row.enabled = bool(context.selected_objects)
    op = row.operator("view3d.tm_export_v2", text="Export Selected (Gbx)", icon="EXPORT")
    op.scope = "SELECTED"


def _draw_export_collections_entry(self, context):
    op = self.layout.operator("view3d.tm_export_v2", text="Export Selected Collections (Gbx)", icon="EXPORT")
    op.scope = "COLLECTIONS"


def register_outliner_menus():
    for menu in _MENUS:
        menu.append(_draw_export_entry)
    for menu in _COLLECTION_MENUS:
        menu.append(_draw_export_collections_entry)

def unregister_outliner_menus():
    for menu in _MENUS:
        menu.remove(_draw_export_entry)
    for menu in _COLLECTION_MENUS:
        menu.remove(_draw_export_collections_entry)