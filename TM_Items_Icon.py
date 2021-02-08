import bpy
import os.path
import re
import math
import statistics as stats
from bpy.types import (
    Collection, Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .MP_Functions import *

from . import *



    
class MP_OT_Icon_Create(Operator):
    bl_idname = "view3d.createicon"
    bl_label = "help"
    bl_desciption = "create icons"
   
    def execute(self, context):
        createIcons(colnames=[])
        return {"FINISHED"}
    
    
class MP_OT_Icon_Create_Test(Operator):
    bl_idname = "view3d.createicontest"
    bl_label = "help"
    bl_desciption = "make a test render, dont save image, only show render result"
   
    def execute(self, context):
        createIconsTest()
        return {"FINISHED"}
    
   
class MP_PT_Icons(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Create Icon"
    bl_idname = "OBJECT_PT_MP_Icons"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    def draw(self, context):
        
        mp_props = context.scene.mp_props
        mats = bpy.data.materials
        selObjs = bpy.context.selected_objects

        layout = self.layout
        
        if not isIniValid():
            row = layout.row().label(text=errorMsgNadeoIni, icon="ERROR")
            return
        
        row=layout.row()
        row.label(text="test icon", icon_value=getIcon("CAM_FRONT"))
                
        row = layout.row()
        row.prop(mp_props, "LI_icon_camPos", text="Cam pos", expand=True, icon_only=True)
        
        row = layout.row()
        row.prop(mp_props, "NU_icon_camPosScale", text="Cam pos/scale") 
        
        row = layout.row()
        row.prop(mp_props, "NU_icon_margin", text="Icon space usage", ) 
        
        row = layout.row()
        row.prop(mp_props, "LI_icon_resInPX", text="Image dimensions in pixel", expand=True ) 
        
        row = layout.row()
        row.prop(mp_props, "CB_selectedItemsOnly", text="Selected items only", ) 
        
        row = layout.row()
        row.prop(context.scene.render, "film_transparent", text="Transparent background", ) 
                
        camstyle= mp_props.LI_icon_camPos
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("view3d.createicon",   text="Create icons", icon="VIEW_CAMERA")
        
        if len(selObjs) > 0:
            if selObjs[0].name not in ["ICON_OBJ", "ICON_CAM"]:
                row = layout.row()
                row.operator("view3d.createicontest",   text="Icon preview, no save", icon="VIEWZOOM")
        else:
            row = layout.row()
            row.label(text="Select an object for preview shoot")
        
        row = layout.row()
        row.separator(factor=spacerFac)
        
        
        
        
        



def createIconsTest():
    """create preview of icon (Render result), just skip saving and use only current selected object"""
    obj = bpy.context.selected_objects[0]
    col = obj.users_collection[0]
    
    deleteObj("ICON_OBJ")
    baseobj = str(obj.name)
    
    pro__print("iconobj exists:", "ICON_OBJ" in [o.name for o in bpy.data.objects])
    
    colname = col.name
    objname = "ICON_OBJ"
    objname = combineObjsOfCollection(colname=colname, newobjname=objname)
    
    pro__print("create test icon")
    pro__print("iconobj exists:", objname)
    
    if objname is not False:
        createIcon(objname=objname, save=False)
    
    if objname is False:
        deleteObj("ICON_OBJ")
          
    deselectAll()
    bpy.context.scene.objects[baseobj].select_set(True)
    pro__print("")



def createIcons(colnames: list=[]):
    """main function to create icons of all visible objects/collections"""
    s = bpy.context.scene
    vlay = bpy.context.view_layer
    
    mp_props = bpy.context.scene.mp_props
    onlySelected = mp_props.CB_icon_onlySelObjs
        
    isViewAlreadyCamera = False
    
    if colnames == []:
        for obj in bpy.context.scene.objects:
            selectAll()
            if obj.select_get() is True:
                for col in obj.users_collection:
                    if col.name.lower() not in notAllowedColnames:
                        colnames.append(col.name)
    
    colnames = set(colnames)
    
    
    #set view to camera if view was camera
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            viewtype = area.spaces[0].region_3d.view_perspective
            isViewAlreadyCamera = True if viewtype == "CAMERA" else False
    
    #create icon
    for colname in colnames:
        deleteObj("ICON_OBJ")
        objname = "ICON_OBJ"
        objname = combineObjsOfCollection(colname=colname, newobjname=objname)
        if objname is not False:
            createIcon(objname=objname)
    
    #delete dummy
    deselectAll()
    if "ICON_OBJ" in s.objects:
        s.objects["ICON_OBJ"].select_set(True)
        bpy.ops.object.delete()



def createIcon(objname, save=True, switchToCamView=True) -> None:
    """create icon of given name of object"""
    objCol      = bpy.context.scene.objects[objname].users_collection[0]
    objCol.name = fixName(name=objCol.name)
    
    bpy.context.space_data.overlay.show_overlays = False
    
    setIconCam(switchToCamView=switchToCamView)
    prepareIconObj(objname)
    renderIcon(objname=objname, save=save)
    bpy.context.space_data.overlay.show_overlays = True

     
     

def setRenderRes(self="", context="") -> None:
    """set render resolution based on user input [32,64,128,256]"""
    s = bpy.context.scene
    res = s.mp_props.LI_icon_resInPX
    s.render.resolution_x = \
    s.render.resolution_y = int(res)
     


def setIconCamByChange(self, context) -> None:
    """this function is called from a update function, calls setIconCam(save=False) 
    and needs to takes self and context as arguments"""
    selObjs = bpy.context.selected_objects
    
    if len(selObjs) > 0:
            
        if selObjs[0].type != "MESH": #avoid ZeroDivisionError (fe: empty, camera etc objects)
            deselectAll()
            setIconCam(switchToCamView=False)
            bpy.context.space_data.overlay.show_overlays = True
            return
        
        if "ICON_OBJ" in bpy.data.objects and selObjs[0].name == "ICON_OBJ":
            bpy.data.objects["ICON_OBJ"].select_set(True)
            bpy.ops.object.delete()
            return
        
        
        selObjName = selObjs[0].name
        createIcon(objname=selObjName, save=False, switchToCamView=False)
        deselectAll()
        bpy.data.objects[selObjName].select_set(True)
        
    else:
        setIconCam(switchToCamView=False)

    
    
def setIconCam(switchToCamView: bool=True) -> None:
    """position/align the camera relative to the object"""
    refreshPanels()
    
    s = bpy.context.scene
    mp_props = s.mp_props
    objs = bpy.data.objects
    cams = bpy.data.cameras
        
    if "ICON_CAM" in [o.name for o in objs]:
        deselectAll()
        cam = objs["ICON_CAM"]
        cam.select_set(True)
        
    else:
        newCam  = cams.new("cam")
        cam = objs.new("ICON_CAM", newCam)
        s.collection.objects.link(cam)
    
    
    camPosScale = mp_props.NU_icon_camPosScale
    camDis = camPosScale * 2
    camPos = mp_props.LI_icon_camPos
    camData = {}
    
    camFrontPos     = (0, -camDis, 0)
    camFrontRot     = (r(90), 0, 0)
    
    camRightPos     = (camDis, 0, 0)
    camRightRot     = (r(90), 0, r(90))
    
    camLeftPos      = (-camDis, 0, 0)
    camLeftRot      = (r(90), 0, -r(90))
    
    camTopPos       = (0, 0, camDis)
    camTopRot       = (0, 0, 0)
    
    camClassicPos   = camFrontPos
    camClassicRot   = camFrontRot
    
    if camPos == "FRONT":   camData = {"pos": camFrontPos,  "rot": camFrontRot}
    if camPos == "LEFT":    camData = {"pos": camLeftPos,   "rot": camLeftRot}
    if camPos == "RIGHT":   camData = {"pos": camRightPos,  "rot": camRightRot}
    if camPos == "TOP":     camData = {"pos": camTopPos,    "rot": camTopRot}
    if camPos == "CLASSIC": camData = {"pos": camClassicPos,"rot": camClassicRot}
    
    cam.rotation_euler = camData["rot"]
    camPosStep = mp_props.NU_icon_camPosScale
    cam.location = (camData["pos"][0], camData["pos"][1], camData["pos"][2])
    
    cam.data.type = "ORTHO" #2d_view
    cam.data.ortho_scale = camPosStep #view 64x64
    cam.data.display_size = camPosScale / 5
    cam.data.show_limits = False
    
    s.camera = cam #set scene cam
    
    if switchToCamView:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break

    

def scaleObjToMatchCamPosRotScale(objname: str):
    """scales/rotates object to fit the camera space"""
    s = bpy.context.scene
    mp_props = s.mp_props
    obj = bpy.context.scene.objects[objname]
    dimX = obj.dimensions[0] * 100
    dimY = obj.dimensions[1] * 100
    dimZ = obj.dimensions[2] * 100
    
    biggestDim = max(dimX, dimY, dimZ)
    
    camPosScale = mp_props.NU_icon_camPosScale
    maxDim = camPosScale
    camPos = mp_props.LI_icon_camPos
    
    maxDims = {"x": 1, "y": 1, "z": 1}
    
    margin = mp_props.NU_icon_margin / 100
    
    if camPos == "FRONT":
        dimFac = camPosScale / max(dimX, dimZ) * margin 
        camPosScale = camPosScale if dimY >= camPosScale else dimY
        obj.dimensions = (dimX*dimFac, dimY*dimFac, dimZ*dimFac)
        
    if camPos == "LEFT" or camPos == "RIGHT":
        dimFac = camPosScale / max(dimY, dimZ) * margin 
        camPosScale = camPosScale if dimX >= camPosScale else dimX
        obj.dimensions = (dimX*dimFac, dimY*dimFac, dimZ*dimFac)
        
    if camPos == "TOP":
        dimFac = camPosScale / max(dimX, dimY) * margin 
        obj.dimensions = (dimX*dimFac, dimY*dimFac, dimZ*dimFac)
        
    if camPos == "CLASSIC":
        obj.rotation_euler = (r(35.3), r(30), -r(35.3))
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
        obj.location = (0,0,0) # reassign origin to center cuz of special rotation of object
       
        dimX = obj.dimensions[0]
        dimY = obj.dimensions[1]
        dimZ = obj.dimensions[2]
        
        biggestDim = max(dimX, dimY, dimZ)
        dimFac = camPosScale / biggestDim * margin
        obj.dimensions = (dimX*dimFac, dimY*dimFac, dimZ*dimFac)
        
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)



def prepareIconObj(objname):
    """copy the icon object, call function,
    to set scale/rotation of the copied object to fit cam settings"""
    objs = bpy.data.objects
    deselectAll()
    
    obj = objs[objname]
    obj.select_set(True)
    
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
    
    obj = bpy.context.selected_objects[0]
    obj.location = (0,0,0)
    
    scaleObjToMatchCamPosRotScale(objname=obj.name, )

    

def renderIcon(objname, save=True):
    """finally render the icon of the object using openGL(viewport render), not eevee/cycles!"""
    fbxname = bpy.context.scene.objects[objname].users_collection[0].name
    setRenderRes()
    relpath     = '/'.join(getCollectionHierachyOfObj(objname=objname, hierachystart=False))
    savepath    = f"{getDocPathWorkItems()}{relpath}/Icon/{fbxname}"
    s = bpy.context.scene
    s.render.filepath = savepath
    s.render.image_settings.file_format = 'TARGA'

    visObjs = []

    #get visibility status of all objects
    for obj in bpy.context.scene.objects:
        visObjs.append({
            "name":    str(obj.name),
            "render":  bool(obj.hide_render),
            "viewport":bool(obj.hide_viewport)
        })
    
    hideAll()
    
    iconObj = bpy.context.scene.objects[objname]
    iconObj.hide_render     = False
    iconObj.hide_viewport   = False
    
    bpy.context.space_data.overlay.show_extras = True
    if save:    bpy.ops.render.opengl(write_still=True) # render + save
    
    #set visibility status of all objs back to before iconshoot
    unhideSelected(objs=visObjs)
    
    
    

def combineObjsOfCollection(colname: str, newobjname: str="MERGED_COLLECTION_OBJ") -> str:
    """Combines all object in a collection to one object, returns objname"""
    cols    = bpy.data.collections
    col     = cols[colname]
    allObjs = col.all_objects
    
    deselectAll()
    
    objsToDuplicate = []
    for obj in allObjs:
        if  obj.type == "MESH" and \
            "ICON_OBJ" not in obj.name and not \
            obj.name.lower().startswith("trigger") or obj.name.lower().startswith("_trigger_"):
                try:
                    obj.select_set(True)
                    objsToDuplicate.append(obj)
                except:
                    pass
    
    if len(objsToDuplicate) == 0: 
        return False
    
    deleteObj(objname="ICON_OBJ")
    
    duplicatedObjs = []
    for obj in objsToDuplicate:
        deselectAll()
        setActiveObj(obj.name)
        obj.select_set(True)
        bpy.ops.object.duplicate()
        objname = bpy.context.object.name
        allObjs = bpy.data.objects
        duplicatedObjs.append(allObjs[objname])
    
    deselectAll()
    
    for obj in duplicatedObjs:
        obj.select_set(True)
        
    activeObj = bpy.data.objects[duplicatedObjs[0].name] if len(duplicatedObjs) > 0 else bpy.data.objects[objsToDuplicate[0].name]
    bpy.context.view_layer.objects.active = activeObj
    bpy.ops.object.join()
    bpy.context.object.name = newobjname
    
    deselectAll()    
    return newobjname
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    