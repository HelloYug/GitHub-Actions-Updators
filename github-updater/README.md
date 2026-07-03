# GitHub Stats Updater

A Python script designed to scrape and update GitHub profile statistics using the official GitHub REST API. This tool is built to be run inside a GitHub Actions workflow to automatically fetch and save your statistics.

## Features

- **No Authentication Required (Mostly)**: Uses the public REST API, avoiding the need for browser automation.
- **Aggregated Stats**: Fetches followers, public repos, and aggregates **total stars** and **total forks** across all repositories.
- **Rate Limit Handling**: Supports `GITHUB_TOKEN` to bypass the 60 requests/hour limit (raises it to 5,000 requests/hour).
- **Fault-Tolerant**: Includes exponential backoff for reliability.
- **Clean JSON Output**: Emits structured statistics to `output.json`.

---

## Installation

1. Ensure you have Python 3.11+ installed.
2. Clone this repository and navigate to the `github-updater` directory.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Edit the `creators.json` file in the directory to include the target GitHub handles:

```json
[
    {
        "id": "1",
        "name": "Your Name",
        "handle": "YourGitHubHandle"
    }
]
```

*(Optional)* If you plan to scrape many profiles, set the `GITHUB_TOKEN` environment variable in your terminal or GitHub Action secrets.

*(Optional)*: If you want the JSON output to retain the raw strings (e.g., `"1.5M"`) instead of converting them to raw integers, open `utils.py` and set `PARSE_NUMBERS = False`.

---

## Running Locally

Run the main script:

```bash
python update.py
```

You should see clean logging indicating the progress:
```text
Extracting stats for YourGitHubHandle...
Successfully scraped YourGitHubHandle
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
        "handle": "YourGitHubHandle",
        "avatarUrl": "https://avatars.githubusercontent.com/u/...",
        "publicRepos": 16,
        "followers": 4,
        "following": 5,
        "totalStars": 15,
        "totalForks": 3,
        "last_updated": "2026-07-03T08:00:00Z"
    }
]
```

---

## 📜 Logging
This updater automatically generates an `updater.log` file tracking API calls, network state, and retry attempts. It employs **rolling logs**, meaning it will only retain the history of the last 5 execution sessions to keep your workspace clean (configurable via `MAX_LOG_SESSIONS` in `utils.py`).

---

## ⚠️ Limitations
The unauthenticated GitHub REST API is strictly limited to 60 requests per hour. You **MUST** provide a `GITHUB_TOKEN` secret in your GitHub Actions environment to increase this limit to 5,000 requests per hour if tracking many accounts.

---

## 💡 About
I originally built this scraper for my own personal projects. I've open-sourced it so that **anyone can use it** for their own portfolios or dashboards! Feel free to copy, fork, and adapt it however you like.
