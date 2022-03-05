# Blender Addon for Trackmania and ManiaPlanet
This addon is for Blender 3.0+, it will simplify all necessary steps and help you with:
- creating icons
- creating materials for the games
- install NadeoImporter.exe with one click
- install textures with one click
- install assets with one click
- export items(collections) as .fbx
- convert exported .fbx files to .gbx (game format)
- documentation https://github.com/skyslide22/blender-addon-for-trackmania-and-maniaplanet/wiki

## Todo list
- https://github.com/skyslide22/blender-addon-for-trackmania-and-maniaplanet/projects/1

## Video Turorials 
- video by MattDTO: https://www.youtube.com/watch?v=JXINd6oBTw4
- 1h30m workshop by Juice & Ealipse https://www.youtube.com/watch?v=EIJKl_q6w10 
- fyi: detailed tutorial video by me(skyslide) is on the todo list... (2025) </sarcasm>


## How to install
- download the latest version on the right side of this website
- go to blender, top left cornder > edit > preferences > addons > install from file (the latest release zip file you downloaded)
- enable addon
- addon can be found in any 3d viewport window
- open the right panel with <kbd>N</kbd> and then choose the tab TrackmaniaAddon (90° rotated)

## How to set it up
- set your author name, displayed on IX
- choose between maniaplanet and trackmania2020
- select the Nadeo.ini file of your game (Where ManiaPlanet.exe or Trackmania.exe is...
- install the latest NadeoImporter (shipped with the addon)
- optionally download the textures/assets-library for your game/environment

## Materials
- materials contain the information for the textures
- you can have multiple materials for any object
- assign the geometry in editmode to the selected material
- materials needs to be created with my addon
- materials can be found in the installed assets library, open a asset browser window for that

## Collections (your objects)
- your objects need to be in a collection, always
- collections can be nested, tree is used for exporting (folders in Work/Items/)
- the collection name is the actual name of your object
- the object names do not matter at all, except the special ones
- special objects are:
- - \_socket\_whatever   (no uvs, no materials, spawn of your waypoint)
- - \_trigger\_whatever  (no uvs, no materials, the mesh which triggers the waypoint)
- - \_notvisible\_whatever  (the mesh will not be visible, but will be collidable)
- - \_notcollidable\_whatever  (the mesh will be visible but not collidable, the player will be able to go through it.)
- - \_ignore\_whatever  (mesh will be completely ignored during the import process.)
- - whatever_Lod0 (optional, highpoly version, visible when near)
- - whatever_Lod1 (optional, lowpoly  version, visible when far away)
- change the waypoint of your collection in the "Object Manipulation" panel

## Export & Convert
- you can choose between export and export & convert
- export will only export the fbx file (the collection(s))
- export visible will export all visible objects (the collection(s))
- export selected will export all selected objects (the collection(s))
- & convert will convert the fbx to GameBox (gbx)
- this addon does not convert fbx to gbx, NadeImporter.exe is required & used for this!
- collections with names which start with \_ignore will not be exported, even if visible or selected
- collections can be exported with multiple scales, no need to duplicate:

## Uvmaps
- most materials require the BaseMateral & LightMap uvlayer
- basematerial stores the texture information, overlapping does not matter
- lightmap stores the uv data for lightmap calculation
- lightmap should not have any overlapping uv islands
- fast lightmap generation can be done with <kbd>U</kbd> > "Smart uv project"
- the blender build in <kbd>U</kbd> > "lightmap pack" is totally wrong, do not use it!

contact me on discord, in the #importer-help channel, http://discord.mania.exchange

