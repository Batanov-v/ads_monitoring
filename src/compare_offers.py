"""Utilities for comparing offer pairs and notifying via Telegram."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Iterable, Mapping, Sequence, Tuple

Pair = Tuple[str, str]


def _normalize_pair(item: object) -> Pair:
    if isinstance(item, Mapping):
        domain = str(item.get("domain", "")).strip()
        sale = str(item.get("sale", "")).strip()
    elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
        if len(item) < 2:  # type: ignore[arg-type]
            raise ValueError("Pair sequence must contain at least two items")
        domain = str(item[0]).strip()  # type: ignore[index]
        sale = str(item[1]).strip()  # type: ignore[index]
    else:
        raise TypeError("Pair must be mapping or sequence")

    if not domain or not sale:
        raise ValueError("Pair must include non-empty 'domain' and 'sale'")

    return domain, sale


def _normalize_pairs(items: Iterable[object]) -> set[Pair]:
    return {_normalize_pair(item) for item in items}


def compare_offer_pairs(
    current: Iterable[object],
    previous: Iterable[object],
) -> tuple[set[Pair], set[Pair]]:
    """Return (added, removed) pair sets regardless of order."""

    current_set = _normalize_pairs(current)
    previous_set = _normalize_pairs(previous)

    added = current_set - previous_set
    removed = previous_set - current_set
    return added, removed


def format_comparison_message(added: Iterable[Pair], removed: Iterable[Pair]) -> str:
    added_list = sorted(added)
    removed_list = sorted(removed)

    if not added_list and not removed_list:
        return "Нет изменений в предложениях."

    lines: list[str] = []
    if added_list:
        lines.append("Новые предложения:")
        lines.extend(f"- {domain} | {sale}" for domain, sale in added_list)
    if removed_list:
        if lines:
            lines.append("")
        lines.append("Удалённые предложения:")
        lines.extend(f"- {domain} | {sale}" for domain, sale in removed_list)

    return "\n".join(lines)


def send_telegram_message(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment"
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except urllib.error.URLError as exc:
        raise ConnectionError("Failed to send Telegram message") from exc


def compare_offers_and_notify(
    current: Iterable[object],
    previous: Iterable[object],
) -> tuple[set[Pair], set[Pair]]:
    added, removed = compare_offer_pairs(current=current, previous=previous)
    message = format_comparison_message(added=added, removed=removed)
    send_telegram_message(message)
    return added, removed


__all__ = [
    "compare_offer_pairs",
    "compare_offers_and_notify",
    "format_comparison_message",
    "send_telegram_message",
]
