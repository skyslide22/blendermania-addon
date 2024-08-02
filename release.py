import zipfile
import os
import subprocess
import shutil
import glob
import ast
import stat

RELEASE_WORK_DIR = "blendermania-addon/"

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

def get_bl_info():
    with open(RELEASE_WORK_DIR+"__init__.py", "r", encoding='UTF-8') as init_file:
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

def shutil_rmtree_onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.
    
    Usage : ``shutil.rmtree(path, onerror=shutil_rmtree_onerror)``

    From: https://stackoverflow.com/a/2656405
    """
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def make_release_zip():
    # Ensure work dir & export file are clean
    if os.path.exists(RELEASE_WORK_DIR):
        shutil.rmtree(RELEASE_WORK_DIR, onerror=shutil_rmtree_onerror)

    # clone the repo
    subprocess.run([
        "git", "clone",
        "--single-branch",
        "--branch", "master",
        "--recurse-submodules",
        "https://github.com/skyslide22/blendermania-addon.git",
        RELEASE_WORK_DIR
    ], shell=True, check=True)

    
    # get release version and clean existing zip 
    release_filename = get_release_filename()
    if os.path.exists(release_filename):
        os.remove(release_filename)
    
    # generate the zip with the whitelisted files
    with zipfile.ZipFile(release_filename, 'w') as f:
        for pattern in PATTERNS_TO_RELEASE:
            for file in glob.glob(RELEASE_WORK_DIR + pattern, recursive=True):
                f.write(file)

    # clean work dir

    shutil.rmtree(RELEASE_WORK_DIR, onerror=shutil_rmtree_onerror)

    print("\nSuccessful Release! " + release_filename)

if __name__ == "__main__":
    make_release_zip()
