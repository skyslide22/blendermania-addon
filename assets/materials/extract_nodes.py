import bpy

def create_mat_nodes_generator(mat: bpy.types.Material, mat_kind_name: str):
    nodes_py = f"def _create_nodes_{mat_kind_name}(mat: bpy.types.Material) -> bpy.types.Material:\n"
    nodes_py += "\tnodes = mat.node_tree.nodes\n"
    nodes_py += "\tcreated_nodes = {}\n\n"

    for node in mat.node_tree.nodes:
        node_type = type(node).__name__.replace("bpy.types.", "")
        nodes_py += f"\tcreated_nodes[\"{node.name}\"] = nodes.new(type=\"{node_type}\")\n"
        nodes_py += f"\tcreated_nodes[\"{node.name}\"].location = {node.location[0]},{node.location[1]}\n"
        nodes_py += f"\tcreated_nodes[\"{node.name}\"].name = \"{node.name}\"\n"
        nodes_py += f"\tcreated_nodes[\"{node.name}\"].label = \"{node.label}\"\n"
        print(node.name)

        if node_type == "ShaderNodeVectorMath":
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].operation = \"{node.operation}\"\n"
            if "Scale" in node.inputs:
                dvs = node.inputs["Scale"].default_value
                nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Scale\"].default_value = {dvs}\n"
        elif node_type == "ShaderNodeMix":
            fdv = node.inputs["Factor"].default_value
            adv = node.inputs["A"].default_value
            bdv = node.inputs["B"].default_value

            nodes_py += f"\tcreated_nodes[\"{node.name}\"].blend_type = \"{node.blend_type}\"\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].data_type = \"{node.data_type}\"\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Factor\"].default_value = {fdv}\n"
            if isinstance(adv, float):
                nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"A\"].default_value = {adv}\n"
            else:
                nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"A\"].default_value = ({adv[0]},{adv[1]},{adv[2]},{adv[3]})\n"

            if isinstance(adv, float):
                nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"B\"].default_value = {bdv}\n"
            else:
                nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"B\"].default_value = ({bdv[0]},{bdv[1]},{bdv[2]},{bdv[3]})\n"
        elif node_type == "ShaderNodeSeparateColor":
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].mode = \"{node.mode}\"\n"
        elif node_type == "ShaderNodeBsdfPrincipled":
            edf = node.inputs["Emission Strength"].default_value
            ecdf = node.inputs["Emission Color"].default_value
            adf = node.inputs["Alpha"].default_value
            rdf = node.inputs["Roughness"].default_value
            twdf = node.inputs[17].default_value
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Emission Strength\"].default_value = {edf}\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Emission Color\"].default_value = ({ecdf[0]},{ecdf[1]},{ecdf[2]},{ecdf[3]})\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Alpha\"].default_value = {adf}\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Roughness\"].default_value = {rdf}\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[17].default_value = {twdf}\n"
        elif node_type == "ShaderNodeTexImage":
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].projection = \"{node.projection}\"\n"
            #if node.image:
            #    nodes_py += f"\tcreated_nodes[\"{node.name}\"].image = bpy.data.images[\"{node.image.name}\"]\n"
        elif node_type == "ShaderNodeTangent":
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].direction_type = \"{node.direction_type}\"\n"
        elif node_type == "ShaderNodeAttribute":
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].attribute_name = \"{node.attribute_name}\"\n"
        elif node_type == "ShaderNodeHueSaturation":
            vdf = node.inputs["Value"].default_value
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Value\"].default_value = {vdf}\n"
        elif node_type == "ShaderNodeBump":
            sdf = node.inputs["Strength"].default_value
            ddf = node.inputs["Distance"].default_value
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Strength\"].default_value = {sdf}\n"
            nodes_py += f"\tcreated_nodes[\"{node.name}\"].inputs[\"Distance\"].default_value = {ddf}\n"

        nodes_py += "\n"

    nodes_py += "\n"
    nodes_py += "\tlinks = mat.node_tree.links\n"
    
    for link in mat.node_tree.links:
        if link.is_valid:
            link_from =  link.from_socket.path_from_id().replace("nodes[", "created_nodes[")
            link_to = link.to_socket.path_from_id().replace("nodes[", "created_nodes[")
            nodes_py += f"\tlinks.new({link_from}, {link_to})\n"

    nodes_py += "\n"
    nodes_py += "\treturn mat\n"
    nodes_py += "\n"

    return nodes_py

generator_content = "import bpy\n\n"
generator_content += "# WARNING\n"
generator_content += "# WARNING\n"
generator_content += "# WARNING\n"
generator_content += "# this file is autogenerated, DO NOT CHANGE MANUALLY\n"
generator_content += "# WARNING\n"
generator_content += "# WARNING\n"
generator_content += "# WARNING\n\n"

generator_functions = ""
generator_functions_list = ""
for mat in bpy.data.materials:
    mat:bpy.types.Material = mat

    if mat.name not in [
        "TM_DecalGeom",
        "TM_DecalGeom_TOp_PyPxzDSN_X2",
        "TM_DynaFacing_ForceNMap_CubeOut_TestOp",
        "TM_GlassBasic",
        "TM_GrassX2",
        "TM_PyPxz_Hue",
        "TM_PyPxzDiff_Spec_Norm",
        "TM_PyPxzDiff_Spec_Norm_LM1",
        "TM_PyPxzTDiffSpecNorm_PyX2Hx2",
        "TM_PyPxzTLayered",
        "TM_TAdd",
        "TM_TAddModCV",
        "TM_TDiff_Spec_Norm",
        "TM_TDSN_CubeOut",
        "TM_TDSN_CubeOut_DispIn",
        "TM_Water_MultiH",
        "TM_WaterWall",
        "TM_OnlyCollidable",
    ]:
        continue



    mat_kind_name = mat.name.replace("TM_", "")
    generator_functions += create_mat_nodes_generator(mat, mat_kind_name)
    generator_functions_list += f"\t\"{mat_kind_name}\": _create_nodes_{mat_kind_name},\n"

generator_content += generator_functions
generator_content += "\n\n"
generator_content += "MATERIAL_NODES_CREATORS = {\n"
generator_content += generator_functions_list
generator_content += "}\n"

with open('.\\nodes_gen.py', 'w') as file:
    file.write(generator_content)