import bpy

from ...properties.PropertyIdentifiers import CollectionProp
from ...utils.FunctionsV2 import get_item_root
from ...utils.Variants import get_variant_issues, get_variant_name
from ...ui.widgets.lists import *
from .attachments import draw_attachment_entry


def _draw_messages(layout, errors: list[str], warnings: list[str]) -> None:
    for messages, icon in ((errors, 'CANCEL'), (warnings, 'ERROR')):
        if not messages:
            continue
        box = layout.box()
        box.alert = True   # red
        for message in messages:
            box.label(text=message, icon=icon)

def draw_item_mode(layout, item: bpy.types.Collection) -> None:
    """item mode (single / variants) of an item collection"""
    layout.prop(item, CollectionProp.ITEM_MODE, text="Item Mode", expand=True)
    errors, warnings = get_variant_issues(item)
    _draw_messages(layout, errors, warnings)

def draw_variant_collection(layout, collection: bpy.types.Collection) -> None:
    """settings of a collection of type Variant"""
    variant = getattr(collection, CollectionProp.VARIANT)

    layout.label(text=f"Variant: {get_variant_name(collection)}", icon='DUPLICATE')
    layout.prop(variant, "hidden_in_manual_cycle", toggle=True)

    box = layout.box()
    box.label(text=f"Tags ({len(variant.tags.entries)})", icon='PRESET')
    item_list(box,
              variant.tags,
              "entries",
              draw_item=draw_attachment_entry,
              add=WIDGET_ADD_BUTTON_BOTTOM,
              add_text="Add Tag",
              show_move=True,
              inline_buttons=True)

    item = get_item_root(collection, bpy.context.scene)
    if item is not None:
        errors, warnings = get_variant_issues(item)
        _draw_messages(layout, errors, warnings)
