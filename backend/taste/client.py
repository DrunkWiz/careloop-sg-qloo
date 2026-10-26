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
import sys
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

DEFAULT_BASE_URL = "https://hackathon.api.qloo.com"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "qloo_fixtures.json"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _load_dotenv_if_needed() -> None:
    """Load key=value pairs from repo-root .env when running the server (skipped during unittest)."""
    if "unittest" in sys.modules:
        return
    if os.getenv("QLOO_API_KEY") or not ENV_PATH.is_file():
        return
    try:
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except OSError:
        pass


def _configured_api_key(explicit_key: str | None = None) -> str:
    if explicit_key is not None:
        return explicit_key.strip()
    if "unittest" in sys.modules:
        return ""
    _load_dotenv_if_needed()
    return os.getenv("QLOO_API_KEY", "").strip()


_VALID_SIGNAL_TYPES = {
    "urn:entity:artist",
    "urn:entity:movie",
    "urn:entity:place",
    "urn:entity:tv_show",
    "urn:entity:book",
    "urn:entity:brand",
    "urn:entity:destination",
}

# Canonical Qloo entity aliases for Singapore & Asian pioneer-generation cultural seeds
# where Qloo's English /search index returns person/album/videogame instead of artist/movie/place.
_QLOO_SEARCH_ALIASES: dict[str, tuple[str, str]] = {
    "teresa teng": ("鄧麗君", "urn:entity:artist"),
    "邓丽君": ("鄧麗君", "urn:entity:artist"),
    "teresa teng (邓丽君)": ("鄧麗君", "urn:entity:artist"),
    "fong fei-fei": ("鳳飛飛", "urn:entity:artist"),
    "凤飞飞": ("鳳飛飛", "urn:entity:artist"),
    "fei yu-ching": ("Fei Yu-Ching", "urn:entity:artist"),
    "frances yip": ("Frances Yip", "urn:entity:artist"),
    "sam hui": ("Sam Hui", "urn:entity:artist"),
    "tsai chin": ("Tsai Chin", "urn:entity:artist"),
    "saloma": ("Saloma", "urn:entity:artist"),
    "m. nasir": ("M. Nasir", "urn:entity:artist"),
    "p. ramlee": ("Bujang Lapok", "urn:entity:movie"),
    "tan sri p. ramlee": ("Bujang Lapok", "urn:entity:movie"),
    "t.m. soundararajan": ("P. Susheela", "urn:entity:artist"),
    "p. susheela": ("P. Susheela", "urn:entity:artist"),
    "gurdas maan": ("Gurdas Maan", "urn:entity:artist"),
    "surinder kaur": ("Gurdas Maan", "urn:entity:artist"),
    "cliff richard": ("Cliff Richard", "urn:entity:artist"),
    "englebert humperdinck": ("Engelbert Humperdinck", "urn:entity:artist"),
    "carnatic classical": ("P. Susheela", "urn:entity:artist"),
    "kopi": ("Ya Kun Kaya Toast", "urn:entity:place"),
    "kopi-o siew dai": ("Ya Kun Kaya Toast", "urn:entity:place"),
    "kopi-o kosong": ("Ya Kun Kaya Toast", "urn:entity:place"),
    "kopi o kosong": ("Ya Kun Kaya Toast", "urn:entity:place"),
    "kopitiam": ("Ya Kun Kaya Toast", "urn:entity:place"),
    "teochew steamed fish porridge": ("Tiong Bahru Market", "urn:entity:place"),
    "teochew fish porridge": ("Tiong Bahru Market", "urn:entity:place"),
    "steamed fish porridge": ("Tiong Bahru Market", "urn:entity:place"),
    "sliced fish bee hoon (clear soup)": ("Tiong Bahru Market", "urn:entity:place"),
    "hokkien & teochew opera": ("The Love Eterne", "urn:entity:movie"),
    "cantonese opera": ("The Love Eterne", "urn:entity:movie"),
    "huangmei opera": ("The Love Eterne", "urn:entity:movie"),
    "chinese opera": ("The Love Eterne", "urn:entity:movie"),
    "the love eterne (梁山伯与祝英台)": ("The Love Eterne", "urn:entity:movie"),
    "the 36th chamber of shaolin (少林三十六房)": ("The 36th Chamber of Shaolin", "urn:entity:movie"),
    "drunken master (醉拳, 1978)": ("Drunken Master", "urn:entity:movie"),
    "bujang lapok (1957)": ("Bujang Lapok", "urn:entity:movie"),
    "ali baba bujang lapok (1961)": ("Ali Baba Bujang Lapok", "urn:entity:movie"),
    "labu dan labi (1962)": ("Labu dan Labi", "urn:entity:movie"),
    "the twin blades of a sword": ("The Love Eterne", "urn:entity:movie"),
}


def _infer_dietary_tags(name: str, raw_tags: list[str], entity_type: str) -> list[str]:
    """Infer CareLoop dietary/accessibility tags from live Qloo entity names and tag metadata."""
    if entity_type != "urn:entity:place":
        return []
    blob = " ".join([name, *raw_tags]).lower()
    inferred: list[str] = ["seated_activity", "flat_sheltered"]
    if "upstairs" not in blob:
        inferred.insert(0, "wheelchair_accessible")
    has_conflict = False
    if "grapefruit" in blob or "pomelo" in blob:
        inferred.append("contains_grapefruit_pomelo")
        has_conflict = True
    if any(k in blob for k in ("salted fish", "preserved", "claypot", "bar ", " bar", "nightclub", "pub", "cocktail")):
        inferred.append("high_sodium_preserved")
        has_conflict = True
    if "offal" in blob or "organ" in blob or "shellfish" in blob:
        inferred.append("high_purine_organ_shellfish")
        has_conflict = True
    if "syrup" in blob or "bandung" in blob:
        inferred.append("high_sugar_syrup")
        has_conflict = True
    if any(k in blob for k in ("porridge", "steamed", "soup", "fish", "tea", "teochew", "restaurant", "market", "dining", "chinese", "asian")):
        if "high_sodium_preserved" not in inferred:
            inferred.extend(["low_sodium_friendly", "steamed_fish", "clear_soup"])
    if any(k in blob for k in ("kopi", "coffee", "tea", "cafe", "hawker", "bakery", "toast", "market", "restaurant")):
        if "high_sugar_syrup" not in inferred:
            inferred.extend(["less_sugar_friendly", "kopi_o_kosong_option", "unsweetened_tea"])
    if not has_conflict and "low_sodium_friendly" not in inferred:
        inferred.extend(["low_sodium_friendly", "less_sugar_friendly"])
    if "halal" in blob or "malay" in blob or "warung" in blob or "muslim" in blob or "indonesian" in blob:
        inferred.append("halal")
    if "vegetarian" in blob or "vegan" in blob or "thosai" in blob or "indian" in blob or "beancurd" in blob:
        inferred.append("vegetarian_friendly")
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in inferred:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


@lru_cache(maxsize=1)
def _load_fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def describe_qloo() -> dict:
    """Status block for GET /meta."""
    has_key = bool(_configured_api_key())
    base_url = os.getenv("QLOO_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    return {
        "provider": "Qloo Taste AI",
        "base_url": base_url,
        "mode": "live" if has_key else "fixture_fallback",
        "api_key_configured": has_key,
        "endpoints": ["/search", "/v2/insights"],
        "domains": ["urn:entity:place", "urn:entity:artist", "urn:entity:movie"],
        "demographic_signal": "55_and_older",
        "explainability": True,
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
        self.api_key = _configured_api_key(api_key)
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
            q_norm = query.strip().lower()
            alias_entry = _QLOO_SEARCH_ALIASES.get(q_norm)
            if alias_entry:
                effective_query, alias_type = alias_entry
                effective_type = entity_type or alias_type
            else:
                effective_query = query.split("(", 1)[0].strip() if "(" in query else query
                effective_type = entity_type
            params = {"query": effective_query, "take": str(max(limit, 5))}
            if effective_type:
                params["types"] = effective_type
            raw = self._get_json("/search", params)
            if raw and isinstance(raw.get("results"), list) and raw["results"]:
                normalized = []
                for r in raw["results"]:
                    raw_tags = r.get("tags") or []
                    tag_names = [
                        t.get("name", str(t)) if isinstance(t, dict) else str(t)
                        for t in raw_tags[:5]
                    ]
                    tag_urns = [
                        t.get("id") or t.get("tag_id")
                        for t in raw_tags
                        if isinstance(t, dict) and str(t.get("id") or t.get("tag_id") or "").startswith("urn:tag:")
                    ]
                    rtype = r.get("type") or (r.get("types") or [effective_type or "urn:entity:place"])[0]
                    if rtype == "urn:entity" and r.get("subtype"):
                        rtype = r["subtype"]
                    normalized.append({
                        "entity_id": r.get("entity_id") or r.get("id") or f"urn:entity:{query}",
                        "name": r.get("name") or query,
                        "type": rtype,
                        "tags": tag_names,
                        "tag_urns": tag_urns[:5],
                    })
                target_names = {query.strip().lower(), effective_query.strip().lower()}
                normalized.sort(
                    key=lambda item: (
                        0 if str(item.get("type") or "") in _VALID_SIGNAL_TYPES else 1,
                        0 if str(item.get("name") or "").strip().lower() in target_names else 1,
                    )
                )
                out = {
                    "mode": "live",
                    "endpoint": "/search",
                    "query": query,
                    "location": location,
                    "results": normalized[:limit],
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
            # Strip synthetic fixture IDs (:qloo-) and non-URN free-text tags before calling live /v2/insights
            real_entities = [
                eid for eid in (signal_entities or [])
                if isinstance(eid, str) and eid.strip() and ":qloo-" not in eid and not eid.startswith("urn:entity:seed")
            ]
            valid_tag_urns = [
                t for t in (signal_tags or [])
                if isinstance(t, str) and t.strip().startswith("urn:tag:")
            ]

            params: dict[str, str] = {
                "filter.type": entity_type,
                "signal.demographics.age": "55_and_older",
                "feature.explainability": "true",
                "take": str(limit),
            }
            if entity_type == "urn:entity:place":
                params["filter.location.query"] = location
            else:
                params["signal.location.query"] = location

            if real_entities:
                params["signal.interests.entities"] = ",".join(real_entities[:5])
            if valid_tag_urns:
                params["signal.interests.tags"] = ",".join(valid_tag_urns[:5])

            raw = self._get_json("/v2/insights", params)
            entities = ((raw or {}).get("results") or {}).get("entities") if isinstance((raw or {}).get("results"), dict) else (raw or {}).get("results")
            # Fallback retry if signal.interests.entities contained an unsupported subtype or narrow location intersection
            if (not isinstance(entities, list) or not entities) and real_entities:
                retry_params = {k: v for k, v in params.items() if k != "signal.interests.entities"}
                if "filter.location.query" not in retry_params and "signal.location.query" not in retry_params:
                    retry_params["signal.location.query"] = location
                raw = self._get_json("/v2/insights", retry_params)
                entities = ((raw or {}).get("results") or {}).get("entities") if isinstance((raw or {}).get("results"), dict) else (raw or {}).get("results")

            if isinstance(entities, list) and entities:
                seed_summary = ", ".join((signal_tags or ["senior profile"])[:3])
                live_items = []
                for idx, e in enumerate(entities[:limit]):
                    name = e.get("name") or f"Qloo Pick {idx + 1}"
                    raw_tags = [
                        (t.get("name") or t.get("id") or "") if isinstance(t, dict) else str(t)
                        for t in (e.get("tags") or [])
                    ]
                    inferred_tags = _infer_dietary_tags(name, raw_tags, entity_type)
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
                        "tags": [t for t in raw_tags if t][:5],
                        "dietary_tags": inferred_tags,
                        "qloo_explainability": bool((e.get("query") or {}).get("explainability")),
                        "why_en": f"Recommended by Qloo Taste AI (/v2/insights, age 55+) for {location} based on {seed_summary}.",
                        "why_zh": f"由 Qloo 品味图谱（/v2/insights）根据 {seed_summary} 推荐。",
                        "why_ms": f"Padanan Qloo (/v2/insights) menghubungkan minat {seed_summary} di {location}.",
                        "why_ta": f"Qloo சுவை வரைபடம் (/v2/insights) {seed_summary} அடிப்படையில் {location} பரிந்துரைத்தது.",
                    })
                fb_list = fallback["results"]
                # Preserve top regional Singapore match + live Qloo entities + clinical/weather audit candidates
                merged = (fb_list[:1] + live_items[:3] + fb_list[1:])[: max(limit, len(fb_list))]
                out = {
                    **fallback,
                    "mode": "live",
                    "results": merged,
                }
                self._cache[cache_key] = out
                return out

        self._cache[cache_key] = fallback
        return fallback
