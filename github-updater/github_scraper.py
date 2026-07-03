import requests
from utils import logger, retry_with_backoff
import os

class GitHubScraper:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Stats-Updater"
        }
        
        # Use token if available to avoid strict rate limits (60 req/hr vs 5000 req/hr)
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    @retry_with_backoff(max_retries=3)
    def scrape(self, username: str) -> dict:
        # 1. Get user profile
        user_url = f"{self.base_url}/users/{username}"
        user_resp = requests.get(user_url, headers=self.headers, timeout=10)
        
        if user_resp.status_code == 404:
            raise Exception(f"User '{username}' not found on GitHub")
        
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        # 2. Get user repositories to calculate total stars and forks
        repos_url = f"{self.base_url}/users/{username}/repos"
        # Fetch up to 100 repositories to aggregate stats
        params = {"per_page": 100, "type": "owner"}
        repos_resp = requests.get(repos_url, headers=self.headers, params=params, timeout=10)
        
        total_stars = 0
        total_forks = 0
        
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()
            for repo in repos_data:
                # Only count original repositories (not forks created by this user)
                if not repo.get("fork", False):
                    total_stars += repo.get("stargazers_count", 0)
                    total_forks += repo.get("forks_count", 0)
        else:
            logger.warning(f"Could not fetch repos for {username} to aggregate stars/forks (Status: {repos_resp.status_code})")
            
        return {
            "name": user_data.get("name"),
            "avatarUrl": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "company": user_data.get("company"),
            "blog": user_data.get("blog"),
            "publicRepos": user_data.get("public_repos", 0),
            "publicGists": user_data.get("public_gists", 0),
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
            "totalStars": total_stars,
            "totalForks": total_forks,
            "createdAt": user_data.get("created_at")
        }
