#!/usr/bin/env python3
"""Clean up Crosswire temporary files and caches."""

import shutil
from pathlib import Path


def clean():
    print("=== Crosswire Cleanup ===\n")

    # Remove __pycache__ directories
    count = 0
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
        count += 1
        print(f"  Removed: {pycache}")

    # Remove .pyc files
    for pyc in Path(".").rglob("*.pyc"):
        pyc.unlink()
        count += 1

    # Remove old log files (keep last 7 days)
    logs_dir = Path("logs")
    if logs_dir.exists():
        import time
        now = time.time()
        for log_file in logs_dir.glob("*.log"):
            if now - log_file.stat().st_mtime > 7 * 86400:
                log_file.unlink()
                count += 1
                print(f"  Removed old log: {log_file}")

    # Remove old backups (keep last 5)
    backups_dir = Path("backups")
    if backups_dir.exists():
        backups = sorted(backups_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
        while len(backups) > 5:
            oldest = backups.pop(0)
            oldest.unlink()
            count += 1
            print(f"  Removed old backup: {oldest}")

    print(f"\nCleaned {count} items.")


if __name__ == "__main__":
    clean()
