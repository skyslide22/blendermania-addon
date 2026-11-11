import bpy

from ...utils.CollectionTypes import TYPES_WITH_TOGGLE
from ...utils.FunctionsV2 import can_convert_to_collection_type


TOGGLES_PER_ROW = 3


def draw_collection_type_toggles(layout, collection: bpy.types.Collection, enabled: bool = True) -> None:
    """one toggle button per collection type of the registry (utils/CollectionTypes.py), max TOGGLES_PER_ROW per row"""
    type_defs = [d for d in TYPES_WITH_TOGGLE if d.show_toggle]
    for start in range(0, len(type_defs), TOGGLES_PER_ROW):
        row = layout.row(align=True)
        for type_def in type_defs[start:start + TOGGLES_PER_ROW]:
            sub = row.row(align=True)
            sub.enabled = enabled and can_convert_to_collection_type(collection, type_def.id)
            sub.prop(collection, type_def.toggle_prop, icon=type_def.toggle_icon, toggle=True)
