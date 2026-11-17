"""`python -m ztes new`: the skeleton of a new system.

The skeleton is a valid system that already passes `check` and runs: every ontology
is undefined (⊥), so every abstraction ends in permanent wait. The author replaces
the bodies, the bindings, and the sections of DESIGN.md, and fills in "expect".
"""
import json
from pathlib import Path

DESIGN = """# {title}: design (step 0)

## 1. Problem

What is to be computed or maintained, in plain terms.

## 2. Decomposition into binary relations

    R ⊆ X × Y      for each relation: what X is (read from the record) and what Y is (the payload)

## 3. Lifting: the abstractions

| Abstraction | Relation | Ontology Sω | Criterion Sτ | Horizon |
|---|---|---|---|---|
{rows}

## 4. Design decisions

Why no selector is needed (D1), what each criterion checks independently of its ontology (D2),
how the abstractions interact only through C.

## 5. Plan

No plan: phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

The admitted values, which abstractions end closed and which in permanent wait, the number of
events. The same facts go into "expect" in system.json.

## 7. Files

```
system.json
DESIGN.md
{files}
```
"""

CRITERION = {
    "note": "[τ] what this criterion admits (replace)",
    "inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
    "body": {"result": "False"},
}
ONTOLOGY = {
    "note": "[ω] what this ontology proposes, and when it is ⊥ (replace)",
    "inputs": {"context": ["k"]},
    "returns": "integer",
    "body": {"result": "None"},
}


def new_system(path, abstractions, title=None):
    """Create the skeleton of a new system in the empty directory `path`: system.json with the given
    abstractions and the default plan, a criterion and an ontology to be written for each
    abstraction, and DESIGN.md with a table to fill. Returns the directory.
    """
    root = Path(path)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"{root} exists and is not empty")
    name = root.name
    title = title or name
    (root / "abstractions").mkdir(parents=True, exist_ok=True)
    system = {
        "system": name,
        "title": title,
        "abstractions": abstractions,
        "types": {},
        "constants": {},
        "bindings": {"k": {"from": "$self", "select": "count"}},
        "plan": [{"phase": 1}, {"phase": 2}, {"phase": 3}, {"kpi": True}],
        "expect": {},
    }
    (root / "system.json").write_text(json.dumps(system, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    for a in abstractions:
        d = root / "abstractions" / a
        d.mkdir()
        (d / "criterion.v1.json").write_text(json.dumps(CRITERION, indent=2) + "\n", encoding="utf8")
        (d / "ontology.v1.json").write_text(json.dumps(ONTOLOGY, indent=2) + "\n", encoding="utf8")
    rows = "\n".join(f"| `{a}` | | | | |" for a in abstractions)
    files = "\n".join(f"abstractions/{a}/{{criterion, ontology}}.v1.json" for a in abstractions)
    (root / "DESIGN.md").write_text(DESIGN.format(title=title, rows=rows, files=files), encoding="utf8")
    return root
