
import json
import bpy
import re

from bpy.types import (
    Panel,
    Operator,
)

from ..operators.OT_Settings import TM_OT_Settings_OpenMessageBox
from ..utils.Functions  import *
from ..utils.Constants  import * 




class TM_PT_Materials(Panel):
    bl_label = "Materials"
    bl_idname = "OBJECT_PT_TM_Materials"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )

    @classmethod
    def poll(self, context):
        return is_selected_nadeoini_file_name_ok()

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_MATERIAL)
    
    def draw_header_preset(self, context):
        layout = self.layout
        tm_props = get_global_props()
        row = layout.row(align=True)
    
        col = row.column(align=True)
        op = col.operator("view3d.tm_open_messagebox", text="", icon=ICON_QUESTION)
        op.link = ""
        op.title = "Material Infos"
        op.infos = TM_OT_Settings_OpenMessageBox.get_text(
            "Here you can configure your materials",
            "-> Materials need to be created or updated with the addon",
            "-> Materials can have any name, TM_ or MP_ will be added automatically to differ from other materials",
            "-> Materials can have optionally a custom physic, if not set, default will be used",
            "-> Some Materials can be colored (TM2020 only)",
            "-> Some Materials can have a second physic called 'Gameplay' (TM2020 only)",
            "-> Materials need to be linked to an existing material created by nadeo",
            "----> Those materials are pre defined in the NadeoImporerMaterialLib.txt file",
            "-> Materials can have custom, non game, textures (Maniaplanet only)",
        ) 


    def draw_trackmania2020(self, left, right, tm_props, use_physicsId, use_gameplayId, action_is_update) -> None:
        
        left.label(text="Link")
        row = right.row()
        row.prop_search(
            tm_props, "ST_selectedLinkedMat", # value of selection
            bpy.context.scene, "tm_props_linkedMaterials", # list to search in 
            icon=ICON_LINKED,
            text="") 
        
        # TODO disable physicsid based on customxxx materials ??
        left.label(text="Physic")
        row = right.row(align=True)
        col = row.column()
        if use_physicsId:
            col.prop(tm_props, "LI_materialPhysicsId", text="")
        else:
            col.enabled = False
            col.label(text="Disabled")
        col = row.column()
        col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=ICON_CHECKED)

        selected_mat = tm_props.ST_selectedLinkedMat
        can_use_gameplay = selected_mat in LINKED_MATERIALS_COMPATIBLE_WITH_GAMEPLAY_ID
    
        left.label(text="Gameplay")
        row = right.row(align=True)
        col = row.column()
        
        if not can_use_gameplay:
            col.enabled = False
            col.label(text="Not supported")

        elif use_gameplayId:
            col.prop(tm_props, "LI_materialGameplayId", text="")
            col = row.column()
            col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon=ICON_CHECKED)
        
        else:
            col.enabled = False
            col.label(text="Disabled")
            col = row.column()
            col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon=ICON_CHECKED)
            
        
        # custom color for materials starts with "custom"
        can_use_custom_color = selected_mat.lower().startswith("custom")

        left.label(text="Color")
        row = right.row(align=True)
        if can_use_custom_color:
            row.prop(tm_props, "NU_materialCustomColor", text="")
            if action_is_update:
                row.operator("view3d.tm_revertcustomcolor", icon=ICON_UPDATE, text="")
        
        else:
            row.enabled = False
            row.label(text="Not supported")



    def draw_maniaplanet(self, left, right, tm_props, use_physicsId) -> None:
        left.label(text="Envi")
        right.prop(tm_props, "LI_materialCollection", text="")
        
        left.label(text="Physic")
        row = right.row(align=True)
        col = row.column()
        if use_physicsId:
            col.prop(tm_props, "LI_materialPhysicsId", text="")
        else:
            col.enabled = False
            col.label(text="Disabled")
        col = row.column()
        col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=ICON_CHECKED)
        
        left.label(text="Texture")
        right.row().prop(tm_props, "LI_materialChooseSource", expand=True)
        
        using_custom_texture = tm_props.LI_materialChooseSource == "CUSTOM"

        if using_custom_texture:
            left.label(text="Path")
            row=right.row(align=True)
            row.alert = True if "/Items/" not in fix_slash(tm_props.ST_materialBaseTexture) else False
            row.prop(tm_props, "ST_materialBaseTexture", text="")
            row.operator("view3d.tm_clearbasetexture", icon=ICON_CANCEL, text="")

            if row.alert:
                left.label(text="")
                row=right.row()
                row.alert = True
                row.label(text=".dds file in Documents/Maniaplanet/Items/")

            # model
            left.label(text="Model")
            right.row().prop(tm_props, "LI_materialModel", text="")
        

        # link
        else:
            left.label(text="Link")
            right.row().prop_search(
                tm_props, "ST_selectedLinkedMat", # value of selection
                bpy.context.scene, "tm_props_linkedMaterials", # list to search in 
                icon=ICON_LINKED,
                text="") 



    def draw(self, context):

        layout   = self.layout
        tm_props = get_global_props()

        action      = tm_props.LI_materialAction
        mat_name     = tm_props.ST_materialAddName
        mat_name_old  = tm_props.ST_selectedExistingMaterial

        action_is_update = action == "UPDATE"
    
        use_physicsId   = tm_props.CB_materialUsePhysicsId
        use_gameplayId  = tm_props.CB_materialUseGameplayId

        #uncomment it during development if you need to generate new assets library file
        #box = layout.box()
        #row = box.row()
        #row.operator("view3d.tm_createassetlib", text=f"Create {tm_props.LI_gameType} Assets Library", icon="ADD")

        row = layout.row()
        left = row.column(align=True)
        left.scale_x = 0.8
        right = row.column(align=True)

        
        left.label(text="Method")
        right.row().prop(tm_props, "LI_materialAction", expand=True)

        left.separator(factor=2)
        right.separator(factor=2)

        if action_is_update:
            left.label(text="Material")
            right.prop_search(tm_props, "ST_selectedExistingMaterial", bpy.data, "materials", text="") 
    
        left.label(text="Name")
        right.prop(tm_props, "ST_materialAddName", text="")


        if is_game_maniaplanet():
            self.draw_maniaplanet(left, right, tm_props, use_physicsId)


        elif is_game_trackmania2020():
            self.draw_trackmania2020(left, right, tm_props, use_physicsId, use_gameplayId, action_is_update)


        layout.separator(factor=UI_SPACER_FACTOR)

        row = layout.row()
        row.scale_y = 1.5

        if action_is_update:
            row.operator("view3d.tm_updatematerial", text=f"Update {mat_name_old}", icon=ICON_UPDATE)

        else:
            row.operator("view3d.tm_creatematerial", text=f"Create {mat_name}",    icon=ICON_ADD)


        layout.separator(factor=UI_SPACER_FACTOR)


            
        

