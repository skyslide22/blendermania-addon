import zipfile
import os
import subprocess
import shutil
import glob

from bl_info import bl_info

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

def get_release_filename():
    bmv_major, bmv_minor, bmv_patch = bl_info["version"]
    blv_major, blv_minor, _ = bl_info["blender"]

    fname = f"blendermania-v{bmv_major}.{bmv_minor}.{bmv_patch}-for-blender-{blv_major}.{blv_minor}.zip"
    return fname


def make_release_zip():
    # Ensure work dir is clean

    if os.path.exists(RELEASE_WORK_DIR):
        shutil.rmtree(RELEASE_WORK_DIR)

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

    release_filename = get_release_filename()

    with zipfile.ZipFile(release_filename, 'w') as f:
        for pattern in PATTERNS_TO_RELEASE:
            print(RELEASE_WORK_DIR + pattern)
            for file in glob.glob(RELEASE_WORK_DIR + pattern, recursive=True):
                f.write(file, os.path.relpath(file, RELEASE_WORK_DIR))

    # clean work dir

    shutil.rmtree(RELEASE_WORK_DIR)

if __name__ == "__main__":
    make_release_zip()
