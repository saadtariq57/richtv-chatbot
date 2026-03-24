from typing import Dict, Iterable, List, Optional, Sequence

from app.llm.budget import (
    PromptBudget,
    PromptBuildResult,
    PromptSection,
    get_default_prompt_budget,
)
from app.llm.client import LLMClient, get_llm_client


def _normalize_text(text: str) -> str:
    return (text or "").strip()


def _join_sections(section_texts: Sequence[str], separator: str) -> str:
    normalized = [_normalize_text(text) for text in section_texts if _normalize_text(text)]
    return separator.join(normalized)


def format_labeled_section(title: str, body: str) -> str:
    """Return a consistently labeled prompt section."""

    normalized_body = _normalize_text(body)
    if not normalized_body:
        return ""
    return f"{title}:\n{normalized_body}"


def format_chat_message(message: Dict[str, str]) -> str:
    """Render a chat message in a stable role/content format."""

    role = (message.get("role") or "user").strip().capitalize()
    content = _normalize_text(message.get("content") or "")
    if not content:
        return ""
    return f"{role}: {content}"


def build_chat_history_text(
    chat_history: Sequence[Dict[str, str]],
    llm_client: Optional[LLMClient] = None,
    max_tokens: Optional[int] = None,
    title: str = "Previous conversation",
) -> str:
    """
    Build a chat history block, keeping the newest messages that fit.

    When `max_tokens` is provided, messages are packed from newest to oldest until
    the section token budget is reached.
    """

    rendered_messages = [format_chat_message(message) for message in chat_history]
    rendered_messages = [message for message in rendered_messages if message]
    if not rendered_messages:
        return ""

    header = f"{title}:\n"
    if max_tokens is None:
        return header + "\n".join(rendered_messages)

    client = llm_client or get_llm_client()
    kept_messages: List[str] = []

    for rendered in reversed(rendered_messages):
        candidate_messages = [rendered, *kept_messages]
        candidate_text = header + "\n".join(candidate_messages)
        if client.count_tokens(candidate_text) <= max_tokens:
            kept_messages.insert(0, rendered)

    if not kept_messages:
        return ""

    return header + "\n".join(kept_messages)


def build_chat_history_section(
    chat_history: Sequence[Dict[str, str]],
    *,
    priority: int,
    llm_client: Optional[LLMClient] = None,
    max_tokens: Optional[int] = None,
    title: str = "Previous conversation",
    name: str = "chat_history",
    required: bool = False,
) -> PromptSection:
    """Create a prompt section from chat history with optional token capping."""

    return PromptSection(
        name=name,
        text=build_chat_history_text(
            chat_history,
            llm_client=llm_client,
            max_tokens=max_tokens,
            title=title,
        ),
        priority=priority,
        required=required,
        max_tokens=max_tokens,
    )


def build_prompt(
    sections: Iterable[PromptSection],
    *,
    budget: Optional[PromptBudget] = None,
    llm_client: Optional[LLMClient] = None,
    separator: str = "\n\n",
) -> PromptBuildResult:
    """
    Assemble a prompt from sections while enforcing the effective input token budget.

    Required sections are validated first. Optional sections are then added in
    ascending priority order until the input budget is exhausted.
    """

    client = llm_client or get_llm_client()
    active_budget = budget or get_default_prompt_budget()

    prepared_sections = [
        section
        for section in sections
        if _normalize_text(section.text)
    ]

    required_sections = [section for section in prepared_sections if section.required]
    optional_sections = [section for section in prepared_sections if not section.required]
    optional_sections.sort(key=lambda section: section.priority)

    prompt_parts: List[str] = []
    included_sections: List[str] = []
    dropped_sections: List[str] = []
    section_token_usage: Dict[str, int] = {}

    def try_add_section(section: PromptSection, *, is_required: bool) -> bool:
        section_text = _normalize_text(section.text)
        if not section_text:
            return not is_required

        section_tokens = client.count_tokens(section_text)
        if section.max_tokens is not None and section_tokens > section.max_tokens:
            if is_required:
                raise ValueError(
                    f"Required section '{section.name}' exceeds its max token cap "
                    f"({section_tokens} > {section.max_tokens})."
                )
            dropped_sections.append(section.name)
            return False

        candidate_prompt = _join_sections([*prompt_parts, section_text], separator)
        candidate_tokens = client.count_tokens(candidate_prompt)
        if candidate_tokens > active_budget.effective_input_budget:
            if is_required:
                raise ValueError(
                    f"Required section '{section.name}' does not fit within the "
                    f"effective input budget ({candidate_tokens} > "
                    f"{active_budget.effective_input_budget})."
                )
            dropped_sections.append(section.name)
            return False

        prompt_parts.append(section_text)
        included_sections.append(section.name)
        section_token_usage[section.name] = section_tokens
        return True

    for section in required_sections:
        try_add_section(section, is_required=True)

    for section in optional_sections:
        try_add_section(section, is_required=False)

    prompt = _join_sections(prompt_parts, separator)
    prompt_tokens = client.count_tokens(prompt)

    return PromptBuildResult(
        prompt=prompt,
        prompt_tokens=prompt_tokens,
        reserved_output_tokens=active_budget.reserved_output_tokens,
        remaining_input_tokens=max(0, active_budget.effective_input_budget - prompt_tokens),
        included_sections=included_sections,
        dropped_sections=dropped_sections,
        section_token_usage=section_token_usage,
    )
