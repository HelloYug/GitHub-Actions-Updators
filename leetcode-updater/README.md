# LeetCode Stats Updater

A Python script designed to scrape and update LeetCode profile statistics using the public LeetCode GraphQL API. This tool is built to be run inside a GitHub Actions workflow to automatically fetch and save your statistics.

## Features

- **No Browser Automation**: Uses LeetCode's public GraphQL API for extremely fast, reliable scraping without Playwright.
- **Comprehensive Stats**: Fetches global ranking, reputation, total solved, and difficulty breakdown (Easy/Medium/Hard).
- **Fault-Tolerant**: Implements retries and handles unavailable profiles gracefully.
- **Clean JSON Output**: Emits structured statistics to `output.json`.

---

## Installation

1. Ensure you have Python 3.11+ installed.
2. Clone this repository and navigate to the `leetcode-updater` directory.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Edit the `creators.json` file in the directory to include the target LeetCode handles:

```json
[
    {
        "id": "1",
        "name": "Your Name",
        "handle": "YourLeetCodeHandle"
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
Extracting stats for YourLeetCodeHandle...
Successfully scraped YourLeetCodeHandle
Writing JSON...
Completed.
```

---

## Expected Output

The script generates (or overwrites) an `output.json` file structured as follows:

```json
[
    {
        "id": "1",
        "name": "Your Name",
        "handle": "YourLeetCodeHandle",
        "ranking": 1331877,
        "reputation": 0,
        "totalSolved": 121,
        "easySolved": 69,
        "mediumSolved": 48,
        "hardSolved": 4,
        "last_updated": "2026-07-03T08:00:00Z"
    }
]
```

---

## 📜 Logging
This updater automatically generates an `updater.log` file tracking API calls, network state, and retry attempts. It employs **rolling logs**, meaning it will only retain the history of the last 5 execution sessions to keep your workspace clean (configurable via `MAX_LOG_SESSIONS` in `utils.py`).

---

## ⚠️ Limitations
The GraphQL API is public and very stable, but avoid sending hundreds of requests per minute to prevent your IP from being temporarily throttled by LeetCode.

---

## 💡 About
I originally built this scraper for my own personal projects. I've open-sourced it so that **anyone can use it** for their own portfolios or dashboards! Feel free to copy, fork, and adapt it however you like.
