"""ztes.model: types, bindings, maps, derived values, function bodies, libraries, errors, validation."""

import pytest


def test_types_are_strict():
    from ztes.model import types
    from fractions import Fraction
    assert types.encode("rational", Fraction(3, 2)) == "3/2"
    assert types.encode({"list": "integer"}, [1, Fraction(4, 2)]) == [1, 2]
    for t, x in (("rational", True), ("integer", Fraction(1, 2)), ({"record": {"a": "integer"}}, {"b": 1})):
        with pytest.raises(TypeError):
            types.encode(t, x)


def test_comprehensions_see_bindings():
    """Regression: names of the body must be visible inside generator expressions and comprehensions."""
    from ztes.model.language import evaluate
    assert evaluate({"k": "3", "result": "all(w % q != 0 for q in primes if q < k)"},
                    {"w": 7, "primes": [2, 3, 5]}) is True


def test_select_one_and_where_with_earlier_bindings(tmp_path):
    from ztes.model import epistemic as context, language
    C = [{"coord": {"kind": "exec", "abstraction": "b"}, "payload": {"n": i, "v": 10 * i}} for i in range(3)]
    s = {"abstraction": "a", "role": "ontology", "version": 1,
         "inputs": {"context": {"k": {"from": "b", "select": "count"},
                                "row": {"from": "b", "select": "one", "where": "x['n'] == k - 2"}}}}
    env = context.project(C, s)
    assert env["row"] == {"n": 1, "v": 10}
    s["inputs"]["context"]["row"]["where"] = "x['n'] >= 0"
    with pytest.raises(ValueError, match="select one found 3"):
        context.project(C, s)


def test_errors_name_the_specification_and_expression(tmp_path):
    from ztes import model as evaluation
    s = {"abstraction": "a", "role": "ontology", "version": 2, "returns": "rational",
         "inputs": {"context": {}}, "body": {"xs": "[1, 2]", "result": "xs[5]"}}
    with pytest.raises(evaluation.SpecError, match=r"a/ontology\.v2, body 'result': IndexError"):
        evaluation.realize([], s)
    s["body"] = {"result": "(1 + 2) / 2"}
    with pytest.raises(evaluation.SpecError, match=r"float, not a rational: use Fraction\(a, b\)"):
        evaluation.realize([], s)


def test_function_body_rules():
    from ztes.model import language as functions
    from ztes.model.language import SAFE
    ok = "def f(k, xs):\n    t = 0\n    for x in xs:\n        t += x\n    return t + k\n"
    assert functions.problems(ok, SAFE) == []
    assert functions.call(ok, {"k": 1, "xs": [2, 3]}, SAFE) == 6
    bad = {
        "while": "def f(k):\n    while True:\n        pass\n",
        "import": "def f(k):\n    import os\n    return k\n",
        "underscore": "def f(k):\n    return k.__class__\n",
        "recursion": "def f(k):\n    return f(k)\n",
        "undeclared": "def f(k):\n    return k + secret\n",
        "two defs": "def f(k):\n    return k\ndef g(k):\n    return k\n",
    }
    for why, src in bad.items():
        assert functions.problems(src, SAFE), why


def test_library_rules_and_subset():
    from ztes.model import language as functions
    from ztes.model.language import SAFE
    lib = ("def sq(x):\n    return x * x\n\n"
           "def norm(a, b):\n    return sq(a) + sq(b)\n\n"
           "def unused(x):\n    return x\n")
    assert functions.library_problems(lib, SAFE) == []
    assert functions.library_names(functions.library_subset(lib, {"norm"})) == ["sq", "norm"]
    assert functions.library(lib, SAFE)["norm"](3, 4) == 25
    later = "def a(x):\n    return b(x)\n\ndef b(x):\n    return x\n"           # calls a def written after it
    mutual = "def a(x):\n    return a(x)\n"
    assert functions.library_problems(later, SAFE) and functions.library_problems(mutual, SAFE)


def test_derived_values_are_computed_once_and_immutable(tmp_path):
    from ztes.model import epistemic as context, language
    from ztes import model as evaluation
    s = {"abstraction": "a", "role": "ontology", "version": 1, "returns": "integer",
         "constants": {"N": 3}, "derived": {"M": "[[i * j for j in range(N)] for i in range(N)]"},
         "inputs": {"context": {}}, "body": {"result": "M[2][2]"}}
    assert evaluation.realize([], s) == 4
    d = context.derived(s, language.SAFE)
    assert d["M"] == ((0, 0, 0), (0, 1, 2), (0, 2, 4))         # tuples: a body cannot alter them
    assert context.derived(s, language.SAFE)["M"] is d["M"]          # the same object: computed once
    s["body"] = {"result": "M[0].append(1)"}
    with pytest.raises(evaluation.SpecError):
        evaluation.realize([], s)


def test_map_binding_is_incremental_read_only_and_prefix_exact():
    from ztes.model import epistemic as context, language
    from ztes.model.view import Index, Record
    events = [{"coord": {"kind": "exec", "abstraction": "e"}, "payload": {"k": i, "v": i * i}} for i in range(5)]
    ix = Index()
    for n, e in enumerate(events):
        ix.add(n, e)
    C = Record(events, 5, ix)
    b = {"from": "e", "select": "map", "type": "json", "key": "x['k']", "value": "x['v']"}
    m = context.bind(C, "m", b, {}, language.SAFE, "t")
    assert dict(m) == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
    m3 = context.bind(C[:3], "m", b, {}, language.SAFE, "t")         # an earlier prefix: a view, not a copy
    assert 2 in m3 and 3 not in m3 and len(m3) == 3
    with pytest.raises(TypeError):
        m[0] = 5                                              # read-only
    dup = dict(b, key="x['k'] % 2")
    with pytest.raises(ValueError, match="occurs twice"):
        context.bind(C, "m", dup, {}, language.SAFE, "t2")


def test_model_does_not_import_the_substrate():
    """The model is independent of Z₀: no module of ztes.model imports ztes.substrate or ztes.system."""
    import ast
    from pathlib import Path
    root = Path(__file__).parent.parent / "ztes" / "model"
    for f in root.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                target = "." * node.level + (node.module or "")
                assert not target.startswith(("..", "ztes.substrate", "ztes.system")), f"{f.name} imports {target}"
            if isinstance(node, ast.Import):
                assert not any(a.name.startswith("ztes") for a in node.names), f"{f.name} imports ztes"


def test_validation_gives_located_reasons():
    from ztes.model import validation
    s = {"abstraction": "a", "role": "criterion", "version": 1, "returns": "boolean", "total": True,
         "constants": {"N": 3},
         "inputs": {"context": {"k": {"from": "a", "select": "count"},
                                "v": {"from": "a", "select": "last", "type": "integer"}},
                    "candidate": {"name": "w", "type": "integer"}},
         "body": {"result": "w == k + N + top"}}
    found = "\n".join(validation.problems(s))
    assert "binding 'v': a criterion binding with select last" in found       # τ would not be total
    assert "body 'result' uses undeclared ['top']" in found
    s["inputs"]["context"]["v"]["default"] = 0
    s["body"] = {"result": "w == k + N + v"}
    assert validation.problems(s) == []


def test_window_reads_only_the_last_k_qualifying_events():
    """A window narrows what is read inside a lineage; the record itself is not touched."""
    from ztes.model import epistemic as context, validation
    C = [{"coord": {"kind": "exec", "abstraction": "b"}, "payload": i} for i in range(6)]
    s = {"abstraction": "a", "role": "ontology", "version": 1, "partial": True, "returns": "integer",
         "criterion": "x", "constants": {"K": 2},
         "inputs": {"context": {"tail": {"from": "b", "select": "all", "window": "K"},
                                "even": {"from": "b", "select": "all", "where": "x % 2 == 0", "window": 2},
                                "wide": {"from": "b", "select": "all", "window": 10}}},
         "body": {"result": "sum(tail)"}}
    env = context.project(C, s)
    assert env["tail"] == [4, 5] and env["even"] == [2, 4] and env["wide"] == [0, 1, 2, 3, 4, 5]
    assert context.project(C[:3], s)["tail"] == [1, 2]                     # a function of the prefix
    assert validation.problems(s) == []
    s["inputs"]["context"]["tail"]["window"] = "Q"
    assert "window 'Q' is not a positive integer" in "\n".join(validation.problems(s))
    s["inputs"]["context"]["tail"] = {"from": "b", "select": "count", "window": 2}
    assert 'a window belongs to select "all"' in "\n".join(validation.problems(s))
