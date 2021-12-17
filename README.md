# Blender Addon for Trackmania and ManiaPlanet
This addon is for Blender 2.93+, it will simplify all necessary steps and help you with:
- creating icons from different perspectives
- creating materials which have the game textures applied in blender automatically (if downloaded)
- download and install the game textures(zip/dds) and the nadeoimporter.exe with one click
- export your blocks with one click in the right folders (collections are exported, not the objects!)
- convert your exported blocks with one click, with progressbar and error reporting
- documentation (in dev...) https://images.mania.exchange/com/skyslide/Blender-Addon-Tutorial/


## How to install
- download the repository as zip
- go to blender 2.93+, edit > preferences > addons > install from file (the zip file)
- enable addon
- addon is in the 3d viewport
- open the right panel (N KEY) and then choose the tab TrackmaniaAddon (90° rotated)

## How to set it up
- set your author name
- choose between maniaplanet and trackmania2020
- select the Nadeo.ini file of your game, try automatic search...
- download the nadeoimporter for your game
- optionally download the textures for your game/environment

## Materials
- materials contain the information for the textures
- you can have multiple materials for any object
- assign the geometry in editmode to the selected material
- materials needs to be created with my addon

## Collections (your objects)
- your objects need to be in a collection, always
- the objectnames do not matter at all, except the special ones
- the collection name is the actual name of your object
- collections can be nested, tree is used for exporting (folders in Work/Items/)
- special objects are:
- - \_socket\_whatever   (no uvs, no materials, spawn of your waypoint)
- - \_trigger\_whatever  (no uvs, no materials, the mesh which triggers the waypoint)
- - \_notvisible\_whatever  (the mesh will not be visible, but will be collidable)
- - \_notcollidable\_whatever  (the mesh will be visible but not collidable, the player will be able to go through it.)
- - whatever_Lod0 (optional, highpoly version, visible when near)
- - whatever_Lod1 (optional, lowpoly  version, visible when far away)
- choose the waypoint type for your collection by rightclick, color:
- - blue:   checkpoint
- - red:    finish
- - green:  start
- - yellow: multilap (startfinish)

## Export & Convert
- you can choose between export and export & convert
- export will only export the fbx file (the collection(s))
- export visible will export all visible objects (the collection(s))
- export selected will export all selected objects (the collection(s))
- & convert will convert the fbx to GameBox (gbx)
- this addon does not convert fbx to gbx, nadeoimporter.exe is required & used for this!
- collections with names which start with \_ignore will not be exported, even if visible or selected
- collections can have different scales, using the following syntax:
- - \<yourcollectionname\>\_#SCALE\_\<from:number\>to\<to:number\>\_x\<step:number\>
- - example: deco_tree_normal_#SCALE_7to2_x6
- - will result in:
- - - deco_tree_normal_#7.fbx - size 6/6 (100%)
- - - deco_tree_normal_#6.fbx - size 5/6 (83.33%)
- - - deco_tree_normal_#5.fbx - size 4/6 (66,66%)
- - - deco_tree_normal_#4.fbx - size 3/6 (50%)
- - - deco_tree_normal_#3.fbx - size 2/6 (33%)
- - - deco_tree_normal_#2.fbx - size 1/6 (16.66%)
- - may be useful for decoration(plants, trees, letters, sings...)
- - 7 and 2 are free choosen, you can use any numbers
- - 7 is the convention in the trackmania2 rpg titlepack for scaling

## Uvmaps
- most materials require the BaseMateral & LightMap uvlayer
- basematerial stores the texture information
- lightmap stores the uv data for lightmap calculation
- lightmap is corrupt if any uv islands overlap
- fast lightmap generation can be done with KEY U > "smart uv project"
- the blender build in KEY U > "lightmap pack" is totally wrong, do not use it!

contact me on discord, in the #importer-help channel, http://discord.mania.exchange

