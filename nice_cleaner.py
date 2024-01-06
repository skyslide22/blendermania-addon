import os
import fnmatch

NICE_DIR = "./NICE/"
patterns_to_keep = [
    "nice.py",
    "blender/*.py",
    "src/gbx_enums.py",
    "src/gbx_structs.py",
    "src/my_construct.py",
    "src/parser.py",
    "src/utils/content.py",
    "__init__.py",
    "src/__init__.py",
    "src/utils/__init__.py",
]

def remove_empty_folders(path, removeRoot=True):
    """Function to remove empty folders"""
    if not os.path.isdir(path):
        return

    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                remove_empty_folders(fullpath)

    # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0 and removeRoot:
        os.rmdir(path)

if __name__ == "__main__":
    for root, dirs, files in os.walk(NICE_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            if not any(fnmatch.fnmatch(full_path, os.path.join(NICE_DIR, pattern)) for pattern in patterns_to_keep):
                os.remove(full_path)

    remove_empty_folders(NICE_DIR, removeRoot=False)
