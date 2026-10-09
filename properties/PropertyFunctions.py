import bpy
from .PropertyIdentifiers import ObjectProp, CollectionProp
from ..utils.Constants import *

#msg bus (rename callbacks)
def subscribe_to_msgbus(owner: object, type: type, property: str, callback: callable):
    """
    Subscribes to a property change in Blender's RNA system using the message bus.

    :param owner: The owner object for the subscription.
    :param property: The name of the property to subscribe to.
    :param callback: The function to call when the property changes.
    """
    bpy.msgbus.clear_by_owner(owner)
    bpy.msgbus.subscribe_rna(
        key=(type, property),
        owner=owner,
        args=(),
        notify=callback,
    )

# enum
def enum_items(enum_cls):
    return [(e.value, e.value, "") for e in enum_cls]

#lod
def get_lod_indexes(obj) -> list[int]:
    return sorted(e.value for e in getattr(obj, ObjectProp.LOD_INDEXES))

def set_lod_indexes(obj, indexes) -> None:
    coll = getattr(obj, ObjectProp.LOD_INDEXES)
    coll.clear()
    for i in sorted(set(indexes)):
        coll.add().value = i

