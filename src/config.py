"""
Intel Briefing - Unified Configuration Layer

Single source of truth for all configuration values.
Replaces the fragmented pattern of manual .env parsing, load_dotenv(),
and os.getenv() scattered across sensors.

Usage:
    from config import cfg

    # Access any config value
    api_key = cfg.xai_api_key
    model = cfg.xai_model
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (handles both local dev and CI)
# Walk up from this file (src/config.py) to find .env at project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, ".env"))


@dataclass(frozen=True)
class IntelConfig:
    """Immutable configuration for the Intel Briefing engine.

    Resolution order for each value:
    1. Environment variable (set by CI/CD or .env)
    2. Hardcoded default (safe fallback)

    All secrets come from env vars. Non-secret operational params
    have sensible defaults.
    """

    # === Core API Keys (SECRETS — no defaults) ===
    deepseek_api_key: Optional[str] = field(default=None)
    xai_api_key: Optional[str] = field(default=None)
    github_token: Optional[str] = field(default=None)
    producthunt_token: Optional[str] = field(default=None)

    # === XAI / Grok Configuration ===
    # Aligned with .github/workflows/daily-report.yml actual values
    xai_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    xai_model: str = "x-ai/grok-4-fast"

    # === DeepSeek Configuration ===
    deepseek_api_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout: int = 60
    deepseek_max_retries: int = 3

    # === Jina Reader Configuration ===
    jina_reader_url: str = "https://r.jina.ai/"
    jina_timeout: int = 30
    jina_max_chars: int = 15000

    # === Operational Parameters ===
    fetch_timeout: int = 15
    grok_timeout: int = 120
    limit_per_source: int = 10
    max_hn_blogs: int = 5
    content_truncate_limit: int = 3000
    llm_rate_limit_delay: float = 1.5

    # === Feature Flags ===
    enable_grok_sentiment: bool = True
    enable_link_verification: bool = True

    @classmethod
    def from_env(cls) -> "IntelConfig":
        """Build config from environment variables."""
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            xai_api_key=os.getenv("XAI_API_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            producthunt_token=os.getenv("PRODUCTHUNT_TOKEN"),
            xai_base_url=os.getenv(
                "XAI_BASE_URL",
                "https://openrouter.ai/api/v1/chat/completions",
            ),
            xai_model=os.getenv("XAI_MODEL", "x-ai/grok-4-fast"),
            deepseek_api_url=os.getenv(
                "DEEPSEEK_API_URL",
                "https://api.deepseek.com",
            ),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            deepseek_timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "60")),
            deepseek_max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3")),
            jina_reader_url=os.getenv("JINA_READER_URL", "https://r.jina.ai/"),
            jina_timeout=int(os.getenv("JINA_TIMEOUT", "30")),
            jina_max_chars=int(os.getenv("JINA_MAX_CHARS", "15000")),
            fetch_timeout=int(os.getenv("FETCH_TIMEOUT", "15")),
            grok_timeout=int(os.getenv("GROK_TIMEOUT", "120")),
            limit_per_source=int(os.getenv("LIMIT_PER_SOURCE", "10")),
            max_hn_blogs=int(os.getenv("MAX_HN_BLOGS", "5")),
            content_truncate_limit=int(os.getenv("CONTENT_TRUNCATE_LIMIT", "3000")),
            enable_grok_sentiment=os.getenv("ENABLE_GROK_SENTIMENT", "true").lower() == "true",
            enable_link_verification=os.getenv("ENABLE_LINK_VERIFICATION", "true").lower() == "true",
        )

    def validate(self) -> list[str]:
        """Return a list of warnings for missing critical config."""
        warnings = []
        if not self.xai_api_key:
            warnings.append("XAI_API_KEY not set — Grok sensor will be disabled")
        if not self.github_token:
            warnings.append("GITHUB_TOKEN not set — GitHub Trending will be disabled")
        if not self.deepseek_api_key:
            warnings.append("DEEPSEEK_API_KEY not set — report generation will fail")
        return warnings


# Singleton instance — import this everywhere
cfg = IntelConfig.from_env()

# Backward-compatible module-level exports
# (used by gemini_translator.py (DeepSeek), jina_reader.py, report_generator.py)
LLM_RATE_LIMIT_DELAY = cfg.llm_rate_limit_delay
DEEPSEEK_API_KEY = cfg.deepseek_api_key
DEEPSEEK_API_URL = cfg.deepseek_api_url
DEEPSEEK_MODEL = cfg.deepseek_model
DEEPSEEK_TIMEOUT = cfg.deepseek_timeout
DEEPSEEK_MAX_RETRIES = cfg.deepseek_max_retries
JINA_READER_URL = cfg.jina_reader_url
JINA_TIMEOUT = cfg.jina_timeout
JINA_MAX_CHARS = cfg.jina_max_chars
CONTENT_TRUNCATE_LIMIT = cfg.content_truncate_limit
