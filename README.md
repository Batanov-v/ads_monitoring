# Ads Monitoring

## Fetching offers

A helper script is available in `scripts/fetch_offers.py` to authenticate (if needed), load the offers page, and parse the offers table into structured JSON.

### Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `FLOCKTORY_LOGIN_URL` | Login URL (with `ssid`/`bid` if needed). | `https://share.flocktory.com/exchange/login?ssid=6156&bid=16115` |
| `FLOCKTORY_OFFERS_URL` | URL of the offers table (can match login URL if the same page contains the table). | `FLOCKTORY_LOGIN_URL` |
| `FLOCKTORY_USERNAME` | Username for login (optional). | _unset_ |
| `FLOCKTORY_PASSWORD` | Password for login (optional). | _unset_ |
| `FLOCKTORY_USERNAME_FIELD` | Form field name for username. | `login` |
| `FLOCKTORY_PASSWORD_FIELD` | Form field name for password. | `password` |
| `FLOCKTORY_LOGIN_PAYLOAD_JSON` | Optional JSON string with extra POST fields (e.g. CSRF token). | _unset_ |

### Usage

```bash
pip install requests beautifulsoup4
./scripts/fetch_offers.py > offers.json
```

The script returns a JSON array of offers with the following fields:
`id`, `site`, `domain`, `category`, `sale`, `conditions`, `motivationAmount`, `offerDuration`, `legalName`, `greenProbability`.
