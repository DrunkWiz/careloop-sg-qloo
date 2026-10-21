"""Deterministic health, medicine-leaflet, weather and preference constraints for CareLoop's taste agent.

Safety boundary (CLAUDE.md):
- The taste agent works ONLY at the suggestion level (places, food, music, films, AAC programmes).
- It never touches the escalation ladder (rungs 0-4 and R) or who gets contacted.
- All health/dietary/medicine-food rules live in a single reviewable table below, marked PLACEHOLDER
  until a clinician or pharmacist signs them off.
- No rule ever advises changing, skipping or stopping a medicine, or makes a diagnosis.
"""
from __future__ import annotations

from backend.reports.medicines import identify

# PLACEHOLDER: reviewable condition -> dietary/mobility filter rules (clinician / dietitian sign-off required before real use).
CONDITION_RULES: dict[str, dict] = {
    "hypertension": {
        "rule_id": "diet.hypertension.low_salt",
        "rule_code": "cond.hypertension",
        "exclude_tags": ["high_sodium_preserved", "heavy_gravies"],
        "prefer_tags": ["low_sodium_friendly", "steamed_fish", "clear_soup"],
        "badge_en": "Lower-salt fit (hypertension)",
        "badge_zh": "少盐适宜（高血压）",
        "badge_ms": "Kurang garam (darah tinggi)",
        "badge_ta": "குறைந்த உப்பு (உயர் இரத்த அழுத்தம்)",
        "note_en": "Lower-salt option preferred (hypertension record, PLACEHOLDER rule): favours steamed or clear-soup dishes and filters out salted preserved dishes and heavy gravies.",
        "note_zh": "优先清淡少盐选项（高血压记录，占位规则）：倾向清蒸或清汤餐点，已过滤咸鱼腊味及浓卤汁。",
        "note_ms": "Pilihan kurang garam diutamakan (rekod darah tinggi, peraturan PLACEHOLDER): mengutamakan ikan kukus atau sup jernih dan menapis makanan masin berkuah pekat.",
        "note_ta": "குறைந்த உப்பு உணவு பரிந்துரைக்கப்படுகிறது (உயர் இரத்த அழுத்தப் பதிவு, PLACEHOLDER விதி): ஆவியில் வேகவைத்த மீன் மற்றும் தெளிவான சூப் வகைகளுக்கு முன்னுரிமை.",
    },
    "type 2 diabetes": {
        "rule_id": "diet.diabetes.less_sugar",
        "rule_code": "cond.diabetes",
        "exclude_tags": ["high_sugar_syrup", "sweetened_condensed_milk"],
        "prefer_tags": ["less_sugar_friendly", "kopi_o_kosong_option", "unsweetened_tea"],
        "badge_en": "Unsweetened / less-sugar fit (diabetes)",
        "badge_zh": "无糖/少糖适宜（糖尿病）",
        "badge_ms": "Tanpa gula / kurang manis (diabetes)",
        "badge_ta": "இனிப்பு குறைந்த / சர்க்கரை இல்லாத (நீரிழிவு)",
        "note_en": "Unsweetened or less-sugar option preferred (type 2 diabetes record, PLACEHOLDER rule): favours kopi-O kosong or plain tea and filters out heavy syrup drinks and sweet desserts.",
        "note_zh": "优先无糖或少糖选项（二型糖尿病记录，占位规则）：倾向无糖咖啡乌或清茶，已过滤浓糖浆饮品与甜品。",
        "note_ms": "Pilihan tanpa gula atau kurang manis diutamakan (rekod diabetes, peraturan PLACEHOLDER): mengutamakan kopi-O kosong atau teh kosong dan menapis minuman sirap manis.",
        "note_ta": "சர்க்கரை இல்லாத அல்லது குறைந்த இனிப்பு விருப்பம் (நீரிழிவுப் பதிவு, PLACEHOLDER விதி): கோப்பி-ஓ கொசோங் அல்லது சாதாரண தேநீருக்கு முன்னுரிமை.",
    },
    "high cholesterol": {
        "rule_id": "diet.cholesterol.light_cooking",
        "rule_code": "cond.cholesterol",
        "exclude_tags": ["deep_fried_lard"],
        "prefer_tags": ["steamed_fish", "grilled_fish", "vegetarian_friendly"],
        "badge_en": "Steamed / grilled fit (cholesterol)",
        "badge_zh": "清蒸/少油适宜（胆固醇）",
        "badge_ms": "Kukus / bakar kurang minyak (kolesterol)",
        "badge_ta": "ஆவியில் வேகவைத்த / எண்ணெய் குறைந்த (கொலஸ்ட்ரால்)",
        "note_en": "Lightly cooked dishes preferred (high cholesterol record, PLACEHOLDER rule): favours steamed, grilled or fermented flatbread options.",
        "note_zh": "优先少油清淡烹调（高胆固醇记录，占位规则）：倾向清蒸、烤或发酵面食。",
        "note_ms": "Masakan kurang minyak diutamakan (rekod kolesterol tinggi, peraturan PLACEHOLDER): mengutamakan hidangan kukus atau bakar.",
        "note_ta": "எண்ணெய் குறைந்த சமையல் பரிந்துரைக்கப்படுகிறது (அதிக கொலஸ்ட்ரால் பதிவு, PLACEHOLDER விதி): ஆவியில் வேகவைத்த அல்லது சுட்ட உணவுகளுக்கு முன்னுரிமை.",
    },
    "gout": {
        "rule_id": "diet.gout.low_purine",
        "rule_code": "cond.gout",
        "exclude_tags": ["high_purine_organ_shellfish", "anchovy_rich_broth"],
        "prefer_tags": ["steamed_fish", "clear_soup", "low_sodium_friendly", "vegetarian_friendly"],
        "badge_en": "Low-purine fit (gout)",
        "badge_zh": "低嘌呤适宜（痛风）",
        "badge_ms": "Rendah purin (gout)",
        "badge_ta": "குறைந்த பியூரின் (கீழ்வாதம்)",
        "note_en": "Low-purine option preferred (gout record, PLACEHOLDER rule): favours clear-soup fish, eggs or vegetable dishes and filters out organ meats, rich anchovy broths and shellfish.",
        "note_zh": "优先低嘌呤清淡餐点（痛风记录，占位规则）：倾向清蒸鱼、蛋类或蔬菜，已过滤动物内脏、浓江鱼仔汤底与贝类。",
        "note_ms": "Pilihan rendah purin diutamakan (rekod gout, peraturan PLACEHOLDER): menapis organ dalaman, kuah bilis pekat dan kerang-kerangan.",
        "note_ta": "குறைந்த பியூரின் உணவு பரிந்துரைக்கப்படுகிறது (கீழ்வாதப் பதிவு, PLACEHOLDER விதி): உறுப்பு இறைச்சி மற்றும் அடர் சூப் வகைகள் தவிர்க்கப்படுகின்றன.",
    },
    "chronic kidney disease": {
        "rule_id": "diet.ckd.renal_light",
        "rule_code": "cond.ckd",
        "exclude_tags": ["high_sodium_preserved", "heavy_gravies", "potassium_salt_substitute", "herbal_tonic_broth"],
        "prefer_tags": ["low_sodium_friendly", "steamed_fish", "clear_soup"],
        "badge_en": "Renal-light / low-sodium fit (CKD)",
        "badge_zh": "护肾少盐适宜（慢性肾病）",
        "badge_ms": "Mesra buah pinggang / kurang garam (CKD)",
        "badge_ta": "சிறுநீரகப் பாதுகாப்பு / குறைந்த உப்பு (CKD)",
        "note_en": "Renal-light option preferred (chronic kidney disease record, PLACEHOLDER rule): avoids preserved salted foods, heavy gravies, herbal tonics and potassium salt substitutes.",
        "note_zh": "优先护肾清淡少盐选项（慢性肾病记录，占位规则）：避开腌制咸品、浓汁、浓药材汤及高钾代盐。",
        "note_ms": "Pilihan mesra buah pinggang diutamakan (rekod CKD, peraturan PLACEHOLDER): mengelakkan makanan jeruk masin, sup herba pekat dan pengganti garam kalium.",
        "note_ta": "சிறுநீரகத்திற்கு ஏற்ற உணவு (CKD பதிவு, PLACEHOLDER விதி): அதிக உப்பு, மூலிகை டானிக் மற்றும் பொட்டாசியம் உப்பு மாற்றீடுகள் தவிர்க்கப்படுகின்றன.",
    },
    "mobility_aid": {
        "rule_id": "mobility.step_free_seated",
        "rule_code": "cond.mobility_aid",
        "exclude_tags": ["strenuous_standing_walk", "uneven_stairs"],
        "prefer_tags": ["wheelchair_accessible", "seated_activity", "flat_sheltered"],
        "badge_en": "Step-free & seated friendly",
        "badge_zh": "无障碍/有座位适宜",
        "badge_ms": "Mesra kerusi roda & tempat duduk",
        "badge_ta": "படிகள் இல்லாத மற்றும் அமரக்கூடிய இடம்",
        "note_en": "Step-free, seated or flat sheltered venues preferred (mobility / joint comfort record, PLACEHOLDER rule): filters out sloped or stair-heavy walks.",
        "note_zh": "优先平坦无障碍及有座位场所（行动与关节关怀记录，占位规则）：已过滤阶梯坡道或长距离站立步行。",
        "note_ms": "Lokasi rata tanpa tangga dan mempunyai tempat duduk diutamakan (rekod mobiliti, peraturan PLACEHOLDER).",
        "note_ta": "படிகள் இல்லாத, சமதளமான மற்றும் அமரக்கூடிய இடங்களுக்கு முன்னுரிமை (நடை / மூட்டு நலப் பதிவு, PLACEHOLDER விதி).",
    },
    "halal": {
        "rule_id": "diet.religious.halal",
        "rule_code": "diet.halal",
        "exclude_tags": ["non_halal_pork_lard"],
        "prefer_tags": ["halal", "vegetarian_friendly", "kopi_o_kosong_option"],
        "badge_en": "Halal-friendly fit",
        "badge_zh": "清真适宜 (Halal)",
        "badge_ms": "Mesra Halal",
        "badge_ta": "ஹலால் உணவு விருப்பம்",
        "note_en": "Halal or Muslim-friendly food and beverage stalls preferred (dietary preference record): filters out non-halal stalls.",
        "note_zh": "优先清真认证或穆斯林友善餐饮档口（饮食偏好记录）：已过滤非清真荤食档口。",
        "note_ms": "Gerai makanan dan minuman Halal atau mesra Muslim diutamakan (rekod pilihan diet).",
        "note_ta": "ஹலால் அல்லது முஸ்லிம் நட்பு உணவுக் கடைகளுக்கு முன்னுரிமை (உணவு விருப்பப் பதிவு).",
    },
    "vegetarian": {
        "rule_id": "diet.preference.vegetarian",
        "rule_code": "diet.vegetarian",
        "exclude_tags": ["meat_seafood_broth", "high_purine_organ_shellfish", "non_halal_pork_lard"],
        "prefer_tags": ["vegetarian_friendly", "unsweetened_tea", "fermented_flatbread"],
        "badge_en": "Vegetarian-friendly fit",
        "badge_zh": "素食友善",
        "badge_ms": "Mesra Vegetarian",
        "badge_ta": "சைவ உணவு விருப்பம்",
        "note_en": "Vegetarian-friendly options preferred (dietary preference record): filters out meat and fish-broth dishes.",
        "note_zh": "优先素食友善选项（饮食偏好记录）：已过滤肉类与荤汤餐点。",
        "note_ms": "Pilihan mesra vegetarian diutamakan (rekod pilihan diet): menapis hidangan daging dan kuah makanan laut.",
        "note_ta": "சைவ உணவு விருப்பங்களுக்கு முன்னுரிமை (உணவு விருப்பப் பதிவு): இறைச்சி மற்றும் மீன் சூப் உணவுகள் தவிர்க்கப்படுகின்றன.",
    },
    "no_beef": {
        "rule_id": "diet.preference.no_beef",
        "rule_code": "diet.no_beef",
        "exclude_tags": ["contains_beef"],
        "prefer_tags": ["steamed_fish", "vegetarian_friendly"],
        "badge_en": "No-beef fit",
        "badge_zh": "不含牛肉",
        "badge_ms": "Tanpa daging lembu",
        "badge_ta": "மாட்டிறைச்சி இல்லாதது",
        "note_en": "No-beef preference applied (dietary preference record): filters out beef dishes and broths.",
        "note_zh": "已应用不吃牛肉偏好（饮食偏好记录）：过滤含牛肉餐点与汤底。",
        "note_ms": "Pilihan tanpa daging lembu digunakan: menapis hidangan berasaskan daging lembu.",
        "note_ta": "மாட்டிறைச்சி தவிர்ப்பு விருப்பம் பயன்படுத்தப்பட்டது.",
    },
}

# Synonym aliases mapped into canonical CONDITION_RULES keys
CONDITION_ALIASES: dict[str, str] = {
    "ckd": "chronic kidney disease",
    "renal": "chronic kidney disease",
    "kidney disease": "chronic kidney disease",
    "diabetes": "type 2 diabetes",
    "osteoarthritis": "mobility_aid",
    "knee pain": "mobility_aid",
    "fall_risk": "mobility_aid",
    "fall risk": "mobility_aid",
    "wheelchair": "mobility_aid",
    "walking stick": "mobility_aid",
    "no beef": "no_beef",
}

# PLACEHOLDER: standard patient-leaflet food interaction rules (pharmacist sign-off required before real use).
# Never tells a senior to change, skip or stop a medicine; only filters food/drink suggestions.
MEDICINE_FOOD_RULES: dict[str, dict] = {
    "cyp3a4_grapefruit": {
        "rule_id": "med_food.grapefruit_pomelo",
        "rule_code": "med.statin_grapefruit",
        "generics": {"amlodipine", "nifedipine", "simvastatin", "atorvastatin"},
        "raw_names": {"zanidip", "lercanidipine", "statin"},
        "exclude_tags": ["contains_grapefruit_pomelo"],
        "badge_en": "No grapefruit/pomelo (medicine leaflet)",
        "badge_zh": "避开西柚/柚子（药物说明书）",
        "badge_ms": "Elakkan limau gedang/bali (risalah ubat)",
        "badge_ta": "பம்பளிமாஸ் / திராட்சைப்பழம் தவிர்க்கவும் (மருந்து குறிப்பு)",
        "note_en": "Filtered out grapefruit and pomelo items (standard patient-leaflet food note for {med}, PLACEHOLDER; ask your pharmacist if unsure).",
        "note_zh": "已过滤含西柚与柚子的甜品饮品（{med} 药物说明书常见饮食提示，占位规则；如有疑问请咨询药剂师）。",
        "note_ms": "Menapis item limau gedang dan limau bali (nota makanan risalah pesakit bagi {med}, PLACEHOLDER; tanya ahli farmasi jika kurang pasti).",
        "note_ta": "பம்பளிமாஸ் மற்றும் திராட்சைப்பழ உணவுகள் தவிர்க்கப்பட்டன ({med} மருந்து தகவல் குறிப்பு, PLACEHOLDER).",
    },
    "raas_potassium": {
        "rule_id": "med_food.potassium_note",
        "rule_code": "med.raas_potassium",
        "generics": {"losartan", "valsartan", "telmisartan", "lisinopril", "enalapril", "perindopril"},
        "raw_names": set(),
        "exclude_tags": ["potassium_salt_substitute"],
        "badge_en": "Natural herbs, no salt substitutes",
        "badge_zh": "天然香料，不用高钾代盐",
        "badge_ms": "Herba asli, tiada pengganti garam kalium",
        "badge_ta": "இயற்கை மூலிகைகள், பொட்டாசியம் உப்பு மாற்றீடு இல்லை",
        "note_en": "Uses natural herbs and spices rather than potassium salt substitutes (standard leaflet note for {med}, PLACEHOLDER).",
        "note_zh": "使用天然香料调味，避免高钾代盐（{med} 药物说明书提示，占位规则）。",
        "note_ms": "Menggunakan herba asli dan bukannya pengganti garam kalium (nota risalah bagi {med}, PLACEHOLDER).",
        "note_ta": "பொட்டாசியம் உப்பு மாற்றீடுகளுக்குப் பதிலாக இயற்கை மூலிகைகள் ({med} மருந்து குறிப்பு, PLACEHOLDER).",
    },
    "warfarin_vit_k": {
        "rule_id": "med_food.warfarin_consistent_greens",
        "rule_code": "med.warfarin_vit_k",
        "generics": {"warfarin"},
        "raw_names": {"warfarin", "marevan"},
        "exclude_tags": ["cranberry_herbal_tonic", "contains_grapefruit_pomelo"],
        "badge_en": "Steady greens, no herbal tonics (warfarin leaflet)",
        "badge_zh": "绿叶菜定量、避开药材补汤（华法林说明书）",
        "badge_ms": "Sayur hijau konsisten, elak tonik herba (warfarin)",
        "badge_ta": "சீரான கீரை அளவு, மூலிகை டானிக் தவிர்க்கவும் (வார்ஃபரின்)",
        "note_en": "Keeps leafy-green portions steady and filters out concentrated herbal tonics or cranberry/grapefruit items (standard patient-leaflet food note for {med}, PLACEHOLDER; ask your pharmacist if unsure).",
        "note_zh": "保持深绿叶蔬菜摄取量稳定，已过滤浓药材补汤与蔓越莓/西柚饮品（{med} 药物说明书饮食提示，占位规则；如有疑问请咨询药剂师）。",
        "note_ms": "Kekalkan pengambilan sayur hijau secara konsisten dan elakkan tonik herba pekat atau kranberi (nota risalah {med}, PLACEHOLDER).",
        "note_ta": "கீரை வகைகளை சீரான அளவில் உட்கொள்ளவும்; அடர் மூலிகை டானிக் தவிர்க்கவும் ({med} மருந்து குறிப்பு, PLACEHOLDER).",
    },
}


def _lang_pick(rule: dict, prefix: str, lang: str) -> str:
    """Return localized string (`prefix_zh`, `prefix_ms`, `prefix_ta`, falling back to `prefix_en`)."""
    key = f"{prefix}_{lang}"
    return rule.get(key) or rule.get(f"{prefix}_en", "")


def medicine_leaflet_note(raw_name: str, generic: str | None = None, *, lang: str = "en") -> dict | None:
    """Return the patient-leaflet food note for a medicine if one applies, or None."""
    lower_raw = (raw_name or "").lower().strip()
    gen = generic or identify(raw_name)
    for mrule in MEDICINE_FOOD_RULES.values():
        matched = (gen in mrule["generics"]) or any(r in lower_raw for r in mrule["raw_names"])
        if matched:
            label = gen or raw_name
            return {
                "rule_id": mrule["rule_id"],
                "badge": _lang_pick(mrule, "badge", lang),
                "note": _lang_pick(mrule, "note", lang).format(med=label),
            }
    return None


def active_constraints(
    senior: dict,
    *,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
) -> dict:
    """Inspect a senior's conditions, dietary_prefs, medicines, weather and hidden list to build the active constraint set."""
    lang = str(senior.get("language") or "en").lower()
    zh = lang == "zh"
    raw_conds = [str(c).lower().strip() for c in (senior.get("conditions") or [])]
    raw_prefs = [str(p).lower().strip() for p in (senior.get("dietary_prefs") or [])]
    conditions: list[str] = []
    for item in [*raw_conds, *raw_prefs]:
        canon = CONDITION_ALIASES.get(item, item)
        if canon and canon not in conditions:
            conditions.append(canon)

    medicines = list(senior.get("medicines") or [])
    existing_med_names = {str(m.get("name", "")).lower().strip() for m in medicines}
    for item in [*raw_conds, *raw_prefs]:
        if item in ("atorvastatin", "simvastatin", "statin", "amlodipine", "warfarin") and not any(item in m for m in existing_med_names):
            med_label = "Atorvastatin 20mg" if item in ("atorvastatin", "statin") else item.capitalize()
            medicines.append({"name": med_label, "raw": med_label})
            existing_med_names.add(med_label.lower())

    # Check if diabetes or gout is implied by medicines even if not explicitly in conditions
    for m in medicines:
        gen = identify(m.get("name", ""))
        if gen == "metformin" and "type 2 diabetes" not in conditions:
            conditions.append("type 2 diabetes")
        if gen in ("allopurinol", "colchicine") and "gout" not in conditions:
            conditions.append("gout")

    excluded_tags: dict[str, dict] = {}
    preferred_tags: set[str] = set()
    active_rules: list[dict] = []
    badges: list[str] = []

    for cond in conditions:
        rule = CONDITION_RULES.get(cond)
        if not rule:
            continue
        preferred_tags.update(rule["prefer_tags"])
        badge = _lang_pick(rule, "badge", lang)
        if badge not in badges:
            badges.append(badge)
        rule_code = rule.get("rule_code", rule["rule_id"])
        active_rules.append({
            "rule_id": rule["rule_id"],
            "rule_code": rule_code,
            "kind": "condition",
            "trigger": cond,
            "badge": badge,
            "explanation": _lang_pick(rule, "note", lang),
        })
        for tag in rule["exclude_tags"]:
            excluded_tags[tag] = {
                "rule_id": rule["rule_id"],
                "rule_code": rule_code,
                "reason_en": f"Filtered out by {rule_code} ({rule['rule_id']} — {cond}): avoids {tag.replace('_', ' ')}.",
                "reason_zh": f"已由规则 {rule_code} / {rule['rule_id']}（{cond}）过滤：避开{tag}。",
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
            badge = _lang_pick(mrule, "badge", lang)
            if badge not in badges:
                badges.append(badge)
            rule_code = mrule.get("rule_code", mrule["rule_id"])
            active_rules.append({
                "rule_id": mrule["rule_id"],
                "rule_code": rule_code,
                "kind": "medicine_leaflet",
                "trigger": raw_name,
                "badge": badge,
                "explanation": _lang_pick(mrule, "note", lang).format(med=label),
            })
            for tag in mrule["exclude_tags"]:
                excluded_tags[tag] = {
                    "rule_id": mrule["rule_id"],
                    "rule_code": rule_code,
                    "reason_en": f"Filtered out by {rule_code} ({mrule['rule_id']} — {raw_name} leaflet note): contains {tag.replace('_', ' ')} or conflicting ingredient.",
                    "reason_zh": f"已由规则 {rule_code} / {mrule['rule_id']}（{raw_name} 说明书提示）过滤：含冲突饮食成分（{tag}）。",
                }

    indoor_only = bool(indoor_only or (psi or 0) > 100 or (rain_mm or 0) >= 5.0)
    if indoor_only:
        why_env = f"rain ({rain_mm} mm)" if (rain_mm or 0) >= 5.0 else f"haze (PSI {psi})" if (psi or 0) > 100 else "weather/air quality"
        why_env_zh = f"降雨（{rain_mm} 毫米）" if (rain_mm or 0) >= 5.0 else f"烟霾（PSI {psi}）" if (psi or 0) > 100 else "天气或空气质量"
        badge = "仅限室内（天气/烟霾）" if zh else f"Indoor-only today ({why_env})"
        badges.insert(0, badge)
        active_rules.insert(0, {
            "rule_id": "env.indoor_only",
            "rule_code": "env.indoor_only",
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
                "rule_code": "preference.not_for_me",
                "rule_ids": ["preference.not_for_me"],
                "reason": "长者此前标记为“不适合我”，不再重复推荐。" if zh else "Senior previously tapped 'Not for me'; remembered and excluded.",
            })
            continue

        if indoor_only and not item.get("indoor", True):
            filtered_out.append({
                "entity_id": eid,
                "name": name,
                "rule_id": "env.indoor_only",
                "rule_code": "env.indoor_only",
                "rule_ids": ["env.indoor_only"],
                "reason": "今日降雨或烟霾超标，已过滤户外无盖地点。" if zh else "Filtered out by env.indoor_only: outdoor venue skipped due to today's rain or haze.",
            })
            continue

        item_tags = item.get("dietary_tags") or []
        conflict = next((t for t in item_tags if t in excluded_tags), None)
        if conflict is not None:
            rule_info = excluded_tags[conflict]
            rcode = rule_info.get("rule_code", rule_info["rule_id"])
            rids = [rcode, rule_info["rule_id"]] if rcode != rule_info["rule_id"] else [rule_info["rule_id"]]
            filtered_out.append({
                "entity_id": eid,
                "name": name,
                "rule_id": rule_info["rule_id"],
                "rule_code": rcode,
                "rule_ids": rids,
                "reason": rule_info["reason_zh"] if zh else rule_info["reason_en"],
            })
            continue

        matched_prefs = [t for t in item_tags if t in preferred_tags]
        fit_badges: list[str] = []
        if "low_sodium_friendly" in matched_prefs:
            fit_badges.append("少盐适宜" if zh else "Lower-salt fit")
        if "less_sugar_friendly" in matched_prefs or "kopi_o_kosong_option" in matched_prefs or "unsweetened_tea" in matched_prefs:
            fit_badges.append("少糖/无糖选项" if zh else "Less-sugar option")
        if "halal" in item_tags and ("halal" in matched_prefs or "halal" in item_tags):
            if "halal" in matched_prefs:
                fit_badges.append("清真适宜" if zh else "Halal-friendly")
        if "vegetarian_friendly" in matched_prefs:
            fit_badges.append("素食友善" if zh else "Vegetarian-friendly")
        if any(t in matched_prefs for t in ("wheelchair_accessible", "seated_activity", "flat_sheltered")):
            fit_badges.append("无障碍有座" if zh else "Step-free & seated")
        if item.get("indoor", True):
            fit_badges.append("室内有盖" if zh else "Indoor / sheltered")

        why_text = (
            item.get(f"why_{lang}")
            or (item.get("why_zh") if zh else None)
            or item.get("why_en", "")
        )
        kept.append({
            **item,
            "display_name": name,
            "why": why_text,
            "fit_badges": fit_badges,
        })

    return kept, filtered_out
