#!/usr/bin/env python3
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

DEFAULT_LOGIN_URL = "https://share.flocktory.com/exchange/login?ssid=6156&bid=16115"

EXPECTED_FIELDS = {
    "id": ["id", "offer id", "ид"],
    "site": ["site", "site name", "сайт"],
    "domain": ["domain", "домен"],
    "category": ["category", "категория"],
    "sale": ["sale", "комиссия", "%", "reward"],
    "conditions": ["conditions", "условия"],
    "motivationAmount": ["motivation amount", "motivation", "мотивация"],
    "offerDuration": ["offer duration", "duration", "длительность"],
    "legalName": ["legal name", "юр. лицо", "юридическое название"],
    "greenProbability": ["green probability", "green", "green prob", "зелёная"],
}


@dataclass
class EnvConfig:
    login_url: str
    username: Optional[str]
    password: Optional[str]
    username_field: str
    password_field: str
    offers_url: str
    login_payload_json: Optional[str]


def load_config() -> EnvConfig:
    return EnvConfig(
        login_url=os.getenv("FLOCKTORY_LOGIN_URL", DEFAULT_LOGIN_URL),
        username=os.getenv("FLOCKTORY_USERNAME"),
        password=os.getenv("FLOCKTORY_PASSWORD"),
        username_field=os.getenv("FLOCKTORY_USERNAME_FIELD", "login"),
        password_field=os.getenv("FLOCKTORY_PASSWORD_FIELD", "password"),
        offers_url=os.getenv("FLOCKTORY_OFFERS_URL", DEFAULT_LOGIN_URL),
        login_payload_json=os.getenv("FLOCKTORY_LOGIN_PAYLOAD_JSON"),
    )


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_number(value: str):
    cleaned = value.replace("\xa0", " ")
    cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return cleaned


def coerce_value(field: str, value: str):
    text = normalize_text(value)
    if field in {"id"}:
        return normalize_number(text)
    if field in {"sale", "motivationAmount", "greenProbability"}:
        return normalize_number(text)
    if field in {"offerDuration"}:
        return normalize_text(text)
    return text


def resolve_field(header: str) -> Optional[str]:
    normalized = normalize_text(header).lower()
    for field, aliases in EXPECTED_FIELDS.items():
        for alias in aliases:
            if alias in normalized:
                return field
    return None


def parse_offers(html: str) -> List[Dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    headers = [normalize_text(th.get_text(" ")) for th in table.find_all("th")]
    field_map = [resolve_field(header) for header in headers]

    offers: List[Dict[str, object]] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        offer: Dict[str, object] = {}
        for idx, cell in enumerate(cells):
            field = field_map[idx] if idx < len(field_map) else None
            if not field:
                continue
            value = cell.get_text(" ")
            offer[field] = coerce_value(field, value)
        if offer:
            offers.append(offer)
    return offers


def login(session: requests.Session, config: EnvConfig) -> None:
    if not config.username or not config.password:
        return

    payload = {
        config.username_field: config.username,
        config.password_field: config.password,
    }
    if config.login_payload_json:
        payload.update(json.loads(config.login_payload_json))
    session.post(config.login_url, data=payload, timeout=30)


def fetch_offers() -> List[Dict[str, object]]:
    config = load_config()
    session = requests.Session()
    login(session, config)
    response = session.get(config.offers_url, timeout=30)
    response.raise_for_status()
    return parse_offers(response.text)


def main() -> None:
    offers = fetch_offers()
    json.dump(offers, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
