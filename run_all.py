import os
import subprocess
import logging
from pathlib import Path

# --- CONFIGURATION ---
ENABLE_LOGGING = True
LOG_FILE = "run_all.log"
MAX_LOG_SESSIONS = 5
# ---------------------

def trim_logs():
    if not os.path.exists(LOG_FILE): return
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        marker = "\n" + "="*50 + "\n=== NEW EXECUTION SESSION STARTED ===\n" + "="*50 + "\n"
        sessions = content.split(marker)
        if len(sessions) > MAX_LOG_SESSIONS + 1:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(sessions[0]) # usually empty
                for s in sessions[-(MAX_LOG_SESSIONS):]:
                    f.write(marker + s)
    except Exception:
        pass

if ENABLE_LOGGING:
    marker = "\n" + "="*50 + "\n=== NEW EXECUTION SESSION STARTED ===\n" + "="*50 + "\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(marker)
    trim_logs()
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def log_print(msg, level="INFO"):
    print(msg)
    if ENABLE_LOGGING:
        if level == "INFO":
            logging.info(msg)
        elif level == "ERROR":
            logging.error(msg)
        elif level == "WARNING":
            logging.warning(msg)

def main():
    base_dir = Path(__file__).parent
    
    # Find all directories ending in -updater
    updaters = [d for d in base_dir.iterdir() if d.is_dir() and d.name.endswith('-updater')]
    
    # Sort for consistent execution order
    updaters.sort(key=lambda x: x.name)
    
    if not updaters:
        log_print("No updater directories found.", "WARNING")
        return
        
    print("\n" + "="*50)

    log_print(f"Found {len(updaters)} updaters. Starting execution...")
    log_print("-" * 40)
    
    success_count = 0
    fail_count = 0

    for updater_dir in updaters:
        update_script = updater_dir / "update.py"
        if not update_script.exists():
            log_print(f"[SKIPPING] {updater_dir.name}: No update.py found.", "WARNING")
            continue
            
        log_print(f"[RUNNING] {updater_dir.name}...")
        
        try:
            # Run the script with the updater_dir as the current working directory
            # Using python execution that works cross-platform
            result = subprocess.run(
                ["python", "update.py"], 
                cwd=updater_dir, 
                capture_output=True, 
                text=True,
                check=True
            )
            log_print(f"[SUCCESS] {updater_dir.name}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            log_print(f"[FAILED] {updater_dir.name}", "ERROR")
            log_print(f"Error Output:\n{e.stderr or e.output}", "ERROR")
            fail_count += 1
            
        log_print("-" * 40)

    log_print(f"[COMPLETE] {success_count} succeeded, {fail_count} failed.")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
