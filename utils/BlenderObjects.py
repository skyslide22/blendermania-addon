import bpy

def duplicate_object(obj: bpy.types.Object):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.duplicate(linked=0, mode='TRANSLATION')
    
    return bpy.context.active_object

def move_obj_to_coll(obj: bpy.types.Object, destColl: bpy.types.Collection):
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    
    destColl.objects.link(obj)

def duplicate_object_to(obj: bpy.types.Object, destColl: bpy.types.Collection):
    newObj = duplicate_object(obj)
    move_obj_to_coll(newObj, destColl)
    return newObj