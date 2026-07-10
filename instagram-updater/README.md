# Instagram Public Profile Stats Updater

A completely standalone, highly resilient Python-based scraper that fetches public Instagram profile statistics (followers, following, posts counts) **without using any official Meta Graph APIs or Facebook APIs**.

This project extracts metadata organically from public profile pages using Playwright, BeautifulSoup, and LXML, prioritizing structured embedded data (e.g., SEO meta tags, JSON-LD, DOM selectors) to provide robust extraction with multiple fallback strategies.

## Features

- **No Official APIs Used**: Works without Meta/Facebook API keys, tokens, or app approvals.
- **Multi-Strategy Extraction**: Uses 4 different extraction methods (JSON-LD, DOM selectors, Meta tags, Embedded JSON) with intelligent fallbacks.
- **Robust Number Parsing**: Accurately interprets numbers like `1.2K`, `2.5M`, `1,200`.
- **Sophisticated Error Handling**: Distinguishes between recoverable errors (rate limits, blocks) and non-recoverable errors (private profiles).
- **Fault-Tolerant**: Implements retries with exponential backoff and handles unavailable or private profiles gracefully.
- **Structured Logging**: Comprehensive logging with step-level progress messages, timestamps, and per-profile debug logs.
- **Automated**: Includes a GitHub Actions workflow to run scraping on a schedule.

---

## Installation

### Prerequisites
- Python 3.11+
- Git

### Setup

1. **Navigate to the Directory**:
   ```bash
   cd instagram-updater
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright Browsers**:
   This project requires Playwright's Chromium browser to render dynamic pages.
   ```bash
   playwright install chromium
   ```

---

## Configuration: Adding Creators

Edit the `creators.json` file in this directory. Add the creators you want to track using the following structure:

```json
[
    {
        "id": 1,
        "name": "Your Creator Name",
        "username": "instagram_username"
    },
    {
        "id": 2,
        "name": "Another Creator",
        "username": "another_username"
    }
]
```

Each creator object requires:
- `id`: A unique numeric identifier
- `name`: Display name for the creator
- `username`: Instagram username (without the @ symbol)

---

## Running Locally

To start the scraper:

```bash
python update.py
```

You should see detailed structured logging indicating progress:
```text
[2026-07-09 13:50:05] [SYSTEM] [SYSTEM] [N/A] [INFO] Starting Instagram Profile Stats Updater...
[2026-07-09 13:50:12] [username] [PROCESS] [N/A] [INFO] Starting scraping process for 'Creator Name' (@username)...
[2026-07-09 13:50:19] [username] [PROCESS] [N/A] [SUCCESS] Updated username followers to 471K
```

---

## Output

The script updates the `creators.json` file in-place, adding or updating the `followers` field for each successfully scraped creator:

```json
[
    {
        "id": 1,
        "name": "Your Creator Name",
        "username": "instagram_username",
        "followers": "125K"
    }
]
```

---

## Logging and Debugging

- **Console Output**: Structured and includes timestamps, usernames, operations, and status values.
- **Per-Profile Logs**: Written to the `debug/` folder with detailed extraction attempts and errors.
- **Diagnostics**: HTML snapshots and full-page screenshots are saved in `debug/` for blocked or failed profiles.
- **Log Rotation**: Old log sessions are automatically rotated to keep the log file manageable.

---

## GitHub Actions Workflow

The repository includes a workflow that:
- Runs on a schedule (typically every 3 days)
- Supports manual execution with `workflow_dispatch`
- Installs dependencies and Playwright Chromium
- Runs the updater
- Commits any changes to the data file

---

## Troubleshooting

### Playwright Installation Issues
If Playwright fails to launch, run:
```bash
playwright install chromium
```

### Instagram Blocking
- If Instagram blocks the request from your IP, the scraper will log this as an external block error and continue gracefully.
- Consider running from a different network or using a VPN if blocks persist.

### Private or Unavailable Profiles
- If a profile is private, suspended, or deleted, the scraper will record the failure and continue with other profiles.
- Check the per-profile logs in `debug/` for detailed error messages.

### Debugging Failed Extractions
- Check `debug/{username}.log` for step-by-step extraction logs.
- Check `debug/{username}.html` for the raw page content.
- Check `debug/{username}.png` for a screenshot of what was rendered.

---

## Advanced Configuration

In `utils.py`, you can customize:
- `ENABLE_FILE_LOGGING`: Set to `True` to enable file logging (default: `False`)
- `MAX_LOG_SESSIONS`: Maximum number of log sessions to keep (default: `4`)
- `PARSE_NUMBERS`: Set to `False` to keep raw strings like `"1.2K"` instead of converting to integers (default: `True`)
        "posts": {
            "display": "486",
            "value": 486
        },
        "last_updated": "2026-07-02T18:42:11Z"
    }
]
```

If a profile fails (e.g., deleted or private), it will log a failed status:
```json
{
    "status": "failed",
    "reason": "Profile unavailable or scraping failed"
}
```

---

## GitHub Actions Automation

A workflow file is included at `.github/workflows/instagram-updater.yml`.

**What it does:**
- Runs automatically every 24 hours via a `schedule` (cron).
- Supports manual execution via `workflow_dispatch`.
- Installs all dependencies (including Playwright Chromium) utilizing caching to speed up the process.
- Executes `update.py`.
- Commits changes to `output.json` directly back to the branch only if the file has changed (preventing empty commit loops).

---

## Troubleshooting

- **Playwright Errors**: If you encounter browser launch errors, make sure you ran `playwright install chromium`. 
- **Timeouts**: Scraping heavily relies on the internet connection speed. Playwright wait timeouts might need adjustment in `instagram.py` if pages load exceptionally slowly.
- **Missing Stats**: If Instagram changes their layout or removes public meta tags, the scraper may fail to extract data. It will fallback to DOM extraction. If both fail, it logs failure and continues.

---

## 📜 Logging
This updater automatically generates an `updater.log` file tracking API calls, network state, and retry attempts. It employs **rolling logs**, meaning it will only retain the history of the last 5 execution sessions to keep your workspace clean (configurable via `MAX_LOG_SESSIONS` in `utils.py`).

---

## ⚠️ Limitations
Instagram aggressively monitors scraping. Do not scrape more than ~5-10 accounts sequentially. If running locally, you might get an IP block. GitHub Actions datacenter IPs are more resilient but can still be flagged.

---

## 💡 About
I originally built this scraper for my own personal projects. I've open-sourced it so that **anyone can use it** for their own portfolios or dashboards! Feel free to copy, fork, and adapt it however you like.
