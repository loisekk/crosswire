import requests
from datetime import datetime
from typing import Optional, List
from .base import BaseSourceAdapter, BaseTargetAdapter, Post


class DevToSourceAdapter(BaseSourceAdapter):
    BASE_URL = "https://dev.to/api"

    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        username = self.config.get("username")
        headers = {"api-key": self.config["api_key"]}

        # Try username-based endpoint first
        url = f"{self.BASE_URL}/articles?username={username}&state=all"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        posts = []
        for article in resp.json():
            published = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
            if since and published <= since:
                continue

            posts.append(Post(
                platform="devto",
                post_id=str(article["id"]),
                content=article.get("description", article.get("body_markdown", "")),
                title=article.get("title"),
                url=article.get("url"),
                tags=article.get("tag_list", []),
                created_at=published,
                raw_data=article
            ))
        return posts

    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        headers = {"api-key": self.config["api_key"]}
        resp = requests.get(f"{self.BASE_URL}/articles/{post_id}", headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        article = resp.json()
        return Post(
            platform="devto",
            post_id=str(article["id"]),
            content=article.get("description", ""),
            title=article.get("title"),
            url=article.get("url"),
            tags=article.get("tag_list", []),
            created_at=datetime.fromisoformat(article["published_at"].replace("Z", "+00:00")),
            raw_data=article
        )


class DevToTargetAdapter(BaseTargetAdapter):
    BASE_URL = "https://dev.to/api"

    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        headers = {
            "api-key": self.config["api_key"],
            "Content-Type": "application/json"
        }
        payload = {
            "article": {
                "title": title or "Cross-posted Article",
                "body_markdown": content,
                "published": True,
                "tags": (tags or [])[:4]
            }
        }
        resp = requests.post(f"{self.BASE_URL}/articles", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) < 10:
            return False, "Content too short for Dev.to"
        return True, "OK"
