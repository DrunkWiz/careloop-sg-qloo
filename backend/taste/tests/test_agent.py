"""Unit tests for CareLoop SG's Qloo Taste Agent, health constraints, and LLM-only comparison."""
from __future__ import annotations

import unittest
from datetime import date

from backend.api.demo import CONDITIONS, MEDS, SENIORS, _AMLO
from backend.eval.taste_eval import run_taste_benchmark
from backend.taste.agent import (
    build_group_taste_plan,
    build_kopi_kakis,
    build_memory_lane,
    build_respite_plan,
    build_taste_plan,
    create_memory_capsule,
)
from backend.taste.client import QlooClient
from backend.taste.profiles import build_taste_profile, extract_taste_seeds_from_text, taste_knows_entries

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

    def test_cross_domain_bridge_visit_kit_and_low_day_nudge(self):
        tan = _demo_senior("tan")
        plan = build_taste_plan(tan, DAY, client=self.client)
        # Feature 5: Cross-domain bridge metadata on every recommendation
        for cat in ("places", "music", "movies"):
            for item in plan["recommendations"][cat]:
                self.assertIn("bridge", item)
                self.assertIn("→", item["bridge"]["path_label"])
                self.assertTrue(item["bridge"]["seed"])
        # Feature 4: Family Visit Kit with WhatsApp text
        kit = plan["visit_kit"]
        self.assertTrue(kit["treat"])
        self.assertTrue(kit["music"])
        self.assertTrue(kit["film"])
        self.assertIn("Family Visit Kit", kit["whatsapp_text"])
        # Feature 3: Rung-2 Low Day Cultural Nudge
        nudge = plan["low_day_nudge"]
        self.assertEqual(nudge["rule_id"], "2.low_day")
        self.assertTrue(nudge["place_pick"])
        self.assertTrue(nudge["nudge_text"])

    def test_extract_taste_seeds_from_checkin_text(self):
        # Feature 1: Multilingual check-in taste extraction
        found = extract_taste_seeds_from_text(
            "Today I listened to Teresa Teng (邓丽君) and had fish soup at the kopitiam",
            client=self.client,
        )
        canonical = [f["canonical"] for f in found]
        self.assertIn("Teresa Teng", canonical)
        self.assertIn("Teochew fish porridge", canonical)
        self.assertIn("kopi", canonical)

    def test_multi_senior_group_taste_intersection(self):
        # Feature 2: Cohort intersection + strictest union of medical/medicine guardrails
        cohort = [_demo_senior("tan"), _demo_senior("rahman"), _demo_senior("wong")]
        group = build_group_taste_plan(
            "aac-ang-mo-kio",
            "AWWA Active Ageing Centre (Ang Mo Kio)",
            cohort,
            psi=52,
            rain_mm=0.0,
            client=self.client,
        )
        self.assertEqual(group["engine"], "qloo_taste_ai")
        self.assertEqual(len(group["seniors"]), 3)
        rules = {c["rule"]: c["triggered_by"] for c in group["cohort_constraints"]}
        self.assertIn("diet.hypertension.low_salt", rules)
        self.assertIn("diet.diabetes.less_sugar", rules)
        self.assertIn("Encik Rahman", rules["diet.diabetes.less_sugar"])
        self.assertIn("med_food.grapefruit_pomelo", rules)
        self.assertGreater(len(group["group_recommendations"]["refreshment_or_outing"]), 0)
        self.assertGreater(len(group["group_recommendations"]["music_playlist"]), 0)
        self.assertGreater(len(group["group_recommendations"]["matinee_film"]), 0)
        self.assertGreater(len(group["filtered_out"]), 0)
        self.assertIn("catering_matrix", group)
        self.assertEqual(group["catering_matrix"]["total_seniors"], 3)
        self.assertGreaterEqual(group["catering_matrix"]["counts"]["low_salt"], 1)
        self.assertIn("Caterer Dietary Sheet", group["catering_matrix"]["caterer_sheet_text"])

    def test_expanded_guardrails_gout_ckd_warfarin_mobility_and_kitchen_card(self):
        tan = _demo_senior("tan")
        tan["conditions"] = ["hypertension", "gout", "chronic kidney disease", "mobility_aid", "no_beef"]
        tan["medicines"].append({
            "name": "warfarin",
            "dose_text": "3mg at night",
            "schedule": "evening",
            "started": "2025-01-10",
            "for_bp": False,
        })
        plan = build_taste_plan(tan, DAY, client=self.client)
        self.assertTrue(plan["guardrail"]["passed"], plan["guardrail"]["reasons"])
        filtered_rules = {f["rule_id"] for f in plan["filtered_out"]}
        active_rules = {r["rule_id"] for r in plan["constraints"]["active_rules"]}
        self.assertIn("diet.gout.low_purine", filtered_rules)
        self.assertIn("diet.ckd.renal_light", filtered_rules)
        self.assertIn("med_food.warfarin_consistent_greens", filtered_rules)
        self.assertIn("mobility.step_free_seated", active_rules)
        self.assertIn("diet.preference.no_beef", active_rules)
        # Kitchen card and doorstep icebreaker are populated and guardrailed
        kc = plan["kitchen_card"]
        self.assertIn("siew dai", kc["drink_order_phrase"])
        self.assertTrue(len(kc["avoid_items"]) >= 3)
        self.assertIn("Hawker & Kitchen Card", kc["copy_text"])
        ice = plan["doorstep_icebreaker"]
        self.assertIn(" Mr Tan", f" {ice['opener']}")
        self.assertTrue(ice["music_icebreaker"])

    def test_four_language_localized_explanations(self):
        rahman = _demo_senior("rahman")
        for lang in ("en", "zh", "ms", "ta"):
            with self.subTest(lang=lang):
                s = {**rahman, "language": lang}
                plan = build_taste_plan(s, DAY, client=self.client)
                self.assertTrue(plan["guardrail"]["passed"], plan["guardrail"]["reasons"])
                self.assertGreater(len(plan["constraints"]["active_rules"]), 0)

    def test_twenty_five_synthetic_persona_simulations(self):
        """Simulate all 25 synthetic user scenarios documented in docs/user-research.md."""
        base = _demo_senior("tan")
        scenarios = [
            {"id": "sim-01", "name": "Mdm Liang", "lang": "zh", "conds": ["hypertension", "type 2 diabetes"], "meds": ["amlodipine", "metformin"], "psi": 48, "rain": 0.0, "likes": ["Cantonese opera", "Frances Yip"]},
            {"id": "sim-02", "name": "Mr Tan", "lang": "en", "conds": ["hypertension"], "meds": ["atorvastatin"], "psi": 50, "rain": 0.0, "likes": ["Teresa Teng", "kopitiam"]},
            {"id": "sim-03", "name": "Cik Siti Rahmah", "lang": "ms", "conds": ["hypertension", "type 2 diabetes", "halal"], "meds": ["losartan"], "psi": 55, "rain": 0.0, "likes": ["P. Ramlee", "Saloma"]},
            {"id": "sim-04", "name": "Mr Govindasamy", "lang": "ta", "conds": ["hypertension", "vegetarian", "no_beef"], "meds": ["amlodipine"], "psi": 50, "rain": 0.0, "likes": ["Carnatic classical", "thosai"]},
            {"id": "sim-05", "name": "Uncle Lim Ah Huat", "lang": "zh", "conds": ["hypertension", "gout"], "meds": ["allopurinol", "losartan"], "psi": 60, "rain": 0.0, "likes": ["Hokkien opera", "morning walks"]},
            {"id": "sim-06", "name": "Mdm Wong Mei Ling", "lang": "zh", "conds": ["hypertension"], "meds": ["warfarin"], "psi": 45, "rain": 0.0, "likes": ["Cantonese opera", "steamed fish"]},
            {"id": "sim-07", "name": "Uncle Salleh", "lang": "ms", "conds": ["chronic kidney disease", "hypertension", "halal"], "meds": ["losartan"], "psi": 52, "rain": 0.0, "likes": ["P. Ramlee", "keroncong"]},
            {"id": "sim-08", "name": "Mdm Koh Swee Neo", "lang": "en", "conds": ["hypertension", "mobility_aid"], "meds": ["amlodipine"], "psi": 49, "rain": 0.0, "likes": ["Teresa Teng", "gardening"]},
            {"id": "sim-09", "name": "Mr Raju", "lang": "en", "conds": ["hypertension", "no_beef"], "meds": ["amlodipine"], "psi": 54, "rain": 0.0, "likes": ["chess", "kopi o kosong"]},
            {"id": "sim-10", "name": "Grace Visit Kit", "lang": "en", "conds": ["hypertension", "type 2 diabetes"], "meds": ["amlodipine", "metformin"], "psi": 44, "rain": 0.0, "likes": ["Frances Yip"]},
            {"id": "sim-11", "name": "Ben Low Day Nudge", "lang": "zh", "conds": ["hypertension"], "meds": ["amlodipine"], "psi": 62, "rain": 0.0, "likes": ["Cantonese opera"]},
            {"id": "sim-12", "name": "Marcus Hawker Order", "lang": "en", "conds": ["hypertension", "high cholesterol"], "meds": ["atorvastatin"], "psi": 48, "rain": 0.0, "likes": ["Teochew porridge"]},
            {"id": "sim-13", "name": "Nurul Halal Mobility", "lang": "ms", "conds": ["halal", "mobility_aid", "type 2 diabetes"], "meds": ["metformin"], "psi": 51, "rain": 0.0, "likes": ["Saloma"]},
            {"id": "sim-14", "name": "Siti Helper Kitchen", "lang": "en", "conds": ["gout", "chronic kidney disease"], "meds": ["allopurinol", "warfarin"], "psi": 50, "rain": 0.0, "likes": ["steamed fish"]},
            {"id": "sim-15", "name": "Priya Handover Call", "lang": "ta", "conds": ["vegetarian", "hypertension"], "meds": ["losartan"], "psi": 47, "rain": 0.0, "likes": ["Carnatic classical"]},
            {"id": "sim-16", "name": "David Downpour Sim", "lang": "en", "conds": ["hypertension"], "meds": ["amlodipine"], "psi": 50, "rain": 14.5, "likes": ["tai chi", "Teresa Teng"]},
            {"id": "sim-17", "name": "Mei Haze Sim", "lang": "zh", "conds": ["hypertension"], "meds": ["amlodipine"], "psi": 138, "rain": 0.0, "likes": ["morning walks", "Frances Yip"]},
            {"id": "sim-18", "name": "Uncle Rahim Doorstep", "lang": "ms", "conds": ["halal", "hypertension"], "meds": ["amlodipine"], "psi": 55, "rain": 0.0, "likes": ["P. Ramlee"]},
            {"id": "sim-19", "name": "Sister Catherine Renal", "lang": "en", "conds": ["chronic kidney disease", "type 2 diabetes"], "meds": ["metformin", "losartan"], "psi": 50, "rain": 0.0, "likes": ["Teresa Teng"]},
            {"id": "sim-20", "name": "Kelvin Gout Audit", "lang": "en", "conds": ["gout", "high cholesterol"], "meds": ["allopurinol", "simvastatin"], "psi": 50, "rain": 0.0, "likes": ["kopitiam"]},
            {"id": "sim-21", "name": "Mdm Farah Malay Audit", "lang": "ms", "conds": ["halal", "hypertension", "mobility_aid"], "meds": ["amlodipine"], "psi": 49, "rain": 0.0, "likes": ["Saloma"]},
            {"id": "sim-22", "name": "Dr Lim GP Brief", "lang": "en", "conds": ["hypertension", "type 2 diabetes", "gout"], "meds": ["amlodipine", "metformin", "allopurinol"], "psi": 50, "rain": 0.0, "likes": ["Teresa Teng"]},
            {"id": "sim-23", "name": "Pharmacist Warfarin", "lang": "en", "conds": ["hypertension"], "meds": ["warfarin", "atorvastatin"], "psi": 50, "rain": 0.0, "likes": ["Frances Yip"]},
            {"id": "sim-24", "name": "Judge Sunny Mode", "lang": "en", "conds": ["hypertension"], "meds": ["amlodipine"], "psi": 45, "rain": 0.0, "likes": ["tai chi"]},
            {"id": "sim-25", "name": "AIC Evaluator Multi", "lang": "ta", "conds": ["vegetarian", "mobility_aid", "type 2 diabetes"], "meds": ["metformin"], "psi": 125, "rain": 8.0, "likes": ["Carnatic classical"]},
        ]
        self.assertEqual(len(scenarios), 25)
        for sc in scenarios:
            with self.subTest(persona=sc["id"], name=sc["name"]):
                senior = {
                    **base,
                    "id": sc["id"],
                    "name": sc["name"],
                    "language": sc["lang"],
                    "conditions": sc["conds"],
                    "likes": sc["likes"],
                    "medicines": [
                        {"name": m, "dose_text": "1 tab daily", "schedule": "morning", "started": "2025-01-01", "for_bp": True}
                        for m in sc["meds"]
                    ],
                }
                plan = build_taste_plan(
                    senior,
                    DAY,
                    psi=sc["psi"],
                    rain_mm=sc["rain"],
                    client=self.client,
                )
                self.assertTrue(plan["guardrail"]["passed"], plan["guardrail"]["reasons"])
                self.assertGreater(len(plan["recommendations"]["places"]), 0)
                self.assertIn("kitchen_card", plan)
                self.assertIn("doorstep_icebreaker", plan)
                self.assertIn("visit_kit", plan)
                self.assertIn("low_day_nudge", plan)
                if sc["psi"] > 100 or sc["rain"] >= 5.0:
                    self.assertTrue(plan["constraints"]["indoor_only"])
                    for p in plan["recommendations"]["places"]:
                        self.assertTrue(p["indoor"])

    def test_judge_scenario_2_statin_gout_haze_rule_codes_and_telemetry(self):
        """Judge Scenario 2: Toggle Atorvastatin + Gout + PSI 135 Haze -> intercepts med.statin_grapefruit, cond.gout, env.indoor_only."""
        tan = _demo_senior("tan")
        tan["conditions"] = ["hypertension", "atorvastatin", "gout"]
        plan = build_taste_plan(tan, DAY, psi=135, indoor_only=True, client=self.client)
        self.assertIn("telemetry", plan)
        self.assertEqual(plan["telemetry"]["guardrail_pass_rate"], 100.0)
        self.assertGreaterEqual(plan["telemetry"]["resolved_count"], 1)
        rule_codes = {f.get("rule_code") for f in plan["filtered_out"]}
        self.assertIn("med.statin_grapefruit", rule_codes)
        self.assertIn("cond.gout", rule_codes)
        self.assertIn("env.indoor_only", rule_codes)
        step3_detail = " ".join(plan["trace"][2]["details"])
        self.assertIn("med.statin_grapefruit", step3_detail)
        self.assertIn("cond.gout", step3_detail)
        self.assertIn("env.indoor_only", step3_detail)

    def test_kopi_kakis_buddy_matching_engine(self):
        """Feature 2: Pairwise Qloo cultural affinity, union constraints, safe meeting spot, and 2-sentence befriender script."""
        cohort = [_demo_senior("tan"), _demo_senior("wong"), _demo_senior("chua"), _demo_senior("rahman"), _demo_senior("osman")]
        res = build_kopi_kakis("aac-100", "Ang Mo Kio Active Ageing Centre", cohort, DAY, focus_senior_id="tan", client=self.client)
        self.assertEqual(res["aac_id"], "aac-100")
        self.assertTrue(res["guardrail"]["passed"], res["guardrail"]["reasons"])
        self.assertGreaterEqual(len(res["matches"]), 3)
        top = res["matches"][0]
        self.assertEqual(top["senior_a"]["id"], "tan")
        self.assertGreaterEqual(top["affinity_pct"], 55)
        self.assertTrue(top["shared_hooks"])
        self.assertTrue(top["safe_meeting_spot"]["name"])
        self.assertIn("befriender_script", top)
        self.assertTrue(top["befriender_script"]["en"])
        self.assertTrue(top["befriender_script"]["zh"])

    def test_memory_lane_reminiscence_prompts_and_capsule_creation(self):
        """Feature 3: Daily Qloo nostalgia reminiscence prompts in 4 languages and Memory Capsule creation."""
        tan = _demo_senior("tan")
        for lang in ("en", "zh", "ms", "ta"):
            lane = build_memory_lane({**tan, "language": lang}, DAY, client=self.client)
            self.assertTrue(lane["guardrail"]["passed"], lane["guardrail"]["reasons"])
            self.assertTrue(lane["daily_prompt"]["prompt"])
            self.assertEqual(len(lane["daily_prompt"]["starter_chips"]), 3)
            self.assertGreaterEqual(len(lane["capsules"]), 2)
        cap = create_memory_capsule(
            tan,
            story_text="In 1974 I took my wife to Capitol Theatre to watch Shaw Brothers films and drank kopi at Tiong Bahru.",
            qloo_seed="Teresa Teng",
            recorded_by="Wei Ling (Daughter)",
            language="en",
            day=DAY,
        )
        self.assertTrue(cap["guardrail"]["passed"], cap["guardrail"]["reasons"])
        self.assertIn("Teresa Teng", cap["qloo_seed"])
        self.assertIn("Capitol Theatre", cap["story_text"])

    def test_caregiver_respite_and_burnout_shield(self):
        """Feature 4: Guilt-free 3-hour respite plan matched to Qloo AAC programme + rota cover + WhatsApp text."""
        tan = _demo_senior("tan")
        contacts = [
            {"id": "tan-weiling", "name": "Wei Ling", "role": "family", "primary": True},
            {"id": "tan-kelvin", "name": "Kelvin", "role": "family", "primary": False},
        ]
        respite = build_respite_plan(tan, DAY, contacts=contacts, streak_days=6, has_recent_vent=True, client=self.client)
        self.assertTrue(respite["guardrail"]["passed"], respite["guardrail"]["reasons"])
        self.assertEqual(respite["window_hours"], 3)
        self.assertEqual(respite["primary_caregiver"]["name"], "Wei Ling")
        self.assertEqual(respite["backup_contact"]["name"], "Kelvin")
        self.assertTrue(respite["matched_programme"]["title"])
        self.assertIn("CareLoop 3-Hour Respite Handover", respite["whatsapp_text"])

    def test_quantitative_qloo_ablation_benchmark(self):
        """Feature 5: 3-architecture ablation across 13 demo seniors + 25 synthetic personas (38 total)."""
        bench = run_taste_benchmark()
        self.assertEqual(bench["total_personas"], 38)
        self.assertEqual(bench["cohorts"]["demo_seniors"], 13)
        self.assertEqual(bench["cohorts"]["synthetic_personas"], 25)
        self.assertEqual(len(bench["architectures"]), 3)
        qloo_arch = next(a for a in bench["architectures"] if a["id"] == "careloop_qloo")
        gen_arch = next(a for a in bench["architectures"] if a["id"] == "generic_llm")
        rf_arch = next(a for a in bench["architectures"] if a["id"] == "rule_filtered_llm")
        self.assertEqual(qloo_arch["clinical_violation_rate_pct"], 0.0)
        self.assertGreater(gen_arch["clinical_violation_rate_pct"], 50.0)
        self.assertGreater(rf_arch["clinical_violation_rate_pct"], 10.0)
        self.assertGreater(qloo_arch["cultural_specificity_score"], gen_arch["cultural_specificity_score"] + 40.0)
        self.assertEqual(qloo_arch["guardrail_pass_rate_pct"], 100.0)
        self.assertEqual(len(bench["multilingual_breakdown"]), 4)


if __name__ == "__main__":
    unittest.main()
