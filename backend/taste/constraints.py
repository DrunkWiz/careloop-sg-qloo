"""Deterministic health, medicine-leaflet, weather and preference constraints for Fondly's taste agent.

Safety boundary (CLAUDE.md):
- The taste agent works ONLY at the suggestion level (places, food, music, films, AAC programmes).
- It never touches the escalation ladder (rungs 0-4 and R) or who gets contacted.
- All health/dietary/medicine-food rules live in a single reviewable table below, marked PLACEHOLDER
  until a clinician or pharmacist signs them off.
- No rule ever advises changing, skipping or stopping a medicine, or makes a diagnosis.
"""
from __future__ import annotations

from backend.reports.medicines import identify

# PLACEHOLDER: reviewable condition -> dietary filter rules (clinician / dietitian sign-off required before real use).
CONDITION_RULES: dict[str, dict] = {
    "hypertension": {
        "rule_id": "diet.hypertension.low_salt",
        "exclude_tags": ["high_sodium_preserved", "heavy_gravies"],
        "prefer_tags": ["low_sodium_friendly", "steamed_fish", "clear_soup"],
        "badge_en": "Lower-salt fit (hypertension)",
        "badge_zh": "少盐适宜（高血压）",
        "note_en": "Lower-salt option preferred (hypertension record, PLACEHOLDER rule): favours steamed or clear-soup dishes and filters out salted preserved dishes and heavy gravies.",
        "note_zh": "优先清淡少盐选项（高血压记录，占位规则）：倾向清蒸或清汤餐点，已过滤咸鱼腊味及浓卤汁。",
    },
    "type 2 diabetes": {
        "rule_id": "diet.diabetes.less_sugar",
        "exclude_tags": ["high_sugar_syrup", "sweetened_condensed_milk"],
        "prefer_tags": ["less_sugar_friendly", "kopi_o_kosong_option", "unsweetened_tea"],
        "badge_en": "Unsweetened / less-sugar fit (diabetes)",
        "badge_zh": "无糖/少糖适宜（糖尿病）",
        "note_en": "Unsweetened or less-sugar option preferred (type 2 diabetes record, PLACEHOLDER rule): favours kopi-O kosong or plain tea and filters out heavy syrup drinks and sweet desserts.",
        "note_zh": "优先无糖或少糖选项（二型糖尿病记录，占位规则）：倾向无糖咖啡乌或清茶，已过滤浓糖浆饮品与甜品。",
    },
    "high cholesterol": {
        "rule_id": "diet.cholesterol.light_cooking",
        "exclude_tags": ["deep_fried_lard"],
        "prefer_tags": ["steamed_fish", "grilled_fish", "vegetarian_friendly"],
        "badge_en": "Steamed / grilled fit (cholesterol)",
        "badge_zh": "清蒸/少油适宜（胆固醇）",
        "note_en": "Lightly cooked dishes preferred (high cholesterol record, PLACEHOLDER rule): favours steamed, grilled or fermented flatbread options.",
        "note_zh": "优先少油清淡烹调（高胆固醇记录，占位规则）：倾向清蒸、烤或发酵面食。",
    },
}

# PLACEHOLDER: standard patient-leaflet food interaction rules (pharmacist sign-off required before real use).
# Never tells a senior to change, skip or stop a medicine; only filters food/drink suggestions.
MEDICINE_FOOD_RULES: dict[str, dict] = {
    "cyp3a4_grapefruit": {
        "rule_id": "med_food.grapefruit_pomelo",
        "generics": {"amlodipine", "nifedipine", "simvastatin", "atorvastatin"},
        "raw_names": {"zanidip", "lercanidipine"},
        "exclude_tags": ["contains_grapefruit_pomelo"],
        "badge_en": "No grapefruit/pomelo (medicine leaflet)",
        "badge_zh": "避开西柚/柚子（药物说明书）",
        "note_en": "Filtered out grapefruit and pomelo items (standard patient-leaflet food note for {med}, PLACEHOLDER; ask your pharmacist if unsure).",
        "note_zh": "已过滤含西柚与柚子的甜品饮品（{med} 药物说明书常见饮食提示，占位规则；如有疑问请咨询药剂师）。",
    },
    "raas_potassium": {
        "rule_id": "med_food.potassium_note",
        "generics": {"losartan", "valsartan", "telmisartan", "lisinopril", "enalapril", "perindopril"},
        "raw_names": set(),
        "exclude_tags": ["potassium_salt_substitute"],
        "badge_en": "Natural herbs, no salt substitutes",
        "badge_zh": "天然香料，不用高钾代盐",
        "note_en": "Uses natural herbs and spices rather than potassium salt substitutes (standard leaflet note for {med}, PLACEHOLDER).",
        "note_zh": "使用天然香料调味，避免高钾代盐（{med} 药物说明书提示，占位规则）。",
    },
}


def active_constraints(
    senior: dict,
    *,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
) -> dict:
    """Inspect a senior's conditions, medicines, weather and hidden list to build the active constraint set."""
    zh = senior.get("language") == "zh"
    conditions = [str(c).lower().strip() for c in (senior.get("conditions") or [])]
    medicines = senior.get("medicines") or []

    # Check if diabetes is implied by metformin even if not explicitly in conditions
    for m in medicines:
        if identify(m.get("name", "")) == "metformin" and "type 2 diabetes" not in conditions:
            conditions.append("type 2 diabetes")

    excluded_tags: dict[str, dict] = {}
    preferred_tags: set[str] = set()
    active_rules: list[dict] = []
    badges: list[str] = []

    for cond in conditions:
        rule = CONDITION_RULES.get(cond)
        if not rule:
            continue
        preferred_tags.update(rule["prefer_tags"])
        badge = rule["badge_zh"] if zh else rule["badge_en"]
        if badge not in badges:
            badges.append(badge)
        active_rules.append({
            "rule_id": rule["rule_id"],
            "kind": "condition",
            "trigger": cond,
            "badge": badge,
            "explanation": rule["note_zh"] if zh else rule["note_en"],
        })
        for tag in rule["exclude_tags"]:
            excluded_tags[tag] = {
                "rule_id": rule["rule_id"],
                "reason_en": f"Filtered out by {rule['rule_id']} ({cond}): avoids {tag.replace('_', ' ')}.",
                "reason_zh": f"已由规则 {rule['rule_id']}（{cond}）过滤：避开{tag}。",
            }

    for m in medicines:
        raw_name = str(m.get("name", "")).strip()
        generic = identify(raw_name)
        lower_raw = raw_name.lower()
        for mrule in MEDICINE_FOOD_RULES.values():
            matched = (generic in mrule["generics"]) or any(r in lower_raw for r in mrule["raw_names"])
            if not matched:
                continue
            label = generic or raw_name
            badge = mrule["badge_zh"] if zh else mrule["badge_en"]
            if badge not in badges:
                badges.append(badge)
            active_rules.append({
                "rule_id": mrule["rule_id"],
                "kind": "medicine_leaflet",
                "trigger": raw_name,
                "badge": badge,
                "explanation": (mrule["note_zh"] if zh else mrule["note_en"]).format(med=label),
            })
            for tag in mrule["exclude_tags"]:
                excluded_tags[tag] = {
                    "rule_id": mrule["rule_id"],
                    "reason_en": f"Filtered out by {mrule['rule_id']} ({raw_name} leaflet note): contains grapefruit/pomelo or conflicting ingredient.",
                    "reason_zh": f"已由规则 {mrule['rule_id']}（{raw_name} 说明书提示）过滤：含西柚/柚子或冲突成分。",
                }

    if indoor_only:
        why_env = f"rain ({rain_mm} mm)" if (rain_mm or 0) >= 5.0 else f"haze (PSI {psi})" if (psi or 0) > 100 else "weather/air quality"
        why_env_zh = f"降雨（{rain_mm} 毫米）" if (rain_mm or 0) >= 5.0 else f"烟霾（PSI {psi}）" if (psi or 0) > 100 else "天气或空气质量"
        badge = "仅限室内（天气/烟霾）" if zh else f"Indoor-only today ({why_env})"
        badges.insert(0, badge)
        active_rules.insert(0, {
            "rule_id": "env.indoor_only",
            "kind": "weather_air",
            "trigger": why_env,
            "badge": badge,
            "explanation": (
                f"因今日{why_env_zh}，仅推荐有盖或室内活动地点。"
                if zh
                else f"Because of {why_env} today, outdoor walks and unsheltered venues are filtered out."
            ),
        })

    return {
        "indoor_only": indoor_only,
        "rain_mm": rain_mm,
        "psi": psi,
        "excluded_tags": excluded_tags,
        "preferred_tags": sorted(preferred_tags),
        "active_rules": active_rules,
        "badges": badges,
        "hidden_ids": list(senior.get("hidden_suggestions") or []),
    }


def filter_qloo_candidates(
    candidates: list[dict],
    constraints: dict,
    *,
    lang: str = "en",
) -> tuple[list[dict], list[dict]]:
    """Apply active health, medicine-leaflet, weather and 'not_for_me' constraints to Qloo candidates.

    Returns (kept_candidates, filtered_out_log).
    """
    zh = lang == "zh"
    excluded_tags: dict[str, dict] = constraints.get("excluded_tags", {})
    preferred_tags = set(constraints.get("preferred_tags", []))
    indoor_only = bool(constraints.get("indoor_only"))
    hidden_ids = set(constraints.get("hidden_ids") or [])

    kept: list[dict] = []
    filtered_out: list[dict] = []

    for item in candidates:
        eid = item.get("entity_id", "")
        name = item.get("name_zh") if zh and item.get("name_zh") else item.get("name", "")
        if eid in hidden_ids:
            filtered_out.append({
                "entity_id": eid,
                "name": name,
                "rule_id": "preference.not_for_me",
                "reason": "长者此前标记为“不适合我”，不再重复推荐。" if zh else "Senior previously tapped 'Not for me'; remembered and excluded.",
            })
            continue

        if indoor_only and not item.get("indoor", True):
            filtered_out.append({
                "entity_id": eid,
                "name": name,
                "rule_id": "env.indoor_only",
                "reason": "今日降雨或烟霾超标，已过滤户外无盖地点。" if zh else "Filtered out by env.indoor_only: outdoor venue skipped due to today's rain or haze.",
            })
            continue

        item_tags = item.get("dietary_tags") or []
        conflict = next((t for t in item_tags if t in excluded_tags), None)
        if conflict is not None:
            rule_info = excluded_tags[conflict]
            filtered_out.append({
                "entity_id": eid,
                "name": name,
                "rule_id": rule_info["rule_id"],
                "reason": rule_info["reason_zh"] if zh else rule_info["reason_en"],
            })
            continue

        matched_prefs = [t for t in item_tags if t in preferred_tags]
        fit_badges: list[str] = []
        if "low_sodium_friendly" in matched_prefs:
            fit_badges.append("少盐适宜" if zh else "Lower-salt fit")
        if "less_sugar_friendly" in matched_prefs or "kopi_o_kosong_option" in matched_prefs or "unsweetened_tea" in matched_prefs:
            fit_badges.append("少糖/无糖选项" if zh else "Less-sugar option")
        if item.get("indoor", True):
            fit_badges.append("室内有盖" if zh else "Indoor / sheltered")

        kept.append({
            **item,
            "display_name": name,
            "why": item.get("why_zh") if zh and item.get("why_zh") else item.get("why_en", ""),
            "fit_badges": fit_badges,
        })

    return kept, filtered_out
