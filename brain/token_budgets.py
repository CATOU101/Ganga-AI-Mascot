"""Central, environment-configurable input and output token targets."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from .answer_format import AnswerFormat


def _positive_env(name: str, default: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


@dataclass(frozen=True)
class TokenBudgets:
    general_short: int = 160
    simple_domain: int = 300
    detailed: int = 600
    comparison: int = 500
    complex: int = 900
    input_context_chars: int = 6000
    general_question_chars: int = 2000

    @classmethod
    def from_environment(cls) -> "TokenBudgets":
        return cls(
            general_short=_positive_env("GANGA_LLM_TOKENS_GENERAL", 160, 1000),
            simple_domain=_positive_env("GANGA_LLM_TOKENS_SIMPLE", 300, 1000),
            detailed=_positive_env("GANGA_LLM_TOKENS_DETAILED", 600, 1000),
            comparison=_positive_env("GANGA_LLM_TOKENS_COMPARISON", 500, 1000),
            complex=_positive_env("GANGA_LLM_TOKENS_COMPLEX", 900, 1500),
            input_context_chars=_positive_env("GANGA_LLM_MAX_CONTEXT_CHARS", 6000, 30000),
            general_question_chars=_positive_env("GANGA_LLM_MAX_GENERAL_QUESTION_CHARS", 2000, 8000),
        )

    def output_for(self, request_format: AnswerFormat, *, general: bool = False) -> int:
        if request_format.word_count is not None:
            # English prose averages fewer than two tokens per word. Leave a small margin.
            return min(self.complex, max(64, math.ceil(request_format.word_count * 1.7)))
        if request_format.detail == "complex":
            return self.complex
        if request_format.style == "comparison_table":
            return self.comparison
        if request_format.detail == "detailed":
            return self.detailed
        if request_format.detail == "brief":
            return min(self.general_short if general else self.simple_domain, 120 if general else 220)
        if general:
            return self.general_short
        return self.simple_domain


def load_token_budgets() -> TokenBudgets:
    return TokenBudgets.from_environment()
