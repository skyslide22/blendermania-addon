import bpy
import webbrowser

from ..utils.Constants import ICON_INFO

class OT_UIWikiLink(bpy.types.Operator):
    """export and or convert an item"""
    bl_idname = "view3d.bm_wiki_link"
    bl_description = "Open wiki"
    bl_label = "Open wiki"
    
    wiki_link : bpy.props.StringProperty(name="wiki_link")

    def execute(self, context):
        webbrowser.open(f"https://github.com/skyslide22/blendermania-addon/wiki/{self.wiki_link}", new=2)

        return {"FINISHED"}


def add_ui_wiki_icon(ui: bpy.types.UILayout, wiki_link: str):
    ot = ui.operator(OT_UIWikiLink.bl_idname, text="", icon=ICON_INFO)
    ot.wiki_link = wiki_link
    return