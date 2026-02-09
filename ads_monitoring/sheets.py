from __future__ import annotations

from typing import Iterable

import gspread
from google.oauth2.service_account import Credentials

from ads_monitoring.fetcher import FIELDS


class SheetsClient:
    def __init__(self, sheet_id: str, service_account_file: str) -> None:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_file(
            service_account_file,
            scopes=scopes,
        )
        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(sheet_id)

    def ensure_sheet(self, sheet_name: str, headers: list[str]) -> gspread.Worksheet:
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=len(headers))
            sheet.append_row(headers)
        else:
            existing_headers = sheet.row_values(1)
            if existing_headers != headers:
                sheet.resize(rows=max(sheet.row_count, 2), cols=len(headers))
                sheet.update("1:1", [headers])
        return sheet

    def read_rows(self, sheet: gspread.Worksheet) -> list[list[str]]:
        values = sheet.get_all_values()
        return values[1:] if len(values) > 1 else []

    def overwrite(self, sheet: gspread.Worksheet, rows: Iterable[Iterable[str]]) -> None:
        data = [FIELDS, *rows]
        sheet.clear()
        sheet.update(data)

    def rotate_current_to_previous(
        self,
        current_sheet_name: str,
        previous_sheet_name: str,
    ) -> list[list[str]]:
        current_sheet = self.ensure_sheet(current_sheet_name, FIELDS)
        previous_sheet = self.ensure_sheet(previous_sheet_name, FIELDS)
        current_rows = self.read_rows(current_sheet)
        self.overwrite(previous_sheet, current_rows)
        return current_rows

    def write_current(self, sheet_name: str, rows: Iterable[Iterable[str]]) -> None:
        sheet = self.ensure_sheet(sheet_name, FIELDS)
        self.overwrite(sheet, rows)
