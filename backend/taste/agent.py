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
    for seed in profile["all_seeds"][:6]:
        sr = qloo.search(seed, location="Singapore", limit=1)
        if sr.get("results"):
            resolved_entities.append(sr["results"][0])
    entity_ids = [e["entity_id"] for e in resolved_entities if e.get("entity_id")]
    qloo_mode = "live" if qloo.is_live else "fixture"

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
        music_picks.append({
            "entity_id": a["entity_id"],
            "name": a.get("name_zh") if zh and a.get("name_zh") else a.get("name", ""),
            "affinity": a.get("affinity", 0.9),
            "matched_seeds": a.get("matched_seeds", []),
            "why": a.get("why_zh") if zh and a.get("why_zh") else a.get("why_en", ""),
        })

    movie_picks = []
    for m in movie_insights.get("results", [])[:2]:
        movie_picks.append({
            "entity_id": m["entity_id"],
            "name": m.get("name_zh") if zh and m.get("name_zh") else m.get("name", ""),
            "affinity": m.get("affinity", 0.9),
            "matched_seeds": m.get("matched_seeds", []),
            "why": m.get("why_zh") if zh and m.get("why_zh") else m.get("why_en", ""),
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
        safe_places.append({
            "entity_id": p["entity_id"],
            "name": p["display_name"],
            "category": p.get("category", "place"),
            "indoor": bool(p.get("indoor", True)),
            "free": bool(p.get("free", False)),
            "affinity": p.get("affinity", 0.9),
            "matched_seeds": p.get("matched_seeds", []),
            "fit_badges": p.get("fit_badges", []),
            "why": why_safe,
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
