#!/usr/bin/env python3
import subprocess
import sys
import time
import logging
import signal
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/supervisor.log")
    ]
)
logger = logging.getLogger(__name__)

SERVICES = [
    {
        "name": "webhook-server",
        "command": [sys.executable, "webhook_server.py"],
        "cwd": str(Path(__file__).parent),
        "restart_delay": 5
    },
    {
        "name": "scheduler",
        "command": [sys.executable, "main.py", "scheduler", "-i", "15"],
        "cwd": str(Path(__file__).parent),
        "restart_delay": 10
    }
]


class Supervisor:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.restart_counts = {}
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info("Shutting down supervisor...")
        self.running = False
        for name, proc in self.processes.items():
            if proc.poll() is None:
                logger.info(f"Stopping {name} (PID {proc.pid})...")
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()

    def start_service(self, service):
        name = service["name"]
        logger.info(f"Starting {name}...")

        proc = subprocess.Popen(
            service["command"],
            cwd=service["cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.processes[name] = proc
        self.restart_counts[name] = self.restart_counts.get(name, 0) + 1
        logger.info(f"{name} started with PID {proc.pid} (restart #{self.restart_counts[name]})")
        return proc

    def monitor_service(self, service):
        name = service["name"]
        proc = self.processes.get(name)

        if proc and proc.poll() is not None:
            exit_code = proc.returncode
            restart_count = self.restart_counts.get(name, 0)

            if restart_count > 10:
                logger.error(f"{name} has restarted {restart_count} times. Too many restarts, skipping...")
                return

            logger.warning(f"{name} exited with code {exit_code}. Restarting in {service['restart_delay']}s...")
            time.sleep(service['restart_delay'])
            self.start_service(service)

    def run(self):
        logger.info("=== Crosswire Supervisor Started ===")
        logger.info("Running 24/7 with auto-restart")
        logger.info("Services: webhook-server, scheduler")
        logger.info("Press Ctrl+C to stop\n")

        for service in SERVICES:
            self.start_service(service)

        while self.running:
            for service in SERVICES:
                self.monitor_service(service)
            time.sleep(2)

        logger.info("=== Supervisor Stopped ===")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    supervisor = Supervisor()
    supervisor.run()
