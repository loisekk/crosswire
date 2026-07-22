#!/usr/bin/env python3
"""Monitor Crosswire services and report status."""

import json
import sys
from pathlib import Path


def check_config():
    config_file = Path("config/settings.json")
    if not config_file.exists():
        print("[WARN] config/settings.json not found")
        return False

    with open(config_file) as f:
        config = json.load(f)

    targets = config.get("targets", {})
    enabled = [k for k, v in targets.items() if v.get("enabled")]
    print(f"[OK] Config: {len(enabled)} platforms enabled")
    return True


def check_state():
    state_file = Path("config/state.json")
    if not state_file.exists():
        print("[INFO] No state.json yet (first run)")
        return

    with open(state_file) as f:
        state = json.load(f)

    posts = len(state.get("posted_hashes", []))
    history = len(state.get("post_history", []))
    print(f"[OK] State: {posts} posts tracked, {history} in history")


def check_logs():
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("[INFO] No logs directory yet")
        return

    log_files = list(logs_dir.glob("*.log"))
    print(f"[OK] Logs: {len(log_files)} log files")


def check_ollama():
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"[OK] Ollama: {len(models)} models available")
        else:
            print("[WARN] Ollama responding but not healthy")
    except Exception:
        print("[WARN] Ollama not reachable (start with: ollama serve)")


def main():
    print("\n=== Crosswire Health Check ===\n")
    check_config()
    check_state()
    check_logs()
    check_ollama()
    print("\nDone.\n")


if __name__ == "__main__":
    main()
