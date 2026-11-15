"""Tiny expression language shared by the schema generator and the Blender runtime.

ChunkL conditions look like ``Type == 1``, ``!BitmapIsFile`` or
``MeshRef == null || MeshRef == ""``.  The generator parses them into a small
JSON-friendly AST and the runtime evaluates that AST against live property
values.  Pure Python, no ``eval``; importable without Blender.

AST nodes (plain lists, so they survive a JSON round-trip):
    ["num", v] ["str", s] ["bool", b] ["null"]
    ["id", name]      identifier not (yet) bound to a schema field
    ["key", key]      bound to a schema field key (runtime lookup)
    ["un", op, a]     op in "!", "-"
    ["bin", op, a, b]
    ["tern", c, a, b]
    ["isnull", a, negate]
"""
from __future__ import annotations

import re
from typing import Any, Callable

__all__ = ["ParseError", "Unresolved", "parse", "evaluate", "fold", "ids",
           "rewrite", "to_str", "is_const", "AND", "NOT"]


class ParseError(ValueError):
    pass


class Unresolved(Exception):
    """Raised by evaluate() when an identifier cannot be looked up."""


_TOKEN = re.compile(
    r"""\s*(?:
        (?P<num>0[xX][0-9A-Fa-f]+|\d+\.\d+(?:[eE][-+]?\d+)?[fFdD]?|\d+[fFdD]|\d+[uUlL]*)
      | (?P<str>"(?:[^"\\]|\\.)*")
      | (?P<id>[A-Za-z_]\w*(?:\??\.[A-Za-z_]\w*)*)
      | (?P<op>&&|\|\||==|!=|<=|>=|\?\?|[-+*/%<>!()?:|&])
    )""",
    re.X,
)


def _tokenize(text: str):
    pos, out = 0, []
    text = text.rstrip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ParseError(f"bad token at {pos} in {text!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def _num(s: str):
    if s[:2].lower() == "0x":
        return int(s, 16)
    if s[-1] in "fFdD" or "." in s or "e" in s.lower():
        return float(s.rstrip("fFdD"))
    return int(s.rstrip("uUlL"))


class _Parser:
    def __init__(self, text: str):
        self.t = _tokenize(text)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, val):
        if self.peek()[1] == val:
            self.i += 1
            return True
        return False

    def parse(self):
        node = self.ternary()
        if self.i != len(self.t):
            raise ParseError(f"trailing tokens: {self.t[self.i:]}")
        return node

    def ternary(self):
        c = self.coalesce()
        if self.accept("?"):
            a = self.ternary()
            if not self.accept(":"):
                raise ParseError("expected ':'")
            b = self.ternary()
            return ["tern", c, a, b]
        return c

    def coalesce(self):
        a = self.or_()
        while self.accept("??"):
            a = ["bin", "??", a, self.or_()]
        return a

    def or_(self):
        a = self.and_()
        while self.accept("||"):
            a = ["bin", "||", a, self.and_()]
        return a

    def and_(self):
        a = self.bitor()
        while self.accept("&&"):
            a = ["bin", "&&", a, self.bitor()]
        return a

    def bitor(self):
        a = self.bitand()
        while self.peek()[1] == "|":
            self.take()
            a = ["bin", "|", a, self.bitand()]
        return a

    def bitand(self):
        a = self.equality()
        while self.peek()[1] == "&":
            self.take()
            a = ["bin", "&", a, self.equality()]
        return a

    def equality(self):
        a = self.relational()
        while self.peek()[1] in ("==", "!="):
            op = self.take()[1]
            a = ["bin", op, a, self.relational()]
        return a

    def relational(self):
        a = self.additive()
        while True:
            v = self.peek()[1]
            if v in ("<", ">", "<=", ">="):
                self.take()
                a = ["bin", v, a, self.additive()]
            elif v == "is":
                self.take()
                neg = self.peek()[1] == "not"
                if neg:
                    self.take()
                if self.take()[1] != "null":
                    raise ParseError("only 'is [not] null' is supported")
                a = ["isnull", a, neg]
            else:
                return a

    def additive(self):
        a = self.mult()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            a = ["bin", op, a, self.mult()]
        return a

    def mult(self):
        a = self.unary()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.take()[1]
            a = ["bin", op, a, self.unary()]
        return a

    def unary(self):
        v = self.peek()[1]
        if v in ("!", "-"):
            self.take()
            return ["un", v, self.unary()]
        return self.primary()

    def primary(self):
        kind, val = self.take()
        if kind == "num":
            return ["num", _num(val)]
        if kind == "str":
            return ["str", val[1:-1].replace('\\"', '"').replace("\\\\", "\\")]
        if kind == "id":
            if val == "null":
                return ["null"]
            if val in ("true", "false"):
                return ["bool", val == "true"]
            return ["id", val]
        if val == "(":
            node = self.ternary()
            if not self.accept(")"):
                raise ParseError("expected ')'")
            return node
        raise ParseError(f"unexpected token {val!r}")


def parse(text: str) -> list:
    """Parse an expression string into an AST."""
    return _Parser(text).parse()


def _isnull(v) -> bool:
    return v is None or v == ""


def _eq(a, b) -> bool:
    if _isnull(a) or _isnull(b):
        return _isnull(a) and _isnull(b)
    return a == b


def _no_lookup(name):
    raise KeyError(name)


def evaluate(ast, lookup: Callable[[str], Any]):
    """Evaluate an AST; ``lookup(name)`` resolves "key"/"id" nodes (KeyError -> Unresolved)."""
    t = ast[0]
    if t in ("num", "str", "bool"):
        return ast[1]
    if t == "null":
        return None
    if t in ("key", "id"):
        try:
            return lookup(ast[1])
        except KeyError:
            raise Unresolved(ast[1]) from None
    if t == "isnull":
        r = _isnull(evaluate(ast[1], lookup))
        return (not r) if ast[2] else r
    if t == "un":
        v = evaluate(ast[2], lookup)
        return (not v) if ast[1] == "!" else -v
    if t == "tern":
        return evaluate(ast[2] if evaluate(ast[1], lookup) else ast[3], lookup)
    if t == "bin":
        op = ast[1]
        if op == "&&":
            return bool(evaluate(ast[2], lookup)) and bool(evaluate(ast[3], lookup))
        if op == "||":
            return bool(evaluate(ast[2], lookup)) or bool(evaluate(ast[3], lookup))
        if op == "??":
            a = evaluate(ast[2], lookup)
            return a if a is not None else evaluate(ast[3], lookup)
        a, b = evaluate(ast[2], lookup), evaluate(ast[3], lookup)
        if op == "==":
            return _eq(a, b)
        if op == "!=":
            return not _eq(a, b)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b if isinstance(a, float) or isinstance(b, float) else a // b
        if op == "%":
            return a % b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        if op == "|":
            return int(a) | int(b)
        if op == "&":
            return int(a) & int(b)
    raise ValueError(f"cannot evaluate {ast!r}")


def is_const(ast) -> bool:
    t = ast[0]
    if t in ("num", "str", "bool", "null"):
        return True
    if t in ("id", "key"):
        return False
    if t == "un":
        return is_const(ast[2])
    if t == "isnull":
        return is_const(ast[1])
    if t == "tern":
        return all(is_const(x) for x in ast[1:])
    if t == "bin":
        return is_const(ast[2]) and is_const(ast[3])
    return False


def _lit(v):
    if v is None:
        return ["null"]
    if isinstance(v, bool):
        return ["bool", v]
    if isinstance(v, str):
        return ["str", v]
    return ["num", v]


def fold(ast):
    """Constant-fold an AST (``Version == 0 || X`` with Version known -> ``X``)."""
    t = ast[0]
    if t == "un":
        ast = ["un", ast[1], fold(ast[2])]
    elif t == "isnull":
        ast = ["isnull", fold(ast[1]), ast[2]]
    elif t == "tern":
        ast = ["tern", fold(ast[1]), fold(ast[2]), fold(ast[3])]
    elif t == "bin":
        a, b = fold(ast[2]), fold(ast[3])
        op = ast[1]
        if op in ("&&", "||"):
            if is_const(a):
                av = bool(evaluate(a, _no_lookup))
                if op == "&&":
                    return b if av else ["bool", False]
                return ["bool", True] if av else b
            if is_const(b):
                bv = bool(evaluate(b, _no_lookup))
                if op == "&&":
                    return a if bv else ["bool", False]
                return ["bool", True] if bv else a
        ast = ["bin", op, a, b]
    if is_const(ast):
        try:
            return _lit(evaluate(ast, _no_lookup))
        except Exception:
            return ast
    return ast


def ids(ast) -> set:
    """All unbound identifier names ("id" nodes) in the AST."""
    t = ast[0]
    if t == "id":
        return {ast[1]}
    out = set()
    if t == "un":
        out |= ids(ast[2])
    elif t == "isnull":
        out |= ids(ast[1])
    elif t == "tern":
        for x in ast[1:]:
            out |= ids(x)
    elif t == "bin":
        out |= ids(ast[2]) | ids(ast[3])
    return out


def rewrite(ast, fn):
    """Replace "id" nodes: ``fn(name)`` returns a replacement AST or None to keep."""
    t = ast[0]
    if t == "id":
        r = fn(ast[1])
        return r if r is not None else ast
    if t == "un":
        return ["un", ast[1], rewrite(ast[2], fn)]
    if t == "isnull":
        return ["isnull", rewrite(ast[1], fn), ast[2]]
    if t == "tern":
        return ["tern"] + [rewrite(x, fn) for x in ast[1:]]
    if t == "bin":
        return ["bin", ast[1], rewrite(ast[2], fn), rewrite(ast[3], fn)]
    return ast


def AND(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return ["bin", "&&", a, b]


def NOT(a):
    return ["un", "!", a]


def to_str(ast) -> str:
    """Human readable form (used in tooltips)."""
    t = ast[0]
    if t == "num":
        return repr(ast[1])
    if t == "str":
        return '"%s"' % ast[1]
    if t == "bool":
        return "true" if ast[1] else "false"
    if t == "null":
        return "null"
    if t in ("id", "key"):
        return ast[1]
    if t == "un":
        return f"{ast[1]}{to_str(ast[2])}"
    if t == "isnull":
        return f"{to_str(ast[1])} is {'not ' if ast[2] else ''}null"
    if t == "tern":
        return f"({to_str(ast[1])} ? {to_str(ast[2])} : {to_str(ast[3])})"
    if t == "bin":
        return f"({to_str(ast[2])} {ast[1]} {to_str(ast[3])})"
    return "?"
