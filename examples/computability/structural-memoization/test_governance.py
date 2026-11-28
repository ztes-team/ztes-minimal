"""Check the domain judgments behind the governance and coverage experiments."""

import unittest
from copy import deepcopy

from ztes.model import SpecError, judge
from ztes.substrate import lookups
from ztes.substrate.store import MemoryStore
from ztes.substrate.z0 import Z0

from governance import governance_system, run_governance


class GovernanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.records = run_governance()
        cls.full = cls.records["governance_complete"]
        cls.system = governance_system()

    def first(self, name):
        return next(e for e in self.full if e["coord"].get("kind") == "exec"
                    and e["coord"].get("abstraction") == name)

    def before(self, name):
        return self.full[:self.first(name)["coord"]["n"]]

    def restore(self, prefix):
        store = MemoryStore()
        for event in prefix:
            self.assertTrue(store.put_if_absent(event["coord"]["n"], event))
        return Z0(store, self.system.services(store))

    def judgment(self, prefix, name, payload):
        spec = lookups.load(prefix, lookups.active(prefix, name, "criterion"))
        return judge(prefix, spec, payload)

    def test_fixed_regime_refuses_supplement_even_with_funded_instrument(self):
        z0 = self.restore(self.before("reform"))
        self.assertEqual(z0.execute("guarantee", self.first("guarantee")["payload"])[0], "admitted")
        complete = self.first("case-credit")["payload"]
        self.assertFalse(self.judgment(z0.prefix(), "case-credit", complete))
        self.assertEqual(z0.execute("case-credit")[0], "false")
        self.assertEqual(z0.execute("inspection", self.first("inspection")["payload"])[0], "false")
        self.assertEqual(z0.execute("order", self.first("order")["payload"])[0], "false")
        self.assertTrue(self.judgment(self.before("case-credit"), "case-credit", complete))
        for change in ({"case": "other"}, {"claim": "other"}, {"beneficiary": "other"},
                       {"primary": 59, "guarantee": 31}, {"instrument": "unfunded"}):
            with self.subTest(change=change):
                self.assertFalse(self.judgment(self.before("case-credit"), "case-credit", {**complete, **change}))

    def test_boundary_cross_case_references_and_authority(self):
        changes = {"order": [{"case": "other"}, {"cap": -1}, {"fee_parties": ["x", "x"]}],
                   "fee-notice": [{"case": "other"}, {"amount": 0}, {"actor": "other"}, {"issuer": "other"}],
                   "inspection": [{"case": "other"}, {"loss": 0}, {"issuer": "other"}],
                   "guarantee": [{"case": "other"}, {"claim": "other"}, {"issuer": "other"},
                                 {"beneficiary": "other"}, {"limit": -1}],
                   "mandate": [{"case": "other"}, {"claim": "other"}, {"issuer": "other"}, {"action": "other"}]}
        for name, mutations in changes.items():
            z0 = self.restore(self.before(name))
            original = self.first(name)["payload"]
            for mutation in mutations:
                with self.subTest(name=name, mutation=mutation):
                    self.assertEqual(z0.execute(name, {**original, **mutation})[0], "false")
            self.assertEqual(z0.execute(name, original)[0], "admitted")

    def test_amounts_have_exact_integer_types(self):
        for name, field in [("order", "cap"), ("inspection", "loss"), ("fee-notice", "amount"),
                            ("guarantee", "limit")]:
            z0 = self.restore(self.before(name))
            n = len(z0.prefix())
            for value in (True, 1.5, "2"):
                with self.subTest(name=name, value=value), self.assertRaises(SpecError):
                    z0.execute(name, {**self.first(name)["payload"], field: value})
                self.assertEqual(len(z0.prefix()), n)

    def test_permit_and_fee_evidence_are_checked_by_prior_rule(self):
        prefix = self.before("reform")
        approved = self.first("reform")["payload"]
        self.assertTrue(self.judgment(prefix, "reform", approved))
        self.assertFalse(self.judgment(self.before("mandate"), "reform", approved))
        for change in ({"case": "other"}, {"affected": approved["affected"][:-1]}, {"mandate": "other"}):
            self.assertFalse(self.judgment(prefix, "reform", {**approved, **change}))
        altered = deepcopy(approved)
        altered["specifications"][0]["body"]["result"] = "True"
        self.assertFalse(self.judgment(prefix, "reform", altered))
        post_trigger = self.restore(self.full[:len(prefix) + 1])
        original = self.first("fee-notice")["payload"]
        self.assertEqual(post_trigger.execute("fee-notice", {**original, "ref": "late"})[0], "false")

    def test_closure_reconstructs_only_affected_actors_and_requires_their_actual_refunds(self):
        closure = self.first("closure")["payload"]
        final = self.before("closure")
        partial = self.records["governance_incomplete"]
        self.assertFalse(self.judgment(partial, "closure", closure))
        self.assertTrue(self.judgment(final, "closure", closure))
        self.assertEqual([r["actor"] for r in closure["witnesses"]], ["carrier", "supplier"])
        self.assertIn("warehouse", self.first("order")["payload"]["fee_parties"])
        # With no prior fee, warehouse is in scope but never affected.
        invalid = deepcopy(closure)
        invalid["witnesses"][-1]["refund"] = 0
        self.assertFalse(self.judgment(final, "closure", invalid))
        invalid["witnesses"][-1] = {"actor": "supplier", "status": "non-compensable"}
        with self.assertRaises(SpecError):
            self.judgment(final, "closure", invalid)
        self.assertTrue(all(not errors for errors in self.result["full_replay_errors"].values()))


if __name__ == "__main__":
    unittest.main()
