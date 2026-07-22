#!/usr/bin/env python3
"""Real-time monitoring dashboard for Crosswire services."""

import time
import sys
from pathlib import Path


def monitor():
    print("Crosswire Monitor (Ctrl+C to stop)\n")

    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")

            print("=== Crosswire Live Monitor ===")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Check Ollama
            try:
                import requests
                resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                if resp.status_code == 200:
                    print("[OK] Ollama: Running")
                else:
                    print("[WARN] Ollama: Unhealthy")
            except Exception:
                print("[FAIL] Ollama: Not running")

            # Check state
            state_file = Path("config/state.json")
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                posts = len(state.get("posted_hashes", []))
                print(f"[OK] Posts tracked: {posts}")
            else:
                print("[INFO] No state yet")

            # Check logs for errors
            logs_dir = Path("logs")
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    try:
                        with open(log_file, 'r', errors='ignore') as f:
                            lines = f.readlines()
                            errors = [l for l in lines if 'ERROR' in l]
                            if errors:
                                print(f"[WARN] {log_file.name}: {len(errors)} errors")
                            else:
                                print(f"[OK] {log_file.name}: Clean")
                    except Exception:
                        pass

            print("\nRefreshing in 5 seconds...")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    monitor()
