#!/usr/bin/env python3
"""Backup Crosswire state to a timestamped file."""

import json
import shutil
from datetime import datetime
from pathlib import Path


def backup_state():
    state_file = Path("config/state.json")
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    if not state_file.exists():
        print("No state.json found. Nothing to backup.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"state_{timestamp}.json"

    shutil.copy2(state_file, backup_file)
    print(f"State backed up to: {backup_file}")

    # Keep only last 10 backups
    backups = sorted(backup_dir.glob("state_*.json"))
    while len(backups) > 10:
        oldest = backups.pop(0)
        oldest.unlink()
        print(f"Removed old backup: {oldest}")


if __name__ == "__main__":
    backup_state()
