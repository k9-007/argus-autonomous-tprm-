"""Central configuration.

Adapted from Studio1HQ/tprm-agent (MIT) `src/config.py`, extended for Argus
(multi-tenant DB, model selection, public URL for invites).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM provider switch: "openai" or "gemini".
    LLM_PROVIDER: str = os.getenv("ARGUS_LLM_PROVIDER", "openai").strip().lower()

    # OpenAI (reasoning agents)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("ARGUS_LLM_MODEL", "gpt-5.6")

    # Google Gemini (reasoning agents)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("ARGUS_GEMINI_MODEL", "gemini-3.5-flash")

    # Bright Data (Discovery / Access tools, vendored from upstream)
    BRIGHT_DATA_API_TOKEN: str = os.getenv("BRIGHT_DATA_API_TOKEN", "")
    BRIGHT_DATA_SERP_ZONE: str = os.getenv("BRIGHT_DATA_SERP_ZONE", "")
    BRIGHT_DATA_UNLOCKER_ZONE: str = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "")

    # Persistence
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./argus.db")

    # Public URL for vendor-collaboration invite links
    PUBLIC_URL: str = os.getenv("ARGUS_PUBLIC_URL", "http://localhost:3000")

    @property
    def active_llm_model(self) -> str:
        """Model name for the currently selected provider."""
        if self.LLM_PROVIDER == "gemini":
            return self.GEMINI_MODEL
        return self.LLM_MODEL

    @property
    def llm_enabled(self) -> bool:
        if self.LLM_PROVIDER == "gemini":
            return bool(self.GEMINI_API_KEY)
        return bool(self.OPENAI_API_KEY)

    @property
    def bright_data_enabled(self) -> bool:
        return bool(self.BRIGHT_DATA_API_TOKEN)


settings = Settings()
