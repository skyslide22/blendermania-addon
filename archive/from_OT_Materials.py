

# only type int|bool|str can be saved as custom prop in fbx,
# so save all props as JSON in a str prop



def saveMatPropsAsJSONinMat(mat) -> None:
    """save mat.prop, mat.prop123 as json string in mat["TM_PROPS_AS_JSON] for export"""
    DICT = {}
    
    # material not created with this addon, no need to save it
    if mat is None or mat.name.startswith(("TM_", "MP_")) is False:
        return

    mat.surfaceColor = mat.diffuse_color[:3]
    if mat.use_nodes:
        mat.surfaceColor = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]

    #tm_props
    for prop_name in MATERIAL_CUSTOM_PROPERTIES:
        prop = getattr(mat, prop_name, None)
        
        if prop is None: continue
        
        if prop.__class__.__name__ == "Color":
            prop = [prop[0], prop[1], prop[2]]

        if isinstance(prop, str):
            if prop.startswith("//"):
                prop = bpy.path.abspath(prop)
                prop = getAbspath(prop)

        DICT[prop_name] = prop
    

    if mat.use_nodes:
        nodes = mat.node_tree.nodes
        tex_d = nodes["tex_D"].image if "tex_D" in nodes else None
        tex_i = nodes["tex_I"].image if "tex_I" in nodes else None
        tex_r = nodes["tex_R"].image if "tex_R" in nodes else None
        tex_n = nodes["tex_N"].image if "tex_N" in nodes else None
        tex_h = nodes["tex_H"].image if "tex_H" in nodes else None
            
        tex_d_path = tex_d.filepath if tex_d else ""
        tex_i_path = tex_i.filepath if tex_i else ""
        tex_r_path = tex_r.filepath if tex_r else ""
        tex_n_path = tex_n.filepath if tex_n else ""
        tex_h_path = tex_h.filepath if tex_h else ""
        
        DICT["tex_d_path"] = get_abs_path(tex_d_path)
        DICT["tex_i_path"] = get_abs_path(tex_i_path)
        DICT["tex_r_path"] = get_abs_path(tex_r_path)
        DICT["tex_n_path"] = get_abs_path(tex_n_path)
        DICT["tex_h_path"] = get_abs_path(tex_h_path)

    JSON = json.dumps(DICT)
    mat[ MAT_PROPS_AS_JSON ] = JSON
    # debug(f"saved json in material <{mat.name}>:")
    # debug(DICT, pp=True)




# custom properties of type int|bool|str can be saved in fbx.materials,
# so convert all custom props to JSON and save them as str prop
def assignMatJSONpropsToMat(mat) -> bool:
    """used for mats of imported objs, take saved props in JSON and assign to the mat"""
    try:
        matJSON = mat.get( MAT_PROPS_AS_JSON )
        if matJSON == "": raise KeyError
    
    except KeyError: #empty or not found
        return False

    if matJSON is None: return False

    try:    DICT = json.loads(matJSON)
    except: return False
    
    mat.use_nodes = True

    #assign mat tm_props to mat
    for prop in DICT:
        if prop.startswith("tex_"): continue
        try:    setattr(mat, prop, DICT[prop])
        except: return False


    #assign textures
    create_material_nodes(mat)
    imgs  = bpy.data.images
    nodes = mat.node_tree.nodes
    tex_d = getattr(nodes, "tex_D", "")
    tex_i = getattr(nodes, "tex_I", "")
    tex_r = getattr(nodes, "tex_R", "")
    tex_n = getattr(nodes, "tex_N", "")
    tex_h = getattr(nodes, "tex_H", "")

    btex  = getattr(DICT, "baseTexture", "")
    envi  = getattr(DICT, "environment", "")
    root  = getGameDocPathItemsAssetsTextures()
    root  = root + envi + "/"

    tex_d_path = getattr(DICT, "tex_d_path", False) or getGameDocPath() + btex + "_D.dds"
    tex_i_path = getattr(DICT, "tex_i_path", False) or getGameDocPath() + btex + "_I.dds"
    tex_r_path = getattr(DICT, "tex_r_path", False) or getGameDocPath() + btex + "_R.dds"
    tex_n_path = getattr(DICT, "tex_n_path", False) or getGameDocPath() + btex + "_N.dds"
    tex_h_path = getattr(DICT, "tex_h_path", False) or getGameDocPath() + btex + "_H.dds"

    test_d_path_as_link = root + tex_d_path.split("/")[-1]
    test_i_path_as_link = root + tex_i_path.split("/")[-1]
    test_r_path_as_link = root + tex_r_path.split("/")[-1]
    test_n_path_as_link = root + tex_n_path.split("/")[-1]
    test_h_path_as_link = root + tex_h_path.split("/")[-1]

    if is_file_exist( test_d_path_as_link ): tex_d_path = test_d_path_as_link
    if is_file_exist( test_i_path_as_link ): tex_i_path = test_i_path_as_link
    if is_file_exist( test_r_path_as_link ): tex_r_path = test_r_path_as_link
    if is_file_exist( test_n_path_as_link ): tex_n_path = test_n_path_as_link
    if is_file_exist( test_h_path_as_link ): tex_h_path = test_h_path_as_link

    debug(tex_d_path)
    debug(test_d_path_as_link)

    success, name = loadDDSTextureIntoBlender(tex_d_path)
    if success and name in imgs:
        tex_d.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_i_path)
    if success and name in imgs:
        tex_i.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_r_path)
    if success and name in imgs:
        tex_r.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_n_path)
    if success and name in imgs:
        tex_n.image = bpy.data.images[ name ]

    success, name = loadDDSTextureIntoBlender(tex_h_path)
    if success and name in imgs:
        tex_h.image = bpy.data.images[ name ]
            
        
    debug(matJSON, pp=True)
    del matJSON
    return True


def fixMaterialNames(obj) -> None:
    """MyMaterial.001 => MyMaterial, join materials."""
    slots = obj.material_slots
    mats  = bpy.data.materials
    regex = r"\.\d+$"
    
    for slot in slots:
        mat     = slot.material
        if mat is None: continue

        if re.search(regex, mat.name):
            
            try:
                matNameNoCountSuffix = re.sub(regex, "", mat.name)
                newmat = mats[matNameNoCountSuffix]
                slot.material = newmat 
            
            except KeyError: #mat.001 exists, mat not
                pass
            
        #delete now unused .001 mat
        if re.search(regex, mat.name):
            bpy.data.materials.remove(mat)


#! not in use
def importMaterialsFromJSON(filepath) -> None:
    """import materials from json file"""
    filepath  = filepath.replace("fbx", "json")
    mats_dict = None
    mats = bpy.data.materials

    with open(filepath, "r") as f:
        content = f.read()
        mats_dict = json.loads(content)
    
    for mat in mats_dict:
        mat = mats_dict[mat]
        
        if mat["name"] not in mats:
            newMat = bpy.data.materials.new(mat["name"])
            for prop in MATERIAL_CUSTOM_PROPERTIES:
                debug(prop)
                exec(f"""{newMat}.{prop}={mat[prop]}""")
    




#! not in use
def exportMaterialsAsJSON(col, filepath) -> None:
    """fbx export custom properties does not export material custom properties, create json..."""
    # filepath = filepath.replace( filename, f".{filename}" ) #dot does not hide files in windows...
    filepath = filepath.replace("json", "Materials.json")
    mats_dict = {}
    objs = col.objects

    for obj in objs:
        if obj.type != "MESH": continue

        for mat in obj.data.materials:
            
            # generate dict for each material
            try:
                if mat.name in mats_dict: continue

                debug(mat.name)

                mat_dict = {}
                for prop_name in MATERIAL_CUSTOM_PROPERTIES:
                    
                    prop = getattr(mat, prop_name)
                    if prop.__class__.__name__ == "Color":
                        prop = [prop.r, prop.g, prop.b]

                    mat_dict[prop_name] = prop
                
                mats_dict[mat.name] = mat_dict
            
            except KeyError: raise



    JSON = json.dumps(mats_dict, indent=4, sort_keys=True)

    debug(f"write material JSON file for {col.name}")
    debug(filepath)
    with open(filepath, "w") as f:
        f.write(JSON)

