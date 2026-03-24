from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.config import settings


@dataclass(frozen=True)
class PromptBudget:
    """Token budget configuration for a single LLM request."""

    model_name: str
    hard_context_window: int
    soft_input_limit: int
    reserved_output_tokens: int
    safety_margin_tokens: int

    @property
    def effective_input_budget(self) -> int:
        return max(
            0,
            min(
                self.soft_input_limit,
                self.hard_context_window
                - self.reserved_output_tokens
                - self.safety_margin_tokens,
            ),
        )

    @property
    def planned_total_tokens(self) -> int:
        return (
            self.effective_input_budget
            + self.reserved_output_tokens
            + self.safety_margin_tokens
        )


@dataclass(frozen=True)
class PromptSection:
    """One candidate section of a prompt with budgeting metadata."""

    name: str
    text: str
    priority: int
    required: bool = False
    max_tokens: Optional[int] = None


@dataclass
class PromptBuildResult:
    """Result of a budget-aware prompt assembly pass."""

    prompt: str
    prompt_tokens: int
    reserved_output_tokens: int
    remaining_input_tokens: int = 0
    included_sections: List[str] = field(default_factory=list)
    dropped_sections: List[str] = field(default_factory=list)
    section_token_usage: Dict[str, int] = field(default_factory=dict)


def get_default_prompt_budget() -> PromptBudget:
    """Return the default per-request budget for the configured LLM."""

    return PromptBudget(
        model_name=settings.gemini_model,
        hard_context_window=settings.llm_context_window,
        soft_input_limit=settings.llm_soft_input_limit,
        reserved_output_tokens=settings.llm_reserved_output_tokens,
        safety_margin_tokens=settings.llm_safety_margin_tokens,
    )


def get_default_chat_history_token_budget() -> int:
    """Return the default share of the prompt budget reserved for raw chat history."""

    budget = get_default_prompt_budget()
    return max(0, min(3000, budget.effective_input_budget // 4))
