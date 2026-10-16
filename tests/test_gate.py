"""Business outcomes and adversarial variants, using only unittest."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest

from gate.engine import DEFAULT_NOW, business_due, evaluate_batch, timestamp
from gate.policies import phrase_in

ROOT = Path(__file__).resolve().parents[1]


class GateTests(unittest.TestCase):
    def setUp(self):
        source = ROOT / "data" / "option_b_gate"
        self.briefs = json.loads((source / "briefs.json").read_text(encoding="utf-8"))
        self.clients = json.loads((source / "clients.json").read_text(encoding="utf-8"))

    def single(self, number=1, **changes):
        brief = deepcopy(self.briefs[number - 1])
        brief.update(changes)
        return evaluate_batch([brief], self.clients)["results"][0]

    def codes(self, result):
        return {i["code"] for i in result["issues"]}

    def test_all_thirty_expected_decisions(self):
        # Independently reviewed against the Definition of Ready.
        blocked = {2: {"INACTIVE_PRODUCT"}, 3: {"BRAIN_PACKAGING"},
                   6: {"BANNED_CLAIM"}, 10: {"PLATFORMS", "FORMATS"},
                   11: {"DISCOUNT_LIMIT"}, 15: {"TURNAROUND"},
                   16: {"QUOTA"}, 19: {"BANNED_CLAIM"},
                   22: {"CLIENT_PAUSED"}, 25: {"BANNED_CLAIM"},
                   29: {"BRAIN_SUPERLATIVE"}}
        report = evaluate_batch(self.briefs, self.clients)
        self.assertEqual(report["summary"], {"total": 30, "passed": 19, "blocked": 11})
        for i, result in enumerate(report["results"], 1):
            with self.subTest(brief=i):
                self.assertEqual(self.codes(result), blocked.get(i, set()))
                self.assertEqual(result["status"], "BLOCKED" if i in blocked else "PASS")
                if i in blocked:
                    self.assertIn(result["id"], result["clarification_message"])
        self.assertEqual(report["final_usage"], {
            "Northpeak Coffee": {"statics": 18, "videos": 2},
            "Lumen Skin": {"statics": 12, "videos": 1},
            "Ridge Outdoor": {"statics": 12, "videos": 3},
            "Pawfect Treats": {"statics": 12, "videos": 5},
            "Halo Sleep": {"statics": 12, "videos": 4},
            "Brightside Kids": {"statics": 3, "videos": 0}})

    def test_batch_order_and_input_immutability(self):
        original = deepcopy((self.briefs, self.clients))
        forward = evaluate_batch(self.briefs, self.clients)
        self.assertEqual(forward, evaluate_batch(list(reversed(self.briefs)), self.clients))
        self.assertEqual(original, (self.briefs, self.clients))
        self.assertEqual(forward, evaluate_batch(self.briefs, self.clients))

    def test_business_days_and_exact_boundary(self):
        self.assertEqual(business_due(date(2026, 10, 13), 3), date(2026, 10, 16))
        self.assertEqual(business_due(date(2026, 10, 13), 5), date(2026, 10, 20))
        self.assertEqual(business_due(date(2026, 10, 16), 3), date(2026, 10, 21))
        self.assertEqual(self.single(due_date="2026-10-16")["status"], "PASS")
        self.assertIn("TURNAROUND", self.codes(self.single(due_date="2026-10-15")))
        self.assertEqual(self.single(23)["status"], "PASS")

    def test_authority_not_mentioned_name(self):
        self.assertEqual(self.single(4)["status"], "PASS")
        self.assertIn("TURNAROUND", self.codes(self.single(15)))
        comment = {"by": "Client", "at": "2026-10-12T20:00:00Z", "text": "Rush approved by Louise"}
        self.assertIn("TURNAROUND", self.codes(self.single(4, comments=[comment])))

    def test_approval_future_negation_revocation_and_request(self):
        for text in ("Rush not approved", "Could rush be approved?", "Rush approved?", "Rush approval requested"):
            with self.subTest(text=text):
                comment = {"by": "Louise", "at": "2026-10-12T20:00:00Z", "text": text}
                self.assertIn("TURNAROUND", self.codes(self.single(4, comments=[comment])))
        future = {"by": "Louise", "at": "2026-10-14T20:00:00Z", "text": "Rush approved"}
        self.assertIn("TURNAROUND", self.codes(self.single(4, comments=[future])))
        revoked = {"by": "Louise", "at": "2026-10-13T08:00:00Z", "text": "Rush revoked"}
        self.assertIn("TURNAROUND", self.codes(self.single(4, comments=self.briefs[3]["comments"] + [revoked])))

    def test_scoped_overage(self):
        self.assertEqual(self.single(18)["status"], "PASS")
        self.assertIn("QUOTA", self.codes(self.single(18, deliverables={"statics": 0, "videos": 2})))
        extra = deepcopy(self.briefs[17])
        extra.update(id="BR-31", created_at="2026-10-13T08:00:00Z", comments=[])
        report = evaluate_batch([self.briefs[17], extra], self.clients)
        self.assertEqual(report["results"][0]["status"], "PASS")
        self.assertIn("QUOTA", self.codes(report["results"][1]))

    def test_quota_only_reserves_passes_and_exact_limit_passes(self):
        first = deepcopy(self.briefs[0])
        first["deliverables"]["statics"] = 12
        later = deepcopy(first)
        later.update(id="BR-99", created_at="2026-10-13T08:00:00Z")
        later["deliverables"]["statics"] = 1
        results = evaluate_batch([later, first], self.clients)["results"]
        self.assertEqual(results[0]["status"], "PASS")
        self.assertIn("QUOTA", self.codes(results[1]))
        first["products"] = ["hazelnut"]
        results = evaluate_batch([first, later], self.clients)["results"]
        self.assertEqual(results[1]["status"], "PASS")

    def test_discount_limit_not_material_percentage(self):
        self.assertEqual(self.single(12)["status"], "PASS")
        self.assertIn("DISCOUNT_LIMIT", self.codes(self.single(12, copy_direction="Save 30.5% today")))
        self.assertEqual(self.single(12, copy_direction="100% recycled fabric")["status"], "PASS")

    def test_alias_article_brand_and_inactive(self):
        self.assertEqual(self.single(26)["resolved_products"], ["PT-JERKY-CHK"])
        self.assertEqual(self.single(products=["brand"])["status"], "PASS")
        self.assertIn("INACTIVE_PRODUCT", self.codes(self.single(2)))
        self.assertIn("UNKNOWN_PRODUCT", self.codes(self.single(products=["oat"])))

    def test_word_boundaries_multilingual_and_tiktok_statics(self):
        self.assertFalse(phrase_in("cure", "curated"))
        self.assertFalse(phrase_in("treat", "treats for dogs"))
        self.assertEqual(self.single(20)["status"], "PASS")
        self.assertEqual(self.single(9)["status"], "PASS")
        self.assertIn("BANNED_CLAIM", self.codes(self.single(25)))
        self.assertEqual(self.single(27)["status"], "PASS")
        self.assertIn("BANNED_CLAIM", self.codes(self.single(6, copy_direction="BEFORE-AFTER")))

    def test_assets_and_drive_hostname(self):
        self.assertEqual(self.single(8)["status"], "PASS")
        self.assertIn("ASSETS", self.codes(self.single(assets_link="")))
        self.assertIn("ASSETS", self.codes(self.single(assets_link="https://drive.google.com.evil.test/folder")))

    def test_bad_required_data(self):
        for counts in ({"statics": -1, "videos": 0}, {"statics": True, "videos": 0}, {"statics": 0, "videos": 0}, {}):
            self.assertIn("DELIVERABLES", self.codes(self.single(deliverables=counts)))
        self.assertIn("DUE_DATE", self.codes(self.single(due_date="tomorrow")))
        self.assertIn("VIDEO_DURATION", self.codes(self.single(23, formats=["9:16"])))
        self.assertIn("FORMATS", self.codes(self.single(formats=["0:0"])))
        self.assertIn("UNKNOWN_CLIENT", self.codes(self.single(client="Missing")))

    def test_changed_brain_requires_review(self):
        self.clients[0]["brain_rules"].append("Never show snow.")
        self.assertIn("UNREVIEWED_POLICY", self.codes(self.single()))

    def test_duplicate_ids_rejected_and_utc_comparison(self):
        with self.assertRaisesRegex(ValueError, "Duplicate brief"):
            evaluate_batch([self.briefs[0], self.briefs[0]], self.clients)
        with self.assertRaises(ValueError):
            timestamp("2026-10-13T09:00:00")
        self.assertEqual(timestamp("2026-10-13T06:00:00-03:00"), DEFAULT_NOW)

    def test_latest_restricted_approval_does_not_restore_older_grant(self):
        old = {"by": "Bea A.", "at": "2026-10-12T15:00:00Z", "text": "Overage approved: 3 videos"}
        new = {"by": "Bea A.", "at": "2026-10-12T16:00:00Z", "text": "Overage approved: 1 video"}
        result = self.single(18, deliverables={"statics": 0, "videos": 2}, comments=[old, new])
        self.assertIn("QUOTA", self.codes(result))

    def test_negated_asset_instruction_is_not_permission(self):
        result = self.single(assets_link="", notes="Do not use the Studio catalog shots.")
        self.assertIn("ASSETS", self.codes(result))
        self.assertEqual(self.single(assets_link="", notes="Use the Studio catalog shots.")["status"], "PASS")

    def test_brain_policy_does_not_depend_on_duplicate_banned_list(self):
        self.clients[2]["banned_claims"] = []
        self.assertIn("BRAIN_WATERPROOF", self.codes(self.single(14, copy_direction="Waterproof shell for every adventure.")))
        self.clients[3]["banned_claims"] = []
        self.assertIn("BRAIN_VET", self.codes(self.single(17, copy_direction="Vet-approved dental chews.")))

    def test_negated_packaging_instruction_does_not_clear_cup_block(self):
        self.assertIn("BRAIN_PACKAGING", self.codes(self.single(3, copy_direction="Pour into a cup. Do not show the can or bag.")))
        self.assertEqual(self.single(3, copy_direction="Pour into a cup. Show the branded can beside it.")["status"], "PASS")

    def test_malformed_container_fails_with_actionable_error(self):
        for field, value in (("platforms", "Meta"), ("formats", [None]), ("products", None), ("notes", 3)):
            with self.subTest(field=field):
                brief = deepcopy(self.briefs[0])
                brief[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    evaluate_batch([brief], self.clients)

    def test_negative_quota_configuration_is_rejected(self):
        self.clients[0]["used_this_month"]["statics"] = -10
        with self.assertRaisesRegex(ValueError, "used_this_month"):
            self.single()


if __name__ == "__main__":
    unittest.main()
