from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
import importlib
import importlib.util
import logging
import re
from typing import Iterable

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


def _bs4_available() -> bool:
    return importlib.util.find_spec("bs4") is not None


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
            self._in_cell = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            text = " ".join("".join(self._current_cell).split())
            self._current_row.append(text)
            self._current_cell = None
            self._in_cell = False
        elif tag == "tr" and self._current_table is not None and self._current_row is not None:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._in_cell and self._current_cell is not None:
            self._current_cell.append(data)


def _extract_tables(html: str) -> list[list[list[str]]]:
    if _bs4_available():
        bs4 = importlib.import_module("bs4")
        soup = bs4.BeautifulSoup(html, "html.parser")
        tables: list[list[list[str]]] = []
        for table in soup.find_all("table"):
            rows: list[list[str]] = []
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if not cells:
                    continue
                rows.append([" ".join(cell.get_text(" ", strip=True).split()) for cell in cells])
            if rows:
                tables.append(rows)
        return tables

    parser = _TableParser()
    parser.feed(html)
    return parser.tables


def fetch_html(url: str, timeout_seconds: int) -> str:
    import requests

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


def parse_offers(html: str) -> list[dict[str, str]]:
    tables = _extract_tables(html)
    if not tables:
        raise OfferParseError("No tables found on the page; page structure may have changed.")

    best_table: list[list[str]] | None = None
    best_mapping: dict[int, str] = {}
    best_header_row_index: int | None = None
    for table in tables:
        for idx, row in enumerate(table):
            if not row:
                continue
            headers = row
            mapping = _match_headers(headers)
            if len(mapping) > len(best_mapping):
                best_mapping = mapping
                best_table = table
                best_header_row_index = idx

    if not best_table or not best_mapping:
        raise OfferParseError(
            "Unable to map table headers to expected fields; "
            "update HEADER_ALIASES or parsing logic."
        )

    rows = best_table
    start_index = (best_header_row_index or 0) + 1
    offers: list[dict[str, str]] = []
    for row in rows[start_index:]:
        if not row:
            continue
        offer_data: dict[str, str] = {field: "" for field in FIELDS}
        for idx, cell in enumerate(row):
            if idx not in best_mapping:
                continue
            offer_data[best_mapping[idx]] = cell
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
