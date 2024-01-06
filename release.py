import bpy
import zipfile
import os
from utils.gitignore_parser import parse_gitignore

from bl_info import bl_info

RELEASE_ROOT_FOLDERS = [
    "assets",
    "icons",
    "NICE"
    "operators",
    "panels",
    "properties",
    "utils",
]
RELEASE_ROOT_FILES = [
    "__init__.py",
]

def get_release_filename():
    bmv_major, bmv_minor, bmv_patch = bl_info["version"]
    blv_major, blv_minor, _ = bl_info["blender"]

    fname = f"blendermania-v{bmv_major}.{bmv_minor}.{bmv_patch}-for-blender-{blv_major}.{blv_minor}.zip"
    return fname


def zip_folder(zipf, folder, gitignore):
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if not gitignore(file_path):
                zipf.write(file_path, os.path.relpath(file_path))


def zip_file(zipf, file, gitignore):
    if not gitignore(file):
        zipf.write(file, os.path.relpath(file))


def make_release_zip():
    release_filename = get_release_filename()
    with zipfile.ZipFile(release_filename, "w") as zipf:
        gitignore_path = os.path.join(os.path.dirname(__file__), ".gitignore")
        gitignore = parse_gitignore(gitignore_path)

        for folder in RELEASE_ROOT_FOLDERS:
            zip_folder(zipf, folder, gitignore)
        for file in RELEASE_ROOT_FILES:
            zip_file(zipf, file, gitignore)


if __name__ == "__main__":
    make_release_zip()





if __name__ == "__main__":
    make_release_zip()