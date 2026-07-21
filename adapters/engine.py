import json
import asyncio
import inspect
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .base import Post

from .devto import DevToSourceAdapter, DevToTargetAdapter
from .hashnode import HashnodeSourceAdapter, HashnodeTargetAdapter
from .linkedin import LinkedInSourceAdapter, LinkedInTargetAdapter
from .x_twitter import XSourceAdapter, XTargetAdapter
from .reddit import RedditSourceAdapter, RedditTargetAdapter
from .browser_automation import IndeedTargetAdapter, NaukriTargetAdapter, run_async

logger = logging.getLogger(__name__)


class CrossPostEngine:
    def __init__(self, config_path: str = "config/settings.json"):
        with open(config_path) as f:
            self.config = json.load(f)

        self.state_file = Path("config/state.json")
        self.state = self._load_state()
        self.dry_run = self.config.get("settings", {}).get("dry_run", True)

        self._init_adapters()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"last_check": {}, "posted_hashes": []}

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _init_adapters(self):
        self.sources = {}
        self.targets = {}

        source_configs = self.config.get("sources", {})
        if source_configs.get("devto", {}).get("enabled"):
            self.sources["devto"] = DevToSourceAdapter(source_configs["devto"])
        if source_configs.get("hashnode", {}).get("enabled"):
            self.sources["hashnode"] = HashnodeSourceAdapter(source_configs["hashnode"])
        if source_configs.get("linkedin", {}).get("enabled"):
            self.sources["linkedin"] = LinkedInSourceAdapter(source_configs["linkedin"])

        target_configs = self.config.get("targets", {})
        if target_configs.get("x", {}).get("enabled"):
            self.targets["x"] = XTargetAdapter(target_configs["x"])
        if target_configs.get("reddit", {}).get("enabled"):
            self.targets["reddit"] = RedditTargetAdapter(target_configs["reddit"])
        if target_configs.get("linkedin", {}).get("enabled"):
            self.targets["linkedin"] = LinkedInTargetAdapter(target_configs["linkedin"])
        if target_configs.get("devto", {}).get("enabled"):
            self.targets["devto"] = DevToTargetAdapter(target_configs["devto"])
        if target_configs.get("hashnode", {}).get("enabled"):
            self.targets["hashnode"] = HashnodeTargetAdapter(target_configs["hashnode"])
        if target_configs.get("indeed", {}).get("enabled"):
            self.targets["indeed"] = IndeedTargetAdapter(target_configs["indeed"])
        if target_configs.get("naukri", {}).get("enabled"):
            self.targets["naukri"] = NaukriTargetAdapter(target_configs["naukri"])

    def _get_rules_for_source(self, source_name: str) -> List[dict]:
        return [r for r in self.config.get("cross_post_rules", []) if r["source"] == source_name]

    def _already_posted(self, post: Post) -> bool:
        return post.content_hash in self.state.get("posted_hashes", [])

    def _mark_posted(self, post: Post):
        if "posted_hashes" not in self.state:
            self.state["posted_hashes"] = []
        self.state["posted_hashes"].append(post.content_hash)
        if len(self.state["posted_hashes"]) > 1000:
            self.state["posted_hashes"] = self.state["posted_hashes"][-500:]

    def check_and_crosspost(self) -> Dict[str, List[dict]]:
        results = {}

        for source_name, source_adapter in self.sources.items():
            logger.info(f"Checking {source_name} for new posts...")
            last_check = self.state.get("last_check", {}).get(source_name)

            if last_check:
                last_check = datetime.fromisoformat(last_check)

            try:
                new_posts = source_adapter.fetch_new_posts(since=last_check)
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue

            logger.info(f"Found {len(new_posts)} new posts on {source_name}")
            results[source_name] = []

            for post in new_posts:
                if self._already_posted(post):
                    continue

                rules = self._get_rules_for_source(source_name)
                for rule in rules:
                    for target_name in rule.get("targets", []):
                        if target_name not in self.targets:
                            logger.warning(f"Target {target_name} not configured, skipping")
                            continue

                        target = self.targets[target_name]
                        transform = rule.get("transform", {})

                        content, tags = target.transform_content(post, transform) if hasattr(target, 'transform_content') else (post.content, post.tags)

                        valid, msg = target.validate_content(content)
                        if not valid:
                            logger.warning(f"Content invalid for {target_name}: {msg}")
                            continue

                        if self.dry_run:
                            logger.info(f"[DRY RUN] Would post to {target_name}: {content[:100]}...")
                            results[source_name].append({
                                "target": target_name,
                                "status": "dry_run",
                                "content_preview": content[:100]
                            })
                            continue

                        try:
                            response = target.post(content, title=post.title, url=post.url, tags=tags)
                            if inspect.iscoroutine(response):
                                response = asyncio.run(response)
                            logger.info(f"Posted to {target_name}: {response}")
                            results[source_name].append({
                                "target": target_name,
                                "status": "posted",
                                "response": response
                            })
                        except Exception as e:
                            logger.error(f"Error posting to {target_name}: {e}")
                            results[source_name].append({
                                "target": target_name,
                                "status": "error",
                                "error": str(e)
                            })

                self._mark_posted(post)

            self.state.setdefault("last_check", {})[source_name] = datetime.now().isoformat()

        self._save_state()
        return results

    def post_directly(self, content: str, targets: List[str], title: Optional[str] = None,
                      url: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, dict]:
        results = {}
        for target_name in targets:
            if target_name not in self.targets:
                results[target_name] = {"status": "error", "error": "Target not configured"}
                continue

            target = self.targets[target_name]
            valid, msg = target.validate_content(content)
            if not valid:
                results[target_name] = {"status": "error", "error": msg}
                continue

            if self.dry_run:
                results[target_name] = {"status": "dry_run", "content_preview": content[:100]}
                continue

            try:
                response = target.post(content, title=title, url=url, tags=tags)
                if inspect.iscoroutine(response):
                    response = asyncio.run(response)
                results[target_name] = {"status": "posted", "response": response}
            except Exception as e:
                results[target_name] = {"status": "error", "error": str(e)}

        return results
