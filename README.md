# Social Media & Platform Stats Updaters

A unified collection of highly resilient, automated Python scrapers designed to run continuously in GitHub Actions. This repository extracts real-time statistics (followers, subscribers, coding metrics, etc.) across various platforms and outputs them as clean JSON data, which can then be seamlessly injected into personal portfolios, dashboards, or websites.

## 🚀 The Architecture

Instead of one monolithic script, this project is divided into **modular, platform-specific updaters**. Each platform has its own dedicated folder containing its logic, dependencies, and configurations. This ensures that if one platform's scraping method breaks, the others continue running unaffected.

Every updater follows the same core workflow:
1. Reads target handles from `creators.json`.
2. Scrapes the data via API or Browser Automation.
3. Formats the data and writes it to `output.json`.
4. (Optional) Commits the updated `output.json` back to the repository via GitHub Actions.

## 📦 Supported Platforms

| Platform | Extraction Method | Data Gathered | Speed / Reliability |
|----------|------------------|---------------|---------------------|
| **GitHub** | Official REST API | Followers, Repos, Total Stars, Total Forks | ⚡ Extremely Fast |
| **LeetCode** | Public GraphQL API | Global Rank, Total Solved, Difficulty Breakdown | ⚡ Extremely Fast |
| **YouTube** | Playwright (Browser Automation) | Subscribers, Total Videos, Total Views | 🐢 Moderate (High Reliability) |
| **Instagram** | Playwright & HTML Parsing | Followers, Following, Total Posts | 🐢 Moderate (Resilient to API limits) |
| **LinkedIn** | `linkedin-api` (Mobile App API) | Followers, Connections, Headline, Summary | ⚠️ Strict (Requires Dummy Account) |

## 🛠️ Global Setup & Templates

Since each updater is modular, they maintain their own `requirements.txt` and `creators.json`. 

**Not sure how to format `creators.json`?** 
We've included a `templates/` folder! Just copy `templates/creators.example.json` into any of the platform folders, rename it to `creators.json`, and add your handles!

To run any updater locally:

1. **Navigate to the target platform folder**:
   ```bash
   cd github-updater
   ```

2. **Install the specific dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: For YouTube and Instagram, you must also run `playwright install chromium`)*

3. **Configure the targets**:
   Edit the `creators.json` file inside the folder to include the usernames/handles you want to track.
   *(Optional)*: Open `utils.py` and set `PARSE_NUMBERS = False` if you want the output to retain raw formatted strings (e.g., `"1.5M"`) instead of converting them to raw integers (e.g., `1500000`).

4. **Run a single updater**:
   ```bash
   python update.py
   ```
   
5. **Or, run ALL updaters at once**:
   Simply run the master script from the root directory to execute every scraper sequentially:
   ```bash
   python run_all.py
   ```

## 🤖 GitHub Actions Integration

The primary purpose of this repository is automation. We have included a **ready-to-use** GitHub Action template at `templates/update-stats.example.yml`! Just copy it to `.github/workflows/update-stats.yml` in your repository!

This action is pre-configured to:
1. Run every Sunday at midnight (UTC) (Once a week).
2. Recursively install all dependencies for every platform.
3. Execute the `run_all.py` master script.
4. Automatically commit and push any changes back to your repository!

**Important Secrets for Automation:**
- `GITHUB_TOKEN`: (Optional but recommended for `github-updater` to increase rate limits to 5,000/hr).
- `LINKEDIN_USERNAME` & `LINKEDIN_PASSWORD`: (Strictly required for `linkedin-updater`. Always use a dummy account to prevent bans. If you do not provide these, the LinkedIn scraper will gracefully skip).

## 📜 Logging & Debugging

This project features a fully automated, rotating logging system to ensure debug traces are easily accessible without cluttering your workspace.

- **Master Execution Log**: Running `python run_all.py` generates a `run_all.log` in the root directory tracking the overall success/failure state and full error traces of every executed platform.
- **Individual Platform Logs**: Each platform maintains an `updater.log` inside its folder. It records detailed API calls, Playwright network states, and exponential backoff retry attempts.

**Log Rotation**: To prevent massive file sizes, the logging system automatically prunes itself! Both the master and individual logs are strictly bounded to retain only the last **5 execution sessions** (configurable via `MAX_LOG_SESSIONS` at the top of the scripts).

## ⚠️ Platform Limitations

Since we are scraping data directly, each platform has unique rate limits:
- **Instagram**: Aggressively monitors IPs. Do not scrape more than ~5-10 accounts sequentially.
- **LinkedIn**: Will instantly block automated traffic. The updater uses a simulated mobile API but strictly requires dummy credentials. Skip if you don't need it!
- **GitHub**: Unauthenticated REST API is limited to 60 req/hour. Use the `GITHUB_TOKEN` secret to bump this to 5,000/hour.
- **YouTube & LeetCode**: Very stable, but avoid sending hundreds of requests per minute to prevent temporary throttling.

## 💡 About & License

I originally built these updaters for my own personal portfolio projects to automate my statistics. I've open-sourced them as a tool on GitHub so that **anyone can use them** for their own portfolios or dashboards!

This project is available under the **[MIT License](LICENSE)**. Feel free to fork it, copy it, adapt it, and use it in any of your own projects!

---

## 👨‍💻 Author

**Yug Agarwal**

* 📧 Email – [yugagarwal704@gmail.com](mailto:yugagarwal704@gmail.com)
* 🔗 GitHub – [@HelloYug](https://github.com/HelloYug)
* 💼 LinkedIn – [yugagarwal704](https://www.linkedin.com/in/yugagarwal704/)
* 🌐 Portfolio – [yugagarwal.dev](https://yugagarwal.dev/?utm_source=github&utm_medium=readme&utm_campaign=GitHub-Actions-Updators_readme)
