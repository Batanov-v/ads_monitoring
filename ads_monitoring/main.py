from __future__ import annotations

import logging

from ads_monitoring.compare import compare_pairs, format_comparison
from ads_monitoring.config import load_settings
from ads_monitoring.fetcher import collect_offers, count_pairs, offers_to_rows
from ads_monitoring.sheets import SheetsClient
from ads_monitoring.telegram_client import send_notifications

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run() -> None:
    settings = load_settings()

    logging.info("Fetching offers from %s", settings.flocktory_url)
    offers = collect_offers(settings.flocktory_url, settings.request_timeout_seconds)
    logging.info("Fetched %s offers", len(offers))

    sheets = SheetsClient(
        sheet_id=settings.google_sheet_id,
        service_account_file=settings.google_service_account_file,
    )

    logging.info("Rotating sheets: %s -> %s", settings.sheet_current_name, settings.sheet_previous_name)
    previous_rows = sheets.rotate_current_to_previous(
        settings.sheet_current_name,
        settings.sheet_previous_name,
    )
    logging.info("Writing current offers to %s", settings.sheet_current_name)
    sheets.write_current(settings.sheet_current_name, offers_to_rows(offers))

    current_pairs = set(count_pairs(offers).keys())
    previous_pairs = set(
        (row[2], row[4]) for row in previous_rows if len(row) >= 5
    )
    comparison = compare_pairs(current_pairs, previous_pairs)
    message = format_comparison(comparison)
    logging.info("Sending Telegram notification")
    send_notifications(
        settings.telegram_api_id,
        settings.telegram_api_hash,
        settings.telegram_session_file,
        settings.telegram_contacts,
        message,
    )


if __name__ == "__main__":
    run()
