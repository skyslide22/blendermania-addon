from ...properties.AttachmentProperties import (
    AttachmentOptionProperties,
    ATTACHMENT_INT_KEYS,
    ATTACHMENT_KNOWN_KEYS,
)
from ...properties.PropertyIdentifiers import CollectionProp
from ...utils.Constants import *
from ...utils.Attachments import get_attachment_locators
from ...ui.widgets.lists import *
from ...ui.widgets.foldouts import *


# callbacks for list items
def _attachment_entry_added(owner, item, index):
    # preselect the first known key which is not used in this option yet
    used = {e.key for e in owner.entries if e != item}
    item.key = next((k for k in ATTACHMENT_KNOWN_KEYS if k not in used), item.key)

def register_attachment_callbacks():
    register_list_hooks(AttachmentOptionProperties, "entries", after_add=_attachment_entry_added)

def unregister_attachment_callbacks():
    unregister_list_hooks(AttachmentOptionProperties, "entries")


# draw methods
def draw_attachment_entry(layout, item, index):
    row = layout.row(align=True)
    key_row = row.row(align=True)
    key_row.ui_units_x = 6
    key_row.prop(item, "key", text="")
    if item.key in ATTACHMENT_INT_KEYS:
        row.prop(item, "intValue", text="")
    else:
        row.prop(item, "value", text="")

def draw_attachment_option(layout, item, index):
    box = layout.box()
    box.label(text=f"Option {index + 1}")
    item_list(box,
              item,
              "entries",
              draw_item=draw_attachment_entry,
              add=WIDGET_ADD_BUTTON_BOTTOM,
              add_text="Add Key/Value",
              show_move=True,
              inline_buttons=True)

def draw_attachments_collection(layout, collection):
    """settings of the _attachments_ collection itself"""
    col = layout.column(align=True)
    col.label(text="Collections inside define one attachment each.", icon='INFO')
    col.label(text="Nothing inside is exported as fbx.")

def draw_attachment_collection(layout, collection):
    """settings of a collection which defines one attachment"""
    attachment = getattr(collection, CollectionProp.ATTACHMENT)

    row = layout.row(align=True)
    row.prop(attachment, "layout", text="Layout")

    # locators: empties, generated particle points, ...
    locator_count = len(get_attachment_locators(collection))
    row = layout.row(align=True)
    row.label(text=f"Attachment points: {locator_count}", icon='EMPTY_AXIS')
    if locator_count == 0:
        layout.label(text="Add empties or objects with particle systems (position/rotation)", icon='INFO')

    option_count = len(attachment.options)
    box = layout.box()
    box.label(text=f"Options ({option_count})", icon='PRESET')
    item_list(box,
              attachment,
              "options",
              draw_item=draw_attachment_option,
              add=WIDGET_ADD_BUTTON_BOTTOM,
              add_text="Add Option",
              show_move=True, show_clipboard=True,
              copy_on_add=WIDGET_NEW_ENTRY_MODE_LAST)
