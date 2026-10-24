import bpy

addon_keymaps = []


def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("view3d.tm_export_v2", "E", "PRESS", ctrl=True, shift=True)
        kmi.properties.scope = "SELECTED"
        addon_keymaps.append((km, kmi))

        # export selected collections (active collection in the 3D view, Outliner selection in the Outliner)
        for name, space in (("3D View", "VIEW_3D"), ("Outliner", "OUTLINER")):
            km = kc.keymaps.new(name=name, space_type=space)
            kmi = km.keymap_items.new("view3d.tm_export_v2", "E", "PRESS", ctrl=True, shift=True, alt=True)
            kmi.properties.scope = "COLLECTIONS"
            addon_keymaps.append((km, kmi))


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()