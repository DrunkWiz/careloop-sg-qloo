"""Qloo Taste AI client with in-memory caching and automatic offline fixture fallback.

Live API (Qloo Hackathon):
- Base URL: QLOO_BASE_URL (default https://hackathon.api.qloo.com)
- Auth header: X-Api-Key: <QLOO_API_KEY>
- Endpoints used:
  1. GET /search?query=<q>&types=<entity_type>
  2. GET /v2/insights?filter.type=<entity_type>&signal.interests.entities=<ids>&filter.location.query=Singapore

Offline & fallback rule (CLAUDE.md):
- Every test runs with no API keys and no network.
- When QLOO_API_KEY is unset (or a live HTTP call fails/times out), QlooClient falls back cleanly
  to backend/taste/fixtures/qloo_fixtures.json and marks mode="fixture" in the trace.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

DEFAULT_BASE_URL = "https://hackathon.api.qloo.com"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "qloo_fixtures.json"


@lru_cache(maxsize=1)
def _load_fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def describe_qloo() -> dict:
    """Status block for GET /meta."""
    has_key = bool(os.getenv("QLOO_API_KEY", "").strip())
    base_url = os.getenv("QLOO_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    return {
        "provider": "Qloo Taste AI",
        "base_url": base_url,
        "mode": "live" if has_key else "fixture_fallback",
        "api_key_configured": has_key,
        "endpoints": ["/search", "/v2/insights"],
        "domains": ["urn:entity:place", "urn:entity:artist", "urn:entity:movie"],
    }


class FixtureQlooClient:
    """Deterministic offline Qloo client backed by backend/taste/fixtures/qloo_fixtures.json."""

    mode = "fixture"

    def __init__(self) -> None:
        self._data = _load_fixtures()

    def search(self, query: str, entity_type: str | None = None, location: str = "Singapore", limit: int = 5) -> dict:
        q = query.strip().lower()
        entities = self._data.get("search_entities", {})
        results: list[dict] = []
        if q in entities:
            results.append(entities[q])
        else:
            for key, item in entities.items():
                if q in key or q in item.get("name", "").lower() or any(q in t for t in item.get("tags", [])):
                    if entity_type is None or item.get("type") == entity_type:
                        results.append(item)
        if not results:
            slug = "".join(ch if ch.isalnum() else "-" for ch in q).strip("-") or "seed"
            results.append({
                "entity_id": f"{entity_type or 'urn:entity:place'}:qloo-{slug}",
                "name": query.strip(),
                "type": entity_type or "urn:entity:place",
                "tags": [slug],
            })
        return {
            "mode": "fixture",
            "endpoint": "/search",
            "query": query,
            "location": location,
            "results": results[:limit],
        }

    def insights(
        self,
        entity_type: str,
        *,
        signal_entities: list[str] | None = None,
        signal_tags: list[str] | None = None,
        region: str = "central",
        location: str = "Singapore",
        limit: int = 8,
    ) -> dict:
        seeds = {s.strip().lower() for s in (signal_tags or []) if s}
        # Map entity IDs back to canonical seed names where known
        for eid in signal_entities or []:
            for key, ent in self._data.get("search_entities", {}).items():
                if ent.get("entity_id") == eid:
                    seeds.add(key)

        if entity_type == "urn:entity:artist":
            pool = self._data.get("artists", [])
        elif entity_type == "urn:entity:movie":
            pool = self._data.get("movies", [])
        else:
            pool = [
                p for p in self._data.get("places", [])
                if p.get("region") in (region, "all", None)
            ]

        scored: list[tuple[float, dict]] = []
        for item in pool:
            item_seeds = [s.lower() for s in item.get("matched_seeds", [])]
            overlap = [s for s in item_seeds if s in seeds]
            # Boost items that match the senior's seeds; keep regional / safety-test items in pool
            score = float(item.get("affinity", 0.8)) + (0.05 * len(overlap))
            enriched = {
                **item,
                "matched_seeds": overlap or item.get("matched_seeds", [])[:2],
                "affinity": round(min(0.99, score), 2),
            }
            scored.append((score, enriched))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return {
            "mode": "fixture",
            "endpoint": "/v2/insights",
            "entity_type": entity_type,
            "region": region,
            "location": location,
            "signal_entities": list(signal_entities or []),
            "signal_tags": sorted(seeds),
            "results": [item for _, item in scored[:limit]],
        }


class QlooClient:
    """Qloo API client with in-memory caching and automatic fallback to FixtureQlooClient."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 4.0,
    ) -> None:
        self.api_key = (api_key if api_key is not None else os.getenv("QLOO_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("QLOO_BASE_URL", DEFAULT_BASE_URL)).strip().rstrip("/")
        self.timeout = timeout
        self._fixture = FixtureQlooClient()
        self._cache: dict[tuple, dict] = {}

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    def _get_json(self, path: str, params: dict[str, str]) -> dict | None:
        if not self.api_key:
            return None
        query_string = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        url = f"{self.base_url}{path}?{query_string}" if query_string else f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={
                "X-Api-Key": self.api_key,
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return None
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return None

    def search(self, query: str, entity_type: str | None = None, location: str = "Singapore", limit: int = 5) -> dict:
        cache_key = ("search", query.strip().lower(), entity_type or "", location, limit, bool(self.api_key))
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.api_key:
            params = {"query": query, "take": str(limit)}
            if entity_type:
                params["types"] = entity_type
            raw = self._get_json("/search", params)
            if raw and isinstance(raw.get("results"), list) and raw["results"]:
                normalized = [
                    {
                        "entity_id": r.get("entity_id") or r.get("id") or f"urn:entity:{query}",
                        "name": r.get("name") or query,
                        "type": r.get("type") or (r.get("types") or [entity_type or "urn:entity:place"])[0],
                        "tags": [t.get("name", str(t)) if isinstance(t, dict) else str(t) for t in (r.get("tags") or [])[:5]],
                    }
                    for r in raw["results"][:limit]
                ]
                out = {
                    "mode": "live",
                    "endpoint": "/search",
                    "query": query,
                    "location": location,
                    "results": normalized,
                }
                self._cache[cache_key] = out
                return out

        out = self._fixture.search(query, entity_type=entity_type, location=location, limit=limit)
        self._cache[cache_key] = out
        return out

    def insights(
        self,
        entity_type: str,
        *,
        signal_entities: list[str] | None = None,
        signal_tags: list[str] | None = None,
        region: str = "central",
        location: str = "Singapore",
        limit: int = 8,
    ) -> dict:
        cache_key = (
            "insights",
            entity_type,
            tuple(sorted(signal_entities or [])),
            tuple(sorted(signal_tags or [])),
            region,
            location,
            limit,
            bool(self.api_key),
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        fallback = self._fixture.insights(
            entity_type,
            signal_entities=signal_entities,
            signal_tags=signal_tags,
            region=region,
            location=location,
            limit=limit,
        )

        if self.api_key:
            params: dict[str, str] = {
                "filter.type": entity_type,
                "filter.location.query": location,
                "take": str(limit),
            }
            if signal_entities:
                params["signal.interests.entities"] = ",".join(signal_entities)
            if signal_tags:
                params["signal.interests.tags"] = ",".join(signal_tags)
            raw = self._get_json("/v2/insights", params)
            entities = ((raw or {}).get("results") or {}).get("entities") if isinstance((raw or {}).get("results"), dict) else (raw or {}).get("results")
            if isinstance(entities, list) and entities:
                live_items = []
                for idx, e in enumerate(entities[:limit]):
                    name = e.get("name") or f"Qloo Pick {idx + 1}"
                    live_items.append({
                        "entity_id": e.get("entity_id") or e.get("id") or f"{entity_type}:live-{idx}",
                        "name": name,
                        "name_zh": name,
                        "region": region,
                        "category": "qloo_live",
                        "indoor": True,
                        "free": False,
                        "affinity": round(float(e.get("affinity") or e.get("popularity") or 0.9), 2),
                        "matched_seeds": list(signal_tags or [])[:3],
                        "dietary_tags": [],
                        "why_en": f"Recommended by Qloo Taste AI (/v2/insights) for {location} based on {', '.join((signal_tags or ['senior profile'])[:3])}.",
                        "why_zh": f"由 Qloo 品味图谱（/v2/insights）根据 {', '.join((signal_tags or ['长者偏好'])[:3])} 推荐。",
                    })
                out = {
                    **fallback,
                    "mode": "live",
                    "results": (live_items + fallback["results"])[:limit],
                }
                self._cache[cache_key] = out
                return out

        self._cache[cache_key] = fallback
        return fallback
