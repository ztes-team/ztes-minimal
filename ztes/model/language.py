"""[Sω/Sτ] The language of bodies: expressions, functions and libraries.   Paper: §3.4.4, S1.2, S1.4

The body of a specification computes ω (ontology) or the judgment (criterion). It is
written in one of two forms:

  expressions   {"name": "expr", …, "result": "expr"}: named Python expressions, in order;
  a function    the source text of one Python function, e.g.

                    def omega(n, primes, prev):
                        g = gcd(n, prev["n"])
                        ...
                        return {"n": n, "factors": factors, "reused": ..., "gcd": g}

The parameters of a function name what it receives: declared bindings, the candidate, and
constants or derived values. Nothing else is visible. The source text is the body that is
recorded in C and addressed, so R2 replays exactly the function that was judged.

Determinism (S1.2) is a property of this language, not of the code around it:

  * a body may use only SAFE (pure functions: no I/O, no clock, no randomness), its inputs,
    and the helper functions of its library;
  * a function body has exactly one top-level `def`, no default values, no *args or **kwargs;
  * only these statements: assignment, augmented assignment, if/elif/else,
    `for` over a finite iterable, `return`, `pass`, `continue`, `break`, and
    expression statements (e.g. `xs.append(x)`);
  * no while, try, with, raise, import, global, nonlocal, class, def, lambda,
    yield, await, del, assert;
  * no name or attribute that starts with an underscore;
  * every name read is a parameter, a local variable, or an allowed function;
  * the function does not call itself.

Together with the bounded `for` this keeps every body terminating and deterministic. It is a
discipline checked before a specification is recorded (τ_root, validation.py), not a security
sandbox.
"""
import ast
import math
from fractions import Fraction

from .errors import SpecError, Undefined

ALLOWED_STATEMENTS = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.If, ast.For, ast.Return,
                      ast.Pass, ast.Continue, ast.Break, ast.Expr)
FORBIDDEN = (ast.While, ast.Try, ast.With, ast.Raise, ast.Import, ast.ImportFrom, ast.Global,
             ast.Nonlocal, ast.ClassDef, ast.AsyncFunctionDef, ast.Lambda, ast.Yield, ast.YieldFrom,
             ast.Await, ast.Delete, ast.Assert, ast.AsyncFor, ast.AsyncWith)
try:
    FORBIDDEN += (ast.TryStar,)
except AttributeError:          # Python < 3.11
    pass

# The only names a body may use besides its inputs and its library: pure functions (S1.2).
SAFE = {"Fraction": Fraction, "gcd": math.gcd, "isqrt": math.isqrt, "floor": math.floor,
        "ceil": math.ceil, "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
        "sorted": sorted, "range": range, "all": all, "any": any, "prod": math.prod, "set": set}
CONSTANT_NAMES = {"None", "True", "False"}


# ---- expressions -----------------------------------------------------------------------

_CODE = {}


def expression(expr, env, ns=None):
    """Evaluate one expression in one namespace, so that comprehensions see every name of env.

    The expression is compiled once per text; its value depends only on env and ns.
    """
    code = _CODE.get(expr)
    if code is None:
        code = _CODE[expr] = compile(expr, "<expression>", "eval")
    return eval(code, {"__builtins__": {}, **(ns or SAFE), **env})


def free_names(expr):
    """The names an expression reads, without those bound inside it (comprehensions, lambdas)."""
    tree = ast.parse(expr, mode="eval")
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    bound |= {a.arg for n in ast.walk(tree) if isinstance(n, ast.Lambda) for a in n.args.args}
    return used - bound


def source_names(src):
    """Every name read anywhere in a function or library source."""
    return {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


# ---- a body written as one function --------------------------------------------------------


def is_function(body):
    return isinstance(body, str)


def parse(src):
    """The single function definition of a body, or ValueError."""
    tree = ast.parse(src)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("a function body must contain exactly one top-level def")
    return tree.body[0]


def parameters(src):
    return [a.arg for a in parse(src).args.args]


def problems(src, allowed):
    """Rule violations of a function body; `allowed` are the extra names it may use (functions)."""
    try:
        fn = parse(src)
    except (SyntaxError, ValueError) as x:
        return [str(x)]
    return _fn_problems(fn, allowed)


def _fn_problems(fn, allowed):
    out = []
    a = fn.args
    if a.vararg or a.kwarg or a.kwonlyargs or a.defaults or a.posonlyargs or fn.decorator_list:
        out.append("parameters must be plain names, without defaults, *args, **kwargs or decorators")
    for node in ast.walk(fn):
        if isinstance(node, FORBIDDEN) or (isinstance(node, ast.FunctionDef) and node is not fn):
            out.append(f"line {node.lineno}: {type(node).__name__} is not allowed")
        elif isinstance(node, ast.stmt) and node is not fn and not isinstance(node, ALLOWED_STATEMENTS):
            out.append(f"line {node.lineno}: {type(node).__name__} is not allowed")
        if isinstance(node, ast.Name) and node.id.startswith("_") and node.id != "_":
            out.append(f"line {node.lineno}: name {node.id} starts with an underscore")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            out.append(f"line {node.lineno}: attribute {node.attr} starts with an underscore")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == fn.name:
            out.append(f"line {node.lineno}: {fn.name} calls itself")
    params = {x.arg for x in a.args}
    stored = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    loaded = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    free = loaded - params - stored - set(allowed) - {"None", "True", "False"}
    if free:
        out.append(f"uses undeclared {sorted(free)}")
    return out


# ---- a library: helper functions shared by the specifications of a system -------------------
#
# lib.py holds pure helper functions, e.g. dist(XY, a, b). Each def obeys the rules above;
# in addition a def may call only the defs written before it, so there is no recursion,
# direct or mutual. When a specification is expanded, the defs it uses (and the defs those
# use) are copied into its "library" field: the recorded specification stays self-contained.


def library_defs(src):
    """The defs of a library, in order: [(name, node)]."""
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            raise ValueError(f"line {node.lineno}: a library contains only function definitions")
        out.append((node.name, node))
    return out


def library_problems(src, allowed):
    try:
        defs = library_defs(src)
    except (SyntaxError, ValueError) as x:
        return [str(x)]
    out, earlier = [], set()
    names = [n for n, _ in defs]
    if len(set(names)) != len(names):
        out.append("a library defines a name twice")
    for name, fn in defs:
        out += [f"{name}: {p}" for p in _fn_problems(fn, set(allowed) | earlier)]
        earlier.add(name)
    return out


def library_names(src):
    return [n for n, _ in library_defs(src)] if src else []


def library_subset(src, used):
    """The source of the defs named in `used` and of every def they call, in library order."""
    if not src:
        return ""
    defs = library_defs(src)
    calls = {n: {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
             for n, fn in defs}
    need, todo = set(), [u for u in used if u in calls]
    while todo:
        n = todo.pop()
        if n not in need:
            need.add(n)
            todo += [c for c in calls[n] if c in calls]
    return "\n\n".join(ast.get_source_segment(src, fn) for n, fn in defs if n in need)


_LIBRARIES = {}


def library(src, safe):
    """The functions of a library, compiled once per source text."""
    if not src:
        return {}
    if src not in _LIBRARIES:
        namespace = {"__builtins__": {}, **safe}
        exec(compile(src, "<library>", "exec"), namespace)
        _LIBRARIES[src] = {n: namespace[n] for n in library_names(src)}
    return _LIBRARIES[src]


_COMPILED = {}


def call(src, env, safe):
    """Run the function with its parameters taken from env. Compiled once per source and namespace."""
    key = (src, id(safe))
    hit = _COMPILED.get(key)
    if hit is None:
        fn = parse(src)
        namespace = {"__builtins__": {}, **safe}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<body>", "exec"), namespace)
        hit = _COMPILED[key] = (namespace[fn.name], tuple(x.arg for x in fn.args.args), safe)  # keep safe alive
    f, params, _ = hit
    try:
        args = [env[p] for p in params]
    except KeyError:
        missing = [p for p in params if p not in env]
        raise NameError(f"parameters {missing} are not declared bindings, the candidate, or constants") from None
    return f(*args)


# ---- the namespace of a specification, and the evaluation of its body ----------------------

_NAMESPACES = {}


def namespace(library_src):
    """The functions a body may call: SAFE and the functions of its library (one dict per library)."""
    if not library_src:
        return SAFE
    ns = _NAMESPACES.get(library_src)
    if ns is None:
        ns = _NAMESPACES[library_src] = {**SAFE, **library(library_src, SAFE)}
    return ns


def evaluate(body, env, ns=None):
    """Evaluate a body on its inputs env: the expressions in order ("result" is the value), or the function.

    ⊥ (Undefined) passes through unchanged; any other failure is a SpecError naming the
    expression that raised it, so that a defect is reported where it is.
    """
    ns = ns or SAFE
    if is_function(body):
        try:
            return call(body, env, ns)
        except Undefined:
            raise
        except Exception as x:
            raise SpecError(f"body function: {type(x).__name__}: {x}") from None
    env = dict(env)
    for name, expr in body.items():
        try:
            env[name] = expression(expr, env, ns)
        except Undefined:
            raise
        except Exception as x:
            raise SpecError(f"body '{name}': {type(x).__name__}: {x}") from None
    return env["result"]
