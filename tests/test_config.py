import os
import tempfile
import unittest

from ads_monitoring.config import load_settings


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_load_settings_validates_path_and_timeout(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            os.environ.update(
                {
                    "FLOCKTORY_URL": "https://example.com",
                    "GOOGLE_SHEET_ID": "sheet_id",
                    "GOOGLE_SERVICE_ACCOUNT_FILE": tmp.name,
                    "SHEET_CURRENT_NAME": "current",
                    "SHEET_PREVIOUS_NAME": "previous",
                    "TELEGRAM_BOT_TOKEN": "token",
                    "TELEGRAM_CHANNEL_ID": "@channel",
                    "REQUEST_TIMEOUT_SECONDS": "15",
                }
            )
            settings = load_settings()
            self.assertEqual(settings.request_timeout_seconds, 15)
            self.assertEqual(settings.google_service_account_file, tmp.name)


if __name__ == "__main__":
    unittest.main()
