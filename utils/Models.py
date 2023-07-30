import bpy

class ExportedItem: 
    name:                   str  = ""
    name_raw:               str  = ""
    r_path:                 str  = "" # relative path in Items/ folder or Work/Items w/o extension
    item_path:              str  = ""
    icon_path:              str  = ""
    fbx_path:               str  = ""
    objects:                list[bpy.types.Object] = None
    color_tag:              str  = ""
    tm_itemxml_template:    str  = ""
    scale:                  int  = 1
    physic_hack:            bool = True
    mesh_xml:               str  = "Not generated!"
    item_xml:               str  = "Not generated!"
    game_is_trackmania2020: bool = False
    game_is_maniaplanet:    bool = False
    game:                   str  = ""