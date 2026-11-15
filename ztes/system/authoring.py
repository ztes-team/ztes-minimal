"""Step 0: authoring format → recorded format.

What a person writes and what is recorded in C are kept apart. A person writes
short specification files and shares declarations; before phase 1 every specification
is expanded into its complete, self-contained form, and only that form is admitted
by Z₀, addressed, and replayed. The calculus never sees the shortcuts,
so S1 and R2 are unaffected: a recorded specification depends on nothing outside
itself.

Shared declarations, in system.json and (overriding them) in
abstractions/<name>/abstraction.json:

    "types":     {"Cert": {"record": {...}}, …}      named types
    "constants": {"E": [10, 14, 20], …}               named JSON values
    "derived":   {"D": "[[dist(XY, a, b) …]]", …}     named values computed from constants and the
                                                      library, once per specification version
    "bindings":  {"self_count": {"from": "$self", "select": "count"}, …}
                                                      named context bindings; "$self" is the
                                                      name of the abstraction that uses them
    lib.py (next to system.json, or in abstractions/<name>/)
                                                      pure helper functions (functions.py rules)

Shortcuts in a specification file (criterion.v<k>.json, ontology.v<k>.json):

    - "abstraction", "role", "version" may be omitted: they come from the path;
    - a criterion may omit "returns": "boolean" and "total": true; an ontology
      may omit "partial": true;
    - a type may be the name of a declared type;
    - a context entry may be the name of a declared binding:  "k": "self_count";
    - the context may be a list of declared binding names:    "context": ["k", "den"];
    - declared constants, derived values and library functions that a specification
      uses are added to it automatically ("constants", "derived", "library"); only
      what it uses, and what that in turn uses, is copied;
    - the body may be written as one Python function in a file next to the JSON,
      <role>.v<k>.py; its source text becomes the "body" of the specification;
    - "body_file": "ontology.v1.py" takes the body from another file of the same
      abstraction, e.g. when a governed change alters only the constants;
    - a boundary ontology ({"boundary": true, "returns": T, "inputs": {"context": {}}}) has
      no body: its candidate is the occurrence bound to the invocation (§5.2);
    - "note": "…" is a comment for the reader (JSON has no comments). It may stand in a
      specification, in a binding (also a declared one in system.json) and in the
      candidate; it is removed before the specification is recorded.
"""
import ast
import json
from pathlib import Path

from ..model.language import is_function, library_subset, parameters, source_names
from ..model.types import BASIC

NOTE = "note"                                                   # authoring-only comment field


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf8")) if Path(path).exists() else {}


def _resolve_type(t, named, seen=()):
    if isinstance(t, str):
        if t in named:
            assert t not in seen, f"type {t} is defined in terms of itself"
            return _resolve_type(named[t], named, seen + (t,))
        return t
    if isinstance(t, dict) and len(t) == 1:
        (k, v), = t.items()
        if k == "list":
            return {"list": _resolve_type(v, named, seen)}
        if k == "record" and isinstance(v, dict):
            return {"record": {f: _resolve_type(x, named, seen) for f, x in v.items()}}
    return t


def _names(expr):
    tree = ast.parse(expr, mode="eval")
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _without_note(d):
    return {k: v for k, v in d.items() if k != NOTE} if isinstance(d, dict) else d


def declarations(system_json, local):
    """Shared declarations visible to one abstraction: system level, overridden by abstraction level."""
    out = {}
    for kind in ("types", "constants", "bindings", "derived"):
        out[kind] = {**system_json.get(kind, {}), **local.get(kind, {})}
    out["library"] = "\n\n".join(x for x in (system_json.get("library", ""), local.get("library", "")) if x)
    clash = set(out["types"]) & set(BASIC)
    assert not clash, f"declared types may not reuse basic type names: {sorted(clash)}"
    return out


def expand(raw, abstraction, role, version, decl):
    """The complete, self-contained specification that will be recorded."""
    s = _without_note(raw)
    for field, value in (("abstraction", abstraction), ("role", role), ("version", version)):
        assert s.get(field, value) == value, \
            f"{abstraction}/{role}.v{version}: {field} must match the file name"
        s[field] = value
    if role == "criterion":
        s.setdefault("returns", "boolean")
        s.setdefault("total", True)
    else:
        s.setdefault("partial", True)
        s["returns"] = _resolve_type(s["returns"], decl["types"])

    inputs = dict(s.get("inputs", {}))
    context = {}
    raw_context = inputs.get("context", {})
    if isinstance(raw_context, list):                          # ["k", "den"] means {"k": "k", "den": "den"}
        raw_context = {name: name for name in raw_context}
    for name, b in raw_context.items():
        if isinstance(b, str):
            assert b in decl["bindings"], f"{abstraction}/{role}.v{version}: no declared binding '{b}'"
            b = decl["bindings"][b]
        b = _without_note(b)
        src = b["from"]
        b["from"] = abstraction if src == "$self" else [abstraction if x == "$self" else x for x in src] \
            if isinstance(src, list) else src
        if "type" in b:
            b["type"] = _resolve_type(b["type"], decl["types"])
        context[name] = b
    inputs["context"] = context
    if isinstance(s.get("requires"), dict):                    # {"$self": 1} names the abstraction itself
        s["requires"] = {abstraction if a == "$self" else a: k for a, k in s["requires"].items()}
    if "candidate" in inputs:
        inputs["candidate"] = dict(_without_note(inputs["candidate"]),
                                   type=_resolve_type(inputs["candidate"]["type"], decl["types"]))
    s["inputs"] = inputs

    body = s.get("body")                                       # None: a boundary ontology (§5.2)
    assert body is not None or (role == "ontology" and s.get("boundary") is True), \
        f"{abstraction}/{role}.v{version}: no body (and not a boundary ontology)"
    # every name the specification uses: in the body (all of a function's code), in the
    # expressions of its bindings, and in its own derived values
    used = (set() if body is None else source_names(body) | set(parameters(body)) if is_function(body)
            else set().union(*[_names(e) for e in body.values()]))
    for b in context.values():
        for f in ("where", "key", "value"):
            if f in b:
                used |= _names(b[f])
        if isinstance(b.get("window"), str):                   # a window given by the name of a constant
            used.add(b["window"])
    if isinstance(s.get("requires"), dict):                    # a count given by the name of a constant
        used |= {k for k in s["requires"].values() if isinstance(k, str)}
    own = set(context) | (set() if body is None or is_function(body) else set(body)) \
        | ({inputs["candidate"]["name"]} if "candidate" in inputs else set())
    # derived values: the declared ones it uses, and those they use, in declaration order
    derived = dict(s.get("derived", {}))
    for e in derived.values():
        used |= _names(e)
    todo = [n for n in used - own if n in decl["derived"] and n not in derived]
    while todo:
        n = todo.pop()
        if n not in derived:
            derived[n] = decl["derived"][n]
            todo += [m for m in _names(derived[n]) if m in decl["derived"] and m not in derived]
            used |= _names(derived[n])
    if derived:
        order = list(decl["derived"])
        s["derived"] = {n: derived[n] for n in sorted(derived, key=lambda n: order.index(n) if n in order else -1)}
    constants = {n: decl["constants"][n] for n in sorted(used - own) if n in decl["constants"]}
    constants.update(s.get("constants", {}))
    if constants:
        s["constants"] = constants
    lib = library_subset(decl["library"], used) if decl["library"] else ""
    if lib:
        s["library"] = lib
        used_by_lib = source_names(lib)
        extra = {n: decl["constants"][n] for n in used_by_lib if n in decl["constants"] and n not in s.get("constants", {})}
        assert not extra, f"{abstraction}/{role}.v{version}: library functions may not read constants {sorted(extra)}"
    return s


# ---- a system as one definition (dict): read from a directory, or built in code ----------------
#
#   {"system": …, "abstractions": […], "types": …, "constants": …, "bindings": …, "derived": …,
#    "library": "source of lib.py",
#    "plan": …, "expect": …, "admission_limit": …,          (as in system.json)
#    "declarations":   {"a": {…}},                            (abstraction.json of each abstraction)
#    "specifications": {"a/criterion.v1": {…}, …}}            (the files, in the authoring form)


def read_directory(path):
    """The definition of a system stored as a directory."""
    path = Path(path)
    d = _load(path / "system.json")
    if (path / "lib.py").exists():
        d["library"] = (path / "lib.py").read_text(encoding="utf8")
    d["declarations"], d["specifications"] = {}, {}
    for a in d["abstractions"] + ([d["kpi"]] if d.get("kpi") else []):
        adir = path / "abstractions" / a
        if (adir / "abstraction.json").exists():
            d["declarations"][a] = _load(adir / "abstraction.json")
        if (adir / "lib.py").exists():
            d["declarations"].setdefault(a, {})["library"] = (adir / "lib.py").read_text(encoding="utf8")
        for f in sorted(adir.glob("*.v*.json")):
            s = _load(f)
            if "body_file" in s:                                         # a body shared with another version
                s["body"] = (adir / s.pop("body_file")).read_text(encoding="utf8")
            elif "body" not in s and f.with_suffix(".py").exists():      # body written as a function
                s["body"] = f.with_suffix(".py").read_text(encoding="utf8")
            d["specifications"][f"{a}/{f.stem}"] = s
    return d


def write_directory(definition, path, design=None):
    """Store a definition as a directory in the standard form (the inverse of read_directory)."""
    path = Path(path)
    (path / "abstractions").mkdir(parents=True, exist_ok=True)
    head = {k: v for k, v in definition.items() if k not in ("declarations", "specifications", "library")}
    (path / "system.json").write_text(json.dumps(head, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    if definition.get("library"):
        (path / "lib.py").write_text(definition["library"], encoding="utf8")
    for a in definition["abstractions"] + ([definition["kpi"]] if definition.get("kpi") else []):
        (path / "abstractions" / a).mkdir(exist_ok=True)
        local = dict(definition.get("declarations", {}).get(a, {}))
        if local.get("library"):
            (path / "abstractions" / a / "lib.py").write_text(local.pop("library"), encoding="utf8")
        if local:
            (path / "abstractions" / a / "abstraction.json").write_text(
                json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    for key, s in definition["specifications"].items():
        (path / "abstractions" / f"{key}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n",
                                                          encoding="utf8")
    if design is not None:
        (path / "DESIGN.md").write_text(design, encoding="utf8")
    return path


def load_specs(definition):
    """All specifications of a system, expanded into their recorded form, keyed "a/role.vk"."""
    out = {}
    for key, raw in definition["specifications"].items():
        a, stem = key.split("/")
        assert a in definition["abstractions"] or a == definition.get("kpi"), \
            f"{key}: {a} is not an abstraction of the system"
        role, v = stem.split(".v")
        assert role in ("criterion", "ontology"), f"{key}: must be <abstraction>/criterion.v<k> or ontology.v<k>"
        decl = declarations(definition, definition.get("declarations", {}).get(a, {}))
        out[key] = expand(raw, a, role, int(v), decl)
    return out
