# YouTube Public Profile Stats Updater

A standalone Python utility for scraping YouTube statistics (subscribers, videos, views) without relying on official Google/YouTube APIs. 

This tool uses Playwright to programmatically fetch public information from a YouTube channel page, parsing internal data objects to extract accurate statistics.

## Features

- **No Official APIs Used**: Works without YouTube Data API v3 keys or quota limits.
- **Robust Number Parsing**: Accurately extracts numbers from raw HTML/JSON sources.
- **Fault-Tolerant**: Implements retries and handles unavailable profiles gracefully without crashing.
- **Clean JSON Output**: Emits structured statistics to `output.json` for easy integration.

---

## Installation

1. Ensure you have Python 3.11+ installed.
2. Clone this repository and navigate to the `youtube-updater` directory.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browsers (Requires Playwright's Chromium browser to render dynamic pages):
   ```bash
   playwright install chromium
   ```

---

## Configuration

Edit the `creators.json` file in the directory to include the target YouTube handles (including the `@`):

```json
[
    {
        "id": 1,
        "name": "Fearless Innocent Math",
        "handle": "@dr.anuj.fearlessinnocentmath"
    }
]
```

*(Optional)*: If you want the JSON output to retain the raw strings (e.g., `"1.5M"`) instead of converting them to raw integers, open `utils.py` and set `PARSE_NUMBERS = False`.

---

## Running Locally

Run the main script:

```bash
python update.py
```

You should see clean logging indicating the progress:
```text
Loading creator...
Opening channel...
Extracting stats...
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
        "handle": "@dr.anuj.fearlessinnocentmath",
        "subscribers": {
            "display": "1.24M",
            "value": 1240000
        },
        "videos": {
            "display": "842",
            "value": 842
        },
        "views": {
            "display": "215M",
            "value": 215000000
        },
        "last_updated": "2026-07-02T18:30:12Z"
    }
]
```

---

## 📜 Logging
This updater automatically generates an `updater.log` file tracking API calls, network state, and retry attempts. It employs **rolling logs**, meaning it will only retain the history of the last 5 execution sessions to keep your workspace clean (configurable via `MAX_LOG_SESSIONS` in `utils.py`).

---

## ⚠️ Limitations
YouTube is highly reliable but heavily limits concurrent Playwright instances. Scraping dozens of channels sequentially might take a few minutes, but it is very unlikely to result in an IP block.

---

## 💡 About
I originally built this scraper for my own personal projects. I've open-sourced it so that **anyone can use it** for their own portfolios or dashboards! Feel free to copy, fork, and adapt it however you like.
