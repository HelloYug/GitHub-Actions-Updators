import re
import os
import sys
import traceback
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

# --- CONFIGURATION ---
ENABLE_FILE_LOGGING = False  # Set to True to enable logging to a file
LOG_FILE = "updater.log"  # Default log file path
MAX_LOG_SESSIONS = 4  # Maximum number of log sessions to keep
PARSE_NUMBERS = True  # Set to True to enable parsing of numbers with K/M/B suffixes

# --- DEBUGGING CONFIGURATION ---
ENABLE_DIAGNOSTICS = True  # Set to True to save HTML snapshots and screenshots for debugging
SAVE_HTML_ON_SUCCESS = False  # Set to True to save HTML even for successful scrapes (only saves on errors by default)
SAVE_SCREENSHOTS = True  # Set to True to save full-page screenshots for debugging
# ---------------------


def trim_logs(log_file: str = LOG_FILE, max_sessions: int = MAX_LOG_SESSIONS):
    if not os.path.exists(log_file):
        return
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "\n" + "=" * 50 + "\n=== NEW UPDATER SESSION ===\n" + "=" * 50 + "\n"
        sessions = content.split(marker)
        if len(sessions) > max_sessions + 1:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(sessions[0])
                for s in sessions[-max_sessions:]:
                    f.write(marker + s)
    except Exception:
        pass


def setup_logger(log_file: str = LOG_FILE):
    """Sets up a clean, minimal logger."""
    logger = logging.getLogger("scraper")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if ENABLE_FILE_LOGGING:
        marker = "\n" + "=" * 50 + "\n=== NEW UPDATER SESSION ===\n" + "=" * 50 + "\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(marker)
        trim_logs(log_file=log_file, max_sessions=MAX_LOG_SESSIONS)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 2.0, backoff_factor: float = 2.0):
    """Decorator for retrying a function with exponential backoff."""
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


def safe_print(text: str):
    """
    Prints a string to stdout while safely handling UnicodeEncodeErrors
    by encoding/decoding with error replacements.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            enc = sys.stdout.encoding or 'utf-8'
            print(text.encode(enc, errors='replace').decode(enc))
        except Exception:
            try:
                print(text.encode('ascii', errors='replace').decode('ascii'))
            except Exception:
                pass


def parse_number(text: str) -> Optional[int]:
    """
    Parses a string representation of a number into an integer.
    Supports K (thousands), M (millions), and B (billions).
    Handles commas and decimals.

    Examples:
    '1.2K' -> 1200
    '2.5M' -> 2500000
    '1,234' -> 1234
    '123' -> 123
    """
    if not text:
        return None

    text = str(text).strip().upper().replace(',', '')
    if not text:
        return None

    multiplier = 1
    if text.endswith('K'):
        multiplier = 1000
        text = text[:-1]
    elif text.endswith('M'):
        multiplier = 1000000
        text = text[:-1]
    elif text.endswith('B'):
        multiplier = 1000000000
        text = text[:-1]

    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def format_number(val: int) -> str:
    """
    Formats an integer back to a string representation with K/M/B suffixes.
    E.g.
    26500 -> '26.5K'
    471000 -> '471K'
    208000 -> '208K'
    1234 -> '1.2K'
    123 -> '123'
    """
    if val is None:
        return ""
    if val >= 1000000000:
        val_str = f"{val / 1000000000:.1f}"
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return f"{val_str}B"
    if val >= 1000000:
        val_str = f"{val / 1000000:.1f}"
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return f"{val_str}M"
    if val >= 1000:
        val_str = f"{val / 1000:.1f}"
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return f"{val_str}K"
    return str(val)

class StructuredLogger:
    def __init__(self, username: str = "SYSTEM"):
        self.username = username
        self.log_file_path = None
        self.logs_list = []

    def set_username(self, username: str):
        self.username = username

    def set_log_file(self, file_path: str):
        self.log_file_path = file_path
        if file_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def log(self, operation: str, status: str, message: str, duration: float = None, exception: str = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration_str = f"{duration:.3f}s" if duration is not None else "N/A"
        exception_str = f" | Exception: {exception}" if exception else ""
        
        # Structured log line format:
        # [timestamp] [username] [operation] [duration] [status] message [exception]
        log_line = f"[{timestamp}] [{self.username}] [{operation}] [{duration_str}] [{status}] {message}{exception_str}"
        
        # Print to console (always, safely handling encoding)
        safe_print(log_line)
        
        # Append to log list and file
        self.logs_list.append(log_line)
        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_line + "\n")
            except Exception as e:
                safe_print(f"[{timestamp}] [SYSTEM] [LOGGING] [N/A] [WARNING] Failed to write to log file: {e}")

    def step(self, message: str):
        self.log("STEP", "INFO", message)

    def info(self, operation: str, message: str, duration: float = None):
        self.log(operation, "INFO", message, duration)

    def success(self, operation: str, message: str, duration: float = None):
        self.log(operation, "SUCCESS", message, duration)

    def warning(self, operation: str, message: str, duration: float = None):
        self.log(operation, "WARNING", message, duration)

    def failed(self, operation: str, message: str, duration: float = None, exception: str = None):
        self.log(operation, "FAILED", message, duration, exception)

def log_exception(username: str, e: Exception, url: str, title: str, retry_num: int, logger: Optional[StructuredLogger] = None):
    """
    Formulates a detailed exception report with traceback, username, url, title, and retry number.
    Outputs to both the logger and stderr/stdout.
    """
    tb = traceback.format_exc()
    timestamp = datetime.now().isoformat()
    msg = (
        f"\n=== EXCEPTION REPORT ===\n"
        f"Timestamp: {timestamp}\n"
        f"Username: {username}\n"
        f"Current URL: {url}\n"
        f"Page Title: {title}\n"
        f"Retry Number: {retry_num}\n"
        f"Traceback:\n{tb}"
        f"========================\n"
    )
    if logger:
        # Write clean error and raw exception block to log file
        logger.log("EXCEPTION_TRACE", "ERROR", f"Traceback logged for {username}", exception=str(e))
        if logger.log_file_path:
            try:
                with open(logger.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(msg + "\n")
            except Exception:
                pass
    # Print the exception report block to console
    safe_print(msg)
