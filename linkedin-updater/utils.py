import re
import time
from typing import Callable, Any
from functools import wraps
import logging
import os

# --- CONFIGURATION ---
ENABLE_FILE_LOGGING = True
LOG_FILE = "updater.log"
MAX_LOG_SESSIONS = 5
PARSE_NUMBERS = True
# ---------------------

def trim_logs():
    if not os.path.exists(LOG_FILE): return
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "\n" + "="*50 + "\n=== NEW UPDATER SESSION ===\n" + "="*50 + "\n"
        sessions = content.split(marker)
        if len(sessions) > MAX_LOG_SESSIONS + 1:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(sessions[0])
                for s in sessions[-(MAX_LOG_SESSIONS):]:
                    f.write(marker + s)
    except Exception:
        pass

def setup_logger():
    """Sets up a clean, minimal logger."""
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    if ENABLE_FILE_LOGGING:
        marker = "\n" + "="*50 + "\n=== NEW UPDATER SESSION ===\n" + "="*50 + "\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(marker)
        trim_logs()
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 2.0, backoff_factor: float = 2.0):
    """
    Decorator for retrying a function with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

def parse_number(num_str: str) -> Any:
    """Parses a string like '1.2K', '1.5M', or '1,234' into an integer."""
    if not PARSE_NUMBERS:
        return str(num_str).strip() if num_str else "0"
    if not num_str:
        return 0
    num_str = str(num_str).strip().upper().replace(',', '')
    try:
        if 'K' in num_str:
            return int(float(num_str.replace('K', '')) * 1000)
        elif 'M' in num_str:
            return int(float(num_str.replace('M', '')) * 1000000)
        elif 'B' in num_str:
            return int(float(num_str.replace('B', '')) * 1000000000)
        return int(float(num_str))
    except ValueError:
        return 0
