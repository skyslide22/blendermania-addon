import zipfile
import os
import subprocess
import shutil
import glob
import ast
import tempfile
import datetime

ADDON_DIR = "blendermania-addon" + os.path.sep
LOCAL = False

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
    "NICE/__init__.py",
    "NICE/src/__init__.py",
    "NICE/src/utils/__init__.py",
]


def get_bl_info(tmpdirname):
    with open(tmpdirname + "__init__.py", "r", encoding="UTF-8") as init_file:
        data = init_file.read()
        ast_data = ast.parse(data)
        for body in ast_data.body:
            if body.__class__ == ast.Assign:
                if len(body.targets) == 1:
                    if getattr(body.targets[0], "id", "") == "bl_info":
                        return ast.literal_eval(body.value)


def get_release_filename(tmpdirname):
    bl_info = get_bl_info(tmpdirname)

    bmv_major, bmv_minor, bmv_patch = bl_info["version"]
    blv_major, blv_minor, _ = bl_info["blender"]
    nightly = ""
    if LOCAL:
        nightly = "-nightly" + datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%S")

    fname = f"blendermania-v{bmv_major}.{bmv_minor}.{bmv_patch}{nightly}-for-blender-{blv_major}.{blv_minor}.zip"
    return fname


def make_release_zip():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname += os.path.sep
        print("Using directory", tmpdirname)

        if LOCAL:
            shutil.copytree("./", tmpdirname, dirs_exist_ok=True)
        else:
            # clone the repo
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--single-branch",
                    "--branch",
                    "master",
                    "--recurse-submodules",
                    "https://github.com/skyslide22/blendermania-addon.git",
                    tmpdirname,
                ],
                shell=True,
                check=True,
            )

        # get release version and clean existing zip
        release_filename = get_release_filename(tmpdirname)
        if os.path.exists(release_filename):
            os.remove(release_filename)

        # generate the zip with the whitelisted files
        with zipfile.ZipFile(release_filename, "w") as f:
            for pattern in PATTERNS_TO_RELEASE:
                for file in glob.glob(tmpdirname + pattern, recursive=True):
                    f.write(file, ADDON_DIR + file.removeprefix(tmpdirname))

    print("\nSuccessful Release! " + release_filename)


if __name__ == "__main__":
    make_release_zip()
