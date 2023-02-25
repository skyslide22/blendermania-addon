import re
import os
import shutil
from ..utils.Functions import (
    get_global_props,
    get_nadeo_importer_lib_path,
    is_file_existing,
)
from ..properties.MateriasOverrides import (
    MaterialPhysicsOverride
)

def _create_original_matlib_file():
    current = get_nadeo_importer_lib_path()
    original = get_nadeo_importer_lib_path().replace("NadeoImporterMaterialLib.txt", "NadeoImporterMaterialLib-original.txt")
    if not is_file_existing(original):
        shutil.copy(current, original)

def reset_original_matlib_file() -> bool:
    current = get_nadeo_importer_lib_path()
    original = get_nadeo_importer_lib_path().replace("NadeoImporterMaterialLib.txt", "NadeoImporterMaterialLib-original.txt")
    if is_file_existing(original):
        os.remove(current)
        shutil.copy(original, current)

        return True

    return False

def apply_materials_overrides(mat_list: list[MaterialPhysicsOverride]):
    if not reset_original_matlib_file():
        _create_original_matlib_file()

    file = open(get_nadeo_importer_lib_path(), 'r+')
    data = file.read().rstrip()

    for item in mat_list:
        if item.enabled:
            def repl(matchobj):
                old_surface = matchobj.group("surface")
                print(matchobj.group().replace(matchobj.group("surface"), item.physic_id))
                return matchobj.group().replace(f"({old_surface})", f"({item.physic_id})")

            pattern = rf'DMaterial\({item.link}\)[\t\s]*\n(.*DLinkFull.*\n)?[\t\s]+DSurfaceId[\t\s]*\((?P<surface>[\w-]+)\)'
            data = re.sub(pattern, repl, data)

    file.truncate(0)
    file.write(data)
