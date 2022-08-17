import bpy

class ExportedItem: 
    name:         str = ""
    r_path:       str = "" # relative path in Items/ folder or Work/Items w/o extension
    item_path:    str = ""
    icon_path:    str = ""
    fbx_path:     str = ""
    coll:         bpy.types.Collection = None
    scale:        int = 1
    physic_hack:  True

    def __init__(self, coll: bpy.types.Collection):
        self.coll = coll