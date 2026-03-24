from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash-lite"
    llm_context_window: int = Field(
        default=128000,
        validation_alias=AliasChoices("LLM_CONTEXT_WINDOW", "GEMINI_CONTEXT_WINDOW"),
    )
    llm_soft_input_limit: int = Field(
        default=12000,
        validation_alias=AliasChoices("LLM_SOFT_INPUT_LIMIT", "PROMPT_SOFT_INPUT_LIMIT"),
    )
    llm_reserved_output_tokens: int = Field(
        default=2048,
        validation_alias=AliasChoices(
            "LLM_RESERVED_OUTPUT_TOKENS",
            "PROMPT_RESERVED_OUTPUT_TOKENS",
        ),
    )
    llm_safety_margin_tokens: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "LLM_SAFETY_MARGIN_TOKENS",
            "PROMPT_SAFETY_MARGIN_TOKENS",
        ),
    )

    # Data Source API Keys
    mboum_api_key: Optional[str] = None
    fmp_api_key: Optional[str] = None
    fmp_base_url: str = "https://financialmodelingprep.com/api/v3"

    # Database (PostgreSQL for chatbot conversations)
    # Example: postgresql+asyncpg://user:password@host:5432/dbname
    database_url: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env (prevents errors)


settings = Settings()

