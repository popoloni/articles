"""Advisory normalization of JSON decision responses; never authorizes an action.

Accepts dictionary responses from the native OpenDecider Python API or its
Jev-compatible HTTP interface. It deliberately derives explicit score semantics
from the full probability distribution instead of trusting a field named score.
No model inference or calibration is performed here.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any


class ContractError(ValueError):
    """The response is not suitable even for advisory consumption."""


def probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ContractError("A probability must be a real number, not text or bool.")
    p = float(value)
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ContractError("A probability must be finite and between zero and one.")
    return p


def distribution(value: Any, keys: set[str]) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ContractError("Missing probability mapping.")
    # JSON keys are strings; also accept integer score keys used by some SDKs.
    if len({str(k) for k in value}) != len(value):
        raise ContractError("Ambiguous duplicate probability keys.")
    values = {str(k): probability(v) for k, v in value.items()}
    if set(values) != keys:
        raise ContractError("Probability labels do not match the question schema.")
    if abs(math.fsum(values.values()) - 1.0) > 1e-3:
        raise ContractError("Probabilities do not sum to one within rounding tolerance.")
    return values


def normalize_answer(answer: Any, question: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(answer, Mapping) or answer.get("truncated"):
        raise ContractError("Missing answer or truncated model input.")
    kind = question.get("type")
    if answer.get("type") != kind:
        raise ContractError("Answer type does not match the requested question.")
    if kind == "noul":
        p = probability(answer.get("noul"))
        if "probabilities" in answer:
            probs = distribution(answer["probabilities"], {"true", "false"})
            if abs(probs["true"] - p) > 1e-3:
                raise ContractError("Noul field and true probability disagree.")
        return {"type": kind, "yes_probability": p, "no_probability": 1.0 - p}
    if kind == "choice":
        criteria = question.get("criteria")
        if not isinstance(criteria, (dict, list)) or len(criteria) < 2:
            raise ContractError("Choice needs at least two criteria.")
        keys = {str(k) for k in criteria}
        if len(keys) != len(criteria):
            raise ContractError("Duplicate choice criteria.")
        probs = distribution(answer.get("probabilities"), keys)
        peak = max(probs.values())
        # Preserve ties instead of letting dictionary order imply certainty.
        winners = sorted(k for k, v in probs.items() if abs(v - peak) < 1e-12)
        reported = answer.get("choice")
        if reported is not None and str(reported) not in winners:
            raise ContractError("Reported choice is not a highest-probability option.")
        return {"type": kind, "top_options": winners,
                "top_probability": peak, "probabilities": probs}
    if kind == "score":
        criteria = question.get("criteria")
        if not isinstance(criteria, list) or len(criteria) < 2:
            raise ContractError("Score needs ordered level descriptions.")
        probs = distribution(answer.get("probabilities"), {str(i) for i in range(len(criteria))})
        peak = max(probs.values())
        levels = sorted(int(k) for k, v in probs.items() if abs(v - peak) < 1e-12)
        expected = math.fsum(int(k) * v for k, v in probs.items())
        return {"type": kind, "most_likely_levels": levels,
                "expected_level": expected, "top_probability": peak,
                "probabilities": probs}
    raise ContractError("Unsupported question type.")


def normalize_result(result: Any, questions: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(result, Mapping) or result.get("warnings"):
        raise ContractError("Missing result or runtime warning: inspect before using.")
    answers = result.get("answers")
    if not isinstance(answers, Mapping) or set(answers) != set(questions):
        raise ContractError("Missing or unexpected answer IDs.")
    return {"advisory_only": True, "model": result.get("model"),
            "answers": {k: normalize_answer(answers[k], q) for k, q in questions.items()}}
