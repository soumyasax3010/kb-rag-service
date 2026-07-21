"""Application settings.

All LLM/embedding calls are funneled through ``EMBED_MODEL`` / ``CHAT_MODEL``
here, so swapping providers later means changing this file + the two thin
clients (``app/retrieval/embed.py``, ``app/generation/answer.py``) only.

The OpenAI SDK is used as a common client for any OpenAI-compatible endpoint
(OpenAI, Fireworks, local, ...). Point ``OPENAI_BASE_URL`` at the provider's
inference root and set the model ids accordingly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str | None = None  # e.g. https://api.fireworks.ai/inference/v1
    database_url: str = "postgresql+asyncpg://kb:kb@localhost:5432/kb"
    database_ssl: bool = False  # set True for managed Postgres (Supabase, etc.)

    embed_model: str = "text-embedding-3-small"
    embed_dim: int = 1536
    chat_model: str = "gpt-4o-mini"

    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64

    top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
