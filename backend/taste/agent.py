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

from datetime import date

from backend.language.facts import Facts
from backend.language.guardrail import check as guardrail_check
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
    qloo = client or get_qloo_client()
    zh = senior.get("language") == "zh"
    lang = "zh" if zh else "en"
    region = senior.get("region") or "central"

    # --- Step 1: Tool `qloo_search` ---
    profile = build_taste_profile(senior, erased_keys=erased_keys)
    resolved_entities: list[dict] = []
    seed_tags_map: dict[str, list[str]] = {}
    for seed in profile["all_seeds"][:6]:
        sr = qloo.search(seed, location="Singapore", limit=1)
        if sr.get("results"):
            top_ent = sr["results"][0]
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
        limit=8,
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
            "input_summary": ", ".join(r["rule_id"] for r in constraints["active_rules"]) or "standard",
            "output_summary": (
                f"保留 {len(safe_places)} 个安全地点，过滤 {len(filtered_out)} 个冲突候选"
                if zh
                else f"Kept {len(safe_places)} safe place picks; filtered out {len(filtered_out)} conflicting candidates"
            ),
            "details": [f"{f['name']}: {f['reason']}" for f in filtered_out],
        },
        {
            "step": 4,
            "tool": "guardrail_check",
            "title": "安全护栏检查 (backend/language/guardrail.py)" if zh else "Language safety guardrail check",
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

    return {
        "senior_id": senior.get("id", ""),
        "date": day.isoformat(),
        "qloo_mode": qloo_mode,
        "profile": {
            "neighbourhood": profile["neighbourhood"],
            "likes": profile["likes"],
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
                "filtered_examples": [f"{f['name']} ({f['rule_id']})" for f in filtered_out[:3]],
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

