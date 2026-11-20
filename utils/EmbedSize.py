"""Embed size of an item including the files it references (Texture.Gbx, images, materials, ...).

A map embeds the item and every custom file it references (recursively). The item file alone (the old
"embed size") misses those, which are usually the biggest part (textures).

The references are read from the GBX reference table (uncompressed, right after the header):
    num_nodes u32, num_external u32, [ancestor_level u32, folders (recursive: count, (name, sub folders)*),
    (flags u32, file name | resource index, node index u32, [use_file u32 (v>=5)], [folder index u32])*]
Sizes are deflate-compressed sizes (maps are zip-like), cached by (path, mtime, size).
"""

from __future__ import annotations

import os
import struct
import zlib

_SIZE_CACHE: dict[tuple[str, float, int], float] = {}


class _Reader:
    def __init__(self, data: bytes, pos: int = 0):
        self.data = data
        self.pos = pos

    def u32(self) -> int:
        (v,) = struct.unpack_from("<I", self.data, self.pos)
        self.pos += 4
        return v

    def string(self) -> str:
        n = self.u32()
        if n > 0x10000:
            raise ValueError("string too long")
        s = self.data[self.pos:self.pos + n].decode("utf-8", "replace")
        self.pos += n
        return s


def _long(path: str) -> str:
    """\\\\?\\ prefix for long paths (texture paths can exceed MAX_PATH)"""
    p = os.path.abspath(path)
    if os.name == "nt" and len(p) >= 240 and not p.startswith("\\\\?\\"):
        return "\\\\?\\" + p
    return p


def read_gbx_references(path: str) -> list[str]:
    """absolute paths of the external files referenced by a gbx file (existing or not), [] if not parseable"""
    try:
        with open(_long(path), "rb") as f:
            # header + reference table are small, but the user data (thumbnail) can be big
            data = f.read(64 * 1024)
            if data[:3] != b"GBX":
                return []
            (version,) = struct.unpack_from("<H", data, 3)
            if version < 6:
                return []
            r = _Reader(data, 3 + 2 + 4 + 4)  # magic, version, format bytes, class id
            user_data_size = r.u32()
            r.pos += user_data_size
            if r.pos + 8 > len(data):
                f.seek(0)
                data = f.read(r.pos + 1024 * 1024)
                r.data = data
            r.u32()  # num nodes
            num_external = r.u32()
            if num_external == 0:
                return []
            if num_external > 10000:
                return []
            ancestor_level = r.u32()

            folders: list[str] = []  # flattened, index 1-based (0 = root)

            def read_folders(prefix: str) -> None:
                count = r.u32()
                if count > 10000:
                    raise ValueError("too many folders")
                for _ in range(count):
                    name = r.string()
                    full = os.path.join(prefix, name) if prefix else name
                    folders.append(full)
                    read_folders(full)

            read_folders("")

            root = os.path.dirname(os.path.abspath(path))
            for _ in range(ancestor_level):
                root = os.path.dirname(root)

            refs = []
            for _ in range(num_external):
                flags = r.u32()
                file_name = None
                if flags & 4 == 0:
                    file_name = r.string()
                else:
                    r.u32()  # resource index (game pack file, never embedded)
                r.u32()  # node index
                if version >= 5:
                    r.u32()  # use file
                if flags & 4 == 0:
                    folder_index = r.u32()
                    if file_name:
                        folder = folders[folder_index - 1] if 0 < folder_index <= len(folders) else ""
                        refs.append(os.path.normpath(os.path.join(root, folder, file_name)))
            return refs
    except (OSError, ValueError, struct.error, IndexError):
        return []


def compressed_size_kb(path: str) -> float:
    """deflate size in kB (same measure as the item embed size), cached by path/mtime/size"""
    try:
        st = os.stat(_long(path))
        key = (os.path.normcase(os.path.abspath(path)), st.st_mtime, st.st_size)
        if key not in _SIZE_CACHE:
            with open(_long(path), "rb") as f:
                _SIZE_CACHE[key] = len(zlib.compress(f.read(), 6)) / 1000
        return _SIZE_CACHE[key]
    except OSError:
        return 0.0


def collect_referenced_files(roots: list[str]) -> list[str]:
    """all existing files referenced (recursively) by the given gbx files, without the roots themselves"""
    seen = {os.path.normcase(os.path.abspath(p)) for p in roots}
    result: list[str] = []
    stack = list(roots)
    while stack:
        current = stack.pop()
        if not current.lower().endswith(".gbx"):
            continue
        for ref in read_gbx_references(current):
            key = os.path.normcase(ref)
            if key in seen:
                continue
            seen.add(key)
            if not os.path.isfile(_long(ref)):
                continue  # game pack file or missing -> not embedded
            result.append(ref)
            stack.append(ref)
    return result


def referenced_files_sizes(roots: list[str]) -> dict[str, float]:
    """{referenced file: compressed kB} for every file the roots reference (recursively)"""
    return {p: compressed_size_kb(p) for p in collect_referenced_files(roots)}
