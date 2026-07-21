import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from typing import Optional, List
from .base import BaseSourceAdapter, BaseTargetAdapter, Post


class RedditSourceAdapter(BaseSourceAdapter):
    BASE_URL = "https://oauth.reddit.com"

    def _get_token(self) -> str:
        auth = HTTPBasicAuth(self.config["client_id"], self.config["client_secret"])
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={
                "grant_type": "password",
                "username": self.config["username"],
                "password": self.config["password"]
            },
            headers={"User-Agent": self.config["user_agent"]}
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.config["user_agent"]
        }

        resp = requests.get(
            f"{self.BASE_URL}/user/{self.config['username']}/submitted",
            headers=headers,
            params={"limit": 10, "sort": "new"}
        )
        resp.raise_for_status()

        posts = []
        for child in resp.json().get("data", {}).get("children", []):
            item = child["data"]
            created = datetime.fromtimestamp(item["created_utc"])
            if since and created <= since:
                continue

            posts.append(Post(
                platform="reddit",
                post_id=item["id"],
                content=item.get("selftext", item.get("title", "")),
                title=item.get("title"),
                url=f"https://reddit.com{item['permalink']}",
                created_at=created,
                raw_data=item
            ))
        return posts

    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.config["user_agent"]
        }
        resp = requests.get(f"{self.BASE_URL}/comments/{post_id}", headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        item = resp.json()[0]["data"]["children"][0]["data"]
        return Post(
            platform="reddit",
            post_id=item["id"],
            content=item.get("selftext", ""),
            title=item.get("title"),
            url=f"https://reddit.com{item['permalink']}",
            created_at=datetime.fromtimestamp(item["created_utc"])
        )


class RedditTargetAdapter(BaseTargetAdapter):
    BASE_URL = "https://oauth.reddit.com"

    def _get_token(self) -> str:
        auth = HTTPBasicAuth(self.config["client_id"], self.config["client_secret"])
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={
                "grant_type": "password",
                "username": self.config["username"],
                "password": self.config["password"]
            },
            headers={"User-Agent": self.config["user_agent"]}
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.config["user_agent"],
            "Content-Type": "application/json"
        }

        results = {}
        subreddits = self.config.get("subreddits", ["programming"])

        for subreddit in subreddits:
            is_link = bool(url)
            payload = {
                "sr": subreddit,
                "kind": "link" if is_link else "self",
                "title": (title or "Cross-posted Article")[:300],
                "resubmit": True
            }

            if is_link:
                payload["url"] = url
            else:
                payload["text"] = content

            resp = requests.post(
                f"{self.BASE_URL}/api/submit",
                json=payload,
                headers=headers
            )

            resp_data = resp.json()
            if resp_data.get("errors"):
                results[subreddit] = {
                    "status": "error",
                    "errors": resp_data["errors"]
                }
            else:
                results[subreddit] = {
                    "status": "posted",
                    "id": resp_data.get("data", {}).get("id"),
                    "url": f"https://reddit.com{resp_data.get('data', {}).get('web_url', '')}"
                }

        return results

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 40000:
            return False, "Content exceeds Reddit's 40000 char limit"
        return True, "OK"
