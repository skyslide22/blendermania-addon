"""Evaluator for Trackmania fx system expressions (effect node expressions, conditions, variable updates).

Language as listed in Trackmania.exe (SPlugExpr): numbers, 'strings', identifiers (Time in ms, variables, context
inputs), + - * / %, comparisons, && || !, member access (.x .y .z .w), indexing, and the functions below.
Values are floats, vectors (tuples) or strings; vector operations work per component.

Used by the viewport preview only (not exported, not the game): unknown context inputs (DecorationColorHSL,
UISequence, ...) evaluate to 0, which matched the game for items (DecorationColorHSL.x gave hue 0 = red).
Stateful functions (val_follow, angle_follow) return their target.

compile_expr(text) -> Expr with .const (True when it uses no Time/variables/rand) and .eval(env, rnd).
"""
import math
import re

_TOKEN = re.compile(r"\s*(?:(?P<num>\d+\.\d*(?:[eE][-+]?\d+)?f?|\.\d+(?:[eE][-+]?\d+)?f?|\d+(?:[eE][-+]?\d+)?f?)"
                    r"|(?P<str>'[^']*'|\"[^\"]*\")|(?P<id>[A-Za-z_]\w*)"
                    r"|(?P<op>&&|\|\||<=|>=|==|!=|[-+*/%<>!(),.\[\]]))")


class ExprError(ValueError):
    pass


def _tokens(text):
    pos, out = 0, []
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ExprError(f"unexpected {text[pos:pos + 8]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


# ------------------------------------------------------------------ value helpers
def _vec(v):
    return isinstance(v, tuple)


def _map2(f, a, b):
    if _vec(a) or _vec(b):
        n = max(len(a) if _vec(a) else 1, len(b) if _vec(b) else 1)
        a = a if _vec(a) else (a,) * n
        b = b if _vec(b) else (b,) * n
        return tuple(f(x, y) for x, y in zip(a, b))
    return f(a, b)


def _map1(f, a):
    return tuple(f(x) for x in a) if _vec(a) else f(a)


def _num(v):
    if isinstance(v, str):
        raise ExprError("string used as number")
    return v


def _truth(v):
    if _vec(v):
        return any(x != 0 for x in v)
    if isinstance(v, str):
        return bool(v)
    return v != 0


def _div(a, b):
    return a / b if b != 0 else 0.0


def _mod(a, b):
    return math.fmod(a, b) if b != 0 else 0.0


def _frac(x):
    return x - math.floor(x)


def _pow(x, y):
    if x < 0:
        if float(y).is_integer():
            return -(abs(x) ** y) if int(y) % 2 else abs(x) ** y
        return 0.0
    return x ** y


def _sat(x):
    return min(1.0, max(0.0, x))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _len(a):
    return math.sqrt(sum(x * x for x in a)) if _vec(a) else abs(a)


def _normalize(a):
    n = _len(a)
    return _map1(lambda x: x / n, a) if n > 1e-12 else a


def _float_n(n):
    def f(*args):
        flat = []
        for a in args:
            flat.extend(a if _vec(a) else (a,))
        if len(flat) == 1:
            flat = flat * n
        if len(flat) != n:
            raise ExprError(f"float{n} needs {n} values")
        return tuple(float(x) for x in flat)
    return f


def _member(v, name):
    if not _vec(v):
        return v                            # unknown input (0) or scalar: every component is the value
    idx = {"x": 0, "y": 1, "z": 2, "w": 3, "r": 0, "g": 1, "b": 2, "a": 3}
    if len(name) == 1:
        return v[idx[name]] if idx.get(name, 99) < len(v) else 0.0
    return tuple(v[idx[c]] if idx.get(c, 99) < len(v) else 0.0 for c in name)


# name -> (min args, max args, function(*args, rnd)); rnd() gives a value in [0, 1)
FUNCTIONS = {
    "min": (2, 2, lambda a, b, r: _map2(min, a, b)),
    "max": (2, 2, lambda a, b, r: _map2(max, a, b)),
    "clamp": (3, 3, lambda a, lo, hi, r: _map2(min, _map2(max, a, lo), hi)),
    "sat": (1, 1, lambda a, r: _map1(_sat, a)),
    "lerp": (3, 3, lambda a, b, f, r: _map2(lambda x, d: x + d, a,
                                            _map2(lambda d, ff: d * ff, _map2(lambda x, y: y - x, a, b), f))),
    "pow": (2, 2, lambda a, b, r: _map2(_pow, a, b)),
    "sqrt": (1, 1, lambda a, r: _map1(lambda x: math.sqrt(max(0.0, x)), a)),
    "sqr": (1, 1, lambda a, r: _map1(lambda x: x * x, a)),
    "sin": (1, 1, lambda a, r: _map1(math.sin, a)),
    "cos": (1, 1, lambda a, r: _map1(math.cos, a)),
    "tan": (1, 1, lambda a, r: _map1(math.tan, a)),
    "asin": (1, 1, lambda a, r: _map1(lambda x: math.asin(max(-1.0, min(1.0, x))), a)),
    "acos": (1, 1, lambda a, r: _map1(lambda x: math.acos(max(-1.0, min(1.0, x))), a)),
    "atan": (1, 1, lambda a, r: _map1(math.atan, a)),
    "atan2": (2, 2, lambda y, x, r: _map2(math.atan2, y, x)),
    "frac": (1, 1, lambda a, r: _map1(_frac, a)),
    "floor": (1, 1, lambda a, r: _map1(math.floor, a)),
    "abs": (1, 1, lambda a, r: _map1(abs, a)),
    "sign": (1, 1, lambda a, r: _map1(lambda x: 1.0 if x > 0 else -1.0, a)),
    "dot": (2, 2, lambda a, b, r: sum(x * y for x, y in zip(a, b))),
    "cross": (2, 2, lambda a, b, r: _cross(a, b)),
    "len": (1, 1, lambda a, r: _len(a)),
    "normalize": (1, 1, lambda a, r: _normalize(a)),
    "yaw": (1, 2, lambda a, *rest: math.atan2(a[0], a[2]) if _vec(a) else 0.0),
    "comp": (2, 2, lambda a, n, r: a[int(n)] if _vec(a) and 0 <= int(n) < len(a) else 0.0),
    "rad2deg": (1, 1, lambda a, r: _map1(math.degrees, a)),
    "deg2rad": (1, 1, lambda a, r: _map1(math.radians, a)),
    "rand": (2, 2, lambda lo, hi, r: lo + (hi - lo) * r()),
    "rand01": (0, 0, lambda r: r()),
    "smoothstep": (1, 1, lambda a, r: _map1(lambda x: _sat(x) * _sat(x) * (3.0 - 2.0 * _sat(x)), a)),
    "select": (3, 3, lambda c, a, b, r: a if _truth(c) else b),
    "cond": (3, 3, lambda c, a, b, r: a if _truth(c) else b),
    "mod": (2, 2, lambda a, b, r: _map2(_mod, a, b)),
    "div": (2, 2, lambda a, b, r: _map2(_div, a, b)),
    "not": (1, 1, lambda a, r: 0.0 if _truth(a) else 1.0),
    "and": (2, 2, lambda a, b, r: 1.0 if _truth(a) and _truth(b) else 0.0),
    "float2": (1, 2, lambda *a: _float_n(2)(*a[:-1])),
    "float3": (1, 3, lambda *a: _float_n(3)(*a[:-1])),
    "float4": (1, 4, lambda *a: _float_n(4)(*a[:-1])),
    "int3": (1, 3, lambda *a: tuple(float(int(x)) for x in _float_n(3)(*a[:-1]))),
    "val_follow": (2, 4, lambda cur, target, *rest: target),
    "angle_follow": (2, 4, lambda cur, target, *rest: target),
    "normalize_angle": (1, 1, lambda a, r: math.atan2(math.sin(a), math.cos(a))),
}
_RANDOM = {"rand", "rand01"}
_BINARY = {
    "+": lambda a, b: _map2(lambda x, y: x + y, _num(a), _num(b)),
    "-": lambda a, b: _map2(lambda x, y: x - y, _num(a), _num(b)),
    "*": lambda a, b: _map2(lambda x, y: x * y, _num(a), _num(b)),
    "/": lambda a, b: _map2(_div, _num(a), _num(b)),
    "%": lambda a, b: _map2(_mod, _num(a), _num(b)),
    "<": lambda a, b: 1.0 if _num(a) < _num(b) else 0.0,
    "<=": lambda a, b: 1.0 if _num(a) <= _num(b) else 0.0,
    ">": lambda a, b: 1.0 if _num(a) > _num(b) else 0.0,
    ">=": lambda a, b: 1.0 if _num(a) >= _num(b) else 0.0,
    "==": lambda a, b: 1.0 if a == b else 0.0,
    "!=": lambda a, b: 1.0 if a != b else 0.0,
}


# ------------------------------------------------------------------ parser -> closures
class _Parser:
    """recursive descent; every rule returns (fn(env, rnd), dynamic)"""

    def __init__(self, text):
        self.toks = _tokens(text)
        self.i = 0

    def peek(self, value=None):
        if self.i >= len(self.toks):
            return None
        t = self.toks[self.i]
        return t if value is None or t[1] == value else None

    def take(self, value=None):
        t = self.peek(value)
        if t is None:
            raise ExprError(f"expected {value!r}" if value else "unexpected end")
        self.i += 1
        return t

    def parse(self):
        fn = self.or_()
        if self.peek() is not None:
            raise ExprError(f"unexpected {self.peek()[1]!r}")
        return fn

    def _chain(self, sub, ops):
        left, dyn = sub()
        while self.peek() is not None and self.peek()[1] in ops:
            op = self.take()[1]
            right, d2 = sub()
            left, dyn = self._bin(op, left, right), dyn or d2
        return left, dyn

    def _bin(self, op, l, r):
        if op in ("&&", "||", "and", "or"):
            if op in ("&&", "and"):
                return lambda e, rnd: 1.0 if _truth(l(e, rnd)) and _truth(r(e, rnd)) else 0.0
            return lambda e, rnd: 1.0 if _truth(l(e, rnd)) or _truth(r(e, rnd)) else 0.0
        f = _BINARY[op]
        return lambda e, rnd: f(l(e, rnd), r(e, rnd))

    def or_(self):
        return self._chain(self.and_, ("||", "or"))

    def and_(self):
        return self._chain(self.cmp, ("&&", "and"))

    def cmp(self):
        return self._chain(self.add, ("<", "<=", ">", ">=", "==", "!="))

    def add(self):
        return self._chain(self.mul, ("+", "-"))

    def mul(self):
        return self._chain(self.unary, ("*", "/", "%"))

    def unary(self):
        t = self.peek()
        if t is not None and t[1] in ("-", "+", "!") and t[0] == "op":
            self.take()
            fn, dyn = self.unary()
            if t[1] == "-":
                return (lambda e, rnd: _map1(lambda x: -x, _num(fn(e, rnd)))), dyn
            if t[1] == "!":
                return (lambda e, rnd: 0.0 if _truth(fn(e, rnd)) else 1.0), dyn
            return fn, dyn
        return self.postfix()

    def postfix(self):
        fn, dyn = self.primary()
        while True:
            if self.peek("."):
                self.take(".")
                name = self.take()[1]
                fn = (lambda f, n: lambda e, rnd: _member(f(e, rnd), n))(fn, name)
            elif self.peek("["):
                self.take("[")
                idx, d2 = self.or_()
                self.take("]")
                fn = (lambda f, ix: lambda e, rnd: (lambda v, k: v[int(k)] if _vec(v) and 0 <= int(k) < len(v) else 0.0)(f(e, rnd), ix(e, rnd)))(fn, idx)
                dyn = dyn or d2
            else:
                return fn, dyn

    def primary(self):
        kind, value = self.take()
        if kind == "num":
            v = float(value.rstrip("fF"))
            return (lambda e, rnd: v), False
        if kind == "str":
            s = value[1:-1]
            return (lambda e, rnd: s), False
        if value == "(":
            fn = self.or_()
            self.take(")")
            return fn
        if kind == "id":
            if self.peek("("):
                return self.call(value)
            if value in ("true", "True"):
                return (lambda e, rnd: 1.0), False
            if value in ("false", "False"):
                return (lambda e, rnd: 0.0), False
            name = value
            return (lambda e, rnd: e.get(name, 0.0)), True    # Time, variables; unknown inputs = 0
        raise ExprError(f"unexpected {value!r}")

    def call(self, name):
        self.take("(")
        args, dyn = [], name in _RANDOM
        if not self.peek(")"):
            while True:
                fn, d = self.or_()
                args.append(fn)
                dyn = dyn or d
                if not self.peek(","):
                    break
                self.take(",")
        self.take(")")
        spec = FUNCTIONS.get(name)
        if spec is None:
            raise ExprError(f"unknown function {name}()")
        lo, hi, f = spec
        if not lo <= len(args) <= hi:
            raise ExprError(f"{name}() takes {lo}..{hi} arguments, got {len(args)}")
        return (lambda e, rnd: f(*[a(e, rnd) for a in args], rnd)), dyn


class Expr:
    def __init__(self, text: str):
        self.text = text
        fn, self.dynamic = _Parser(text).parse()
        self._fn = fn
        self.const = not self.dynamic
        self._value = fn({}, lambda: 0.5) if self.const else None

    def eval(self, env=None, rnd=None):
        if self.const:
            return self._value
        return self._fn(env or {}, rnd or (lambda: 0.5))


_cache: dict = {}


def compile_expr(text):
    """Expr or None (empty / invalid: the caller uses its default); compiled once per text"""
    if not text or not str(text).strip():
        return None
    text = str(text)
    if text not in _cache:
        try:
            _cache[text] = Expr(text)
        except (ExprError, KeyError, IndexError, ValueError, TypeError, ZeroDivisionError):
            _cache[text] = None
    return _cache[text]


def truthy(v) -> bool:
    return _truth(v)
