from __future__ import annotations

import os
from functools import lru_cache
from typing import List


class Settings:
    """Application settings loaded from environment at instantiation time."""

    def __init__(self) -> None:
        # Core endpoints and toggles
        self.FORM_TEMPLATE_BASE_URL: str = os.getenv(
            "FORM_TEMPLATE_BASE_URL", "http://localhost:8080"
        )
        self.SUBMIT_API_BASE_URL: str = os.getenv(
            "SUBMIT_API_BASE_URL", "http://localhost:8000"
        )
        self.APPROVAL_API_BASE_URL: str = os.getenv(
            "APPROVAL_API_BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper"
        )

        # Optional registry configuration (future use)
        self.FORM_TEMPLATES_CONFIG_URL: str = os.getenv("FORM_TEMPLATES_CONFIG_URL", "")
        self.FORM_TEMPLATES_CONFIG_PATH: str = os.getenv(
            "FORM_TEMPLATES_CONFIG_PATH", "config/forms.json"
        )
        try:
            self.FORM_TEMPLATES_CACHE_TTL: int = int(
                os.getenv("FORM_TEMPLATES_CACHE_TTL", "300")
            )
        except ValueError:
            self.FORM_TEMPLATES_CACHE_TTL = 300

        # Feature flags
        self.ENABLE_LOCAL_TEMPLATES: bool = (
            os.getenv("ENABLE_LOCAL_TEMPLATES", "false").lower() == "true"
        )
        self.ENABLE_LOCAL_PUBLISHING_ROUTES: bool = (
            os.getenv("ENABLE_LOCAL_PUBLISHING_ROUTES", "false").lower() == "true"
        )

        # CORS
        self.ALLOWED_CORS_ORIGINS: str = os.getenv(
            "ALLOWED_CORS_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000,null",
        )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
