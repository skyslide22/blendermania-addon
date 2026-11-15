"""Minimal ChunkL (.chunkl) parser used by the schema generator.

ChunkL is the layout language GBX.NET uses to describe Gbx classes
(https://github.com/BigBang1112/gbx-net/blob/master/Docs/ChunkL.md).  This is
not a full implementation of the language: it understands exactly what is
needed to turn a class layout into a flat, version-resolved field list, and it
keeps unknown constructs as ``Raw`` statements instead of failing, so a new
GBX.NET release never silently breaks the generator.

Stdlib only.  AST:

    ClassDef(name, id, attrs, chunks, archives, enums)
    Chunk(offset, attrs, games, base, body)
    Archive(name, attrs, body)
    Enum(name, members)
    body statements: Field | VersionBlock | If | Assign | Special | Raw
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class ChunkLError(Exception):
    pass


# --------------------------------------------------------------------------- AST
@dataclass
class Field:
    type: str                       # base type name: float, CPlugMaterial, data, version ...
    name: Optional[str] = None
    array: Optional[str] = None     # None=scalar, ""=variable list, "N"/"expr"=sized
    cast: Optional[str] = None      # int<EnumName> -> "EnumName"
    nullable: bool = False
    default: Optional[str] = None   # raw default expression
    attrs: dict = field(default_factory=dict)
    line: int = 0
    member: str = ""                # assigned by number_members()

    @property
    def is_version(self):
        return self.type in ("version", "versionb")

    @property
    def is_special(self):
        return self.type in ("return", "throw", "base")


@dataclass
class VersionBlock:
    op: str                         # "=", "+", "-", ".."
    a: int
    b: Optional[int]
    selector: Optional[str]         # "archive" | "chunk" | None
    body: list
    line: int = 0


@dataclass
class If:
    cond: str
    body: list
    elifs: list = field(default_factory=list)       # [(cond, body)]
    else_body: Optional[list] = None
    line: int = 0


@dataclass
class Assign:
    name: str
    expr: str
    line: int = 0


@dataclass
class Special:
    kind: str                       # return | throw | base
    raw: str = ""
    line: int = 0


@dataclass
class Raw:
    text: str
    body: list = field(default_factory=list)
    line: int = 0


@dataclass
class Chunk:
    offset: int
    attrs: dict
    games: dict                     # {"TM2020": 4, "MP4": None, ...}
    base: Optional[int]
    comment: str
    body: list
    line: int = 0


@dataclass
class Archive:
    name: str
    attrs: dict
    body: list
    line: int = 0


@dataclass
class Enum:
    name: str
    members: list                   # [(name, value)]
    flags: bool = False


@dataclass
class ClassDef:
    name: str
    id: int
    attrs: dict
    chunks: list
    archives: dict
    enums: dict
    path: str = ""


# ------------------------------------------------------------------------ helpers
PRIMITIVES = {
    "int", "uint", "short", "ushort", "byte", "sbyte", "long", "ulong", "int8", "int16",
    "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "double", "bool",
    "boolbyte", "boolean", "string", "id", "lookbackstring", "vec2", "vec3", "vec4",
    "int2", "int3", "int4", "byte3", "iso4", "iso8", "quat", "box", "boxaligned", "rect",
    "color", "data", "version", "versionb", "return", "throw", "base", "bytes", "time",
    "timeint", "timefloat", "int128", "uint128", "datauint", "dataulong", "dataint",
    "datashort", "dataushort", "databyte", "mat3", "mat4", "plane", "triangle", "mat2",
    "pack", "u", "variable",
}

_CHUNK_HDR = re.compile(r"^0x([0-9A-Fa-f]{1,3})\s*(?:\((?P<attrs>[^)]*)\))?\s*(?:\[(?P<games>[^\]]*)\])?\s*$")
_VERSION = re.compile(r"^v(\d+)(=|\+|-|\.\.(\d+))\s*(?:\((archive|chunk)\))?\s*$")
_TYPE = re.compile(
    r"^(?P<type>[A-Za-z_][\w.]*)(?P<cast><[^>]*>)?(?P<nullable>\?)?(?P<arr>\[[^\]]*\])?(?:\s+(?P<rest>.*))?$"
)
_ASSIGN = re.compile(r"^([A-Za-z_]\w*)\s*(\+=|-=|\|=|&=|=)\s*(.+)$")


def strip_comment(line: str) -> str:
    """Remove a trailing ``// comment`` that is not inside a string."""
    in_str = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"':
            in_str = not in_str
        elif c == "\\" and in_str:
            i += 1
        elif c == "/" and not in_str and line[i:i + 2] == "//":
            return line[:i]
        i += 1
    return line


def get_comment(line: str) -> str:
    code = strip_comment(line)
    return line[len(code) + 2:].strip() if len(code) < len(line) else ""


def split_top(text: str, sep=",") -> list:
    """Split on ``sep`` outside of quotes and brackets."""
    out, depth, in_str, cur = [], 0, False, []
    i = 0
    while i < len(text):
        c = text[i]
        if c == '"':
            in_str = not in_str
        elif c == "\\" and in_str:
            cur.append(c)
            i += 1
            c = text[i] if i < len(text) else ""
        elif not in_str:
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == sep and depth == 0:
                out.append("".join(cur).strip())
                cur = []
                i += 1
                continue
        cur.append(c)
        i += 1
    last = "".join(cur).strip()
    if last or out:
        out.append(last)
    return out


def parse_attrs(text: str) -> dict:
    """``local, write: "x", version: Version - 1`` -> dict."""
    out = {}
    for item in split_top(text):
        if not item:
            continue
        if ":" in item:
            k, v = item.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] == '"':
                v = v[1:-1]
            out[k.strip()] = v
        else:
            out[item] = True
    return out


def _find_top(text: str, ch: str, start=0) -> int:
    depth, in_str = 0, False
    for i in range(start, len(text)):
        c = text[i]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == ch and depth == 0:
                return i
    return -1


def parse_field_line(text: str, lineno: int) -> Optional[Field]:
    m = _TYPE.match(text)
    if not m:
        return None
    f = Field(type=m.group("type"), line=lineno)
    if m.group("cast"):
        f.cast = m.group("cast")[1:-1]
    f.nullable = bool(m.group("nullable"))
    if m.group("arr") is not None:
        f.array = m.group("arr")[1:-1].strip()
    rest = (m.group("rest") or "").strip()
    # trailing [TM10 = 100, ...] game-specific defaults: ignored
    if rest.endswith("]") and re.search(r"\[[A-Za-z0-9_]+\s*=", rest):
        rest = rest[:rest.rindex("[")].rstrip()
    # trailing (attrs)
    attrs_text = None
    if rest.endswith(")"):
        # find the matching "(" of the final group
        depth, i = 0, len(rest) - 1
        while i >= 0:
            if rest[i] == ")":
                depth += 1
            elif rest[i] == "(":
                depth -= 1
                if depth == 0:
                    break
            i -= 1
        if i >= 0:
            before = rest[:i].rstrip()
            # "= (1, 2, 3)" is a tuple default, not attributes
            if not before.endswith("="):
                attrs_text = rest[i + 1:-1]
                rest = before
    if attrs_text is not None:
        f.attrs = parse_attrs(attrs_text)
    # name / default
    nm = re.match(r"^([A-Za-z_]\w*)(?:\s*(.*))?$", rest)
    if nm and not rest.startswith("="):
        f.name = nm.group(1)
        rest = (nm.group(2) or "").strip()
    if rest.startswith("="):
        f.default = rest[1:].strip()
    elif rest:
        return None
    return f


# ------------------------------------------------------------------------ parsing
@dataclass
class _Line:
    indent: int
    text: str
    no: int
    raw: str


def _lines(text: str):
    out = []
    for no, raw in enumerate(text.splitlines(), 1):
        code = strip_comment(raw).rstrip()
        if not code.strip():
            continue
        stripped = code.lstrip(" ")
        indent = len(code) - len(stripped)
        out.append(_Line(indent // 2, stripped, no, raw))
    return out


def _parse_body(lines, i, indent):
    """Parse consecutive statements at ``indent``; returns (stmts, next_index)."""
    stmts = []
    while i < len(lines) and lines[i].indent >= indent:
        ln = lines[i]
        if ln.indent > indent:       # stray deeper line (shouldn't happen) -> skip
            i += 1
            continue
        text = ln.text
        i += 1

        def child():
            nonlocal i
            body, i = _parse_body(lines, i, indent + 1)
            return body

        m = _VERSION.match(text)
        if m:
            n = int(m.group(1))
            if m.group(2) == "=":
                op, a, b = "=", n, None
            elif m.group(2) == "+":
                op, a, b = "+", n, None
            elif m.group(2) == "-":
                op, a, b = "-", n, None
            else:
                op, a, b = "..", n, int(m.group(3))
            stmts.append(VersionBlock(op, a, b, m.group(4), child(), ln.no))
            continue

        if text.startswith("if ") or text == "if":
            node = If(text[3:].strip(), child(), line=ln.no)
            while i < len(lines) and lines[i].indent == indent:
                t2 = lines[i].text
                if t2.startswith("else if "):
                    i += 1
                    node.elifs.append((t2[8:].strip(), child()))
                elif t2 == "else" or t2.startswith("else "):
                    i += 1
                    node.else_body = child()
                    break
                else:
                    break
            stmts.append(node)
            continue

        if re.match(r"^(throw|return)\b", text):
            kind = "return" if text.startswith("return") else "throw"
            stmts.append(Special(kind, text, ln.no))
            continue
        if text == "base" or text.startswith("base "):
            stmts.append(Special("base", text, ln.no))
            continue

        first = re.match(r"^[A-Za-z_][\w.]*", text)
        ftok = first.group(0) if first else ""
        am = _ASSIGN.match(text)
        if am and ftok not in PRIMITIVES:
            stmts.append(Assign(am.group(1), am.group(3), ln.no))
            continue

        # keyword-introduced control flow we do not interpret (loops, switch, ...)
        if ftok in ("for", "foreach", "while", "switch", "case", "default", "do", "unless"):
            stmts.append(Raw(text, child(), ln.no))
            continue

        f = parse_field_line(text, ln.no)
        if f is None:
            stmts.append(Raw(text, child(), ln.no))
        else:
            if i < len(lines) and lines[i].indent > indent:
                # a field with an indented body (e.g. nested archive / unknown); keep as raw child
                child()
            stmts.append(f)
    return stmts, i


def parse_text(text: str, path: str = "") -> ClassDef:
    lines = _lines(text)
    if not lines:
        raise ChunkLError(f"{path}: empty file")
    head = re.match(r"^([A-Za-z_][\w.]*)\s+0x([0-9A-Fa-f]+)\s*$", lines[0].text)
    if not head:
        raise ChunkLError(f"{path}: bad class header {lines[0].text!r}")
    cd = ClassDef(head.group(1), int(head.group(2), 16), {}, [], {}, {}, path)
    i = 1
    while i < len(lines):
        ln = lines[i]
        if ln.indent != 0:
            i += 1
            continue
        t = ln.text
        i += 1
        if t.startswith("- "):
            k, _, v = t[2:].partition(":")
            cd.attrs[k.strip()] = v.strip() or True
            continue
        cm = _CHUNK_HDR.match(t)
        if cm:
            attrs = parse_attrs(cm.group("attrs") or "")
            base = None
            if "base" in attrs:
                base = int(str(attrs.pop("base")), 16)
            games = {}
            for g in split_top(cm.group("games") or ""):
                if not g:
                    continue
                gm = re.match(r"^([A-Za-z0-9_]+)(?:\.v(\d+))?$", g)
                if gm:
                    games[gm.group(1)] = int(gm.group(2)) if gm.group(2) else None
            body, i = _parse_body(lines, i, 1)
            cd.chunks.append(Chunk(int(cm.group(1), 16), attrs, games, base,
                                   get_comment(ln.raw), body, ln.no))
            continue
        am = re.match(r"^archive(?:\s+([A-Za-z_]\w*))?\s*(?:\(([^)]*)\))?\s*$", t)
        if am:
            body, i = _parse_body(lines, i, 1)
            name = am.group(1) or ""
            cd.archives[name] = Archive(name, parse_attrs(am.group(2) or ""), body, ln.no)
            continue
        em = re.match(r"^(enum|flags)\s+([A-Za-z_]\w*)", t)
        if em:
            members, nxt = [], 0
            while i < len(lines) and lines[i].indent >= 1:
                mt = lines[i].text
                i += 1
                mm = re.match(r"^([A-Za-z_]\w*)(?:\s*=\s*(.+))?$", mt)
                if mm:
                    if mm.group(2):
                        try:
                            nxt = int(mm.group(2), 0)
                        except ValueError:
                            pass
                    members.append((mm.group(1), nxt))
                    nxt += 1
            cd.enums[em.group(2)] = Enum(em.group(2), members, flags=em.group(1) == "flags")
            continue
        # unknown top-level construct: skip its body
        while i < len(lines) and lines[i].indent >= 1:
            i += 1
    return cd


def parse_file(path) -> ClassDef:
    p = Path(path)
    return parse_text(p.read_text(encoding="utf-8-sig"), str(p))


# ------------------------------------------------------------- member numbering
_UNKNOWN_NAME = re.compile(r"^U\d\d$")


def walk(stmts):
    """Depth-first pre-order walk, identical to GBX.NET's ``ScopeModel.Walk``."""
    for s in stmts:
        yield s
        if isinstance(s, VersionBlock):
            yield from walk(s.body)
        elif isinstance(s, If):
            yield from walk(s.body)
            for _, b in s.elifs:
                yield from walk(b)
            if s.else_body:
                yield from walk(s.else_body)
        elif isinstance(s, Raw):
            yield from walk(s.body)


def number_members(body: list) -> None:
    """Assign ``Field.member`` exactly like the GBX.NET generator.

    Within one scope (a chunk body or an archive body) every unnamed field - and
    every field explicitly named ``Unn`` - increments a counter in declaration
    order across *all* version branches.  Unnamed fields are then called
    ``U<counter:02>``.  ``version`` and special keywords do not count.
    """
    count = 0
    for s in walk(body):
        if not isinstance(s, Field) or s.is_special:
            continue
        unknown = (not s.name) or bool(_UNKNOWN_NAME.match(s.name))
        if unknown and not s.is_version:
            count += 1
        if s.is_version:
            s.member = "Version"
        elif s.name:
            s.member = s.name
        else:
            s.member = f"U{count:02d}"
