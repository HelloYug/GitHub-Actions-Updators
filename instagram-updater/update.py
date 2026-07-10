import json
import time
import random
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
from instagram import InstagramScraper
from utils import StructuredLogger, format_number, ENABLE_DIAGNOSTICS, SAVE_HTML_ON_SUCCESS, SAVE_SCREENSHOTS


def is_external_block_error(details):
    if not details:
        return False

    details_lower = str(details).lower()
    block_keywords = [
        "redirected to instagram login page",
        "logged-out access is blocked",
        "challenge",
        "checkpoint",
        "captcha",
        "suspicious activity",
        "rate limit",
        "something went wrong",
    ]
    return any(keyword in details_lower for keyword in block_keywords)


def determine_exit_code(results):
    if not results:
        return 1

    success_count = sum(1 for result in results if result.get("status") == "SUCCESS")
    if success_count > 0:
        return 0

    failed_results = [result for result in results if result.get("status") == "FAIL"]
    if failed_results and all(is_external_block_error(result.get("details")) for result in failed_results):
        return 0

    return 1


def setup_page_listeners(page, log_file_path):
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, 'w', encoding='utf-8') as f:
        f.write("=== PLAYWRIGHT CONSOLE AND NETWORK LOGS ===\n")
        
    def on_console(msg):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [CONSOLE] [{msg.type}] {msg.text}\n"
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass

    def on_request_failed(request):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            err = request.failure.error_text if request.failure else "Unknown Error"
            log_line = f"[{timestamp}] [NETWORK_FAILURE] {request.method} {request.url} - Error: {err}\n"
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass

    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)
    
    def cleanup():
        try:
            page.remove_listener("console", on_console)
        except Exception:
            pass
        try:
            page.remove_listener("requestfailed", on_request_failed)
        except Exception:
            pass
            
    return cleanup

def main():
    logger = StructuredLogger(username="SYSTEM")
    logger.info("SYSTEM", "Starting Instagram Profile Stats Updater...")
    
    json_path = os.path.join(os.path.dirname(__file__), 'creators.json')
    json_path = os.path.abspath(json_path)
    
    output_path = os.path.join(os.path.dirname(__file__), 'output.json')
    output_path = os.path.abspath(output_path)
    
    debug_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'debug'))
    os.makedirs(debug_dir, exist_ok=True)
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            creators = json.load(f)
    except FileNotFoundError:
        logger.failed("SYSTEM", f"JSON data file not found at: {json_path}")
        sys.exit(1)
    
    # Ensure it's a list
    if not isinstance(creators, list):
        logger.failed("SYSTEM", "creators.json must contain a list of creator objects")
        sys.exit(1)
        
    results = []
    output_data = []
    any_failures = False
    
    with sync_playwright() as p:
        # Launch Chromium with stealth args
        try:
            logger.info("SYSTEM", "Launching Chromium browser via Playwright...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
        except Exception as e:
            logger.warning("SYSTEM", f"Failed to launch Chromium via Playwright ({e}).")
            raise
            
        # Get default user agent of browser and strip Headless
        temp_ctx = browser.new_context()
        temp_page = temp_ctx.new_page()
        default_ua = temp_page.evaluate("navigator.userAgent")
        temp_ctx.close()
        
        stealth_ua = default_ua.replace("HeadlessChrome/", "Chrome/").replace("Headless", "")
        
        first_run = True
        for idx, creator in enumerate(creators):
            name = creator.get('name', 'Unknown')
            username = creator.get('username')
            creator_id = creator.get('id', idx + 1)
            logger.set_username(username if username else "UNKNOWN")
            
            if not username:
                logger.failed("PROCESS", f"No username provided for creator {idx}")
                results.append({
                    "name": name,
                    "username": "N/A",
                    "status": "FAIL",
                    "status_icon": "❌",
                    "followers": "N/A",
                    "details": "Missing username in JSON config"
                })
                output_data.append({
                    "id": creator_id,
                    "name": name,
                    "username": "N/A",
                    "status": "failed",
                    "reason": "Missing username in JSON config"
                })
                any_failures = True
                continue
                
            # Random delay between profile runs to mimic human browsing and avoid session linking
            if not first_run:
                sleep_time = random.uniform(5.0, 10.0)
                logger.info("SYSTEM", f"Sleeping for {sleep_time:.2f}s to avoid rate limiting...")
                time.sleep(sleep_time)
            first_run = False
            
            logger.info("PROCESS", f"Starting scraping process for '{name}' (@{username})...")
            
            log_file_path = os.path.join(debug_dir, f"{username}.log")
            logger.set_log_file(log_file_path)
            
            # Create a completely isolated context for each creator
            context = browser.new_context(
                user_agent=stealth_ua,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                color_scheme="dark",
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                permissions=["geolocation", "notifications"]
            )
            
            # Inject stealth scripts
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgieooff', description: 'Portable Document Format' }
                    ]
                });
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel(R) Iris(R) Xe Graphics';
                    return getParameter.apply(this, arguments);
                };
            """)
            
            page = context.new_page()
            
            # Setup Page Console/Network Error Listeners
            cleanup_listeners = setup_page_listeners(page, log_file_path)
            
            scraper = InstagramScraper(page, logger, debug_dir, enable_diagnostics=ENABLE_DIAGNOSTICS, save_html_on_success=SAVE_HTML_ON_SUCCESS, save_screenshots=SAVE_SCREENSHOTS)
            
            try:
                stats = scraper.get_profile_stats(username)
                
                if stats and stats.followers is not None:
                    logger.success("PROCESS", f"Updated {username} followers to {stats.followers.display}")
                    results.append({
                        "name": name,
                        "username": username,
                        "status": "SUCCESS",
                        "status_icon": "✅",
                        "followers": stats.followers.display,
                        "details": "Updated successfully"
                    })
                    output_data.append({
                        "id": creator_id,
                        "name": name,
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
                        "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    })
                else:
                    raise Exception("Stats could not be extracted.")
                    
            except Exception as e:
                logger.failed("PROCESS", f"Process failed for {username}: {e}")
                results.append({
                    "name": name,
                    "username": username,
                    "status": "FAIL",
                    "status_icon": "❌",
                    "followers": "N/A",
                    "details": str(e)
                })
                output_data.append({
                    "id": creator_id,
                    "name": name,
                    "username": username,
                    "status": "failed",
                    "reason": str(e)
                })
                any_failures = True
                
            finally:
                # Remove listeners for this creator
                cleanup_listeners()
                try:
                    page.close()
                except Exception:
                    pass
                try:
                    context.close()
                except Exception:
                    pass
                # Clear log file path back to none/system for safety
                logger.set_log_file(None)
                logger.set_username("SYSTEM")
                
        browser.close()
        
    # Write output to output.json
    logger.info("SYSTEM", "Writing statistics to output.json...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        logger.success("SYSTEM", "Instagram data written to output.json successfully.")
    except Exception as e:
        logger.failed("SYSTEM", f"Failed to write output.json: {e}")
        any_failures = True
        
    # Write GitHub Actions Step Summary if applicable
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_path:
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# 📱 Instagram Profile Stats Updater Summary\n\n")
                f.write(f"Executed at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n")
                f.write("| Creator | Username | Status | Followers | Details |\n")
                f.write("| --- | --- | --- | --- | --- |\n")
                for res in results:
                    f.write(f"| **{res['name']}** | `@{res['username']}` | {res['status_icon']} {res['status']} | **{res['followers']}** | {res['details']} |\n")
                f.write("\n---\n*Generated by GitHub Actions automated workflow.*")
        except Exception as e:
            logger.warning("SYSTEM", f"Failed to write GITHUB_STEP_SUMMARY: {e}")
            
    exit_code = determine_exit_code(results)
    if exit_code == 0:
        if any_failures:
            if results and all(result.get("status") == "FAIL" for result in results) and all(is_external_block_error(result.get("details")) for result in results if result.get("status") == "FAIL"):
                logger.warning("SYSTEM", "Instagram blocked access for this runner IP, so the workflow completed with warnings instead of failing.")
            elif any(result.get("status") == "SUCCESS" for result in results):
                logger.warning("SYSTEM", "Some profiles could not be updated, but the workflow completed successfully because at least one profile was updated.")
            else:
                logger.warning("SYSTEM", "The workflow completed with warnings because the scraper was blocked by Instagram.")
        else:
            logger.success("SYSTEM", "All Instagram profile statistics updated successfully.")
    else:
        logger.failed("SYSTEM", "Workflow failed because none of the profiles could be updated successfully.")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
