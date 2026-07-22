#!/usr/bin/env python3
"""Crosswire setup script — installs dependencies and configures the project."""

import subprocess
import sys
from pathlib import Path


def run(cmd, check=True):
    print(f"  Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    print("\n=== Crosswire Setup ===\n")

    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ required")
        sys.exit(1)
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}")

    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    run(f"{sys.executable} -m pip install -r requirements.txt")

    # Install Playwright browsers
    print("\nInstalling Playwright browsers...")
    run(f"{sys.executable} -m playwright install chromium")

    # Create .env if not exists
    env_path = Path(".env")
    env_example = Path(".env.example")
    if not env_path.exists() and env_example.exists():
        print("\nCreating .env from .env.example...")
        env_path.write_text(env_example.read_text())
        print("  Edit .env with your API keys")

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    print("\n[OK] Setup complete!")
    print("\nNext steps:")
    print("  1. Edit .env with your API keys")
    print("  2. Edit config/settings.json with your credentials")
    print("  3. Run: python dashboard/app.py")
    print("  4. Open http://localhost:8080\n")


if __name__ == "__main__":
    main()
