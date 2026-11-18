#!/usr/bin/env python3
"""Generate ``tm_fx/schema/base/*.json`` from GBX.NET ``.chunkl`` layouts.

    python tools/gen_schema.py --gbxnet /path/to/gbx-net

For every class reachable from the root classes this resolves, for one game
(TM2020), which chunks exist, at which version they are written, and exactly
which fields each version contains.  The result is a flat, version-free field
list per chunk, so the Blender side never has to know about version branches.

What it keeps verbatim from GBX.NET
    * field order, types, array kinds, defaults, enum members
    * member names: named fields keep their name; unnamed ones become ``U01..``
      numbered exactly like the GBX.NET source generator (checked in
      ``tests/test_numbering.py``), so they address real C# members
    * ``if`` conditions (as a small AST, see ``tm_fx/expr.py``)

Hand-written knowledge (labels, ranges, grouping, confidence) never lives in
the base files - see ``tm_fx/schema/overlay``.  Regenerate the base freely.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import chunkl  # noqa: E402
import expr  # noqa: E402  (FX/expr.py, pure python)

GAME = "TM2020"
SCHEMA_FORMAT = 1

#: Item prefab ents reference a CPlugFxSystem (Nadeo's *.FxSys.Gbx); it is also the root the
#: TM_GenericMapping ParticleFxConverter expects.
DEFAULT_ROOTS = ["CPlugFxSystem"]

#: Classes that become editable child nodes in the UI.  Everything else that
#: looks like a class reference is a file reference or opaque (passthrough).
DEFAULT_MODELED = [
    "CPlugFxSystem",
    "CPlugParticleEmitterModel",
    "CPlugParticleEmitterSubModel",
    "CPlugParticleGpuSpawn",
    "CPlugParticleGpuModel",
    "CPlugParticleSplashModel",
    "CFuncEnvelope",
    "CPlugFuncColorGradient",
]

#: Class references that are authored as a string (or empty): an asset id for CPlugBitmap
#: members (see FX/schema.py ASSET_REFS), otherwise a .Gbx path.
REF_CLASSES = {
    "CPlugMaterial", "CPlugBitmap", "CPlugShader", "CPlugSound", "CPlugDecalModel",
    "CPlugSoundSurface", "CPlugSolid2Model", "CPlugFileImg", "CPlugBitmapAtlas",
}

INT_TYPES = {
    "int": (32, True), "int32": (32, True), "uint": (32, False), "uint32": (32, False),
    "short": (16, True), "int16": (16, True), "ushort": (16, False), "uint16": (16, False),
    "byte": (8, False), "uint8": (8, False), "sbyte": (8, True), "int8": (8, True),
}
INT64_TYPES = {"long", "ulong", "int64", "uint64"}
VEC_TYPES = {"vec2": ("float", 2), "vec3": ("float", 3), "vec4": ("float", 4),
             "quat": ("float", 4), "int2": ("int", 2), "int3": ("int", 3),
             "int4": ("int", 4), "byte3": ("int", 3)}


class Generator:
    def __init__(self, engines_dir: Path, modeled, game=GAME):
        self.game = game
        self.modeled = set(modeled)
        self.index: dict[str, chunkl.ClassDef] = {}
        for f in sorted(engines_dir.glob("*/*.chunkl")):
            cd = chunkl.parse_file(f)
            cd.path = f"Engines/{f.parent.name}/{f.name}"
            self.index[cd.name] = cd
        self.out: dict[str, dict] = {}
        self.queue: deque[str] = deque()
        self.warnings: list[str] = []
        self._archive_memo: dict[tuple, str] = {}

    # ----------------------------------------------------------------- plumbing
    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def enqueue(self, cname):
        if cname not in self.out and cname in self.index:
            self.out[cname] = {}
            self.queue.append(cname)

    def run(self, roots):
        for r in roots:
            if r not in self.index:
                raise SystemExit(f"root class {r!r} not found in chunkl index")
            self.enqueue(r)
        while self.queue:
            self.emit_class(self.queue.popleft())

    # ------------------------------------------------------------------- classes
    def emit_class(self, cname):
        cd = self.index[cname]
        entry = {
            "schema_format": SCHEMA_FORMAT,
            "class": cd.name,
            "kind": "node",
            "id": f"0x{cd.id:08X}",
            "game": self.game,
            "source": cd.path,
            "chunks": [],
            "archives": {},
            "enums": {n: [[m, v] for m, v in e.members] for n, e in cd.enums.items()},
        }
        self.out[cname] = entry
        if cd.attrs.get("inherits"):
            parent = cd.attrs["inherits"]
            if parent in self.index and any(self._has_game(c) for c in self.index[parent].chunks):
                self.warn(f"{cname} inherits {parent}, whose {self.game} chunks are NOT merged")

        # names declared anywhere in this class's TM2020 chunks (for condition binding)
        class_named = set()
        for c in cd.chunks:
            if self._has_game(c):
                chunkl.number_members(c.body)
                for s in chunkl.walk(c.body):
                    if isinstance(s, chunkl.Field) and s.name and not s.is_special and not s.is_version \
                            and not s.attrs.get("local") and not re.fullmatch(r"U\d\d", s.name):
                        class_named.add(s.name)

        seen: dict[str, dict] = {}
        for c in cd.chunks:
            if not self._has_game(c):
                continue
            has_ver = any(isinstance(s, chunkl.Field) and s.is_version for s in chunkl.walk(c.body))
            ver = c.games.get(self.game)
            if ver is None and has_ver:
                ver = self._declared_version(c.body)
            if ver is None:
                ver = 0
            chunk_entry = {
                "id": f"0x{(cd.id + c.offset) & 0xFFFFFFFF:08X}",
                "offset": f"0x{c.offset:03X}",
                "version": ver if has_ver else None,
                "attrs": sorted(k for k in c.attrs),
                "comment": c.comment,
                "fields": [],
            }
            if c.base is not None:
                self.warn(f"{cname} chunk 0x{c.offset:03X} has base 0x{c.base:03X}: base fields not merged")
            r = Resolver(self, cd, scope=f"c{c.offset:03X}", is_chunk=True, caller_v=ver,
                         own_v=ver if has_ver else None, class_named=class_named, body=c.body)
            for fld in r.run():
                prev = seen.get(fld["key"])
                if prev is not None:
                    if prev["type"] != fld["type"]:
                        self.warn(f"{cname}.{fld['key']} declared with different types in several chunks")
                    continue            # same named property declared again: keep first
                seen[fld["key"]] = fld
                chunk_entry["fields"].append(fld)
            entry["chunks"].append(chunk_entry)

    def _has_game(self, chunk):
        return self.game in chunk.games

    @staticmethod
    def _declared_version(body):
        for s in chunkl.walk(body):
            if isinstance(s, chunkl.Field) and s.is_version and s.default is not None:
                try:
                    return int(s.default, 0)
                except ValueError:
                    return None
        return None

    # ------------------------------------------------------------------ archives
    def resolve_archive(self, owner: chunkl.ClassDef, name: str, caller_v: int) -> str:
        """Resolve an archive for a caller version; returns its qualified name."""
        qual = f"{owner.name}.{name}"
        key = (qual, caller_v)
        if key in self._archive_memo:
            return self._archive_memo[key]
        self._archive_memo[key] = qual
        # same archive requested with another caller version -> keep first, warn
        arch0 = owner.archives[name]
        for (q, v), _ in list(self._archive_memo.items()):
            if q == qual and v != caller_v:
                if any(isinstance(s, chunkl.VersionBlock) for s in chunkl.walk(arch0.body)):
                    self.warn(f"archive {qual} is version dependent but used with different caller "
                              f"versions ({v} and {caller_v}); keeping the first")
                return qual
        self.enqueue(owner.name)
        # make sure the owner entry exists (it may still be queued)
        arch = owner.archives[name]
        chunkl.number_members(arch.body)
        has_ver = any(isinstance(s, chunkl.Field) and s.is_version for s in chunkl.walk(arch.body))
        own_v = self._declared_version(arch.body) if has_ver else None
        placeholder = {"version": own_v, "caller_version": caller_v, "fields": []}
        owner_entry = self.out.setdefault(owner.name, {})
        owner_entry.setdefault("archives", {})[name] = placeholder
        class_named = {s.name for s in chunkl.walk(arch.body)
                       if isinstance(s, chunkl.Field) and s.name and not s.is_special
                       and not s.is_version and not re.fullmatch(r"U\d\d", s.name)}
        r = Resolver(self, owner, scope="", is_chunk=False, caller_v=caller_v, own_v=own_v,
                     class_named=class_named, body=arch.body)
        placeholder["fields"] = r.run()
        return qual

    def find_archive_owner(self, ref_type: str, owner: chunkl.ClassDef):
        """``Name`` -> archive of ``owner``; ``Class.Name`` -> archive of another class."""
        if "." in ref_type:
            cname, aname = ref_type.rsplit(".", 1)
            cd = self.index.get(cname)
            if cd and aname in cd.archives:
                return cd, aname
            return None
        if ref_type in owner.archives:
            return owner, ref_type
        return None

    def find_enum(self, name: str, owner: chunkl.ClassDef):
        if name in owner.enums:
            return owner.enums[name]
        for cd in self.index.values():
            if name in cd.enums:
                return cd.enums[name]
        return None


class _Stop(Exception):
    pass


class Resolver:
    """Flatten one chunk/archive body for a fixed version."""

    def __init__(self, gen: Generator, owner: chunkl.ClassDef, scope: str, is_chunk: bool,
                 caller_v: int, own_v, class_named: set, body: list):
        self.g = gen
        self.owner = owner
        self.scope = scope            # "c033" for chunks, "" for archives
        self.is_chunk = is_chunk
        self.caller_v = caller_v
        self.own_v = own_v
        self.class_named = class_named
        self.body = body
        self.stopped = False
        self.extra_conds: list = []
        # keys for every field declared in this scope (all branches), for condition binding
        self.scope_keys: dict[str, str] = {}
        self.env: dict[str, object] = {}
        for s in chunkl.walk(body):
            if isinstance(s, chunkl.Field) and not s.is_special and not s.is_version \
                    and not s.attrs.get("local"):
                self.scope_keys[s.member] = self.key_of(s)
                if s.name:
                    self.scope_keys[s.name] = self.key_of(s)
            if isinstance(s, chunkl.Field) and s.name and s.default is not None:
                try:
                    self.env[s.name] = expr.evaluate(expr.parse(s.default), self._env_lookup)
                except Exception:
                    pass

    # -- environment for constant expressions (e.g. "(version: ParameterVersion)")
    def _env_lookup(self, name):
        if name == "Version":
            return self.own_v if self.own_v is not None else self.caller_v
        if name == "v":
            return self.caller_v
        return self.env[name]

    def key_of(self, d: chunkl.Field) -> str:
        if d.name and not re.fullmatch(r"U\d\d", d.name):
            return d.name
        return f"{self.scope}_{d.member}" if self.scope else d.member

    # --------------------------------------------------------------------- walk
    def run(self) -> list:
        out: list = []
        try:
            self._walk(self.body, [], out)
        except _Stop:
            pass
        return out

    def _version_for(self, selector):
        if selector == "archive":
            return self.own_v if self.own_v is not None else self.caller_v
        if selector == "chunk":
            return self.caller_v
        if self.is_chunk:
            return self.own_v if self.own_v is not None else self.caller_v
        return self.caller_v

    @staticmethod
    def _vmatch(vb: chunkl.VersionBlock, v: int) -> bool:
        if vb.op == "=":
            return v == vb.a
        if vb.op == "+":
            return v >= vb.a
        if vb.op == "-":
            return v <= vb.a
        return vb.a <= v <= vb.b

    def _walk(self, stmts, conds, out):
        for s in stmts:
            if self.stopped:
                raise _Stop
            if isinstance(s, chunkl.VersionBlock):
                if self._vmatch(s, self._version_for(s.selector)):
                    self._walk(s.body, conds, out)
            elif isinstance(s, chunkl.If):
                self._walk_if(s, conds, out)
            elif isinstance(s, chunkl.Special):
                if s.kind == "return":
                    if not conds:
                        self.stopped = True
                        raise _Stop
                    self.extra_conds.append(expr.NOT(self._and(conds)))
                elif s.kind == "throw":
                    self.stopped = True
                    raise _Stop
            elif isinstance(s, chunkl.Raw):
                self.g.warn(f"{self.owner.name}: unsupported construct {s.text!r} (line {s.line}) ignored")
            elif isinstance(s, chunkl.Field):
                if s.is_version or s.is_special or s.attrs.get("local"):
                    continue
                out.append(self._make_field(s, conds))

    def _parse_cond(self, text):
        try:
            return expr.parse(text)
        except expr.ParseError:
            self.g.warn(f"{self.owner.name}: cannot parse condition {text!r}")
            return ["id", text]

    def _walk_if(self, node: chunkl.If, conds, out):
        c1 = self._parse_cond(node.cond)
        self._walk(node.body, conds + [c1], out)
        negs = [expr.NOT(c1)]
        for ctext, body in node.elifs:
            c = self._parse_cond(ctext)
            self._walk(body, conds + negs + [c], out)
            negs.append(expr.NOT(c))
        if node.else_body is not None:
            self._walk(node.else_body, conds + negs, out)

    @staticmethod
    def _and(conds):
        r = None
        for c in conds:
            r = expr.AND(r, c)
        return r

    # ------------------------------------------------------------------ a field
    def _bind(self, ast):
        """Bind identifiers to schema keys / known constants."""
        unresolved = []

        def fn(name):
            if name == "Version":
                return ["num", self._env_lookup("Version")]
            if name in self.scope_keys:
                return ["key", self.scope_keys[name]]
            if name in self.class_named:
                return ["key", name]
            if name in self.env:
                return ["num", self.env[name]] if isinstance(self.env[name], (int, float)) else None
            unresolved.append(name)
            return None

        return expr.fold(expr.rewrite(ast, fn)), unresolved

    def _make_field(self, d: chunkl.Field, conds) -> dict:
        allc = list(conds) + self.extra_conds
        when, unresolved = None, []
        if allc:
            bound, unresolved = self._bind(self._and(allc))
            # unbound identifiers stay as "id" nodes: evaluating one raises expr.Unresolved, which
            # counts as visible, so e.g. "Type == 5 && IsSoundSurface" still hides the field for Type 0
            if bound != ["bool", True]:
                when = bound
        fld = {
            "key": self.key_of(d),
            "member": d.member,
            "scope": "archive" if not self.is_chunk else ("node" if (d.name and not re.fullmatch(r"U\d\d", d.name)) else "chunk"),
            "name": d.name if (d.name and not re.fullmatch(r"U\d\d", d.name)) else None,
        }
        fld.update(self._classify(d))
        dv = self._default(d, fld)
        if dv is not None:
            fld["default"] = dv
        if when is not None:
            fld["when"] = when
        if unresolved:
            fld["when_unresolved"] = [expr.to_str(self._and(allc))]
        flags = sorted(k for k in d.attrs if k in ("deprec", "direct", "list", "nullable", "time"))
        if flags:
            fld["attrs"] = flags
        fld["line"] = d.line
        return fld

    # ----------------------------------------------------------------- typing
    def _classify(self, d: chunkl.Field) -> dict:
        t = d.type
        arr = d.array
        res: dict = {}

        def finish(r):
            if arr is None:
                r["array"] = None
            elif arr == "" or not re.fullmatch(r"\d+", arr):
                r["array"] = "list"
            else:
                r["array"] = int(arr)
            return r

        if t == "data" or (t in ("byte", "sbyte", "uint8", "int8") and arr is not None):
            n = int(arr) if (arr and re.fullmatch(r"\d+", arr)) else None
            return {"type": "blob", "length": n, "array": None}
        if t in INT_TYPES or t in ("float", "double") or t in INT64_TYPES:
            if d.cast and not re.fullmatch(r"\w+", d.cast or ""):
                pass
            en = self.g.find_enum(d.cast, self.owner) if d.cast else None
            if en is not None and not en.flags:
                bits, signed = INT_TYPES.get(t, (32, True))
                return finish({"type": "enum", "enum": en.name, "bits": bits,
                               "items": [[m, v] for m, v in en.members]})
            if t in INT64_TYPES:
                self.g.warn(f"{self.owner.name}.{d.member}: 64-bit integer treated as opaque")
                return finish({"type": "opaque", "ref": t})
            if t in INT_TYPES:
                bits, signed = INT_TYPES[t]
                return finish({"type": "int", "bits": bits, "signed": signed})
            return finish({"type": "float"})
        if t in ("bool", "boolean", "boolbyte"):
            return finish({"type": "bool"})
        if t in ("string", "id", "lookbackstring"):
            r = {"type": "string"}
            if t != "string":
                r["sub"] = "id"
            return finish(r)
        if t in VEC_TYPES:
            kind, n = VEC_TYPES[t]
            return finish({"type": "vec", "kind": kind, "size": n})
        if t == "iso4":
            return finish({"type": "iso4"})
        if t in ("box", "boxaligned"):
            return finish({"type": "box"})
        if t == "PlugCurve":
            expr_text = d.attrs.get("version")
            if expr_text:
                try:
                    cv = expr.evaluate(expr.parse(expr_text), self._env_lookup)
                except Exception:
                    cv = 0
                if cv < 0:
                    self.g.warn(f"{self.owner.name}.{d.member}: legacy (node reference) curve stored as opaque")
                    return finish({"type": "opaque", "ref": "CFuncKeysReal"})
            return finish({"type": "curve"})
        # archives (inline structs)
        found = self.g.find_archive_owner(t, self.owner)
        if found:
            aowner, aname = found
            cv = self._child_version(d)
            qual = self.g.resolve_archive(aowner, aname, cv)
            return finish({"type": "struct", "ref": qual})
        base = t.rstrip("*")
        if base in self.g.modeled:
            self.g.enqueue(base)
            return finish({"type": "node", "ref": base})
        if base in REF_CLASSES:
            return finish({"type": "ref", "ref": base})
        return finish({"type": "opaque", "ref": base})

    def _child_version(self, d: chunkl.Field) -> int:
        text = d.attrs.get("version")
        if text:
            try:
                v = expr.evaluate(expr.parse(text), self._env_lookup)
                return int(v)
            except Exception:
                self.g.warn(f"{self.owner.name}.{d.member}: cannot evaluate (version: {text}); using scope version")
        return self.own_v if (self.is_chunk and self.own_v is not None) else (
            self.own_v if (not self.is_chunk and self.own_v is not None) else self.caller_v)

    # ---------------------------------------------------------------- defaults
    def _default(self, d: chunkl.Field, fld: dict):
        if d.default is None or fld["type"] in ("node", "struct", "curve", "opaque", "blob"):
            return None
        text = d.default.strip()
        try:
            if fld.get("type") == "vec" and text.startswith("("):
                parts = [expr.evaluate(expr.parse(p), self._env_lookup) for p in chunkl.split_top(text[1:-1])]
                return parts
            if text == "empty":
                return "" if fld["type"] == "string" else None
            v = expr.evaluate(expr.parse(text), self._env_lookup)
        except Exception:
            return None
        if fld["type"] == "float" and isinstance(v, (int, float)):
            return float(v)
        if fld["type"] == "bool":
            return bool(v)
        if fld["type"] == "int" and isinstance(v, (int, float)):
            return int(v)
        if fld["type"] == "enum" and isinstance(v, int):
            return v
        if fld["type"] == "string" and isinstance(v, str):
            return v
        return None


# ------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gbxnet", required=True, help="path to a gbx-net checkout")
    ap.add_argument("--out", default=str(HERE.parent / "schema" / "base"))
    ap.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS)
    ap.add_argument("--modeled", nargs="*", default=DEFAULT_MODELED,
                    help="classes that become editable child nodes")
    ap.add_argument("--commit", default=None, help="gbx-net commit id to record (default: git rev-parse)")
    a = ap.parse_args(argv)

    root = Path(a.gbxnet)
    engines = root / "Src" / "GBX.NET" / "Engines"
    if not engines.is_dir():
        raise SystemExit(f"{engines} not found")
    commit = a.commit
    if commit is None:
        try:
            commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                             text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            commit = "unknown"

    gen = Generator(engines, a.modeled)
    gen.run(a.roots)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    for cname, entry in sorted(gen.out.items()):
        entry["gbxnet_commit"] = commit
        (out / f"{cname}.json").write_text(json.dumps(entry, indent=1) + "\n", encoding="utf-8")
    (out / "_index.json").write_text(json.dumps({
        "schema_format": SCHEMA_FORMAT, "game": GAME, "gbxnet_commit": commit,
        "roots": a.roots, "classes": sorted(gen.out), "warnings": gen.warnings,
    }, indent=1) + "\n", encoding="utf-8")

    n_fields = sum(len(c["fields"]) for e in gen.out.values() for c in e["chunks"]) + \
        sum(len(x["fields"]) for e in gen.out.values() for x in e["archives"].values())
    print(f"wrote {len(gen.out)} classes, {n_fields} fields -> {out}")
    for w in gen.warnings:
        print("warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
