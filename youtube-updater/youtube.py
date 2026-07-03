from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser
import json
import re

from utils import parse_number, retry_with_backoff, logger

class PlatformScraper(ABC):
    """Base class for future social media scrapers."""
    
    @abstractmethod
    def scrape(self, handle: str) -> Dict[str, Any]:
        """Scrapes the platform and returns a dictionary of stats."""
        pass

class YouTubeScraper(PlatformScraper):
    def __init__(self):
        self.base_url = "https://www.youtube.com/"
        
    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def _fetch_page(self, handle: str) -> str:
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page: Page = context.new_page()
            
            # Navigate to the channel home page
            url = f"{self.base_url}{handle}"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for main content to load
            try:
                page.wait_for_selector("yt-page-header-renderer", timeout=15000)
            except Exception:
                page.wait_for_timeout(5000)

            # Try to click the "More about this channel" chevron to load the about modal and get views/details
            try:
                page.locator("yt-description-preview-view-model").click(timeout=3000)
                page.wait_for_timeout(2000)
            except Exception:
                try:
                    page.locator("text=more about this channel").click(timeout=3000)
                    page.wait_for_timeout(2000)
                except Exception:
                    pass
                
            html = page.content()
            browser.close()
            return html

    def scrape(self, handle: str) -> Dict[str, Any]:
        html = self._fetch_page(handle)
        soup = BeautifulSoup(html, "lxml")
        
        # Core Stats
        subscribers_display = None
        views_display = None
        videos_display = None
        
        # Extended Metadata
        channel_id = None
        title = None
        description = None
        keywords = None
        is_family_safe = None
        avatar_url = None
        banner_url = None
        rss_url = None
        vanity_url = None
        joined_date = None
        country = None
        links = []
        
        # Strategy 1: Extract from ytInitialData (highly resilient to UI changes)
        script_tags = soup.find_all("script")
        yt_initial_data = None
        for script in script_tags:
            if script.string and "var ytInitialData =" in script.string:
                try:
                    match = re.search(r"var ytInitialData = ({.*?});", script.string)
                    if match:
                        yt_initial_data = json.loads(match.group(1))
                        break
                except Exception:
                    continue
                    
        if yt_initial_data:
            try:
                def search_dict(d, target_key):
                    if isinstance(d, dict):
                        if target_key in d:
                            return d[target_key]
                        for k, v in d.items():
                            res = search_dict(v, target_key)
                            if res is not None:
                                return res
                    elif isinstance(d, list):
                        for item in d:
                            res = search_dict(item, target_key)
                            if res is not None:
                                return res
                    return None
                    
                # Extract Subscribers
                sub_data = search_dict(yt_initial_data, "subscriberCountText")
                if sub_data and "simpleText" in sub_data:
                    sub_str = sub_data["simpleText"]
                    subscribers_display = sub_str.split(" ")[0]
                    
                # Extract Videos
                vid_data = search_dict(yt_initial_data, "videoCountText")
                if vid_data:
                    if "runs" in vid_data:
                        vid_str = "".join([r.get("text", "") for r in vid_data["runs"]])
                        videos_display = vid_str.split(" ")[0].replace(",", "")
                    elif "simpleText" in vid_data:
                        videos_display = vid_data["simpleText"].split(" ")[0].replace(",", "")
                        
                # Extract Views (might not be present unless about modal is loaded, but sometimes it is)
                view_data = search_dict(yt_initial_data, "viewCountText")
                if view_data and "simpleText" in view_data:
                    views_str = view_data["simpleText"]
                    views_display = views_str.split(" ")[0]

                # Extract Extended Metadata from channelMetadataRenderer
                metadata = search_dict(yt_initial_data, "channelMetadataRenderer")
                if metadata:
                    channel_id = metadata.get("externalId")
                    title = metadata.get("title")
                    description = metadata.get("description")
                    keywords = metadata.get("keywords")
                    is_family_safe = metadata.get("isFamilySafe")
                    rss_url = metadata.get("rssUrl")
                    vanity_url = metadata.get("vanityChannelUrl")
                    
                    if "avatar" in metadata and "thumbnails" in metadata["avatar"] and metadata["avatar"]["thumbnails"]:
                        avatar_url = metadata["avatar"]["thumbnails"][0].get("url")

                # Extract Banner
                header = search_dict(yt_initial_data, "pageHeaderRenderer") or search_dict(yt_initial_data, "c4TabbedHeaderRenderer")
                if header:
                    banner_data = header.get("banner") or header.get("tvBanner") or header.get("mobileBanner")
                    if banner_data and "thumbnails" in banner_data and banner_data["thumbnails"]:
                        banner_url = banner_data["thumbnails"][0].get("url")

                # Look for links in the data
                links_data = search_dict(yt_initial_data, "links")
                if links_data and isinstance(links_data, list):
                    for link_obj in links_data:
                        try:
                            # It's usually inside channelAboutFullMetadataRenderer -> primaryLinks
                            url = link_obj.get("navigationEndpoint", {}).get("urlEndpoint", {}).get("url")
                            if url:
                                # Clean up YouTube redirect URLs (e.g. https://www.youtube.com/redirect?q=https://...)
                                if "/redirect?q=" in url:
                                    import urllib.parse
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                                    if 'q' in parsed:
                                        url = parsed['q'][0]
                                links.append(url)
                        except Exception:
                            pass
            except Exception as e:
                pass

        # Strategy 2: Fallback to HTML text parsing for missing fields
        text_content = soup.get_text()
        
        if not subscribers_display:
            sub_match = re.search(r"([\d\.]+[KMBkmb]?)\s+subscribers", text_content)
            if sub_match:
                subscribers_display = sub_match.group(1)
        
        if not videos_display:
            vid_match = re.search(r"([\d,]+)\s+videos", text_content)
            if vid_match:
                videos_display = vid_match.group(1)
                
        if not views_display:
            view_match = re.search(r"([\d,]+)\s+views", text_content)
            if view_match:
                views_display = view_match.group(1)

        if not joined_date:
            joined_match = re.search(r"Joined\s+([A-Za-z]+\s+\d+,\s+\d{4})", text_content)
            if joined_match:
                joined_date = joined_match.group(1)

        # Look for country in text if not found yet (very naive regex for common locations)
        if not country:
            country_match = re.search(r"Location:\s*([A-Za-z\s]+)", text_content)
            if country_match:
                country = country_match.group(1).strip()

        # Fallback links extraction from actual anchor tags inside the about modal
        if not links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Filter out standard youtube internal links, grab external ones
                if href.startswith("http") and "youtube.com" not in href and "google.com" not in href:
                    if href not in links:
                        links.append(href)
                elif "/redirect?q=" in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'q' in parsed:
                        real_url = parsed['q'][0]
                        if real_url not in links:
                            links.append(real_url)

        if not subscribers_display:
            raise ValueError("Could not extract subscribers count. The page structure might have changed or you are being blocked.")
            
        result = {
            "metadata": {
                "channel_id": channel_id,
                "title": title,
                "description": description,
                "keywords": keywords,
                "is_family_safe": is_family_safe,
                "avatar_url": avatar_url,
                "banner_url": banner_url,
                "rss_url": rss_url,
                "vanity_url": vanity_url,
                "country": country,
                "joined_date": joined_date,
                "links": list(set(links))  # Deduplicate links
            },
            "subscribers": {
                "display": subscribers_display,
                "value": parse_number(subscribers_display)
            },
            "videos": {
                "display": videos_display or "0",
                "value": parse_number(videos_display) if videos_display else 0
            },
            "views": {
                "display": views_display or "0",
                "value": parse_number(views_display) if views_display else 0
            }
        }
        return result
