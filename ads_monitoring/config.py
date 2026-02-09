from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    flocktory_url: str
    google_sheet_id: str
    google_service_account_file: str
    sheet_current_name: str
    sheet_previous_name: str
    telegram_bot_token: str
    telegram_chat_id: str
    request_timeout_seconds: int


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        flocktory_url=_get_env("FLOCKTORY_URL"),
        google_sheet_id=_get_env("GOOGLE_SHEET_ID"),
        google_service_account_file=_get_env("GOOGLE_SERVICE_ACCOUNT_FILE"),
        sheet_current_name=_get_env("SHEET_CURRENT_NAME", "current"),
        sheet_previous_name=_get_env("SHEET_PREVIOUS_NAME", "previous"),
        telegram_bot_token=_get_env("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_get_env("TELEGRAM_CHAT_ID"),
        request_timeout_seconds=int(_get_env("REQUEST_TIMEOUT_SECONDS", "30")),
    )
