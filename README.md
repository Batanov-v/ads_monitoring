# Ads Monitoring

Скрипт каждый час собирает офферы со страницы Flocktory, пишет данные в Google Sheets (лист `current` и `previous`), сравнивает пары `domain + sale` и отправляет результат в Telegram.

## Требования
- Python 3.10+
- Доступ к странице офферов без авторизации
- Google Sheets API (Service Account)
- Telegram бот

## Настройка Google Sheets
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/), создайте проект.
2. Включите API: **Google Sheets API** и **Google Drive API**.
3. Создайте **Service Account** и скачайте JSON‑ключ.
4. Откройте таблицу Google Sheets и **поделитесь** с email сервисного аккаунта (например, `my-sa@project.iam.gserviceaccount.com`) с правами редактора.
5. Скопируйте `Spreadsheet ID` из URL таблицы (между `/d/` и `/edit`).

## Переменные окружения
Создайте файл `.env` (или задайте переменные окружения другим способом) по примеру `.env.example`:

- `FLOCKTORY_URL` — ссылка на страницу офферов.
- `GOOGLE_SHEET_ID` — ID таблицы.
- `GOOGLE_SERVICE_ACCOUNT_FILE` — путь к JSON ключу.
- `SHEET_CURRENT_NAME` — имя листа с текущими данными (`current`).
- `SHEET_PREVIOUS_NAME` — имя листа с предыдущими данными (`previous`).
- `TELEGRAM_BOT_TOKEN` — токен бота.
- `TELEGRAM_CHAT_ID` — ID получателя (можно чат/контакт).
- `REQUEST_TIMEOUT_SECONDS` — таймаут запросов.

## Установка
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск
```bash
python -m ads_monitoring.main
```

## Развертывание на PythonAnywhere (paid)
1. **Создайте виртуальное окружение**:
   ```bash
   mkvirtualenv ads_monitoring --python=python3.11
   pip install -r /home/<username>/ads_monitoring/requirements.txt
   ```
2. **Загрузите проект** в домашнюю директорию (например, `/home/<username>/ads_monitoring`).
3. **Сохраните JSON‑ключ** сервисного аккаунта (например, `/home/<username>/ads_monitoring/credentials.json`).
4. **Задайте переменные окружения** через вкладку **Files** → редактирование `~/.bashrc` или в секции **Web** → `Environment Variables`:
   ```bash
   export FLOCKTORY_URL="https://share.flocktory.com/exchange/login?ssid=6156&bid=16115"
   export GOOGLE_SHEET_ID="<spreadsheet_id>"
   export GOOGLE_SERVICE_ACCOUNT_FILE="/home/<username>/ads_monitoring/credentials.json"
   export SHEET_CURRENT_NAME="current"
   export SHEET_PREVIOUS_NAME="previous"
   export TELEGRAM_BOT_TOKEN="<token>"
   export TELEGRAM_CHAT_ID="<chat_id>"
   export REQUEST_TIMEOUT_SECONDS="30"
   ```
5. **Проверьте ручной запуск**:
   ```bash
   workon ads_monitoring
   python -m ads_monitoring.main
   ```
6. **Настройте расписание** через вкладку **Tasks**:
   - Command: `workon ads_monitoring && python -m ads_monitoring.main`
   - Schedule: `Every hour`

## Логика сравнения
Сравнение выполняется по парам `(domain, sale)` без учета порядка. Если изменений нет — отправляется сообщение `Изменений нет.`

## Структура листов Google Sheets
Листы `current` и `previous` имеют одинаковые колонки в порядке:
`id`, `site`, `domain`, `category`, `sale`, `conditions`, `motivationAmount`, `offerDuration`, `legalName`, `greenProbability`.
