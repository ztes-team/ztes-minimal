"""Regression tests for the plan that is shared across the two diagnostic abstractions."""

import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from ztes.model import judge, language
from ztes.model.errors import SpecError
from ztes.model.view import Record

import case_model
import planner


class PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(planner.__file__).read_text(encoding="utf-8")
        problems = language.library_problems(source, language.SAFE)
        if problems:
            raise AssertionError(problems)
        cls.embedded = language.namespace(source)

    def test_whole_signature_is_independent_of_amounts(self):
        signature = self.embedded["funding_signature"](90, 60, 40)
        reference = self.embedded["search_graph"](signature)
        graph = reference["graph"]
        self.assertTrue(self.embedded["verify_graph"](signature, graph))
        for primary in (1, 45, 60, 10**22):
            for gap in (1, 20, 30, primary + 1):
                for headroom in (0, 1, primary + gap):
                    owed = primary + gap
                    guarantee = gap + headroom
                    with self.subTest(owed=owed, primary=primary, guarantee=guarantee):
                        local = self.embedded["funding_signature"](owed, primary, guarantee)
                        self.assertEqual(local, signature)
                        self.assertEqual(self.embedded["search_graph"](local), reference)
                        self.assertEqual(self.embedded["bind_graph"](graph, owed, primary, guarantee),
                                         {"primary": primary, "supplemental": gap, "credit": owed})

    def test_wiring_and_symbolic_validity_are_separate_checks(self):
        signature = planner.split_signature()
        fresh = planner.search_graph(signature)
        graph = fresh["graph"]
        malformed = deepcopy(graph)
        malformed[1]["inputs"][1] = "supplemental_draw"  # forward reference
        duplicate = deepcopy(graph)
        duplicate[-1]["inputs"] = ["primary_draw", "primary_draw"]
        for bad in (malformed, duplicate, graph[:-1], graph + [graph[-1]]):
            with self.subTest(graph=bad):
                self.assertFalse(self.embedded["verify_graph"](signature, bad))
                self.assertIsNone(self.embedded["bind_graph"](bad, 65, 45, 30))

        # At the exact cap a supplemental-first graph happens to yield 45 + 20.
        # It fails the general claim when the same role admits additional headroom.
        reverse = next(entry["graph"] for entry in fresh["trace"]
                       if len(entry["graph"]) == 4 and entry["graph"][0]["role"] == "supplemental")
        self.assertEqual(planner.wiring_error(reverse), "")
        self.assertEqual(self.embedded["bind_graph"](reverse, 65, 45, 20),
                         {"primary": 45, "supplemental": 20, "credit": 65})
        self.assertIsNone(self.embedded["bind_graph"](reverse, 65, 45, 30))
        self.assertFalse(self.embedded["verify_graph"](signature, reverse))

    def test_version_or_signature_mismatch_leaves_fresh_search_available(self):
        signature = planner.split_signature()
        versions = planner.construction_versions()
        publication = {"signature": signature, "versions": versions}
        self.assertTrue(self.embedded["compatible_pattern"](publication, signature, versions))
        for component in versions:
            changed = dict(versions, **{component: "another-revision"})
            with self.subTest(component=component):
                self.assertFalse(self.embedded["compatible_pattern"](publication, signature, changed))
        self.assertFalse(self.embedded["compatible_pattern"](publication, [], versions))
        self.assertTrue(self.embedded["search_graph_avoiding"](signature, [], False)["graph"])
        for amounts in ((45, 45, 30), (80, 45, 30), (20, 0, 30)):
            self.assertIsNone(self.embedded["funding_signature"](*amounts))
        for unsupported in (None, []):
            self.assertEqual(self.embedded["search_graph"](unsupported),
                             {"graph": [], "trace": [], "expansions": 0, "tested": 0})

    def test_skipped_graphs_do_not_call_the_proof_checker(self):
        signature = planner.split_signature()
        baseline = planner.search_graph(signature)
        tested = [entry["graph"] for entry in baseline["trace"]]
        self.assertEqual((baseline["expansions"], baseline["tested"]), (7, 4))
        self.assertEqual(tested[-1], baseline["graph"])
        for index in (0, len(tested) - 1):
            with self.subTest(index=index), patch.object(planner, "proof_error", wraps=planner.proof_error) as calls:
                result = planner.search_graph_avoiding(signature, [tested[index]], False)
                actual = [call.args[1] for call in calls.call_args_list]
                self.assertEqual(actual, tested[:index] + tested[index + 1:])
                self.assertEqual(result["tested"], len(actual))
                self.assertEqual(result["graph"], [] if index == len(tested) - 1 else baseline["graph"])
        with patch.object(planner, "extensions", side_effect=AssertionError("unexpected search expansion")):
            self.assertTrue(planner.verify_graph(signature, baseline["graph"]))
            self.assertEqual(planner.bind_graph(baseline["graph"], 65, 45, 30)["credit"], 65)

    def test_versioned_search_order_changes_the_trace(self):
        signature = planner.split_signature()
        legacy = self.embedded["search_graph"](signature)
        revised = self.embedded["search_graph_avoiding"](signature, [], True)
        self.assertEqual(legacy["trace"][0]["graph"][0]["role"], "supplemental")
        self.assertEqual(revised["trace"][0]["graph"][0]["role"], "primary")
        self.assertNotEqual(legacy["trace"], revised["trace"])
        self.assertEqual((revised["expansions"], revised["tested"]), (6, 3))
        self.assertEqual(revised["graph"], legacy["graph"])
        self.assertTrue(self.embedded["verify_graph"](signature, revised["graph"]))

    def test_publication_rejects_malformed_json_before_plan_verification(self):
        criterion = next(tau for tau, _ in case_model.specifications() if tau["abstraction"] == "catalogue")
        publication = {
            "ordinal": 1, "ref": "catalogue/1", "case": "A", "signature": planner.split_signature(),
            "versions": {**planner.construction_versions(), "certification": "standard"},
            "diag_ref": "diag/A", "plan_ref": "plan/A", "payment_ref": "payment/A", "obligations": [],
        }
        for malformed in ([None], [3], [{"op": "allocate"}]):
            with self.subTest(graph=malformed), self.assertRaisesRegex(SpecError, "TypeError"):
                judge(Record.of([]), criterion, {**publication, "graph": malformed})


if __name__ == "__main__":
    unittest.main()
