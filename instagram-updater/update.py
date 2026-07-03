import json
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from instagram import InstagramScraper

def main():
    try:
        with open('creators.json', 'r', encoding='utf-8') as f:
            creators = json.load(f)
    except FileNotFoundError:
        print("Error: creators.json not found.")
        return

    output = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()
        scraper = InstagramScraper(page)

        for creator in creators:
            print("Loading creator...")
            username = creator.get('username')
            if not username:
                print(f"Error: No username provided for creator {creator.get('id')}")
                continue

            print("Opening Instagram profile...")
            
            try:
                # Add retry logic
                max_retries = 3
                stats = None
                for attempt in range(max_retries):
                    try:
                        print("Extracting statistics...")
                        stats = scraper.get_profile_stats(username)
                        if stats and stats.followers is not None:
                            break # successfully scraped
                        else:
                            time.sleep(2) # wait and retry if stats are missing
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        time.sleep(2)
                
                if stats and stats.followers is not None:
                    # Successful scrape
                    entry = {
                        "id": creator.get('id'),
                        "name": creator.get('name'),
                        "username": username,
                        "followers": {
                            "display": stats.followers.display,
                            "value": stats.followers.value
                        },
                        "following": {
                            "display": stats.following.display if stats.following else "0",
                            "value": stats.following.value if stats.following else 0
                        },
                        "posts": {
                            "display": stats.posts.display if stats.posts else "0",
                            "value": stats.posts.value if stats.posts else 0
                        },
                        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    }
                else:
                    raise Exception("Stats could not be extracted.")
            except Exception as e:
                entry = {
                    "id": creator.get('id'),
                    "name": creator.get('name'),
                    "username": username,
                    "status": "failed",
                    "reason": "Profile unavailable or scraping failed"
                }

            output.append(entry)

        browser.close()

    print("Writing JSON...")
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
        
    print("Completed.")

if __name__ == "__main__":
    main()
