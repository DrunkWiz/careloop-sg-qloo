"""Escalation guardrail package shim re-exporting canonical language guardrail."""
from .guardrail import Audience, Facts, GuardrailResult, Rung, check

__all__ = ["Audience", "Facts", "GuardrailResult", "Rung", "check"]
