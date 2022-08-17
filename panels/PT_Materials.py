
import json
import bpy
import re

from bpy.types import (
    Panel,
    Operator,
)
from ..utils.Functions  import *
from ..utils.Constants  import * 




class TM_PT_Materials(Panel):
    bl_label = "Material Creation/Update"
    bl_idname = "OBJECT_PT_TM_Materials"
    locals().update( PANEL_CLASS_COMMON_DEFAULT_PROPS )


    def draw_header(self, context):
        layout = self.layout
        layout.label(icon=ICON_MATERIAL)
    

    def draw(self, context):

        layout   = self.layout
        tm_props = get_global_props()
        
        if requireValidNadeoINI(self) is False: return

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


        # choose action & mat name
        layout.row().prop(tm_props, "LI_materialAction", expand=True)

        if action_is_update:
            layout.row().prop_search(tm_props, "ST_selectedExistingMaterial", bpy.data, "materials") 
    
        matcol = layout.column(align=True)
        matcol.prop(tm_props, "ST_materialAddName")

        # row = layout.row()
        # row.enabled = True if not tm_props.CB_converting else False
        # row.prop(tm_props, "LI_gameType", text="Game")





        if is_game_maniaplanet():
            matcol.prop(tm_props, "LI_materialCollection", text="Collection")
            
            enable = True if use_physicsId else False
            icon   = ICON_CHECKED if enable else ICON_UNCHECKED

            row = matcol.row(align=True)
            col = row.column()
            col.enabled = enable
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=ICON_CHECKED)
            
            layout.separator(factor=UI_SPACER_FACTOR)

            # choose custom tex or linked mat
            row = layout.row(align=True)
            # col = row.column()
            # col.label(text="Source:")

            # col = row.column()
            # row = col.row()
            row.prop(tm_props, "LI_materialChooseSource", expand=True)
            
            using_custom_texture = tm_props.LI_materialChooseSource == "CUSTOM"

            # basetexture
            if using_custom_texture:
                row = layout.row(align=True)
                row.alert = True if "/Items/" not in fixSlash(tm_props.ST_materialBaseTexture) else False
                row.prop(tm_props, "ST_materialBaseTexture", text="Location")
                row.operator("view3d.tm_clearbasetexture", icon=ICON_CANCEL, text="")

                if row.alert:
                    row=layout.row()
                    row.alert = True
                    row.label(text=".dds file in Documents/Maniaplanet/Items/")

                # model
                row = layout.row()
                row.prop(tm_props, "LI_materialModel")
            

            # link
            else:
                row = layout.row()
                row.prop_search(
                    tm_props, "ST_selectedLinkedMat", # value of selection
                    context.scene, "tm_props_linkedMaterials", # list to search in 
                    icon=ICON_LINKED,
                    text="Link") 




        elif is_game_trackmania2020():
            # physics id
            enable = True if use_physicsId else False

            # TODO disable physicsid based on customxxx materials ??
            row = matcol.row(align=True)
            col = row.column()
            col.enabled = enable
            col.prop(tm_props, "LI_materialPhysicsId", text="Physics")
            col = row.column()
            col.prop(tm_props, "CB_materialUsePhysicsId", text="", toggle=True, icon=ICON_CHECKED)

            selected_mat = tm_props.ST_selectedLinkedMat

            # gameplay id
            if selected_mat in LINKED_MATERIALS_COMPATIBLE_WITH_GAMEPLAY_ID:
                row = matcol.row(align=True)
                col = row.column()
                col.enabled = use_gameplayId
                col.prop(tm_props, "LI_materialGameplayId", text="Gameplay")
                col = row.column()
                col.prop(tm_props, "CB_materialUseGameplayId", text="", toggle=True, icon=ICON_CHECKED)
            # else:
            #     row = matcol.row(align=True)
            #     row.label(text="Gameplay:")
            #     row.label(text="Material not supported")
                
            # custom color for materials starts with "custom"
            mat_uses_custom_color = selected_mat.lower().startswith("custom")

            row = matcol.row(align=True)
            row.alert = mat_uses_custom_color
            col = row.column()
            col.scale_x = .55
            col.label(text="Color")
            col = row.column()
            col.prop(tm_props, "NU_materialCustomColor", text="")
            if action_is_update:
                row.operator("view3d.tm_revertcustomcolor", icon=ICON_UPDATE, text="")
            
            # Link
            row = matcol.row()
            row.prop_search(
                tm_props, "ST_selectedLinkedMat", # value of selection
                context.scene, "tm_props_linkedMaterials", # list to search in 
                icon=ICON_LINKED,
                text="Link") 


        row = layout.row()
        row.scale_y = 1.5

        if action_is_update:
            row.operator("view3d.tm_updatematerial", text=f"Update {mat_name_old}", icon=ICON_UPDATE)

        else:
            row.operator("view3d.tm_creatematerial", text=f"Create {mat_name}",    icon=ICON_ADD)


        layout.separator(factor=UI_SPACER_FACTOR)


            
        

