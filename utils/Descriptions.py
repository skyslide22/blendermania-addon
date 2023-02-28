





### MESH XML
### MESH XML
### MESH XML

DESC_MULTI_SCALE_EXPORT = f"""
    You can export your object in multiple scales:
        yourCollectionName_#SCALE_<n1>to<n2>_x<n3>
        n1 = number, where to start from, like 7
        n2 = number, scale to here, like 5 or 10
        n3 = number, the step(division) (4 == 1, .75, .5, .25)
    
    example:
        fancy_finish_ring_#SCALE_7to5_x4
    
    results in:
        fancy_finish_ring_#7.fbx - scale: 1
        fancy_finish_ring_#6.fbx - scale: 0.75
        fancy_finish_ring_#5.fbx - scale: 0.5
    
    7 to 5 are randomly choosen, but a convention in the RPG Titlepack.
    You can also go from 5 to 10, where 5 is the original and 10 the biggest.
    """

DESC_OBJ_SCALE = f"""
    Overwrite the original object scale for your collection(s)
    if enabled, your exported collection is scaled up/down

    be sure to always apply your scale using CRTL+A => apply scale
"""

DESC_LIGHT_POWER = f"""Overwrite the power of all lights"""
DESC_LIGHT_COLOR = f"""Overwrite the color of all lights"""
DESC_LIGHT_RADIUS = f"""Overwrite the radius/distance of all lights"""

DESC_MESH_XML = f"""
    Generate the mesh.xml file.
    This file is mandatory for a convert from fbx to gbx
"""

DESC_MESH_XML_OVERWRITE = f"""
    Overwrite the mesh.xml file.
    disabled:
        mesh.xml file only generated if it does not exist
"""



### ITEM XML
### ITEM XML
### ITEM XML

DESC_ITEM_XML = f"""
    Generate the item.xml file.
    This file is mandatory for a convert from fbx to gbx
"""

DESC_ITEM_XML_OVERWRITE = f"""
    Overwrite the item.xml file.
    disabled:
        item.xml file only generated if it does not exist
"""

DESC_ITEM_XML_GRID_LEVITATION = f"""
    Set the grid and levitation parameters.
    x = horizontal (x,y)
    y = vertical (z)

    if x and or y are 0:
        object sticks to the surface, good for plants, trees     
"""

DESC_ITEM_XML_GHOSTMODE = f"""
    If activated, the item will never be placed "on anything".
    it will completely ignore surrounding blocks and items, 
    going through them if necessary.
""".replace("\n","")

DESC_ITEM_XML_AUTOROTATION = f"""
    If activated, the Map Editor will try to automatically rotate 
    the item you are about to place according to the direction of 
    the surface you are aiming at with the mouse pointer. 
    It can be useful for items which are supposed to stay 
    perpendicular to the ground for example. 
    Note: this will not work if there is any grid snapping, 
    so both Grid Horizontal Size and Grid Vertical Size 
    must be set to 0.
""".replace("\n", "")

DESC_ITEM_XML_NOT_ON_ITEM = f"""
    If activated, the item cannot be placed on another item, 
    it can only be placed on blocks (or in the air, 
    if Fly Step is greater than 0). It is recommended to 
    leave it deactivated.
""".replace("\n", "")

DESC_ITEM_XML_NOT_ON_ITEM = f"""
    When you place an item in the map, the mouse cursor is 
    aiming at a particular point in the map. But how should the 
    item be placed compared to this point? If your item is a cube, 
    should the editor place the item so that the cursor point is 
    at the center of the cube ? Or the center of the bottom face? 
    Or one corner of the cube?

    Pivots are here to answer that question: a pivot is a point of 
    the item that will coincide with the point of the map that is aimed 
    by the cursor.

    An item can have multiple pivots. In that case, the Map Editor 
    might choose automatically one pivot according to the context, 
    or you might be able to press the Q key (A with azerty keyboards) 
    to cycle through the pivots of the current item
""".replace("\n", "")








DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""

DESC_ = f"""
    
"""
