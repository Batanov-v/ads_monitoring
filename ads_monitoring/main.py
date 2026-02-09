from __future__ import annotations

import logging

from ads_monitoring.compare import compare_pairs, format_comparison
from ads_monitoring.config import load_settings
from ads_monitoring.fetcher import collect_offers, count_pairs, offers_to_rows
from ads_monitoring.sheets import SheetsClient
from ads_monitoring.telegram import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    settings = load_settings()

    logger.info("Fetching offers from %s", settings.flocktory_url)
    offers = collect_offers(settings.flocktory_url, settings.request_timeout_seconds)
    logger.info("Fetched %s offers", len(offers))

    sheets = SheetsClient(
        sheet_id=settings.google_sheet_id,
        service_account_file=settings.google_service_account_file,
    )

    logger.info(
        "Rotating sheets: %s -> %s",
        settings.sheet_current_name,
        settings.sheet_previous_name,
    )
    previous_rows = sheets.rotate_current_to_previous(
        settings.sheet_current_name,
        settings.sheet_previous_name,
    )
    logger.info("Writing current offers to %s", settings.sheet_current_name)
    sheets.write_current(settings.sheet_current_name, offers_to_rows(offers))

    current_pairs = set(count_pairs(offers).keys())
    previous_pairs = set(
        (row[2], row[4]) for row in previous_rows if len(row) >= 5
    )
    comparison = compare_pairs(current_pairs, previous_pairs)
    message = format_comparison(comparison)
    logger.info("Sending Telegram notification")
    send_message(settings.telegram_bot_token, settings.telegram_channel_id, message)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("Ads monitoring run failed")
        raise
