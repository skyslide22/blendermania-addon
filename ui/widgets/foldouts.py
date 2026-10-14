from operator import index

from ...utils.Constants import *


# =============================================================================
# 1. FOLDOUTS
#    Native collapsible headers. No registration needed.
# =============================================================================

FOLDOUT_STYLE_PANEL = 'PANEL'
FOLDOUT_STYLE_FLAT = 'FLAT'

def foldout_toggle(layout, obj, prop, label, enable_prop=None, enable_owner=None, indent=0.0, style=FOLDOUT_STYLE_PANEL):
    """Native foldout header. Returns the layout to draw content into, or None if collapsed.
    indent: horizontal indent in separator units (0 = none, ~2 = visible)."""
    header, body = layout.panel_prop(obj, prop)
    if enable_prop:
        header.prop(enable_owner if enable_owner else obj, enable_prop, text="")
    header.label(text=label)

    if not body:
        return None, header

    if indent > 0:
        if style == FOLDOUT_STYLE_PANEL:
            row = body.row()
        else:
            row = layout.row()
        row.separator(factor=indent)    # horizontal gap
        content = row.column()          # content goes here
    else:
        if style == FOLDOUT_STYLE_PANEL:
            content = body.column()
        else:
            content = layout.column()

    if enable_prop:
        content.active = getattr(enable_owner if enable_owner else obj, enable_prop)
    return content, header
