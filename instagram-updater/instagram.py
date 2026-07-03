import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup
from utils import parse_number

@dataclass
class StatValue:
    display: str
    value: int

@dataclass
class InstagramStats:
    followers: Optional[StatValue] = None
    following: Optional[StatValue] = None
    posts: Optional[StatValue] = None

class InstagramScraper:
    def __init__(self, page):
        self.page = page

    def get_profile_stats(self, username: str) -> InstagramStats:
        url = f"https://www.instagram.com/{username}/"
        
        try:
            # Wait for domcontentloaded; usually initial metadata is present then.
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Additional wait to let initial JS inject SEO tags if it's an SPA
            self.page.wait_for_timeout(2000)
            
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'lxml')
            
            stats = InstagramStats()
            
            # Primary Strategy: Scrape from DOM header stats (more precise)
            try:
                self.page.wait_for_selector('header', timeout=5000)
                li_texts = self.page.evaluate('''() => {
                    const elements = document.querySelectorAll('header li, header span');
                    return Array.from(elements).map(el => el.innerText || el.textContent);
                }''')
                
                for text in li_texts:
                    if not text: continue
                    text_lower = text.lower()
                    if 'follower' in text_lower:
                        val_str = text_lower.replace('followers', '').replace('follower', '').strip()
                        val = parse_number(val_str)
                        if val is not None and stats.followers is None:
                            stats.followers = StatValue(display=val_str, value=val)
                    elif 'following' in text_lower:
                        val_str = text_lower.replace('following', '').strip()
                        val = parse_number(val_str)
                        if val is not None and stats.following is None:
                            stats.following = StatValue(display=val_str, value=val)
                    elif 'post' in text_lower:
                        val_str = text_lower.replace('posts', '').replace('post', '').strip()
                        val = parse_number(val_str)
                        if val is not None and stats.posts is None:
                            stats.posts = StatValue(display=val_str, value=val)
                            
                if stats.followers is not None:
                    return stats
            except Exception:
                pass

            # Fallback Strategy: Extract from meta description (might be rounded)
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and 'content' in meta_desc.attrs:
                content = meta_desc['content']
                match = re.search(r'([\d\.,KM]+)\s*Followers?,\s*([\d\.,KM]+)\s*Following,\s*([\d\.,KM]+)\s*Posts?', content, re.IGNORECASE)
                if match:
                    f_display = match.group(1)
                    fw_display = match.group(2)
                    p_display = match.group(3)
                    
                    f_val = parse_number(f_display)
                    fw_val = parse_number(fw_display)
                    p_val = parse_number(p_display)
                    
                    if f_val is not None and stats.followers is None:
                        stats.followers = StatValue(display=f_display, value=f_val)
                    if fw_val is not None and stats.following is None:
                        stats.following = StatValue(display=fw_display, value=fw_val)
                    if p_val is not None and stats.posts is None:
                        stats.posts = StatValue(display=p_display, value=p_val)
                        
            return stats
            
        except Exception as e:
            raise Exception(f"Failed to scrape profile: {str(e)}")
