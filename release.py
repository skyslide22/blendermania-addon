import zipfile
import os
import subprocess
import shutil
import glob
import ast

RELEASE_WORK_DIR = "tmp_release/"

PATTERNS_TO_RELEASE = [
    # blendermania
    "__init__.py",
    "assets/**",
    "icons/**",
    "operators/**",
    "panels/**",
    "properties/**",
    "utils/**",
    # NICE
    "NICE/nice.py",
    "NICE/blender/**/*.py",
    "NICE/src/gbx_enums.py",
    "NICE/src/gbx_structs.py",
    "NICE/src/my_construct.py",
    "NICE/src/parser.py",
    "NICE/src/utils/content.py",
    "NICE/src/utils/math.py",
    "NICE/**/__init__.py",
]

def get_bl_info():
    with open("__init__.py", "r", encoding='UTF-8') as init_file:
        data = init_file.read()
        ast_data = ast.parse(data)
        for body in ast_data.body:
            if body.__class__ == ast.Assign:
                if len(body.targets) == 1:
                    if getattr(body.targets[0], "id", "") == "bl_info":
                        return ast.literal_eval(body.value)

def get_release_filename():
    bl_info = get_bl_info()

    bmv_major, bmv_minor, bmv_patch = bl_info["version"]
    blv_major, blv_minor, _ = bl_info["blender"]

    fname = f"blendermania-v{bmv_major}.{bmv_minor}.{bmv_patch}-for-blender-{blv_major}.{blv_minor}.zip"
    return fname


def make_release_zip():
    release_filename = get_release_filename()

    # Ensure work dir & export file are clean

    if os.path.exists(RELEASE_WORK_DIR):
        shutil.rmtree(RELEASE_WORK_DIR)

    if os.path.exists(release_filename):
        os.remove(release_filename)

    # clone the repo

    subprocess.run([
        "git", "clone",
        "--single-branch",
        "--branch", "master",
        "--recurse-submodules",
        "https://github.com/skyslide22/blendermania-addon.git",
        RELEASE_WORK_DIR
    ])

    # generate the zip with the whitelisted files

    with zipfile.ZipFile(release_filename, 'w') as f:
        for pattern in PATTERNS_TO_RELEASE:
            for file in glob.glob(RELEASE_WORK_DIR + pattern, recursive=True):
                f.write(file, os.path.relpath(file, RELEASE_WORK_DIR))

    # clean work dir

    shutil.rmtree(RELEASE_WORK_DIR)

if __name__ == "__main__":
    make_release_zip()
