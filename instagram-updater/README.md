# Instagram Public Profile Stats Updater

A completely standalone, highly resilient Python-based scraper that fetches public Instagram profile statistics (followers, following, posts counts) **without using any official Meta Graph APIs or Facebook APIs**.

This project extracts metadata organically from public profile pages using Playwright, BeautifulSoup, and LXML, prioritizing structured embedded data (e.g., SEO meta tags) to avoid brittle DOM selectors.

## Features

- **No Official APIs Used**: Works without Meta/Facebook API keys, tokens, or app approvals.
- **Robust Number Parsing**: Accurately interprets numbers like `1.2K`, `2.5M`, `1,200`.
- **Fault-Tolerant**: Implements retries and handles unavailable or private profiles gracefully without crashing.
- **Clean JSON Output**: Emits structured statistics to `output.json` for easy integration.
- **Automated**: Includes a GitHub Actions workflow to run scraping daily.

---

## Installation

### Prerequisites
- Python 3.11+
- Git

### Setup

1. **Clone or Navigate to the Directory**:
   Ensure you are in the `instagram-updater` directory.

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

Edit the `creators.json` file in the root directory. Add the creators you want to track using the following structure:

```json
[
    {
        "id": 1,
        "name": "Fearless Innocent Math",
        "username": "dr.anuj.fearlessinnocentmath"
    },
    {
        "id": 2,
        "name": "Another Creator",
        "username": "creator_username"
    }
]
```

*(Optional)*: If you want the JSON output to retain the raw strings (e.g., `"1.5M"`) instead of converting them to raw integers, open `utils.py` and set `PARSE_NUMBERS = False`.

---

## Running Locally

To start the scraper:

```bash
python update.py
```

You should see clean logging indicating the progress:
```text
Loading creator...
Opening Instagram profile...
Extracting statistics...
Writing JSON...
Completed.
```

---

## Expected Output

The script generates (or overwrites) an `output.json` file structured as follows:

```json
[
    {
        "id": 1,
        "name": "Fearless Innocent Math",
        "username": "dr.anuj.fearlessinnocentmath",
        "followers": {
            "display": "125K",
            "value": 125000
        },
        "following": {
            "display": "12",
            "value": 12
        },
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
