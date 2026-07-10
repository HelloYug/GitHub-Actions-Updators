import re
import os
import json
import time
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup
from utils import parse_number, format_number, StructuredLogger, log_exception, ENABLE_DIAGNOSTICS, SAVE_HTML_ON_SUCCESS, SAVE_SCREENSHOTS

@dataclass
class StatValue:
    display: str
    value: int

@dataclass
class InstagramStats:
    followers: Optional[StatValue] = None
    following: Optional[StatValue] = None
    posts: Optional[StatValue] = None

class InstagramBlockError(Exception):
    """Raised when Instagram blocks access (redirect to login, checkpoint, rate limits, etc.)"""
    pass

class InstagramValidationError(Exception):
    """Raised when the profile page itself has non-recoverable issues (private, unavailable/404)"""
    pass

class InstagramScraper:
    def __init__(self, page, logger: StructuredLogger, debug_dir: str, enable_diagnostics: bool = ENABLE_DIAGNOSTICS, save_html_on_success: bool = SAVE_HTML_ON_SUCCESS, save_screenshots: bool = SAVE_SCREENSHOTS):
        self.page = page
        self.logger = logger
        self.debug_dir = debug_dir
        self.enable_diagnostics = enable_diagnostics
        self.save_html_on_success = save_html_on_success
        self.save_screenshots = save_screenshots

    def detect_page_state(self, url: str, title: str, content: str):
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        try:
            body_text = self.page.evaluate("() => document.body ? document.body.innerText : ''").lower()
        except Exception:
            body_text = ""
            
        # 1. Login redirects
        if "accounts/login" in url_lower or "/login/" in url_lower or "login" in title_lower:
            raise InstagramBlockError("Redirected to Instagram login page. Logged-out access is blocked for this IP.")
            
        # 2. Challenge / Consent / Checkpoints
        if "challenge" in url_lower or "checkpoint" in url_lower or "challenge" in title_lower or "checkpoint" in title_lower:
            raise InstagramBlockError("Redirected to Instagram challenge/checkpoint verification page.")
            
        # 3. Block messages / Rate limits / Captchas
        if "something went wrong" in body_text or "something went wrong" in title_lower:
            raise InstagramBlockError("Instagram returned 'Something went wrong' page.")
            
        if "please wait a few minutes" in body_text:
            raise InstagramBlockError("Instagram rate limit: 'Please wait a few minutes before you try again'.")
            
        if "suspicious activity" in body_text or "unusual activity" in body_text or "suspicious login" in body_text:
            raise InstagramBlockError("Blocked by Instagram's suspicious activity detection.")
            
        if "captcha" in body_text or "recaptcha" in body_text or re.search(r'\brobot\b', body_text):
            raise InstagramBlockError("Blocked by Captcha/Robot verification screen.")

        if "this page is unavailable" in body_text or "this page is not available" in body_text:
            raise InstagramBlockError("Instagram denied access to this page from this IP range.")

        if "for your security" in body_text or "security check" in body_text:
            raise InstagramBlockError("Instagram security check blocked this request from the runner IP.")

    def save_diagnostics(self, username: str):
        if not self.enable_diagnostics:
            self.logger.info("DIAGNOSTICS", "Diagnostics disabled. Skipping save.")
            return
            
        try:
            os.makedirs(self.debug_dir, exist_ok=True)
            html_path = os.path.join(self.debug_dir, f"{username}.html")
            png_path = os.path.join(self.debug_dir, f"{username}.png")
            
            url = self.page.url
            try:
                title = self.page.title()
            except Exception:
                title = "N/A"
                
            try:
                ua = self.page.evaluate("navigator.userAgent")
            except Exception:
                ua = "N/A"
                
            try:
                ready_state = self.page.evaluate("document.readyState")
            except Exception:
                ready_state = "N/A"
                
            self.logger.info("DIAGNOSTICS", f"URL: {url} | Title: {title} | UA: {ua} | ReadyState: {ready_state}")
            
            # Save HTML source
            content = self.page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info("DIAGNOSTICS", f"Saved HTML source to {html_path}")
            
            # Save Screenshot
            if self.save_screenshots:
                try:
                    self.page.screenshot(path=png_path, full_page=True, timeout=10000)
                    self.logger.info("DIAGNOSTICS", f"Saved full-page screenshot to {png_path}")
                except Exception as e:
                    # Fallback to standard viewport screenshot
                    try:
                        self.page.screenshot(path=png_path, full_page=False, timeout=5000)
                        self.logger.info("DIAGNOSTICS", f"Saved standard screenshot to {png_path}")
                    except Exception as e2:
                        self.logger.warning("DIAGNOSTICS", f"Failed to save screenshot: {e2}")
            else:
                self.logger.info("DIAGNOSTICS", "Screenshot saving disabled.")
        except Exception as e:
            self.logger.warning("DIAGNOSTICS", f"Diagnostics saving encountered error: {e}")

    def extract_from_json_ld(self, soup) -> Optional[InstagramStats]:
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string or '')
                    if not isinstance(data, dict):
                        continue
                    
                    # Target structure: ProfilePage or Person
                    main_entity = data.get("mainEntity")
                    if not main_entity or not isinstance(main_entity, dict):
                        if data.get("@type") == "Person":
                            main_entity = data
                        else:
                            continue
                            
                    interaction_stats = main_entity.get("interactionStatistic")
                    if not interaction_stats:
                        continue
                    if not isinstance(interaction_stats, list):
                        interaction_stats = [interaction_stats]
                        
                    followers_val = None
                    posts_val = None
                    
                    for stat in interaction_stats:
                        if not isinstance(stat, dict):
                            continue
                        it_type = stat.get("interactionType", "")
                        count = stat.get("userInteractionCount")
                        if count is None:
                            continue
                        try:
                            count = int(count)
                        except ValueError:
                            continue
                            
                        if "FollowAction" in it_type:
                            followers_val = count
                        elif "WriteAction" in it_type:
                            posts_val = count
                            
                    if followers_val is not None:
                        stats = InstagramStats()
                        stats.followers = StatValue(display=format_number(followers_val), value=followers_val)
                        if posts_val is not None:
                            stats.posts = StatValue(display=format_number(posts_val), value=posts_val)
                        self.logger.info("EXTRACTION", f"Strategy JSON-LD success: Followers={stats.followers.display}")
                        return stats
                except Exception as e:
                    self.logger.warning("EXTRACTION", f"JSON-LD element parsing failed: {e}")
        except Exception as e:
            self.logger.warning("EXTRACTION", f"JSON-LD strategy failed: {e}")
        return None

    def extract_from_meta_tags(self, soup) -> Optional[InstagramStats]:
        desc_attrs = [
            {'name': 'description'},
            {'property': 'og:description'},
            {'name': 'twitter:description'},
            {'property': 'og:title'},
        ]

        patterns = [
            r'([\d\.,KMkm]+)\s*Followers?,\s*([\d\.,KMkm]+)\s*Following,\s*([\d\.,KMkm]+)\s*Posts?',
            r'([\d\.,KMkm]+)\s*Followers?',
        ]

        best_stats = None
        best_precision_score = None

        def precision_score(display: str):
            if not display:
                return (-1, -1, -1)

            cleaned = str(display).strip().upper().replace(',', '')
            suffix = ''
            if cleaned.endswith('K'):
                suffix = 'K'
                cleaned = cleaned[:-1]
            elif cleaned.endswith('M'):
                suffix = 'M'
                cleaned = cleaned[:-1]
            elif cleaned.endswith('B'):
                suffix = 'B'
                cleaned = cleaned[:-1]

            if '.' in cleaned:
                whole, frac = cleaned.split('.', 1)
                decimal_places = len(frac)
            else:
                whole, decimal_places = cleaned, 0

            digits = len(whole.replace('.', ''))
            return (1 if '.' in cleaned else 0, decimal_places, digits)

        for attrs in desc_attrs:
            metas = soup.find_all('meta', attrs=attrs)
            for meta in metas:
                if not meta or not meta.get('content'):
                    continue
                content = meta['content']
                self.logger.info("EXTRACTION", f"Strategy Meta Check ({attrs}): {content}")

                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if not match:
                        continue

                    if pattern == patterns[0]:
                        f_display = match.group(1).upper()
                        fw_display = match.group(2).upper()
                        p_display = match.group(3).upper()

                        f_val = parse_number(f_display)
                        fw_val = parse_number(fw_display)
                        p_val = parse_number(p_display)

                        if f_val is None:
                            continue

                        stats = InstagramStats(
                            followers=StatValue(display=f_display, value=f_val),
                            following=StatValue(display=fw_display, value=fw_val) if fw_val is not None else None,
                            posts=StatValue(display=p_display, value=p_val) if p_val is not None else None
                        )
                    else:
                        f_display = match.group(1).upper()
                        f_val = parse_number(f_display)
                        if f_val is None:
                            continue
                        stats = InstagramStats(followers=StatValue(display=f_display, value=f_val))

                    candidate_value = stats.followers.value if stats and stats.followers else None
                    if candidate_value is None:
                        continue

                    candidate_score = precision_score(stats.followers.display)
                    if best_precision_score is None or candidate_score > best_precision_score:
                        best_precision_score = candidate_score
                        best_stats = stats

                    self.logger.info("EXTRACTION", f"Strategy Meta success: Followers={stats.followers.display}")

        if best_stats and best_stats.followers is not None:
            self.logger.info("EXTRACTION", f"Strategy Meta best match: Followers={best_stats.followers.display}")
            return best_stats

        return None

    def extract_from_embedded_json(self, soup) -> Optional[InstagramStats]:
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                content = script.string or ''
                if not content:
                    continue
                
                if 'window._sharedData' in content:
                    match = re.search(r'window\s*_\s*sharedData\s*=\s*({.*?});', content, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            user_data = data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})
                            if user_data:
                                f_val = user_data.get("edge_followed_by", {}).get("count")
                                fw_val = user_data.get("edge_follow", {}).get("count")
                                p_val = user_data.get("edge_owner_to_timeline_media", {}).get("count")
                                
                                if f_val is not None:
                                    stats = InstagramStats(
                                        followers=StatValue(display=format_number(f_val), value=int(f_val)),
                                        following=StatValue(display=format_number(fw_val), value=int(fw_val)) if fw_val is not None else None,
                                        posts=StatValue(display=format_number(p_val), value=int(p_val)) if p_val is not None else None
                                    )
                                    self.logger.info("EXTRACTION", f"Strategy Embedded JSON (_sharedData) success: Followers={stats.followers.display}")
                                    return stats
                        except Exception as e:
                            self.logger.warning("EXTRACTION", f"Failed parsing window._sharedData: {e}")
                            
                if 'window.__additionalDataLoaded' in content:
                    match = re.search(r'window\s*__additionalDataLoaded\s*\(\s*\'[^\']+\'\s*,\s*({.*?})\s*\);', content, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            user_data = data.get("graphql", {}).get("user", {})
                            if user_data:
                                f_val = user_data.get("edge_followed_by", {}).get("count")
                                fw_val = user_data.get("edge_follow", {}).get("count")
                                p_val = user_data.get("edge_owner_to_timeline_media", {}).get("count")
                                
                                if f_val is not None:
                                    stats = InstagramStats(
                                        followers=StatValue(display=format_number(f_val), value=int(f_val)),
                                        following=StatValue(display=format_number(fw_val), value=int(fw_val)) if fw_val is not None else None,
                                        posts=StatValue(display=format_number(p_val), value=int(p_val)) if p_val is not None else None
                                    )
                                    self.logger.info("EXTRACTION", f"Strategy Embedded JSON (__additionalDataLoaded) success: Followers={stats.followers.display}")
                                    return stats
                        except Exception as e:
                            self.logger.warning("EXTRACTION", f"Failed parsing window.__additionalDataLoaded: {e}")
        except Exception as e:
            self.logger.warning("EXTRACTION", f"Embedded JSON strategy failed: {e}")
        return None

    def extract_from_dom_selectors(self) -> Optional[InstagramStats]:
        try:
            result = self.page.evaluate('''() => {
                const findStat = (type) => {
                    const link = document.querySelector(`a[href$="/${type}/"]`, `a[href*="/${type}"]`);
                    if (link) {
                        const text = link.innerText || link.textContent;
                        if (text) return text;
                    }
                    
                    const ariaElements = document.querySelectorAll(`[aria-label*="${type}"], [title*="${type}"]`);
                    for (const el of ariaElements) {
                        const text = el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title');
                        if (text) return text;
                    }
                    
                    const header = document.querySelector('header');
                    if (header) {
                        const items = header.querySelectorAll('li, span');
                        for (const item of items) {
                            const text = item.innerText || item.textContent;
                            if (text && text.toLowerCase().includes(type)) {
                                return text;
                            }
                        }
                    }
                    return null;
                };
                
                return {
                    followers: findStat('follower'),
                    following: findStat('following'),
                    posts: findStat('post')
                };
            }''')
            
            followers_text = result.get('followers')
            following_text = result.get('following')
            posts_text = result.get('posts')
            
            def clean_stat_text(text, term):
                if not text:
                    return None
                match = re.search(r'([\d\.,KMkm]+)\s*' + term, text, re.IGNORECASE)
                if match:
                    return match.group(1).upper()
                match = re.search(r'([\d\.,KMkm]+)', text)
                if match:
                    return match.group(1).upper()
                return None

            f_display = clean_stat_text(followers_text, 'follower')
            fw_display = clean_stat_text(following_text, 'following')
            p_display = clean_stat_text(posts_text, 'post')
            
            f_val = parse_number(f_display) if f_display else None
            fw_val = parse_number(fw_display) if fw_display else None
            p_val = parse_number(p_display) if p_display else None
            
            if f_val is not None:
                stats = InstagramStats(
                    followers=StatValue(display=f_display, value=f_val),
                    following=StatValue(display=fw_display, value=fw_val) if fw_val is not None else None,
                    posts=StatValue(display=p_display, value=p_val) if p_val is not None else None
                )
                self.logger.info("EXTRACTION", f"Strategy DOM selectors success: Followers={stats.followers.display}")
                return stats
        except Exception as e:
            self.logger.warning("EXTRACTION", f"DOM selectors strategy failed: {e}")
        return None

    def get_profile_stats(self, username: str) -> InstagramStats:
        url = f"https://www.instagram.com/{username}/"
        max_nav_retries = 3
        backoff_factor = 3 # 3s, 9s, 27s
        
        # 1. Navigation Retry Loop
        for attempt in range(max_nav_retries):
            retry_num = attempt + 1
            start_time = time.time()
            self.logger.step(f"Starting navigation to {url} (attempt {retry_num}/{max_nav_retries})")
            self.logger.info("NAVIGATE", f"Attempting navigation to {url} (Attempt {retry_num}/{max_nav_retries})...")
            
            try:
                # Go to the url
                response = self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                status_code = response.status if response else "Unknown"
                self.logger.info("NAVIGATE", f"Initial page loaded. Status: {status_code}")
                
                # Wait for network idle or hydration timeout
                try:
                    self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    self.logger.info("NAVIGATE", "Timeout waiting for networkidle state. Continuing...")
                
                # Let Javascript fully hydrate the page and execute initial animations/injections
                self.page.wait_for_timeout(3000)
                
                # Save diagnostics immediately
                self.save_diagnostics(username)
                
                # Retrieve current state
                current_url = self.page.url
                try:
                    title = self.page.title()
                except Exception:
                    title = "N/A"
                content = self.page.content()
                
                # Check for blocks or redirection
                self.detect_page_state(current_url, title, content)
                
                self.logger.success("NAVIGATE", "Page loaded and validated successfully.", duration=time.time() - start_time)
                break # successfully navigated and validated
                
            except InstagramValidationError as e:
                # Non-recoverable validation errors: private profile, profile not found.
                # Do not retry. Fail immediately.
                duration = time.time() - start_time
                self.logger.failed("NAVIGATE", f"Validation error (non-recoverable): {e}", duration=duration)
                log_exception(username, e, self.page.url, self.page.title() if self.page else "N/A", retry_num, self.logger)
                raise e
                
            except Exception as e:
                # Recoverable errors: blocks, timeouts, network issues.
                duration = time.time() - start_time
                self.logger.failed("NAVIGATE", f"Navigation failed: {e}", duration=duration)
                log_exception(username, e, self.page.url if self.page else "N/A", self.page.title() if self.page else "N/A", retry_num, self.logger)
                
                if attempt == max_nav_retries - 1:
                    raise e
                    
                sleep_time = backoff_factor ** retry_num
                self.logger.info("NAVIGATE", f"Sleeping for {sleep_time}s before retrying navigation...")
                time.sleep(sleep_time)

        # 2. Statistical Extraction
        start_extract_time = time.time()
        self.logger.step("Starting multi-strategy extraction")
        self.logger.info("EXTRACTION", "Starting multi-strategy extraction...")
        
        try:
            soup = BeautifulSoup(self.page.content(), 'lxml')
            
            # Try Strategy 1: JSON-LD (structured data)
            stats = self.extract_from_json_ld(soup)
            if stats and stats.followers is not None:
                self.logger.success("EXTRACTION", f"Successfully extracted statistical data: Followers={stats.followers.display}", duration=time.time() - start_extract_time)
                return stats
                
            # Try Strategy 2: DOM Selectors (often the most precise, visible in page markup)
            stats = self.extract_from_dom_selectors()
            if stats and stats.followers is not None:
                self.logger.success("EXTRACTION", f"Successfully extracted statistical data: Followers={stats.followers.display}", duration=time.time() - start_extract_time)
                return stats

            # Try Strategy 3: SEO Meta Tags
            stats = self.extract_from_meta_tags(soup)
            if stats and stats.followers is not None:
                self.logger.success("EXTRACTION", f"Successfully extracted statistical data: Followers={stats.followers.display}", duration=time.time() - start_extract_time)
                return stats
                
            # Try Strategy 4: Embedded JSON
            stats = self.extract_from_embedded_json(soup)
            if stats and stats.followers is not None:
                self.logger.success("EXTRACTION", f"Successfully extracted statistical data: Followers={stats.followers.display}", duration=time.time() - start_extract_time)
                return stats
                
            raise Exception("All extraction strategies failed. Follower statistics could not be found in the DOM or metadata.")
            
        except Exception as e:
            duration = time.time() - start_extract_time
            self.logger.failed("EXTRACTION", f"Extraction failed: {e}", duration=duration)
            log_exception(username, e, self.page.url, self.page.title() if self.page else "N/A", 1, self.logger)
            raise e
