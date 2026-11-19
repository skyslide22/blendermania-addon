"""
Shared GitHub release installer for downloadable asset libraries (TM2020 Material Assets Library, default assets).

Release format (same as BigthirstyTM/TM2020-Material-Assets-Library):
    release.json = {"version": "1.0.0", "edition": "...", "archives": [{"name", "bytes", "sha256"}, ...],
                    "files": {"relative/path": "sha256", ...}, ...extra keys}
    + the zip parts listed in "archives", all extracted into the same folder.
Pure python (no bpy): used from worker threads.
"""
import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

HTTP_HEADERS = {"User-Agent": "blendermania-addon", "Accept": "application/vnd.github+json"}
CHUNK = 1024 * 1024
VALID_ARCHIVE = re.compile(r"^[A-Za-z0-9._-]+\.zip$")
SPLIT_BYTES = 1900 * 2**20      # GitHub release assets must stay below 2 GiB


class Cancelled(Exception):
    pass


def get_json(url: str):
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def latest_version(releases_api: str, tag_pattern: re.Pattern) -> str | None:
    """newest non-draft/prerelease version whose tag matches (group 1 = version) and has a release.json.
    Raises urllib.error.URLError / OSError / ValueError when GitHub can't be asked."""
    for release in get_json(releases_api):   # the API lists newest first
        m = tag_pattern.match(release.get("tag_name", ""))
        if m and not release.get("draft") and not release.get("prerelease") \
                and any(a.get("name") == "release.json" for a in release.get("assets", [])):
            return m.group(1)
    return None


def version_key(version: str) -> tuple:
    """'1.10.0' > '1.9.2'; non-numeric parts compare as text"""
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in re.split(r"[.\-+]", version or ""))


def long_path(path) -> str:
    """windows long path (\\\\?\\), texture paths of the libraries come close to MAX_PATH"""
    s = str(path)
    prefix = "\\\\?\\"
    if os.name == "nt" and not s.startswith(prefix):
        s = prefix + os.path.abspath(s)
    return s


def sha256(path, cancelled=lambda: False) -> str:
    h = hashlib.sha256()
    with open(long_path(path), "rb") as f:
        while True:
            if cancelled():
                raise Cancelled()
            data = f.read(CHUNK * 4)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def download_and_extract(base_url: str, manifest: dict, cache: Path, staging: Path,
                         report=lambda text, fraction=None: None, cancelled=lambda: False,
                         span: tuple = (0.0, 0.9, 1.0)) -> set:
    """
    Download all archives of the manifest into cache (verified cached files are reused, sha256 checked),
    extract them into staging (must not exist) and check the file list. Progress fractions:
    download span[0]..span[1], extraction span[1]..span[2]. Returns the extracted relative paths (lowercase).
    """
    archives = manifest.get("archives", [])
    for a in archives:
        if not VALID_ARCHIVE.match(a.get("name", "")):
            raise RuntimeError("invalid archive name in release.json")
    start, mid, end = span

    cache.mkdir(parents=True, exist_ok=True)
    total = sum(int(a["bytes"]) for a in archives) or 1
    done_bytes = 0
    for i, a in enumerate(archives, 1):
        target = cache / a["name"]
        label = f"part {i}/{len(archives)}"
        if target.is_file() and target.stat().st_size == int(a["bytes"]):
            report(f"Checking cached {label}...")
            if sha256(target, cancelled) == a["sha256"]:
                done_bytes += int(a["bytes"])
                continue
        tmp = target.with_name(target.name + ".part")
        h = hashlib.sha256()
        req = urllib.request.Request(base_url + a["name"], headers={"User-Agent": HTTP_HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            got = 0
            while True:
                if cancelled():
                    raise Cancelled()
                data = r.read(CHUNK)
                if not data:
                    break
                f.write(data)
                h.update(data)
                got += len(data)
                report(f"Downloading {label} ({(done_bytes + got) // 2**20} / {total // 2**20} MB)",
                       start + (done_bytes + got) / total * (mid - start))
        if h.hexdigest() != a["sha256"]:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"checksum mismatch: {a['name']}")
        tmp.replace(target)
        done_bytes += int(a["bytes"])

    staging.mkdir(parents=True)
    staging_resolved = staging.resolve()
    count_total = 0
    for a in archives:
        with zipfile.ZipFile(cache / a["name"]) as z:
            count_total += len([e for e in z.infolist() if not e.is_dir()])
    count, seen = 0, set()
    for a in archives:
        with zipfile.ZipFile(cache / a["name"]) as z:
            for entry in z.infolist():
                if entry.is_dir():
                    continue
                if cancelled():
                    raise Cancelled()
                rel = entry.filename.replace("\\", "/")
                target = (staging / rel).resolve()
                if staging_resolved not in target.parents:
                    raise RuntimeError(f"archive path escapes the installation folder: {rel}")
                if rel.lower() in seen:
                    raise RuntimeError(f"duplicate archive entry: {rel}")
                seen.add(rel.lower())
                os.makedirs(long_path(target.parent), exist_ok=True)
                with z.open(entry) as src, open(long_path(target), "wb") as dst:
                    shutil.copyfileobj(src, dst, CHUNK)
                count += 1
                if count % 25 == 0:
                    report(f"Extracting ({count} / {count_total} files)", mid + count / max(1, count_total) * (end - mid))

    expected = {k.replace("\\", "/").lower() for k in manifest.get("files", {})}
    missing = expected - seen
    if expected and missing:
        raise RuntimeError(f"{len(missing)} files missing, e.g. {sorted(missing)[0]}")
    return seen


def write_release(files: list, source_root: Path, dest_dir: Path, archive_prefix: str, manifest: dict,
                  report=lambda text, fraction=None: None, cancelled=lambda: False, overrides: dict | None = None) -> Path:
    """
    Package files (paths relative to source_root) into <archive_prefix>-partNN.zip (split below 2 GiB) + release.json
    in dest_dir. manifest gets "archives" and "files" added. Returns the release.json path.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(files)
    hashes, archives = {}, []
    total = sum(os.path.getsize(long_path(source_root / f)) for f in files) or 1
    done = 0
    part, size, zf = 0, 0, None

    def close():
        if zf is not None:
            zf.close()
            path = dest_dir / archives[-1]["name"]
            archives[-1]["bytes"] = path.stat().st_size
            archives[-1]["sha256"] = sha256(path, cancelled)

    try:
        for rel in files:
            if cancelled():
                raise Cancelled()
            src = (overrides or {}).get(rel) or source_root / rel   # overrides: rel -> file packed instead
            fsize = os.path.getsize(long_path(src))
            if zf is None or size + fsize > SPLIT_BYTES:
                close()
                part += 1
                name = f"{archive_prefix}-part{part:02d}.zip"
                archives.append({"name": name})
                zf = zipfile.ZipFile(dest_dir / name, "w", zipfile.ZIP_DEFLATED, compresslevel=1)
                size = 0
            zf.write(long_path(src), rel)
            hashes[rel] = sha256(src, cancelled)
            size += fsize
            done += fsize
            report(f"Packing {done // 2**20} / {total // 2**20} MB", done / total)
        close()
        zf = None
    finally:
        if zf is not None:
            zf.close()

    manifest = dict(manifest, archives=archives, files=hashes)
    path = dest_dir / "release.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
