import json
import os
from datetime import datetime, timezone
from pathlib import Path
from youtube import YouTubeScraper
from utils import logger

def main():
    base_dir = Path(__file__).parent
    creators_file = base_dir / "creators.json"
    output_file = base_dir / "output.json"
    
    if not creators_file.exists():
        logger.error(f"Creators file not found at {creators_file}")
        return

    try:
        with open(creators_file, "r", encoding="utf-8") as f:
            creators = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read creators.json: {e}")
        return

    scraper = YouTubeScraper()
    results = []

    for creator in creators:
        logger.info(f"Loading creator...")
        logger.info(f"Opening channel...")
        
        try:
            logger.info("Extracting stats...")
            stats = scraper.scrape(creator.get('handle'))
            
            result = {
                "id": creator.get("id"),
                "name": creator.get("name"),
                "handle": creator.get("handle"),
                **stats,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            results.append(result)
        except Exception as e:
            result = {
                "id": creator.get("id"),
                "name": creator.get("name"),
                "handle": creator.get("handle"),
                "status": "failed",
                "reason": str(e),
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            results.append(result)

    logger.info("Writing JSON...")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        logger.info("Completed.")
    except Exception as e:
        logger.error(f"Failed to write output.json: {e}")

if __name__ == "__main__":
    main()
