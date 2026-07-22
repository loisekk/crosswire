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
from .browser_automation import IndeedTargetAdapter, NaukriTargetAdapter
from .medium import MediumTargetAdapter
from .job_platforms import (
    GlassdoorTargetAdapter, ZipRecruiterTargetAdapter, ShineTargetAdapter,
    TimesJobsTargetAdapter, ApnaTargetAdapter, IIMJobsTargetAdapter
)
from .ai_transformer import AITransformer

logger = logging.getLogger(__name__)


class CrossPostEngine:
    def __init__(self, config_path: str = "config/settings.json"):
        with open(config_path) as f:
            self.config = json.load(f)

        self.state_file = Path("config/state.json")
        self.state = self._load_state()
        self.dry_run = self.config.get("settings", {}).get("dry_run", True)
        self.ai_enabled = self.config.get("settings", {}).get("ai_transform", False)

        self._init_adapters()
        self._init_ai()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"last_check": {}, "posted_hashes": [], "post_history": []}

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
        adapter_map = {
            "x": XTargetAdapter,
            "reddit": RedditTargetAdapter,
            "linkedin": LinkedInTargetAdapter,
            "devto": DevToTargetAdapter,
            "hashnode": HashnodeTargetAdapter,
            "indeed": IndeedTargetAdapter,
            "naukri": NaukriTargetAdapter,
            "medium": MediumTargetAdapter,
            "glassdoor": GlassdoorTargetAdapter,
            "ziprecruiter": ZipRecruiterTargetAdapter,
            "shine": ShineTargetAdapter,
            "timesjobs": TimesJobsTargetAdapter,
            "apna": ApnaTargetAdapter,
            "iimjobs": IIMJobsTargetAdapter,
        }

        for name, adapter_class in adapter_map.items():
            if target_configs.get(name, {}).get("enabled"):
                self.targets[name] = adapter_class(target_configs[name])

    def _init_ai(self):
        self.transformer = None
        if self.ai_enabled:
            try:
                model = self.config.get("settings", {}).get("ai_model", "qwen2.5:3b")
                self.transformer = AITransformer(model=model)
                logger.info(f"AI transformer initialized with model: {model}")
            except Exception as e:
                logger.warning(f"AI transformer not available: {e}")
                self.ai_enabled = False

    def _get_rules_for_source(self, source_name: str) -> List[dict]:
        return [r for r in self.config.get("cross_post_rules", []) if r["source"] == source_name]

    def _already_posted(self, post: Post) -> bool:
        return post.content_hash in self.state.get("posted_hashes", [])

    def _mark_posted(self, post: Post, target: str, result: dict):
        if "posted_hashes" not in self.state:
            self.state["posted_hashes"] = []
        self.state["posted_hashes"].append(post.content_hash)
        if len(self.state["posted_hashes"]) > 1000:
            self.state["posted_hashes"] = self.state["posted_hashes"][-500:]

        if "post_history" not in self.state:
            self.state["post_history"] = []
        self.state["post_history"].append({
            "platform": post.platform,
            "post_id": post.post_id,
            "target": target,
            "status": result.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "title": post.title,
            "url": post.url
        })
        if len(self.state["post_history"]) > 500:
            self.state["post_history"] = self.state["post_history"][-500:]

    def _transform_content(self, post: Post, target_name: str) -> tuple[str, str]:
        if not self.ai_enabled or not self.transformer:
            return post.content, post.title or ""

        result = self.transformer.transform(
            content=post.content,
            title=post.title or "",
            platform=target_name,
            source_platform=post.platform
        )

        if result.get("transformed"):
            logger.info(f"AI transformed content for {target_name}")
            return result["content"], result.get("title", post.title or "")

        return post.content, post.title or ""

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

                        if self.ai_enabled and self.transformer:
                            content, title = self._transform_content(post, target_name)
                        else:
                            title = post.title

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
                            response = target.post(content, title=title, url=post.url, tags=tags)
                            if inspect.iscoroutine(response):
                                response = asyncio.run(response)
                            logger.info(f"Posted to {target_name}: {response}")
                            results[source_name].append({
                                "target": target_name,
                                "status": "posted",
                                "response": response
                            })
                            self._mark_posted(post, target_name, {"status": "posted"})
                        except Exception as e:
                            logger.error(f"Error posting to {target_name}: {e}")
                            results[source_name].append({
                                "target": target_name,
                                "status": "error",
                                "error": str(e)
                            })

            self.state.setdefault("last_check", {})[source_name] = datetime.now().isoformat()

        self._save_state()
        return results

    def post_directly(self, content: str, targets: List[str], title: Optional[str] = None,
                      url: Optional[str] = None, tags: Optional[List[str]] = None,
                      source_platform: str = "linkedin") -> Dict[str, dict]:
        results = {}

        transformed = {}
        if self.ai_enabled and self.transformer:
            transformed = self.transformer.transform_for_all(
                content=content,
                title=title or "",
                platforms=targets,
                source_platform=source_platform
            )

        for target_name in targets:
            if target_name not in self.targets:
                results[target_name] = {"status": "error", "error": "Target not configured"}
                continue

            target = self.targets[target_name]

            if target_name in transformed and transformed[target_name].get("transformed"):
                post_content = transformed[target_name]["content"]
                post_title = transformed[target_name].get("title", title)
            else:
                post_content = content
                post_title = title

            valid, msg = target.validate_content(post_content)
            if not valid:
                results[target_name] = {"status": "error", "error": msg}
                continue

            if self.dry_run:
                results[target_name] = {"status": "dry_run", "content_preview": post_content[:100]}
                continue

            try:
                response = target.post(post_content, title=post_title, url=url, tags=tags)
                if inspect.iscoroutine(response):
                    response = asyncio.run(response)
                results[target_name] = {"status": "posted", "response": response}
            except Exception as e:
                results[target_name] = {"status": "error", "error": str(e)}

        return results

    def get_status(self) -> dict:
        return {
            "sources": list(self.sources.keys()),
            "targets": list(self.targets.keys()),
            "dry_run": self.dry_run,
            "ai_enabled": self.ai_enabled,
            "ai_model": self.config.get("settings", {}).get("ai_model", "N/A"),
            "posted_count": len(self.state.get("posted_hashes", [])),
            "last_checks": self.state.get("last_check", {}),
            "recent_posts": self.state.get("post_history", [])[-20:]
        }
