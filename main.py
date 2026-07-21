#!/usr/bin/env python3
import argparse
import json
import sys
import time
import logging
from pathlib import Path

from adapters.engine import CrossPostEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/crosspost.log")
    ]
)
logger = logging.getLogger(__name__)


def cmd_check(args):
    engine = CrossPostEngine(args.config)
    results = engine.check_and_crosspost()
    print(json.dumps(results, indent=2, default=str))


def cmd_post(args):
    engine = CrossPostEngine(args.config)
    targets = args.targets.split(",")
    content = args.content or sys.stdin.read()
    results = engine.post_directly(content, targets, title=args.title, url=args.url)
    print(json.dumps(results, indent=2, default=str))


def cmd_scheduler(args):
    engine = CrossPostEngine(args.config)
    interval = args.interval * 60

    logger.info(f"Starting scheduler (every {args.interval} minutes)")
    logger.info("Press Ctrl+C to stop")

    while True:
        try:
            results = engine.check_and_crosspost()
            for source, posts in results.items():
                for post in posts:
                    if post["status"] == "posted":
                        logger.info(f"Cross-posted from {source} to {post['target']}")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        time.sleep(interval)


def cmd_status(args):
    engine = CrossPostEngine(args.config)
    print(f"Sources enabled: {list(engine.sources.keys())}")
    print(f"Targets enabled: {list(engine.targets.keys())}")
    print(f"Dry run: {engine.dry_run}")
    print(f"State: {json.dumps(engine.state, indent=2, default=str)}")


def main():
    Path("logs").mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Crosswire — content syndication engine")
    parser.add_argument("-c", "--config", default="config/settings.json", help="Config file path")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Check for new posts and cross-post")

    post_parser = subparsers.add_parser("post", help="Post content directly to targets")
    post_parser.add_argument("-t", "--targets", required=True, help="Comma-separated target platforms")
    post_parser.add_argument("-c", "--content", help="Content to post (or pipe via stdin)")
    post_parser.add_argument("--title", help="Post title")
    post_parser.add_argument("--url", help="URL to include")

    sched_parser = subparsers.add_parser("scheduler", help="Run continuous scheduler")
    sched_parser.add_argument("-i", "--interval", type=int, default=15, help="Check interval in minutes")

    subparsers.add_parser("status", help="Show current status")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check(args)
    elif args.command == "post":
        cmd_post(args)
    elif args.command == "scheduler":
        cmd_scheduler(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
