"""Unit tests for Fondly's Qloo Taste Agent, health constraints, and LLM-only comparison."""
from __future__ import annotations

import unittest
from datetime import date

from backend.api.demo import CONDITIONS, MEDS, SENIORS, _AMLO
from backend.taste.agent import build_taste_plan
from backend.taste.client import QlooClient
from backend.taste.profiles import build_taste_profile, taste_knows_entries

DAY = date(2026, 10, 13)


def _demo_senior(sid: str) -> dict:
    row = next(r for r in SENIORS if r[0] == sid)
    _, name, lang, postal, region, path, aac, likes, _, _ = row
    return {
        "id": sid,
        "name": name,
        "language": lang,
        "home_postal": postal,
        "region": region,
        "path": path,
        "aac_id": aac,
        "conditions": CONDITIONS.get(sid, ["hypertension"]),
        "medicines": [
            {"name": n, "dose_text": dose, "schedule": when, "started": "2024-03-01", "for_bp": bp}
            for n, dose, when, bp in MEDS.get(sid, [_AMLO])
        ],
        "likes": list(likes),
        "usual_checkin_time": "08:00",
        "hidden_suggestions": [],
    }


class TestTasteAgent(unittest.TestCase):
    def setUp(self):
        self.client = QlooClient(api_key="")

    def test_all_thirteen_demo_seniors_produce_valid_guardrailed_plans(self):
        for row in SENIORS:
            sid = row[0]
            senior = _demo_senior(sid)
            with self.subTest(senior_id=sid):
                plan = build_taste_plan(senior, DAY, client=self.client)
                self.assertEqual(plan["senior_id"], sid)
                self.assertTrue(plan["guardrail"]["passed"], plan["guardrail"]["reasons"])
                self.assertEqual(len(plan["trace"]), 4)
                self.assertGreater(len(plan["recommendations"]["places"]), 0)
                self.assertGreater(len(plan["recommendations"]["music"]), 0)
                self.assertGreater(len(plan["recommendations"]["movies"]), 0)
                self.assertGreater(len(plan["filtered_out"]), 0)

    def test_mr_tan_grapefruit_and_high_sodium_filtered_out(self):
        tan = _demo_senior("tan")
        plan = build_taste_plan(tan, DAY, client=self.client)
        filtered_rules = {f["rule_id"] for f in plan["filtered_out"]}
        self.assertIn("med_food.grapefruit_pomelo", filtered_rules)
        self.assertIn("diet.hypertension.low_salt", filtered_rules)
        top_place = plan["recommendations"]["places"][0]
        self.assertEqual(top_place["entity_id"], "urn:entity:place:qloo-tp-porridge")

    def test_encik_rahman_diabetes_hypertension_and_halal_warung_match(self):
        rahman = _demo_senior("rahman")
        plan = build_taste_plan(rahman, DAY, client=self.client)
        filtered_rules = {f["rule_id"] for f in plan["filtered_out"]}
        self.assertIn("diet.diabetes.less_sugar", filtered_rules)
        self.assertIn("diet.hypertension.low_salt", filtered_rules)
        self.assertIn("med_food.grapefruit_pomelo", filtered_rules)
        place_ids = [p["entity_id"] for p in plan["recommendations"]["places"]]
        self.assertIn("urn:entity:place:qloo-taman-jurong-warung", place_ids)
        self.assertEqual(plan["recommendations"]["music"][0]["entity_id"], "urn:entity:artist:qloo-p-ramlee")
        self.assertEqual(plan["recommendations"]["movies"][0]["entity_id"], "urn:entity:movie:qloo-bujang-lapok")

    def test_haze_or_rain_enforces_indoor_only(self):
        kaur = _demo_senior("kaur")
        plan = build_taste_plan(kaur, DAY, indoor_only=True, psi=142, client=self.client)
        self.assertTrue(plan["constraints"]["indoor_only"])
        for p in plan["recommendations"]["places"]:
            self.assertTrue(p["indoor"], f"Outdoor place leaked on hazy day: {p}")
        filtered_rules = {f["rule_id"] for f in plan["filtered_out"]}
        self.assertIn("env.indoor_only", filtered_rules)

    def test_not_for_me_excludes_place(self):
        wong = _demo_senior("wong")
        wong["hidden_suggestions"] = ["urn:entity:place:qloo-yuhua-tea-song"]
        plan = build_taste_plan(wong, DAY, client=self.client)
        kept_ids = [p["entity_id"] for p in plan["recommendations"]["places"]]
        self.assertNotIn("urn:entity:place:qloo-yuhua-tea-song", kept_ids)
        filtered_rules = {f["rule_id"] for f in plan["filtered_out"]}
        self.assertIn("preference.not_for_me", filtered_rules)

    def test_erased_taste_seeds_respected(self):
        wong = _demo_senior("wong")
        before = build_taste_profile(wong)
        self.assertIn("Teresa Teng", before["music_seeds"])
        after = build_taste_profile(wong, erased_keys={"Teresa Teng"})
        self.assertNotIn("Teresa Teng", after["music_seeds"])
        knows = taste_knows_entries(wong, erased_keys={"Teresa Teng"})
        self.assertFalse(any("Teresa Teng" in k["text"] for k in knows))


if __name__ == "__main__":
    unittest.main()
