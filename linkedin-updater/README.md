# LinkedIn Stats Updater

A Python script designed to scrape LinkedIn profile statistics (followers, connections, headline, summary, industry) using the unofficial `linkedin-api` Python package.

⚠️ **CRITICAL WARNING:** LinkedIn aggressively monitors and bans accounts that use automated scraping tools. 
- **DO NOT** use your main personal account credentials to run this script. 
- **DO NOT** run this script too frequently (e.g. limit to once a day).
- Create a secondary/dummy LinkedIn account to provide the credentials.

## Features

- **Simulated Mobile API**: Uses the `linkedin-api` package which mimics the official LinkedIn mobile app to bypass typical browser blockers.
- **Deep Insights**: Fetches detailed profile info including followers, connections, headline, summary, and industry.
- **Fault-Tolerant**: Implements exponential backoff for API reliability.
- **Clean JSON Output**: Emits structured statistics to `output.json`.

---

## Installation

1. Ensure you have Python 3.11+ installed.
2. Clone this repository and navigate to the `linkedin-updater` directory.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Add Secrets**: In your terminal or GitHub repository (if using Actions), set two environment variables:
   - `LINKEDIN_USERNAME`: The email of your dummy account.
   - `LINKEDIN_PASSWORD`: The password of your dummy account.
2. Edit the `creators.json` file with the target LinkedIn handles (the part of the URL after `linkedin.com/in/`):

```json
[
    {
        "id": "1",
        "name": "Your Name",
        "handle": "your-linkedin-handle"
    }
]
```

*(Optional)*: If you want the JSON output to retain the raw strings (e.g., `"1.5M"`) instead of converting them to raw integers, open `utils.py` and set `PARSE_NUMBERS = False`.

---

## Running Locally

Run the main script:

```bash
# Example for Windows
set LINKEDIN_USERNAME=dummy@email.com
set LINKEDIN_PASSWORD=dummy_password
python update.py
```

---

## Expected Output

The script generates (or overwrites) an `output.json` file structured as follows:

```json
[
    {
        "id": "1",
        "name": "Your Name",
        "handle": "your-linkedin-handle",
        "followersCount": 500,
        "connectionsCount": 490,
        "headline": "Software Engineer",
        "last_updated": "2026-07-03T08:00:00Z"
    }
]
```

---

## 📜 Logging
This updater automatically generates an `updater.log` file tracking API calls, network state, and retry attempts. It employs **rolling logs**, meaning it will only retain the history of the last 5 execution sessions to keep your workspace clean (configurable via `MAX_LOG_SESSIONS` in `utils.py`).

---

## ⚠️ Limitations
LinkedIn aggressively monitors and bans accounts that use automated scraping tools. Do not scrape more than ~5 accounts per day. **DO NOT** use your main personal account credentials. If credentials are not provided, the scraper will gracefully skip execution.

---

## 💡 About
I originally built this scraper for my own personal projects. I've open-sourced it so that **anyone can use it** for their own portfolios or dashboards! Feel free to copy, fork, and adapt it however you like.
