"""CareLoop SG's Qloo Taste AI package: cross-domain taste discovery with deterministic health & weather guardrails."""
from backend.taste.agent import (
    build_group_taste_plan,
    build_kopi_kakis,
    build_memory_lane,
    build_respite_plan,
    build_taste_plan,
    create_memory_capsule,
    get_qloo_client,
)
from backend.taste.baseline_llm import llm_only_baseline
from backend.taste.client import FixtureQlooClient, QlooClient, describe_qloo
from backend.taste.constraints import CONDITION_RULES, MEDICINE_FOOD_RULES, active_constraints, filter_qloo_candidates
from backend.taste.profiles import SENIOR_TASTE_PROFILES, build_taste_profile, extract_taste_seeds_from_text, taste_knows_entries

__all__ = [
    "CONDITION_RULES",
    "FixtureQlooClient",
    "MEDICINE_FOOD_RULES",
    "QlooClient",
    "SENIOR_TASTE_PROFILES",
    "active_constraints",
    "build_group_taste_plan",
    "build_kopi_kakis",
    "build_memory_lane",
    "build_respite_plan",
    "build_taste_plan",
    "build_taste_profile",
    "create_memory_capsule",
    "describe_qloo",
    "extract_taste_seeds_from_text",
    "filter_qloo_candidates",
    "get_qloo_client",
    "llm_only_baseline",
    "taste_knows_entries",
]
