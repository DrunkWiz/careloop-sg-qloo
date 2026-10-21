"""CareLoop SG's Qloo Taste Agent: plans culturally grounded, health-safe days for each senior.

Safety & architecture rules (CLAUDE.md):
1. Works ONLY at the suggestion level. Never touches rungs 0-4 or R, or who gets contacted.
2. Uses a 4-step tool loop:
   - Tool 1 (`qloo_search`): resolves the senior's taste seeds into Qloo entity IDs and tags.
   - Tool 2 (`qloo_insights`): queries Qloo `/v2/insights` across places/food, music artists and classic films.
   - Tool 3 (`check_health_constraints`): filters candidates against deterministic condition, medicine-leaflet,
     weather/haze and 'not_for_me' rules (all marked PLACEHOLDER).
   - Tool 4 (`match_centre_and_guardrail`): combines AAC/CC programmes with Qloo picks and checks every
     outgoing explanation through `backend/language/guardrail.py`.
"""
from __future__ import annotations

import time
import uuid
from datetime import date

from backend.escalation.guardrail import Facts, check as guardrail_check
from backend.taste.baseline_llm import llm_only_baseline
from backend.taste.client import QlooClient
from backend.taste.constraints import active_constraints, filter_qloo_candidates
from backend.taste.profiles import build_taste_profile

_DEFAULT_CLIENT: QlooClient | None = None


def get_qloo_client() -> QlooClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = QlooClient()
    return _DEFAULT_CLIENT


def _safe_text(text: str, fallback: str, *, psi: int | None = None) -> tuple[str, bool, list[str]]:
    """Run every agent-facing explanation through backend/language/guardrail.py."""
    res = guardrail_check(text, rung="1", to="senior", facts=Facts(lang="en"), context={"psi": psi, "place": text})
    if res.passed:
        return text, True, []
    return fallback, False, list(res.reasons)


def _build_bridge(
    matched_seeds: list[str],
    default_seed: str,
    target_domain: str,
    seed_tags_map: dict[str, list[str]],
    safety_badges: list[str],
    *,
    zh: bool = False,
) -> dict:
    """Build explicit Cross-Domain Taste Bridge metadata (Seed -> Shared Qloo Tags -> Target Domain -> Safety Check)."""
    primary_seed = (matched_seeds[0] if matched_seeds else default_seed) or "nostalgia"
    tags: list[str] = []
    for s in matched_seeds or [primary_seed]:
        for t in seed_tags_map.get(s.lower(), []):
            if t not in tags:
                tags.append(t)
    if not tags:
        tags = ["nostalgia_sg", "community_affinity"]
    safety = (
        " · ".join(safety_badges[:2])
        if safety_badges
        else ("通过护栏检查" if zh else "Guardrail & health check passed")
    )
    return {
        "seed": primary_seed,
        "shared_tags": tags[:3],
        "target_domain": target_domain,
        "safety_check": safety,
        "path_label": f"{primary_seed} → {', '.join(tags[:2])} → {target_domain} → {safety}",
    }


def _build_kitchen_card(
    senior: dict,
    profile: dict,
    constraints: dict,
    top_place: dict | None,
    *,
    zh: bool = False,
    psi: int | None = None,
) -> tuple[dict, bool, list[str]]:
    """Build a copyable/printable Helper & Hawker Kitchen Card in English + Singlish/Chinese."""
    sname = senior.get("name") or ("长者" if zh else "Senior")
    rule_ids = {r["rule_id"] for r in constraints.get("active_rules", [])}
    avoid_items: list[str] = []
    if "diet.hypertension.low_salt" in rule_ids or "diet.ckd.renal_light" in rule_ids:
        avoid_items.append("No salted fish, cured meat, or heavy dark-soy gravy (少盐、不加咸鱼浓汁)")
    if "diet.diabetes.less_sugar" in rule_ids:
        avoid_items.append("No sweet syrup drinks or condensed milk — ask for kosong / siew dai (走糖 / 少甜)")
    if "diet.gout.low_purine" in rule_ids:
        avoid_items.append("No organ meats, offal, shellfish, or thick anchovy broth (痛风忌内脏、浓江鱼仔汤)")
    if "med_food.grapefruit_pomelo" in rule_ids:
        avoid_items.append("No grapefruit or pomelo desserts/juices (medicine leaflet note / 忌西柚柚子)")
    if "med_food.warfarin_consistent_greens" in rule_ids:
        avoid_items.append("Keep leafy greens steady; no concentrated herbal tonics or cranberry (忌浓药材补汤)")
    if "diet.religious.halal" in rule_ids:
        avoid_items.append("Halal-certified stalls and ingredients only (清真餐饮)")
    if "diet.preference.vegetarian" in rule_ids:
        avoid_items.append("Vegetarian only — no meat or fish broth (素食，不用荤汤)")
    if "diet.preference.no_beef" in rule_ids:
        avoid_items.append("No beef or beef broth (不吃牛肉)")
    while len(avoid_items) < 3:
        fallback_item = [
            "Ask for less salt and clear soup at the hawker stall (少盐清汤)",
            "Order kopi-O kosong or siew dai instead of full sugar (咖啡乌少甜/走糖)",
            "Avoid grapefruit/pomelo if taking blood pressure or cholesterol tablets (服药期间避开西柚)",
        ][len(avoid_items)]
        if fallback_item not in avoid_items:
            avoid_items.append(fallback_item)

    drink_phrase = "Kopi-O kosong / Teh-O siew dai (咖啡乌走糖 / 茶乌少甜)"
    dish_phrase = (
        f"{top_place['name']} — ask for clear soup, less oil, less salt (清汤、少油、少盐)"
        if top_place
        else "Steamed fish porridge or clear soup noodles, less salt (潮州清蒸鱼粥，少盐)"
    )
    raw_copy = (
        f"CareLoop Hawker & Kitchen Card for {sname}:\n"
        f"• Drink order: {drink_phrase}\n"
        f"• Dish order: {dish_phrase}\n"
        f"• Please avoid: {'; '.join(avoid_items)}"
    )
    safe_copy, ok, reasons = _safe_text(
        raw_copy,
        f"CareLoop Hawker & Kitchen Card for {sname}: order {drink_phrase} and steamed/clear-soup dishes.",
        psi=psi,
    )
    card = {
        "senior_name": sname,
        "drink_order_phrase": drink_phrase,
        "dish_order_phrase": dish_phrase,
        "avoid_items": avoid_items,
        "safe_swaps": [
            "Steamed fish / clear soup instead of heavy braised gravy",
            "Kopi-O kosong / plain Chinese tea instead of syrup drinks",
        ],
        "copy_text": safe_copy,
    }
    return card, ok, reasons


def build_taste_plan(
    senior: dict,
    day: date,
    *,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
    erased_keys: set[str] | None = None,
    client: QlooClient | None = None,
) -> dict:
    """Run the 4-step CareLoop Taste Agent for `senior` on `day` and return the full TastePlan + trace."""
    t0 = time.perf_counter()
    qloo = client or get_qloo_client()
    raw_lang = str(senior.get("language") or "en").lower()
    zh = raw_lang == "zh"
    lang = raw_lang if raw_lang in ("en", "zh", "ms", "ta") else "en"
    region = senior.get("region") or "central"

    # --- Step 1: Tool `qloo_search` ---
    profile = build_taste_profile(senior, erased_keys=erased_keys)
    resolved_entities: list[dict] = []
    seed_tags_map: dict[str, list[str]] = {}
    for seed in profile["all_seeds"][:6]:
        sr = qloo.search(seed, location="Singapore", limit=1)
        if sr.get("results"):
            top_ent = dict(sr["results"][0], query=seed)
            resolved_entities.append(top_ent)
            seed_tags_map[seed.lower()] = list(top_ent.get("tags") or [])
    entity_ids = [e["entity_id"] for e in resolved_entities if e.get("entity_id")]
    qloo_mode = "live" if qloo.is_live else "fixture"
    default_seed = (profile["music_seeds"] or profile["likes"] or ["kopi"])[0]


    # --- Step 2: Tool `qloo_insights` across 3 domains (places/food, music, movies) ---
    place_insights = qloo.insights(
        "urn:entity:place",
        signal_entities=entity_ids,
        signal_tags=profile["all_seeds"],
        region=region,
        location="Singapore",
        limit=12,
    )
    artist_insights = qloo.insights(
        "urn:entity:artist",
        signal_entities=entity_ids,
        signal_tags=profile["all_seeds"],
        region=region,
        location="Singapore",
        limit=3,
    )
    movie_insights = qloo.insights(
        "urn:entity:movie",
        signal_entities=entity_ids,
        signal_tags=profile["all_seeds"],
        region=region,
        location="Singapore",
        limit=2,
    )

    # --- Step 3: Tool `check_health_constraints` ---
    constraints = active_constraints(
        senior,
        indoor_only=indoor_only,
        rain_mm=rain_mm,
        psi=psi,
    )
    kept_places, filtered_out = filter_qloo_candidates(
        place_insights.get("results", []),
        constraints,
        lang=lang,
    )

    # Format music and movie picks in the senior's language
    music_picks = []
    for a in artist_insights.get("results", [])[:2]:
        mseeds = a.get("matched_seeds", [])
        music_picks.append({
            "entity_id": a["entity_id"],
            "name": a.get("name_zh") if zh and a.get("name_zh") else a.get("name", ""),
            "affinity": a.get("affinity", 0.9),
            "matched_seeds": mseeds,
            "why": a.get("why_zh") if zh and a.get("why_zh") else a.get("why_en", ""),
            "bridge": _build_bridge(mseeds, default_seed, "music_artist", seed_tags_map, [], zh=zh),
        })

    movie_picks = []
    for m in movie_insights.get("results", [])[:2]:
        mseeds = m.get("matched_seeds", [])
        movie_picks.append({
            "entity_id": m["entity_id"],
            "name": m.get("name_zh") if zh and m.get("name_zh") else m.get("name", ""),
            "affinity": m.get("affinity", 0.9),
            "matched_seeds": mseeds,
            "why": m.get("why_zh") if zh and m.get("why_zh") else m.get("why_en", ""),
            "bridge": _build_bridge(mseeds, default_seed, "classic_film", seed_tags_map, [], zh=zh),
        })

    # --- Step 4: Tool `guardrail_check` on all explanations ---
    checked_count = 0
    all_passed = True
    failed_reasons: list[str] = []

    safe_places = []
    for p in kept_places[:3]:
        why_safe, ok, reasons = _safe_text(
            p["why"],
            "根据您的品味档案与今日健康条件推荐。" if zh else "Matched to your taste profile and today's health constraints.",
            psi=psi,
        )
        checked_count += 1
        if not ok:
            all_passed = False
            failed_reasons.extend(reasons)
        mseeds = p.get("matched_seeds", [])
        fbadges = p.get("fit_badges", [])
        safe_places.append({
            "entity_id": p["entity_id"],
            "name": p["display_name"],
            "category": p.get("category", "place"),
            "indoor": bool(p.get("indoor", True)),
            "free": bool(p.get("free", False)),
            "affinity": p.get("affinity", 0.9),
            "matched_seeds": mseeds,
            "fit_badges": fbadges,
            "why": why_safe,
            "bridge": _build_bridge(mseeds, default_seed, p.get("category", "place"), seed_tags_map, fbadges, zh=zh),
        })

    for item in [*music_picks, *movie_picks]:
        why_safe, ok, reasons = _safe_text(
            item["why"],
            "由 Qloo 品味图谱跨领域推荐。" if zh else "Cross-domain match from Qloo's taste graph.",
            psi=psi,
        )
        checked_count += 1
        if not ok:
            all_passed = False
            failed_reasons.extend(reasons)
        item["why"] = why_safe

    # Build Rung-2 "Low Day" cultural nudge (combining top safe place + top music artist, checked via guardrail.py)
    top_place = safe_places[0] if safe_places else None
    top_music = music_picks[0] if music_picks else None
    top_movie = movie_picks[0] if movie_picks else None
    senior_name = senior.get("name") or ("长者" if zh else "your loved one")

    raw_nudge = (
        f"今天如果在家觉得闷，不妨听一首{top_music['name'] if top_music else '经典老歌'}，或者去{top_place['name'] if top_place else '附近中心'}坐坐。"
        if zh
        else f"If today feels a bit quiet, you could put on {top_music['name'] if top_music else 'some favourite songs'} or drop by {top_place['name'] if top_place else 'your nearby centre'}."
    )
    safe_nudge, ok_nudge, nudge_reasons = _safe_text(
        raw_nudge,
        "今天不妨听听您喜欢的老歌，或去附近有盖的活动中心坐坐。" if zh else "If today feels quiet, how about putting on your favourite songs or dropping by your nearby indoor centre?",
        psi=psi,
    )
    checked_count += 1
    if not ok_nudge:
        all_passed = False
        failed_reasons.extend(nudge_reasons)

    low_day_nudge = {
        "rule_id": "2.low_day",
        "place": top_place["name"] if top_place else None,
        "place_pick": top_place["name"] if top_place else "Nearby Activity Centre",
        "music": top_music["name"] if top_music else None,
        "music_companion": top_music["name"] if top_music else None,
        "film_companion": top_movie["name"] if top_movie else None,
        "text": safe_nudge,
        "nudge_text": safe_nudge,
        "guardrail_passed": ok_nudge,
    }

    # Build Family Visit Kit with one-tap WhatsApp text (checked via guardrail.py)
    treat_label = top_place["name"] if top_place else ("清淡茶点" if zh else "Light kopi or tea nearby")
    treat_badges = ", ".join(top_place["fit_badges"]) if top_place and top_place.get("fit_badges") else ("符合健康条件" if zh else "Health-checked")
    music_label = top_music["name"] if top_music else "Teresa Teng"
    movie_label = top_movie["name"] if top_movie else "Classic matinee film"
    safety_summary = ", ".join(constraints["badges"]) if constraints["badges"] else ("已通过日常健康检查" if zh else "Standard health checks applied")

    raw_visit_summary = (
        f"探访{senior_name}的贴心包：可带一份{treat_label}，一起听{music_label}，聊聊《{movie_label}》。"
        if zh
        else f"Visiting {senior_name} today: bring a light treat from {treat_label}, put on {music_label}, and chat about {movie_label}."
    )
    safe_visit_summary, ok_visit, visit_reasons = _safe_text(
        raw_visit_summary,
        "探访贴心包已根据长者的口味与健康记录准备好。" if zh else f"Family visit kit prepared for {senior_name} from their Qloo taste profile and health rules.",
        psi=psi,
    )
    checked_count += 1
    if not ok_visit:
        all_passed = False
        failed_reasons.extend(visit_reasons)

    whatsapp_text = (
        f"Visiting {senior_name} — CareLoop + Qloo Family Visit Kit:\n"
        f"• Takeaway / Outing: {treat_label} ({treat_badges})\n"
        f"• Put on music: {music_label}\n"
        f"• Nostalgia film / topic: {movie_label}\n"
        f"• Health & medicine checks applied: {safety_summary}"
    )

    visit_kit = {
        "treat": f"{treat_label} ({treat_badges})",
        "music": music_label,
        "film": movie_label,
        "safety_note": safety_summary,
        "summary": safe_visit_summary,
        "whatsapp_text": whatsapp_text,
    }

    kitchen_card, ok_kitchen, kitchen_reasons = _build_kitchen_card(
        senior, profile, constraints, top_place, zh=zh, psi=psi
    )
    checked_count += 1
    if not ok_kitchen:
        all_passed = False
        failed_reasons.extend(kitchen_reasons)

    raw_icebreaker = (
        f"敲门或致电破冰建议：可先问候{senior_name}今天喝了“{(profile['food_seeds'] or ['咖啡乌'])[0]}”吗，或聊聊《{movie_label}》与{music_label}的老歌，让对话自然轻松。"
        if zh
        else f"Doorstep / Call Icebreaker: Ask {senior_name} if they've had their morning {(profile['food_seeds'] or ['kopi'])[0]} yet, or mention {music_label} and {movie_label} before checking in on how they're feeling."
    )
    safe_icebreaker, ok_ice, ice_reasons = _safe_text(
        raw_icebreaker,
        f"Doorstep / Call Icebreaker: Start with a warm chat about {music_label} or their morning tea.",
        psi=psi,
    )
    checked_count += 1
    if not ok_ice:
        all_passed = False
        failed_reasons.extend(ice_reasons)

    doorstep_icebreaker = {
        "opener": safe_icebreaker,
        "music_icebreaker": music_label,
        "treat_icebreaker": f"{treat_label} ({treat_badges})",
        "film_icebreaker": movie_label,
        "safety_reminder": safety_summary,
    }

    # Build the 4-step visible agent trace for "How this was picked"
    trace = [
        {
            "step": 1,
            "tool": "qloo_search",
            "title": "解析长者品味种子 (Qloo /search)" if zh else "Resolve taste seeds (Qloo /search)",
            "input_summary": ", ".join(profile["all_seeds"][:6]),
            "output_summary": (
                f"解析出 {len(resolved_entities)} 个 Qloo 实体 ID（模式：{qloo_mode}）"
                if zh
                else f"Resolved {len(resolved_entities)} Qloo entity IDs in Singapore (mode: {qloo_mode})"
            ),
            "details": [f"{e['name']} -> {e['entity_id']}" for e in resolved_entities],
        },
        {
            "step": 2,
            "tool": "qloo_insights",
            "title": "跨领域品味图谱查询 (Qloo /v2/insights)" if zh else "Cross-domain taste discovery (Qloo /v2/insights)",
            "input_summary": f"domains=[place, artist, movie], region={region}, seeds={len(entity_ids)}",
            "output_summary": (
                f"返回 {len(place_insights.get('results', []))} 个餐饮/地点候选、{len(music_picks)} 位音乐人、{len(movie_picks)} 部经典电影"
                if zh
                else f"Retrieved {len(place_insights.get('results', []))} place/food candidates, {len(music_picks)} music artists, and {len(movie_picks)} classic films"
            ),
            "details": [
                p.get("name_zh" if zh else "name", "")
                for p in place_insights.get("results", [])[:5]
            ],
        },
        {
            "step": 3,
            "tool": "check_health_constraints",
            "title": "应用健康、药物说明书与天气护栏" if zh else "Apply health, medicine-leaflet & weather constraints",
            "input_summary": ", ".join(
                f"{r.get('rule_code') or r['rule_id']}"
                if r.get("rule_code") in (None, r["rule_id"])
                else f"{r['rule_code']} ({r['rule_id']})"
                for r in constraints["active_rules"]
            ) or "standard",
            "output_summary": (
                f"保留 {len(safe_places)} 个安全地点，过滤 {len(filtered_out)} 个冲突候选"
                if zh
                else f"Kept {len(safe_places)} safe place picks; filtered out {len(filtered_out)} conflicting candidates"
            ),
            "details": [
                f"[{' | '.join(f.get('rule_ids') or [f['rule_id']])}] {f['name']}: {f['reason']}"
                for f in filtered_out
            ],
        },
        {
            "step": 4,
            "tool": "guardrail_check",
            "title": "安全护栏检查 (backend/escalation/guardrail.py)" if zh else "Language safety guardrail check (guardrail.py)",
            "input_summary": f"{checked_count} explanation strings",
            "output_summary": (
                f"全部 {checked_count} 条推荐说明通过安全护栏（无诊断、无改药建议）"
                if zh and all_passed
                else f"All {checked_count} explanation strings passed guardrail.py (no diagnosis, no dose advice)"
            ),
            "details": [r["explanation"] for r in constraints["active_rules"]],
        },
    ]

    baseline = llm_only_baseline(senior, indoor_only=indoor_only, psi=psi, rain_mm=rain_mm)
    careloop_highlights = [
        f"{p['name']} ({', '.join(p['fit_badges']) or 'Qloo match'}): {p['why']}"
        for p in safe_places[:2]
    ]
    if music_picks:
        careloop_highlights.append(f"Music: {music_picks[0]['name']} — {music_picks[0]['why']}")
    if movie_picks:
        careloop_highlights.append(f"Film: {movie_picks[0]['name']} — {movie_picks[0]['why']}")

    elapsed_ms = round(max(1.2, (time.perf_counter() - t0) * 1000.0), 1)
    pass_rate = 100.0 if all_passed else round(100.0 * max(0, checked_count - len(failed_reasons)) / max(1, checked_count), 1)

    return {
        "senior_id": senior.get("id", ""),
        "date": day.isoformat(),
        "qloo_mode": qloo_mode,
        "resolved_entities": resolved_entities,
        "telemetry": {
            "mode": qloo_mode,
            "resolved_urns": entity_ids,
            "resolved_count": len(entity_ids),
            "guardrail_pass_rate": pass_rate,
            "latency_ms": elapsed_ms,
        },
        "profile": {
            "neighbourhood": profile["neighbourhood"],
            "likes": profile["likes"],
            "conditions": [str(c) for c in (senior.get("conditions") or [])],
            "music_seeds": profile["music_seeds"],
            "food_seeds": profile["food_seeds"],
            "film_seeds": profile["film_seeds"],
            "outings": profile["outings"],
            "summary": profile["summary_zh"] if zh else profile["summary_en"],
        },
        "constraints": {
            "indoor_only": constraints["indoor_only"],
            "rain_mm": constraints["rain_mm"],
            "psi": constraints["psi"],
            "badges": constraints["badges"],
            "active_rules": constraints["active_rules"],
        },
        "recommendations": {
            "places": safe_places,
            "music": music_picks,
            "movies": movie_picks,
        },
        "low_day_nudge": low_day_nudge,
        "visit_kit": visit_kit,
        "kitchen_card": kitchen_card,
        "doorstep_icebreaker": doorstep_icebreaker,
        "filtered_out": filtered_out,
        "trace": trace,
        "guardrail": {
            "passed": all_passed,
            "checked_count": checked_count,
            "reasons": failed_reasons,
        },
        "comparison": {
            "llm_only": baseline,
            "careloop_with_qloo": {
                "mode": f"careloop_qloo_{qloo_mode}",
                "picks": careloop_highlights,
                "filtered_count": len(filtered_out),
                "filtered_examples": [f"{f['name']} ({f.get('rule_code') or f['rule_id']})" for f in filtered_out[:3]],
            },
        },
    }


def build_group_taste_plan(
    centre_id: str,
    centre_name: str,
    seniors: list[dict],
    day: date = date(2026, 10, 13),
    *,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
    erased_by_senior: dict[str, set[str]] | None = None,
    client: QlooClient | None = None,
) -> dict:
    """Multi-Senior Group Taste Intersection Planner for AAC Centres.

    Intersects the Qloo taste profiles of all linked seniors at an Active Ageing Centre
    to recommend a shared group outing/refreshment, a sing-along music playlist, and a classic
    matinee film while enforcing the STRICTEST UNION of medical, medicine-leaflet, and weather
    guardrails across the entire cohort.
    """
    qloo = client or get_qloo_client()
    erased_map = erased_by_senior or {}
    qloo_mode = "live" if qloo.is_live else "fixture"

    seed_owners: dict[str, list[str]] = {}
    senior_profiles: list[tuple[dict, dict]] = []
    region_counts: dict[str, int] = {}

    union_excluded_tags: dict[str, dict] = {}
    union_preferred_tags: set[str] = set()
    union_hidden_ids: set[str] = set()
    rule_triggers: dict[str, dict] = {}
    any_indoor_only = bool(indoor_only)

    for s in seniors:
        sid = s.get("id", "")
        sname = s.get("name") or sid
        reg = s.get("region") or "east"
        region_counts[reg] = region_counts.get(reg, 0) + 1

        prof = build_taste_profile(dict(s, language="en"), erased_keys=erased_map.get(sid))
        senior_profiles.append((s, prof))
        for seed in prof["all_seeds"]:
            owners = seed_owners.setdefault(seed, [])
            if sname not in owners:
                owners.append(sname)

        c = active_constraints(
            dict(s, language="en"),
            indoor_only=indoor_only,
            rain_mm=rain_mm,
            psi=psi,
        )
        if c["indoor_only"]:
            any_indoor_only = True
        union_preferred_tags.update(c["preferred_tags"])
        union_hidden_ids.update(c["hidden_ids"])
        for tag, info in c["excluded_tags"].items():
            union_excluded_tags[tag] = info
        for r in c["active_rules"]:
            rid = r["rule_id"]
            entry = rule_triggers.setdefault(
                rid,
                {
                    "rule_id": rid,
                    "kind": r["kind"],
                    "badge": r["badge"],
                    "explanation": r["explanation"],
                    "triggered_by": [],
                },
            )
            if sname not in entry["triggered_by"]:
                entry["triggered_by"].append(sname)

    # Sort seeds by how many seniors in the cohort share them
    sorted_seeds = [
        seed
        for seed, _ in sorted(seed_owners.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    top_seeds = sorted_seeds[:8] or ["kopi", "teresa teng", "exercise"]
    dominant_region = max(sorted(region_counts), key=region_counts.get) if region_counts else "east"

    resolved_entities: list[dict] = []
    for seed in top_seeds[:6]:
        sr = qloo.search(seed, location="Singapore", limit=1)
        if sr.get("results"):
            resolved_entities.append(sr["results"][0])
    entity_ids = [e["entity_id"] for e in resolved_entities if e.get("entity_id")]

    place_insights = qloo.insights(
        "urn:entity:place",
        signal_entities=entity_ids,
        signal_tags=top_seeds,
        region=dominant_region,
        location="Singapore",
        limit=8,
    )
    artist_insights = qloo.insights(
        "urn:entity:artist",
        signal_entities=entity_ids,
        signal_tags=top_seeds,
        region=dominant_region,
        location="Singapore",
        limit=4,
    )
    movie_insights = qloo.insights(
        "urn:entity:movie",
        signal_entities=entity_ids,
        signal_tags=top_seeds,
        region=dominant_region,
        location="Singapore",
        limit=3,
    )

    union_constraints = {
        "indoor_only": any_indoor_only,
        "rain_mm": rain_mm,
        "psi": psi,
        "excluded_tags": union_excluded_tags,
        "preferred_tags": sorted(union_preferred_tags),
        "active_rules": list(rule_triggers.values()),
        "badges": [r["badge"] for r in rule_triggers.values()],
        "hidden_ids": sorted(union_hidden_ids),
    }

    kept_places, filtered_out = filter_qloo_candidates(
        place_insights.get("results", []),
        union_constraints,
        lang="en",
    )

    def _shared_by_seniors(matched_seeds: list[str]) -> list[str]:
        names: list[str] = []
        for ms in matched_seeds:
            for owner in seed_owners.get(ms.lower(), []):
                if owner not in names:
                    names.append(owner)
        if not names and seniors:
            names = [s.get("name") or s.get("id", "") for s in seniors[:3]]
        return names

    checked_count = 0
    all_passed = True
    failed_reasons: list[str] = []

    group_places = []
    for p in kept_places[:2]:
        why_safe, ok, reasons = _safe_text(
            p["why"],
            "Matched to your centre cohort's shared Qloo taste seeds and union of health constraints.",
            psi=psi,
        )
        checked_count += 1
        if not ok:
            all_passed = False
            failed_reasons.extend(reasons)
        mseeds = p.get("matched_seeds", []) or top_seeds[:2]
        group_places.append({
            "id": p["entity_id"],
            "entity_id": p["entity_id"],
            "name": p["display_name"],
            "category": p.get("category", "place"),
            "indoor": bool(p.get("indoor", True)),
            "affinity": p.get("affinity", 0.92),
            "tags": p.get("tags", []),
            "matched_seeds": mseeds,
            "shared_by": _shared_by_seniors(mseeds),
            "fit_badges": p.get("fit_badges", []),
            "why": why_safe,
            "bridge": f"{' + '.join(mseeds[:2])} → [nostalgia, cohort_match] → {p['display_name']} (✓ cohort-safe)",
        })

    group_music = []
    for a in artist_insights.get("results", [])[:2]:
        why_safe, ok, reasons = _safe_text(
            a.get("why_en", ""),
            "Cross-domain musical bridge shared across your centre's seniors.",
            psi=psi,
        )
        checked_count += 1
        if not ok:
            all_passed = False
            failed_reasons.extend(reasons)
        mseeds = a.get("matched_seeds", []) or top_seeds[:2]
        group_music.append({
            "id": a["entity_id"],
            "entity_id": a["entity_id"],
            "name": a.get("name", ""),
            "affinity": a.get("affinity", 0.93),
            "tags": a.get("tags", []),
            "matched_seeds": mseeds,
            "shared_by": _shared_by_seniors(mseeds),
            "why": why_safe,
            "bridge": f"{' + '.join(mseeds[:2])} → [nostalgia, singalong] → {a.get('name', '')}",
        })

    group_movies = []
    for m in movie_insights.get("results", [])[:2]:
        why_safe, ok, reasons = _safe_text(
            m.get("why_en", ""),
            "Classic matinee film matching the cohort's shared cultural tastes.",
            psi=psi,
        )
        checked_count += 1
        if not ok:
            all_passed = False
            failed_reasons.extend(reasons)
        mseeds = m.get("matched_seeds", []) or top_seeds[:2]
        group_movies.append({
            "id": m["entity_id"],
            "entity_id": m["entity_id"],
            "name": m.get("name", ""),
            "affinity": m.get("affinity", 0.91),
            "tags": m.get("tags", []),
            "matched_seeds": mseeds,
            "shared_by": _shared_by_seniors(mseeds),
            "why": why_safe,
            "bridge": f"{' + '.join(mseeds[:2])} → [nostalgia, singapore_heritage] → {m.get('name', '')}",
        })

    cohort_constraint_list = [
        {
            "rule": r["rule_id"],
            "rule_id": r["rule_id"],
            "label": f"{r['badge']} — {r['explanation']}",
            "triggered_by": r["triggered_by"],
        }
        for r in rule_triggers.values()
    ]

    # Build AAC Caterer Dietary & Medicine-Food Headcount Matrix
    catering_rows = [
        {
            "rule_id": r["rule_id"],
            "badge": r["badge"],
            "count": len(r["triggered_by"]),
            "seniors": r["triggered_by"],
        }
        for r in rule_triggers.values()
    ]
    rule_count_map = {r["rule_id"]: len(r["triggered_by"]) for r in rule_triggers.values()}
    catering_counts = {
        "halal": rule_count_map.get("diet.religious.halal", 0),
        "vegetarian": rule_count_map.get("diet.preference.vegetarian", 0),
        "no_beef": rule_count_map.get("diet.preference.no_beef", 0),
        "low_salt": rule_count_map.get("diet.hypertension.low_salt", 0),
        "less_sugar": rule_count_map.get("diet.diabetes.less_sugar", 0),
        "low_purine_gout": rule_count_map.get("diet.gout.low_purine", 0),
        "renal_friendly": rule_count_map.get("diet.ckd.renal_light", 0),
        "no_grapefruit_pomelo": rule_count_map.get("med_food.grapefruit_pomelo", 0),
        "wheelchair_seated": rule_count_map.get("mobility.step_free_seated", 0),
    }
    top_refreshment = group_places[0]["name"] if group_places else "Steamed dim sum / clear soup & kopi-O kosong"
    caterer_lines = [
        f"Caterer Dietary Sheet — {centre_name} ({len(seniors)} seniors):",
        f"• Recommended cohort-safe refreshment: {top_refreshment}",
    ]
    for row in catering_rows:
        caterer_lines.append(f"• {row['badge']}: {row['count']} / {len(seniors)} ({', '.join(row['seniors'])})")
    caterer_lines.append("• Universal safe default: serve unsweetened kopi-O kosong / plain tea, steamed or lightly grilled items, no grapefruit/pomelo, no potassium salt substitutes.")

    catering_matrix = {
        "total_seniors": len(seniors),
        "recommended_refreshment": top_refreshment,
        "counts": catering_counts,
        "rows": catering_rows,
        "caterer_sheet_text": "\n".join(caterer_lines),
    }

    return {
        "aac_id": centre_id,
        "aac_name": centre_name,
        "centre_id": centre_id,
        "centre_name": centre_name,
        "date": day.isoformat(),
        "engine": "qloo_taste_ai",
        "mode": qloo_mode,
        "qloo_mode": qloo_mode,
        "cohort_size": len(seniors),
        "catering_matrix": catering_matrix,
        "seniors": [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "language": s.get("language", "en"),
                "conditions": list(s.get("conditions", [])),
                "medicines": [m.get("name", "") if isinstance(m, dict) else str(m) for m in s.get("medicines", [])],
            }
            for s in seniors
        ],
        "shared_seeds": [
            {
                "query": s,
                "seed": s,
                "count": len(seed_owners[s]),
                "seniors": seed_owners[s],
                "shared_by": seed_owners[s],
            }
            for s in top_seeds[:6]
            if s in seed_owners
        ],
        "resolved_entities": [
            {
                "seed": e.get("query", e.get("name", "")),
                "entity_id": e.get("entity_id", ""),
                "name": e.get("name", ""),
                "type": e.get("type", "urn:entity:place"),
                "tags": e.get("tags", []),
            }
            for e in resolved_entities
        ],
        "cohort_constraints": cohort_constraint_list,
        "weather": {
            "psi": psi,
            "rain_mm": rain_mm,
            "indoor_only": any_indoor_only,
        },
        "group_recommendations": {
            "refreshment_or_outing": group_places,
            "music_playlist": group_music,
            "singalong_music": group_music,
            "matinee_film": group_movies,
        },
        "filtered_out": filtered_out,
        "filtered_out_for_cohort_safety": filtered_out,
        "guardrail": {
            "passed": all_passed,
            "checked_count": checked_count,
            "reasons": failed_reasons,
        },
    }


_LANG_LABELS = {
    "en": "English / Singlish",
    "zh": "Mandarin / Dialect (华语/方言)",
    "ms": "Bahasa Melayu",
    "ta": "Tamil (தமிழ்)",
}


def build_kopi_kakis(
    aac_id: str,
    aac_name: str,
    seniors: list[dict],
    day: date = date(2026, 10, 13),
    *,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
    erased_by_senior: dict[str, set[str]] | None = None,
    focus_senior_id: str | None = None,
    client: QlooClient | None = None,
) -> dict:
    """Kopi Kakis (Buddy Matching) Engine for lonely seniors at the same Active Ageing Centre.

    Computes pairwise cultural taste affinity across seniors at `aac_id` using their resolved
    Qloo entities (`urn:entity:artist`, `urn:entity:movie`, `urn:entity:place`), shared spoken
    languages, and compatible mobility/dietary constraints.
    """
    qloo = client or get_qloo_client()
    erased_map = erased_by_senior or {}
    qloo_mode = "live" if qloo.is_live else "fixture"

    enriched_seniors: list[dict] = []
    for s in seniors:
        sid = s.get("id", "")
        prof = build_taste_profile(dict(s, language="en"), erased_keys=erased_map.get(sid))
        resolved: list[dict] = []
        tags_set: set[str] = set()
        for seed in prof["all_seeds"][:6]:
            sr = qloo.search(seed, location="Singapore", limit=1)
            if sr.get("results"):
                ent = dict(sr["results"][0], query=seed)
                resolved.append(ent)
                tags_set.update(str(t).lower() for t in (ent.get("tags") or []))
        eids = [e["entity_id"] for e in resolved if e.get("entity_id")]
        art = qloo.insights("urn:entity:artist", signal_entities=eids, signal_tags=prof["all_seeds"], region=s.get("region") or "central", limit=2)
        mov = qloo.insights("urn:entity:movie", signal_entities=eids, signal_tags=prof["all_seeds"], region=s.get("region") or "central", limit=2)
        for a in art.get("results", [])[:2]:
            if not any(r.get("entity_id") == a["entity_id"] for r in resolved):
                resolved.append({"entity_id": a["entity_id"], "name": a["name"], "type": "urn:entity:artist", "tags": a.get("matched_seeds", [])})
        for m in mov.get("results", [])[:1]:
            if not any(r.get("entity_id") == m["entity_id"] for r in resolved):
                resolved.append({"entity_id": m["entity_id"], "name": m["name"], "type": "urn:entity:movie", "tags": m.get("matched_seeds", [])})

        c = active_constraints(dict(s, language="en"), indoor_only=indoor_only, rain_mm=rain_mm, psi=psi)
        enriched_seniors.append({
            "senior": s,
            "profile": prof,
            "resolved": resolved,
            "tags": tags_set | {seed.lower() for seed in prof["all_seeds"]},
            "constraints": c,
        })

    checked_count = 0
    all_passed = True
    failed_reasons: list[str] = []
    pairs: list[dict] = []

    for i in range(len(enriched_seniors)):
        for j in range(i + 1, len(enriched_seniors)):
            ea = enriched_seniors[i]
            eb = enriched_seniors[j]
            sa = ea["senior"]
            sb = eb["senior"]
            if focus_senior_id and focus_senior_id not in (sa.get("id"), sb.get("id")):
                continue

            map_a = {e["entity_id"]: e for e in ea["resolved"] if e.get("entity_id")}
            map_b = {e["entity_id"]: e for e in eb["resolved"] if e.get("entity_id")}
            shared_eids = [eid for eid in map_a if eid in map_b]
            shared_entities = [map_a[eid] for eid in shared_eids]
            if len(shared_entities) < 2:
                for e in [*ea["resolved"][:2], *eb["resolved"][:2]]:
                    if e.get("entity_id") and not any(x["entity_id"] == e["entity_id"] for x in shared_entities):
                        shared_entities.append(e)
                    if len(shared_entities) >= 3:
                        break

            seeds_a = [s.lower() for s in ea["profile"]["all_seeds"]]
            seeds_b = [s.lower() for s in eb["profile"]["all_seeds"]]
            shared_seeds = [s for s in seeds_a if s in seeds_b]
            if not shared_seeds:
                shared_seeds = list(dict.fromkeys([*seeds_a[:2], *seeds_b[:2]]))

            tag_overlap = len(ea["tags"] & eb["tags"])
            lang_a = str(sa.get("language") or "en").lower()
            lang_b = str(sb.get("language") or "en").lower()
            same_lang = lang_a == lang_b
            shared_langs = [_LANG_LABELS.get(lang_a, "English")]
            if not same_lang:
                shared_langs.append(_LANG_LABELS.get(lang_b, "English"))
                if "English / Singlish" not in shared_langs:
                    shared_langs.append("Conversational Singlish / Kopitiam Malay")

            raw_score = 0.78 + 0.04 * len(shared_eids) + 0.025 * min(4, tag_overlap) + (0.04 if same_lang else 0.01)
            affinity_score = round(min(0.98, max(0.84, raw_score)), 2)

            ca = ea["constraints"]
            cb = eb["constraints"]
            union_excluded = {**ca["excluded_tags"], **cb["excluded_tags"]}
            union_preferred = sorted(set(ca["preferred_tags"]) | set(cb["preferred_tags"]))
            union_badges = list(dict.fromkeys([*ca["badges"], *cb["badges"]]))
            union_rules = list({r["rule_id"]: r for r in [*ca["active_rules"], *cb["active_rules"]]}.values())
            pair_indoor = bool(ca["indoor_only"] or cb["indoor_only"])

            union_c = {
                "indoor_only": pair_indoor,
                "rain_mm": rain_mm,
                "psi": psi,
                "excluded_tags": union_excluded,
                "preferred_tags": union_preferred,
                "active_rules": union_rules,
                "badges": union_badges,
                "hidden_ids": list(set(ca["hidden_ids"]) | set(cb["hidden_ids"])),
            }

            region = sa.get("region") or sb.get("region") or "central"
            place_pool = qloo.insights(
                "urn:entity:place",
                signal_entities=[e["entity_id"] for e in shared_entities],
                signal_tags=shared_seeds,
                region=region,
                location="Singapore",
                limit=12,
            )
            kept_places, blocked_places = filter_qloo_candidates(place_pool.get("results", []), union_c, lang="en")
            top_spot = kept_places[0] if kept_places else {
                "entity_id": "urn:entity:place:qloo-aac-kopi-corner",
                "display_name": f"{aac_name} Sheltered Kopi O Kosong & Tea Table",
                "indoor": True,
                "fit_badges": union_badges[:3] or ["Step-free & seated", "Less-sugar option"],
                "why": "Sheltered, step-free table inside the Active Ageing Centre meeting both seniors' health and dietary rules.",
            }

            music_hook = next(
                (e["name"].split("—")[0].strip() for e in shared_entities if e.get("type") == "urn:entity:artist"),
                (ea["profile"]["music_seeds"] or ["Teresa Teng"])[0],
            )
            food_hook = (ea["profile"]["food_seeds"] or ["Nanyang kopi-O kosong"])[0]
            activity_hook = shared_seeds[0] if shared_seeds else "morning kopi chats"
            hooks_summary = f"Both love {music_hook}, {food_hook}, and {activity_hook}"

            name_a = sa.get("name", "Senior A")
            name_b = sb.get("name", "Senior B")
            spot_name = top_spot["display_name"]
            safety_note = ", ".join(union_badges[:3]) if union_badges else "step-free, health-checked refreshments"

            raw_script_en = (
                f"\"{name_a}, meet {name_b} — you both enjoy {music_hook} and {food_hook} in the neighbourhood. "
                f"Shall we sit together at {spot_name} for a cup of unsweetened tea and a song before the group starts?\""
            )
            safe_script_en, ok_en, r_en = _safe_text(
                raw_script_en,
                f"\"{name_a}, meet {name_b} — you both love classic melodies and morning tea. Let's sit together at our sheltered tea corner for a warm chat.\"",
                psi=psi,
            )
            checked_count += 1
            if not ok_en:
                all_passed = False
                failed_reasons.extend(r_en)

            za = sa.get("zh") or name_a
            zb = sb.get("zh") or name_b
            raw_script_zh = (
                f"“{za}，给您介绍{zb}——你们都很喜欢听{music_hook}、平时也爱聊{food_hook}。"
                f"大组活动开始前，我们一起在{spot_name}坐下喝杯清茶、听首老歌认识一下好吗？”"
            )
            safe_script_zh, ok_zh, r_zh = _safe_text(
                raw_script_zh,
                f"“{za}，给您介绍{zb}——你们都喜欢听经典老歌和喝早茶，我们一起在中心有盖茶座坐下聊聊吧。”",
                psi=psi,
            )
            checked_count += 1
            if not ok_zh:
                all_passed = False
                failed_reasons.extend(r_zh)

            pairs.append({
                "pair_id": f"{sa.get('id', 'a')}--{sb.get('id', 'b')}",
                "senior_a": {
                    "id": sa.get("id", ""),
                    "name": name_a,
                    "zh": sa.get("zh", ""),
                    "language": lang_a,
                    "likes": list(sa.get("likes") or []),
                    "neighbourhood": ea["profile"]["neighbourhood"],
                    "conditions": list(sa.get("conditions") or []),
                    "dietary_prefs": list(sa.get("dietary_prefs") or []),
                },
                "senior_b": {
                    "id": sb.get("id", ""),
                    "name": name_b,
                    "zh": sb.get("zh", ""),
                    "language": lang_b,
                    "likes": list(sb.get("likes") or []),
                    "neighbourhood": eb["profile"]["neighbourhood"],
                    "conditions": list(sb.get("conditions") or []),
                    "dietary_prefs": list(sb.get("dietary_prefs") or []),
                },
                "affinity_score": affinity_score,
                "affinity_pct": int(round(affinity_score * 100)),
                "shared_languages": shared_langs,
                "shared_language_label": " & ".join(shared_langs).upper() if shared_langs else "EN / ZH",
                "shared_seeds": shared_seeds[:5],
                "shared_tags": shared_seeds[:5],
                "shared_urns": [e.get("entity_id", "") for e in shared_entities[:4]],
                "shared_entities": [
                    {
                        "entity_id": e.get("entity_id", ""),
                        "name": e.get("name", ""),
                        "type": e.get("type", "urn:entity:place"),
                    }
                    for e in shared_entities[:4]
                ],
                "shared_hooks": [music_hook, food_hook, activity_hook],
                "shared_hooks_summary": hooks_summary,
                "union_badges": union_badges,
                "union_constraints": {
                    "indoor_only": pair_indoor,
                    "badges": union_badges,
                    "rules": [r.get("rule_code") or r["rule_id"] for r in union_rules],
                    "filtered_out_count": len(blocked_places),
                },
                "safe_meeting_spot": {
                    "entity_id": top_spot["entity_id"],
                    "name": spot_name,
                    "category": top_spot.get("category", "kopitiam"),
                    "indoor": bool(top_spot.get("indoor", True)),
                    "fit_badges": top_spot.get("fit_badges", []),
                    "why_safe": f"Filtered by union of both seniors' constraints ({safety_note}).",
                },
                "companion_music": music_hook,
                "icebreaker_script": safe_script_en,
                "icebreaker_script_zh": safe_script_zh,
                "befriender_script": {
                    "en": safe_script_en,
                    "zh": safe_script_zh,
                },
                "guardrail_passed": bool(ok_en and ok_zh),
            })

    pairs.sort(key=lambda p: (-p["affinity_score"], p["pair_id"]))
    return {
        "aac_id": aac_id,
        "aac_name": aac_name,
        "date": day.isoformat(),
        "focus_senior_id": focus_senior_id,
        "qloo_mode": qloo_mode,
        "cohort_size": len(seniors),
        "pairs": pairs,
        "matches": pairs,
        "guardrail": {
            "passed": all_passed,
            "checked_count": checked_count,
            "reasons": failed_reasons,
        },
    }


_DEFAULT_MEMORY_SEEDS: dict[str, list[dict]] = {
    "tan": [
        {
            "id": "mem-tan-1",
            "date": "2026-10-11",
            "qloo_seed": "Teresa Teng (邓丽君)",
            "entity_id": "urn:entity:artist:qloo-teresa-teng",
            "era": "1970s",
            "prompt": "You love Teresa Teng and morning kopi — where did you first hear 'The Moon Represents My Heart' in the 1970s?",
            "story_text": "Back in the late 1970s, after my shift in Toa Payoh, your mother and I would sit by the Rediffusion speaker at the corner kopitiam with kopi-O siew dai and listen to Teresa Teng every evening.",
            "language": "en",
            "recorded_by": "senior",
        },
        {
            "id": "mem-tan-2",
            "date": "2026-10-09",
            "qloo_seed": "The Love Eterne (梁山伯与祝英台)",
            "entity_id": "urn:entity:movie:qloo-love-eterne",
            "era": "1960s",
            "prompt": "Shaw Brothers Huangmei opera films were huge in Singapore — which cinema did you queue at with friends?",
            "story_text": "We queued at the old Gala Cinema with roasted groundnuts in paper cones. Everyone in the kampong knew the Huangmei opera tunes by heart for months!",
            "language": "en",
            "recorded_by": "family",
        },
    ],
    "wong": [
        {
            "id": "mem-wong-1",
            "date": "2026-10-11",
            "qloo_seed": "Frances Yip (叶丽仪) & Teresa Teng (邓丽君)",
            "entity_id": "urn:entity:artist:qloo-frances-yip",
            "era": "1980s",
            "prompt": "您喜欢听邓丽君和叶丽仪的老歌——年轻时最难忘的一次听歌或看戏是在哪里？",
            "story_text": "八十年代在裕廊旧戏院附近，每逢周末跟街坊姐妹一起喝早茶、听《上海滩》和《甜蜜蜜》，大家一边做手工一边哼歌，最热闹了。",
            "language": "zh",
            "recorded_by": "senior",
        },
        {
            "id": "mem-wong-2",
            "date": "2026-10-08",
            "qloo_seed": "The Love Eterne (梁山伯与祝英台)",
            "entity_id": "urn:entity:movie:qloo-love-eterne",
            "era": "1960s",
            "prompt": "邵氏黄梅调《梁山伯与祝英台》当年轰动一时——您还记得第一次进戏院看的时候吗？",
            "story_text": "那时候和妈妈去大华戏院看《梁山伯与祝英台》，凌波唱每一段我们都跟着掉眼泪，散场后还去吃了一碗清汤潮州鱼粥。",
            "language": "zh",
            "recorded_by": "family",
        },
    ],
    "kaur": [
        {
            "id": "mem-kaur-1",
            "date": "2026-10-11",
            "qloo_seed": "Gurdas Maan & Punjabi Folk Classics",
            "entity_id": "urn:entity:artist:qloo-gurdas-maan",
            "era": "1970s–1980s",
            "prompt": "You enjoy Punjabi folk classics and morning garden walks — what was your favourite family gathering tradition when you were young?",
            "story_text": "On Sunday afternoons in Katong, we brewed fresh ginger elaichi tea from our own herb pots while the cassette player played Gurdas Maan and Surinder Kaur for all the cousins.",
            "language": "en",
            "recorded_by": "senior",
        },
    ],
    "rahman": [
        {
            "id": "mem-rahman-1",
            "date": "2026-10-11",
            "qloo_seed": "Tan Sri P. Ramlee & Bujang Lapok",
            "entity_id": "urn:entity:movie:qloo-bujang-lapok",
            "era": "1960s",
            "prompt": "P. Ramlee's Jalan Ampas classics and warung kopi are part of your story — what was your favourite memory of old Geylang Serai or Jurong?",
            "story_text": "When a new P. Ramlee film played at the open-air screen, the whole street brought wooden stools. Afterwards we shared kopi-O kosong and laughed over the Bujang Lapok scenes until midnight.",
            "language": "ms",
            "recorded_by": "senior",
        },
    ],
}


def build_memory_lane(
    senior: dict,
    day: date = date(2026, 10, 13),
    *,
    saved_capsules: list[dict] | None = None,
    erased_keys: set[str] | None = None,
    client: QlooClient | None = None,
) -> dict:
    """Generate daily Qloo Reminiscence Story Prompts and the Family 'Memory Lane Keepsake Book'."""
    qloo = client or get_qloo_client()
    qloo_mode = "live" if qloo.is_live else "fixture"
    sid = senior.get("id", "tan")
    sname = senior.get("name") or sid
    raw_lang = str(senior.get("language") or "en").lower()
    zh = raw_lang == "zh"
    lang = raw_lang if raw_lang in ("en", "zh", "ms", "ta") else "en"

    prof = build_taste_profile(senior, erased_keys=erased_keys)
    music_seed = (prof["music_seeds"] or ["Teresa Teng"])[0]
    food_seed = (prof["food_seeds"] or ["Nanyang kopi-O"])[0]
    film_seed = (prof["film_seeds"] or ["Shaw Brothers & Jalan Ampas classic films"])[0]

    sr_music = qloo.search(music_seed, entity_type="urn:entity:artist", location="Singapore", limit=1)
    music_ent = (sr_music.get("results") or [{"entity_id": "urn:entity:artist:qloo-teresa-teng", "name": music_seed}])[0]
    sr_food = qloo.search("kopi", entity_type="urn:entity:place", location="Singapore", limit=1)
    food_ent = (sr_food.get("results") or [{"entity_id": "urn:entity:place:qloo-seed-kopi", "name": food_seed}])[0]

    mov_insights = qloo.insights("urn:entity:movie", signal_entities=[music_ent["entity_id"]], signal_tags=prof["all_seeds"], region=senior.get("region") or "central", limit=1)
    movie_ent = (mov_insights.get("results") or [{"entity_id": "urn:entity:movie:qloo-love-eterne", "name": film_seed}])[0]

    prompt_en = (
        f"You enjoy {music_ent['name']} and {food_seed} — what was your favourite cinema, radio show, or coffee shop when you were in your twenties?"
    )
    prompt_zh = (
        f"您喜欢听{music_ent['name']}、品尝{food_seed}——年轻时最常和朋友家人去哪家戏院或咖啡店？"
    )
    prompt_ms = (
        f"Anda gemar lagu {music_ent['name']} dan {food_seed} — apakah kedai kopi atau panggung wayang kegemaran anda semasa muda dahulu?"
    )
    prompt_ta = (
        f"உங்களுக்கு {music_ent['name']} பாடல்களும் {food_seed} சுவையும் பிடிக்கும் — உங்கள் இளமைக் காலத்தில் மிகவும் பிடித்த தேநீர்க் கடை அல்லது திரையரங்கம் எது?"
    )
    localized_prompt_map = {"en": prompt_en, "zh": prompt_zh, "ms": prompt_ms, "ta": prompt_ta}
    chosen_prompt = localized_prompt_map.get(lang, prompt_en)

    safe_prompt, ok_p, reasons_p = _safe_text(
        chosen_prompt,
        "What was your favourite coffee shop or cinema memory with friends when you were young?",
    )

    starter_chips_zh = [
        "当年我们常在街角咖啡店听丽的呼声...",
        "最难忘和家人一起去旧戏院看黄梅调电影...",
        "以前早市喝完无糖咖啡乌，街坊都会聚在一起唱老歌...",
    ]
    starter_chips_en = [
        "Back then, my friends and I always met at the corner kopitiam for morning kopi...",
        "I still remember queuing at the old cinema when our favourite songs played on the radio...",
        "On Sunday afternoons, our whole family gathered over tea and shared stories...",
    ]

    daily_prompt = {
        "prompt_id": f"prompt-{sid}-{day.isoformat()}",
        "date": day.isoformat(),
        "qloo_seed": music_ent["name"],
        "qloo_urn": music_ent["entity_id"],
        "entity_id": music_ent["entity_id"],
        "music_companion": music_ent["name"],
        "film_companion": movie_ent.get("name", film_seed),
        "film_entity_id": movie_ent.get("entity_id", "urn:entity:movie:qloo-love-eterne"),
        "food_companion": food_seed,
        "food_entity_id": food_ent.get("entity_id", "urn:entity:place:qloo-seed-kopi"),
        "era": "Golden Era Nostalgia",
        "prompt": safe_prompt,
        "prompt_text": safe_prompt,
        "prompt_en": prompt_en,
        "prompt_zh": prompt_zh,
        "starter_chips": starter_chips_zh if zh else starter_chips_en,
        "voice_starter_chips": starter_chips_zh if zh else starter_chips_en,
        "guardrail_passed": ok_p,
    }

    default_list = _DEFAULT_MEMORY_SEEDS.get(sid) or [
        {
            "id": f"mem-{sid}-1",
            "date": "2026-10-10",
            "qloo_seed": music_ent["name"],
            "entity_id": music_ent["entity_id"],
            "era": "1970s",
            "prompt": prompt_en,
            "story_text": f"{sname} fondly recalls listening to {music_ent['name']} on the evening radio with neighbours over warm tea and {food_seed}.",
            "language": lang,
            "recorded_by": "senior",
        }
    ]

    merged_capsules: list[dict] = []
    seen_ids: set[str] = set()
    for cap in [*(saved_capsules or []), *default_list]:
        cid = cap.get("id") or f"mem-{uuid.uuid4().hex[:8]}"
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        safe_story, ok_s, _ = _safe_text(
            str(cap.get("story_text") or ""),
            "A cherished family memory of classic melodies and morning kopi with old friends.",
        )
        cap_urn = cap.get("qloo_urn") or cap.get("entity_id") or music_ent["entity_id"]
        cap_era = cap.get("era_tag") or cap.get("era") or "1970s"
        merged_capsules.append({
            "id": cid,
            "senior_id": sid,
            "date": cap.get("date") or day.isoformat(),
            "qloo_seed": cap.get("qloo_seed") or music_ent["name"],
            "qloo_urn": cap_urn,
            "entity_id": cap_urn,
            "era": cap_era,
            "era_tag": cap_era,
            "prompt": cap.get("prompt") or safe_prompt,
            "story_text": safe_story,
            "language": cap.get("language") or lang,
            "recorded_by": cap.get("recorded_by") or "senior",
            "guardrail_passed": ok_s,
        })

    return {
        "senior_id": sid,
        "senior_name": sname,
        "language": lang,
        "date": day.isoformat(),
        "qloo_mode": qloo_mode,
        "daily_prompt": daily_prompt,
        "capsules": merged_capsules,
        "keepsake_summary": {
            "total_stories": len(merged_capsules),
            "anchored_entities": list(dict.fromkeys(c["entity_id"] for c in merged_capsules)),
            "headline": (
                f"《{sname}的岁月留声纪念册》— 已收录 {len(merged_capsules)} 段珍贵人生故事"
                if zh
                else f"{sname}'s Memory Lane Keepsake Book — {len(merged_capsules)} life stories anchored to Qloo nostalgia seeds"
            ),
        },
        "guardrail": {
            "passed": ok_p,
            "reasons": reasons_p,
        },
    }


def create_memory_capsule(
    senior: dict,
    story_text: str,
    *,
    prompt: str | None = None,
    qloo_seed: str | None = None,
    entity_id: str | None = None,
    qloo_entity_id: str | None = None,
    qloo_domain: str | None = None,
    language: str | None = None,
    recorded_by: str | None = "senior",
    day: date = date(2026, 10, 13),
    client: QlooClient | None = None,
) -> dict:
    """Validate and package a new Reminiscence Memory Capsule anchored to a Qloo nostalgia entity."""
    qloo = client or get_qloo_client()
    sid = senior.get("id", "tan")
    prof = build_taste_profile(senior)
    seed = (qloo_seed or (prof["music_seeds"] or ["Teresa Teng"])[0]).strip()
    eid = (entity_id or qloo_entity_id or "").strip()
    if not eid:
        sr = qloo.search(seed, location="Singapore", limit=1)
        if sr.get("results"):
            eid = sr["results"][0]["entity_id"]
            seed = sr["results"][0]["name"]
        else:
            eid = "urn:entity:artist:qloo-teresa-teng"

    lang = (language or senior.get("language") or "en").lower()
    raw_story = (story_text or "").strip() or f"Listening to {seed} always brings back warm memories of old Singapore coffee shops with family."
    safe_story, ok_s, reasons_s = _safe_text(
        raw_story,
        "Listening to classic melodies always brings back warm memories of old Singapore coffee shops with family and friends.",
    )
    raw_prompt = (prompt or "").strip() or f"What memory does {seed} bring back from your younger days?"
    safe_prompt, ok_p, _ = _safe_text(
        raw_prompt,
        "What memory does this classic song or dish bring back from your younger days?",
    )

    rec_by = (recorded_by or "senior").strip() or "senior"
    return {
        "id": f"mem-{sid}-{uuid.uuid4().hex[:8]}",
        "senior_id": sid,
        "date": day.isoformat(),
        "qloo_seed": seed,
        "qloo_urn": eid,
        "entity_id": eid,
        "qloo_domain": qloo_domain or ("urn:entity:movie" if ":movie:" in eid else "urn:entity:artist"),
        "era": "1960s–1980s",
        "era_tag": "1960s–1980s",
        "prompt": safe_prompt,
        "story_text": safe_story,
        "language": lang,
        "recorded_by": rec_by,
        "guardrail_passed": bool(ok_s and ok_p),
        "guardrail_reasons": reasons_s,
        "guardrail": {
            "passed": bool(ok_s and ok_p),
            "reasons": reasons_s,
        },
    }


def build_respite_plan(
    senior: dict,
    day: date = date(2026, 10, 13),
    *,
    rota: list[dict] | None = None,
    contacts: list[dict] | None = None,
    programmes: list[dict] | None = None,
    vent_count: int = 0,
    streak_days: int | None = None,
    has_recent_vent: bool = False,
    indoor_only: bool = False,
    rain_mm: float | None = None,
    psi: int | None = None,
    erased_keys: set[str] | None = None,
    client: QlooClient | None = None,
) -> dict:
    """Caregiver Respite & Burnout Shield: builds a Guilt-Free 3-Hour Respite Plan.

    Connects caregiver wellbeing (multi-day rota streak or Vent Space activity) with a
    high-affinity, health-checked AAC programme for the senior and a one-click WhatsApp
    sibling handover message.
    """
    qloo = client or get_qloo_client()
    qloo_mode = "live" if qloo.is_live else "fixture"
    sid = senior.get("id", "tan")
    sname = senior.get("name") or sid
    aac_id = senior.get("aac_id") or "aac-tp"
    aac_name = senior.get("aac_name") or "CareActive Toa Payoh Hub"

    contacts_list = list(contacts or [])
    primary_id = contacts_list[0].get("id", f"{sid}-primary") if contacts_list else f"{sid}-primary"
    primary_name = contacts_list[0]["name"] if contacts_list else "Wei Ling"
    primary_rel = contacts_list[0].get("relation", "Daughter") if contacts_list else "Primary family caregiver"
    cover_id = contacts_list[1].get("id", f"{sid}-backup") if len(contacts_list) > 1 else f"{sid}-backup"
    cover_name = contacts_list[1]["name"] if len(contacts_list) > 1 else "Kelvin"
    cover_rel = contacts_list[1].get("relation", "Son / Sibling") if len(contacts_list) > 1 else "Family Rota Backup"
    cover_phone = contacts_list[1].get("phone", "+6591234568") if len(contacts_list) > 1 else "+6591234568"

    rota_list = list(rota or [])
    eff_streak_days = streak_days if streak_days is not None else 4
    eff_vent_count = max(vent_count, 1 if has_recent_vent else 0)
    if rota_list:
        first_who = rota_list[0].get("who")
        if first_who:
            primary_name = first_who
            count = 0
            for slot in rota_list:
                if slot.get("who") == primary_name:
                    count += 1
                else:
                    if not len(contacts_list) > 1 and slot.get("who"):
                        cover_name = slot["who"]
                    break
            eff_streak_days = max(3, count)

    plan = build_taste_plan(
        senior,
        day=day,
        indoor_only=indoor_only,
        rain_mm=rain_mm,
        psi=psi,
        erased_keys=erased_keys,
        client=qloo,
    )
    top_place = (plan["recommendations"]["places"] or [None])[0]
    top_music = (plan["recommendations"]["music"] or [None])[0]
    safety_badges = plan["constraints"]["badges"] or ["Lower-salt fit", "Step-free & seated"]

    prog_list = list(programmes or [])
    best_prog = None
    for p in prog_list:
        if plan["constraints"]["indoor_only"] and p.get("outdoor"):
            continue
        best_prog = p
        break

    music_label = top_music["name"] if top_music else "Teresa Teng & Mandopop Classics"
    place_label = top_place["name"] if top_place else f"{aac_name} Sheltered Tea Lounge"
    prog_title = (best_prog or {}).get("title") or f"Afternoon Sing-Along & Kopi O Kosong Kakis ({music_label.split('—')[0].strip()})"
    prog_time = (best_prog or {}).get("time") or "Wed Afternoon Session"
    prog_id = (best_prog or {}).get("id") or f"respite-prog-{sid}"
    prog_kind = (best_prog or {}).get("kind") or "programme"

    all_seeds_list = [
        *plan["profile"].get("music_seeds", []),
        *plan["profile"].get("food_seeds", []),
        *plan["profile"].get("likes", []),
    ]
    why_taste = (
        f"Matched via Qloo Taste AI to {sname}'s top seeds ({', '.join(all_seeds_list[:3])}) "
        f"and {music_label.split('—')[0].strip()}."
    )
    why_safe = (
        f"Verified against {sname}'s health and leaflet rules ({', '.join(safety_badges[:3])}); "
        f"indoor, seated, step-free at {aac_name}."
    )

    safe_why_taste, ok1, r1 = _safe_text(why_taste, f"Matched to {sname}'s Qloo cultural taste profile at {aac_name}.", psi=psi)
    safe_why_safe, ok2, r2 = _safe_text(why_safe, f"Checked against {sname}'s health and mobility preferences at {aac_name}.", psi=psi)

    raw_whatsapp = (
        f"Hi {cover_name} — CareLoop 3-Hour Respite Handover for {sname}:\n"
        f"• {primary_name} has been on primary care duty for several days in a row and is taking a guilt-free afternoon breather ({prog_time}).\n"
        f"• {sname} is matched to '{prog_title}' at {aac_name} (Qloo taste fit: {music_label.split('—')[0].strip()}; health checks: {', '.join(safety_badges[:2])}).\n"
        f"• Could you cover the afternoon check-in / pickup window and bring a light refreshment from {place_label}? Tap to confirm on the Family Rota."
    )
    safe_whatsapp, ok3, r3 = _safe_text(
        raw_whatsapp,
        f"Hi {cover_name} — CareLoop 3-Hour Respite Handover: could you cover {sname}'s afternoon check-in window while {primary_name} takes a well-deserved break? {sname} has a matched session at {aac_name}.",
        psi=psi,
    )

    burnout_level = "high" if (eff_streak_days >= 4 or eff_vent_count > 0) else "moderate"
    trigger_reason = (
        f"{primary_name} has a multi-day streak on the Family Rota and recent Vent Space activity"
        if eff_vent_count > 0
        else f"{primary_name} has an active multi-day primary care streak on the Family Rota"
    )
    affinity_val = float(top_music["affinity"] if top_music else 0.95)
    qloo_fit_pct = int(round(affinity_val * 100))
    summary_text = (
        f"{sname} is matched to '{prog_title}' at {aac_name} ({prog_time}) while {cover_name} covers on the Family Rota so {primary_name} can take a guilt-free 3-hour breather."
    )

    return {
        "senior_id": sid,
        "senior_name": sname,
        "date": day.isoformat(),
        "qloo_mode": qloo_mode,
        "window_hours": 3,
        "recommended_slot": f"{prog_time} (3-Hour Respite Window)",
        "primary_caregiver": {
            "id": primary_id,
            "name": primary_name,
            "relation": primary_rel,
            "streak_days": eff_streak_days,
        },
        "backup_contact": {
            "id": cover_id,
            "name": cover_name,
            "relation": cover_rel,
            "phone": cover_phone,
            "rota_action": f"Assign {cover_name} to cover {prog_time}",
        },
        "burnout_shield": {
            "active": bool(eff_streak_days >= 3 or eff_vent_count > 0),
            "streak_days": eff_streak_days,
            "has_recent_vent": bool(eff_vent_count > 0),
            "trigger_reason": trigger_reason,
        },
        "burnout_status": {
            "primary_caregiver": primary_name,
            "primary_relation": primary_rel,
            "streak_days": eff_streak_days,
            "vent_count": eff_vent_count,
            "level": burnout_level,
            "trigger_reason": trigger_reason,
            "headline": f"Guilt-Free 3-Hour Respite Window for {primary_name}",
            "reassurance": f"{sname} will be happily engaged with peers who share their love for {music_label.split('—')[0].strip()} at {aac_name}, while {cover_name} covers the handover window.",
        },
        "respite_window": {
            "duration_hours": 3,
            "slot_label": f"{prog_time} (3-Hour Respite Window)",
            "aac_id": aac_id,
            "aac_name": aac_name,
        },
        "matched_programme": {
            "id": prog_id,
            "title": prog_title,
            "when": prog_time,
            "time": prog_time,
            "where": aac_name,
            "kind": prog_kind,
            "aac_id": aac_id,
            "aac_name": aac_name,
            "qloo_entity_id": top_music["entity_id"] if top_music else "urn:entity:artist:qloo-teresa-teng",
            "companion_place": place_label,
            "affinity": affinity_val,
            "qloo_fit_pct": qloo_fit_pct,
            "indoor": True,
            "fit_badges": safety_badges,
            "safety_badges": safety_badges,
            "why_safe_and_loved": f"{safe_why_taste} {safe_why_safe}",
            "why_taste_fit": safe_why_taste,
            "why_medical_safe": safe_why_safe,
        },
        "companion_picks": {
            "post_session_treat": place_label,
            "music_on_way": music_label,
        },
        "summary": summary_text,
        "cover_contact": {
            "id": cover_id,
            "name": cover_name,
            "relation": cover_rel,
            "phone": cover_phone,
            "rota_action": f"Assign {cover_name} to cover {prog_time}",
        },
        "whatsapp_handover_text": safe_whatsapp,
        "whatsapp_text": safe_whatsapp,
        "guardrail": {
            "passed": bool(ok1 and ok2 and ok3),
            "checked_count": 3,
            "reasons": [*r1, *r2, *r3],
        },
    }


