"""Application settings.

All LLM/embedding calls are funneled through ``EMBED_MODEL`` / ``CHAT_MODEL``
here, so swapping providers later means changing this file + the two thin
clients (``app/retrieval/embed.py``, ``app/generation/answer.py``) only.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    database_url: str = "postgresql+asyncpg://kb:kb@localhost:5432/kb"

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
