import os
from utils import logger, retry_with_backoff

class LinkedInScraper:
    def __init__(self):
        try:
            # pyrefly: ignore [missing-import]
            from linkedin_api import Linkedin
        except ImportError:
            logger.warning("⚠️ linkedin_api package is not installed. Skipping.")
            self.api = None
            return
        self.username = os.environ.get("LINKEDIN_USERNAME")
        self.password = os.environ.get("LINKEDIN_PASSWORD")
        
        if not self.username or not self.password:
            logger.warning("⚠️ LINKEDIN_USERNAME and/or LINKEDIN_PASSWORD environment variables are missing.")
            logger.warning("Please set these to a DUMMY LinkedIn account in your GitHub Secrets.")
            self.api = None
            return
            
        try:
            logger.info("Authenticating with LinkedIn...")
            self.api = Linkedin(self.username, self.password)
            logger.info("Successfully authenticated.")
        except Exception as e:
            logger.error(f"Failed to authenticate with LinkedIn: {e}")
            self.api = None

    @retry_with_backoff(max_retries=3, initial_delay=5.0)
    def scrape(self, profile_id: str) -> dict:
        if not self.api:
            raise Exception("LinkedIn API not initialized. Missing credentials or blocked by LinkedIn.")
            
        logger.info(f"Fetching profile data for {profile_id}...")
        profile = self.api.get_profile(profile_id)
        
        if not profile:
            raise Exception(f"User '{profile_id}' not found on LinkedIn")
            
        # Network stats (followers, connections) require a separate call
        logger.info(f"Fetching network info for {profile_id}...")
        try:
            network_info = self.api.get_profile_network_info(profile_id)
        except Exception as e:
            logger.warning(f"Could not fetch network info: {e}")
            network_info = {}
            
        # Display picture handling
        display_pic = None
        if profile.get("displayPictureUrl"):
            display_pic = profile.get("displayPictureUrl")

        return {
            "firstName": profile.get("firstName"),
            "lastName": profile.get("lastName"),
            "headline": profile.get("headline"),
            "summary": profile.get("summary"),
            "industryName": profile.get("industryName"),
            "locationName": profile.get("locationName"),
            "followersCount": network_info.get("followersCount", 0) if network_info else 0,
            "connectionsCount": network_info.get("connectionsCount", 0) if network_info else 0,
            "displayPictureUrl": display_pic
        }
