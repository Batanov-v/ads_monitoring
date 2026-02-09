"""Google Sheets storage integration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence

from google.oauth2 import service_account
from googleapiclient.discovery import build


COLUMNS: Sequence[str] = (
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
)


@dataclass(frozen=True)
class SheetConfig:
    credentials_path: str
    spreadsheet_id: str
    sheet_current: str
    sheet_previous: str


class GoogleSheetsStorage:
    """Persist run results into Google Sheets."""

    def __init__(self, config: SheetConfig | None = None) -> None:
        self._config = config or self._load_config_from_env()
        self._service = self._build_service()

    def write_run(self, rows: Iterable[dict]) -> None:
        """Move current data to previous sheet and write new results."""
        values = [list(COLUMNS)]
        for row in rows:
            values.append([row.get(column, "") for column in COLUMNS])

        self._copy_current_to_previous()
        self._write_values(self._config.sheet_current, values)

    def _copy_current_to_previous(self) -> None:
        current_values = self._read_values(self._config.sheet_current)
        if not current_values:
            return
        self._write_values(self._config.sheet_previous, current_values)

    def _read_values(self, sheet_name: str) -> list[list[str]]:
        response = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=self._config.spreadsheet_id, range=sheet_name)
            .execute()
        )
        return response.get("values", [])

    def _write_values(self, sheet_name: str, values: list[list[str]]) -> None:
        body = {"values": values}
        (
            self._service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self._config.spreadsheet_id,
                range=sheet_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )

    def _build_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            self._config.credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return build("sheets", "v4", credentials=credentials)

    @staticmethod
    def _load_config_from_env() -> SheetConfig:
        credentials_path = _get_env("GOOGLE_SHEETS_CREDENTIALS")
        spreadsheet_id = _get_env("GOOGLE_SHEET_ID")
        sheet_current = _get_env("SHEET_CURRENT_NAME")
        sheet_previous = _get_env("SHEET_PREVIOUS_NAME")
        return SheetConfig(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id,
            sheet_current=sheet_current,
            sheet_previous=sheet_previous,
        )


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
