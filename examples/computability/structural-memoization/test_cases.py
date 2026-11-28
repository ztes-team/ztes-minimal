"""End-to-end checks of the declared horizons and case-local judgments."""

import unittest
from copy import deepcopy

from ztes.substrate import ADMITTED, NOT_YET
from ztes.substrate.replay import verify

from case_model import fixture_inputs
from experiment import admitted, direct_judgment, new_executor, run_case


class DisputeTests(unittest.TestCase):
    def test_generic_summary_can_precede_case_specific_evidence(self):
        for case, higher, missing in (("A", "transport", "inspection"), ("B", "cold_chain", "calibration")):
            with self.subTest(case=case):
                executor = new_executor()
                for name, observation in fixture_inputs(case):
                    if observation.get("kind") == missing:
                        saved = observation
                    else:
                        admitted(executor, name, observation)
                admitted(executor, "base")
                n = len(executor.prefix())
                self.assertEqual(executor.execute(higher), (NOT_YET, None))
                self.assertEqual(len(executor.prefix()), n)
                admitted(executor, "evidence", saved)
                self.assertEqual(executor.execute(higher)[0], ADMITTED)
                self.assertEqual(verify(executor.prefix()), [])

    def test_wrong_sensor_or_missing_review_blocks_corresponding_step(self):
        for mode in ("wrong sensor", "missing review"):
            with self.subTest(mode=mode):
                executor = new_executor()
                for name, observation in fixture_inputs("B", stricter=mode == "missing review"):
                    if observation.get("kind") == "review":
                        continue
                    if mode == "wrong sensor" and observation.get("kind") == "calibration":
                        observation["sensor"] = "other instrument"
                    admitted(executor, name, observation)
                admitted(executor, "base")
                if mode == "missing review":
                    admitted(executor, "cold_chain")
                    admitted(executor, "snapshot")
                blocked = "cold_chain" if mode == "wrong sensor" else "plan"
                self.assertEqual(executor.execute(blocked), (NOT_YET, None))

    def test_real_publication_outside_snapshot_cannot_justify_target_plan(self):
        summary, record, _ = run_case("cold")
        plan_event = next(e for e in record if e["coord"].get("abstraction") == "plan"
                          and e["coord"]["kind"] == "exec" and e["payload"]["case"] == "B")
        cut = record[:plan_event["coord"]["n"]]
        self.assertTrue(any(e["coord"]["kind"] == "exec" and e["coord"].get("abstraction") == "catalogue"
                            for e in cut))
        forged = deepcopy(plan_event["payload"])
        forged.update(origin="reuse", publication=summary["publication"]["ordinal"], trace=[])
        self.assertFalse(direct_judgment(cut, "plan", forged))

    def test_exclusion_refuses_the_exact_otherwise_payable_candidate(self):
        positive, _, _ = run_case("warm")
        negative, record, _ = run_case("exclusion")
        self.assertEqual(positive["target_candidate"], negative["target_candidate"])
        self.assertFalse(direct_judgment(record, "settle", positive["target_candidate"]))
        self.assertTrue(negative["local_checks"]["attempt_appended_nothing"])


if __name__ == "__main__":
    unittest.main()
