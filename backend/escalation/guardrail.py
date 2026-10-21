"""Re-exports the canonical outgoing-copy guardrail from backend.language.guardrail."""
from __future__ import annotations

from ..language.facts import Audience, Facts, GuardrailResult, Rung
from ..language.guardrail import (
    ALWAYS_OK_NUMBERS,
    CALM,
    CONDITIONS_EN,
    CONDITIONS_ZH,
    MASKS,
    OUTDOORS,
    RULES,
    URGENT,
    check,
)

__all__ = [
    "ALWAYS_OK_NUMBERS",
    "Audience",
    "CALM",
    "CONDITIONS_EN",
    "CONDITIONS_ZH",
    "Facts",
    "GuardrailResult",
    "MASKS",
    "OUTDOORS",
    "RULES",
    "Rung",
    "URGENT",
    "check",
]
