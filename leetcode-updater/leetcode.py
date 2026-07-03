import requests
from utils import logger, retry_with_backoff

class LeetCodeScraper:
    def __init__(self):
        self.url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    @retry_with_backoff(max_retries=3)
    def scrape(self, username: str) -> dict:
        query = """
        query userPublicProfile($username: String!) {
            matchedUser(username: $username) {
                profile {
                    realName
                    userAvatar
                    aboutMe
                    school
                    websites
                    countryName
                    ranking
                    reputation
                }
                submitStats {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """
        
        variables = {"username": username}
        
        # Add referer specific to the user
        headers = self.headers.copy()
        headers["Referer"] = f"https://leetcode.com/{username}/"

        response = requests.post(
            self.url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
            
        matched_user = data.get("data", {}).get("matchedUser")
        if not matched_user:
            raise Exception(f"User '{username}' not found or empty matchedUser returned")
            
        profile = matched_user.get("profile", {}) or {}
        stats = matched_user.get("submitStats", {}).get("acSubmissionNum", [])
        
        # Extract stats
        solved_counts = {item.get("difficulty"): item.get("count") for item in stats}
        
        return {
            "realName": profile.get("realName"),
            "userAvatar": profile.get("userAvatar"),
            "aboutMe": profile.get("aboutMe"),
            "school": profile.get("school"),
            "websites": profile.get("websites", []),
            "countryName": profile.get("countryName"),
            "ranking": profile.get("ranking"),
            "reputation": profile.get("reputation"),
            "totalSolved": solved_counts.get("All", 0),
            "easySolved": solved_counts.get("Easy", 0),
            "mediumSolved": solved_counts.get("Medium", 0),
            "hardSolved": solved_counts.get("Hard", 0)
        }
