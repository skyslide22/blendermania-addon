import bpy
from ..utils.Functions import get_global_props

def render_donwload_progress_bar(layout: bpy.types.UILayout):
    tm_props = get_global_props()
    dlTexRunning = tm_props.CB_DL_ProgressRunning is False

    dlTexError          = tm_props.ST_DL_ProgressErrors
    statusText          = "Downloading..." if not dlTexRunning else "Done" if not dlTexError else dlTexError
    showDLProgressbar   = tm_props.CB_DL_ProgressShow

    if showDLProgressbar:
        row=layout.row()
        row.enabled = False
        row.prop(tm_props, "NU_DL_Progress", text=statusText)