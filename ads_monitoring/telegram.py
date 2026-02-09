from __future__ import annotations

import requests


def send_message(token: str, channel_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={"chat_id": channel_id, "text": message})
    response.raise_for_status()
