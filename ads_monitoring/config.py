from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Settings:
    flocktory_url: str
    google_sheet_id: str
    google_service_account_file: str
    sheet_current_name: str
    sheet_previous_name: str
    telegram_bot_token: str
    telegram_channel_id: str
    request_timeout_seconds: int


def _load_dotenv(env_path: Path) -> None:
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_path_env(name: str, default: str | None = None) -> str:
    value = _get_env(name, default)
    path = Path(value).expanduser()
    if not path.is_file():
        raise RuntimeError(f"File not found for {name}: {path}")
    return str(path)


def _get_positive_int(name: str, default: str) -> int:
    raw = _get_env(name, default)
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer for {name}: {raw}") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be positive, got {value}")
    return value


def _collect_errors() -> list[str]:
    errors: list[str] = []
    required_keys: Iterable[str] = (
        "FLOCKTORY_URL",
        "GOOGLE_SHEET_ID",
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHANNEL_ID",
    )

    for key in required_keys:
        if not os.getenv(key):
            errors.append(f"Missing required environment variable: {key}")

    service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_path:
        path = Path(service_account_path).expanduser()
        if not path.is_file():
            errors.append(
                f"File not found for GOOGLE_SERVICE_ACCOUNT_FILE: {path}"
            )

    timeout_value = os.getenv("REQUEST_TIMEOUT_SECONDS", "30")
    try:
        timeout = int(timeout_value)
    except ValueError:
        errors.append(
            f"Invalid integer for REQUEST_TIMEOUT_SECONDS: {timeout_value}"
        )
    else:
        if timeout <= 0:
            errors.append(
                f"REQUEST_TIMEOUT_SECONDS must be positive, got {timeout}"
            )

    return errors


def load_settings() -> Settings:
    _load_dotenv(Path(os.getenv("ENV_FILE", ".env")).expanduser())
    errors = _collect_errors()
    if errors:
        raise RuntimeError("; ".join(errors))

    return Settings(
        flocktory_url=_get_env("FLOCKTORY_URL"),
        google_sheet_id=_get_env("GOOGLE_SHEET_ID"),
        google_service_account_file=_get_path_env("GOOGLE_SERVICE_ACCOUNT_FILE"),
        sheet_current_name=_get_env("SHEET_CURRENT_NAME", "current"),
        sheet_previous_name=_get_env("SHEET_PREVIOUS_NAME", "previous"),
        telegram_bot_token=_get_env("TELEGRAM_BOT_TOKEN"),
        telegram_channel_id=_get_env("TELEGRAM_CHANNEL_ID"),
        request_timeout_seconds=_get_positive_int("REQUEST_TIMEOUT_SECONDS", "30"),
    )
