from __future__ import annotations

from collections import defaultdict
import logging
import re
from typing import Iterable

import requests
from bs4 import BeautifulSoup

FIELDS = [
    "id",
    "site",
    "domain",
    "category",
    "sale",
    "conditions",
    "motivationAmount",
    "offerDuration",
    "legalName",
    "greenProbability",
]

HEADER_ALIASES = {
    "id": {"id", "offer id"},
    "site": {"site", "сайт"},
    "domain": {"domain", "домен"},
    "category": {"category", "категория"},
    "sale": {"sale", "продажа", "скидка"},
    "conditions": {"conditions", "условия"},
    "motivationAmount": {
        "motivationamount",
        "motivation amount",
        "reward",
        "вознаграждение",
        "мотивация",
    },
    "offerDuration": {"offerduration", "offer duration", "duration", "срок", "срок действия"},
    "legalName": {"legalname", "legal name", "legal", "юр. лицо", "юридическое лицо"},
    "greenProbability": {
        "greenprobability",
        "green probability",
        "green",
        "вероятность green",
    },
}


class OfferParseError(RuntimeError):
    pass


def fetch_html(url: str, timeout_seconds: int) -> str:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.text


logger = logging.getLogger(__name__)


def _normalize_header(text: str) -> str:
    cleaned = re.sub(r"[^\w]+", " ", text.lower())
    return " ".join(cleaned.strip().split())


def _match_headers(headers: Iterable[str]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    normalized = [_normalize_header(header) for header in headers]
    for idx, header in enumerate(normalized):
        for field, aliases in HEADER_ALIASES.items():
            normalized_aliases = {_normalize_header(alias) for alias in aliases}
            if header in normalized_aliases or any(
                alias and alias in header for alias in normalized_aliases
            ):
                mapping[idx] = field
                break
        if idx not in mapping:
            logger.debug("Unmatched header: %s", headers[idx])
    return mapping


def _text(cell) -> str:
    return " ".join(cell.get_text(" ", strip=True).split())


def parse_offers(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        raise OfferParseError("No tables found on the page; page structure may have changed.")

    best_table = None
    best_mapping: dict[int, str] = {}
    for table in tables:
        header_cells = table.find_all("th")
        headers = [_text(cell) for cell in header_cells]
        if not headers:
            first_row = table.find("tr")
            if not first_row:
                continue
            headers = [_text(cell) for cell in first_row.find_all("td")]
        mapping = _match_headers(headers)
        if len(mapping) > len(best_mapping):
            best_mapping = mapping
            best_table = table

    if not best_table or not best_mapping:
        raise OfferParseError(
            "Unable to map table headers to expected fields; "
            "update HEADER_ALIASES or parsing logic."
        )

    rows = best_table.find_all("tr")
    offers: list[dict[str, str]] = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        offer_data: dict[str, str] = {field: "" for field in FIELDS}
        for idx, cell in enumerate(cells):
            if idx not in best_mapping:
                continue
            offer_data[best_mapping[idx]] = _text(cell)
        if any(offer_data.values()):
            offers.append(offer_data)

    if not offers:
        raise OfferParseError("Parsed table but found no offer rows.")

    return offers


def collect_offers(url: str, timeout_seconds: int) -> list[dict[str, str]]:
    html = fetch_html(url, timeout_seconds)
    return parse_offers(html)


def offers_to_rows(offers: Iterable[dict[str, str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for offer in offers:
        rows.append([offer.get(field, "") for field in FIELDS])
    return rows


def count_pairs(offers: Iterable[dict[str, str]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for offer in offers:
        key = (offer.get("domain", ""), offer.get("sale", ""))
        if any(key):
            counts[key] += 1
    return counts
