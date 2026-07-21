import requests
from datetime import datetime
from typing import Optional, List
from .base import BaseSourceAdapter, BaseTargetAdapter, Post


class LinkedInSourceAdapter(BaseSourceAdapter):
    BASE_URL = "https://api.linkedin.com/v2"

    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        headers = {"Authorization": f"Bearer {self.config['access_token']}"}
        person_urn = self.config["person_urn"]

        resp = requests.get(
            f"{self.BASE_URL}/ugcPosts",
            headers=headers,
            params={"q": "authors", "authors": f"List({person_urn})", "count": 10}
        )
        resp.raise_for_status()

        posts = []
        for item in resp.json().get("elements", []):
            created = datetime.fromtimestamp(item["created"]["time"] / 1000)
            if since and created <= since:
                continue

            content = ""
            for frag in item.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", ""):
                content = frag if isinstance(frag, str) else str(frag)

            posts.append(Post(
                platform="linkedin",
                post_id=item["id"],
                content=content,
                url=f"https://www.linkedin.com/feed/update/{item['id']}",
                created_at=created,
                raw_data=item
            ))
        return posts

    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        headers = {"Authorization": f"Bearer {self.config['access_token']}"}
        resp = requests.get(f"{self.BASE_URL}/ugcPosts/{post_id}", headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        item = resp.json()
        return Post(
            platform="linkedin",
            post_id=item["id"],
            content=item.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", ""),
            created_at=datetime.fromtimestamp(item["created"]["time"] / 1000),
            raw_data=item
        )


class LinkedInTargetAdapter(BaseTargetAdapter):
    BASE_URL = "https://api.linkedin.com/v2"

    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": self.config["person_urn"],
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "ARTICLE" if url else "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        if url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": url,
                "title": {"text": title or "Shared Article"}
            }]

        resp = requests.post(f"{self.BASE_URL}/ugcPosts", json=payload, headers=headers)
        resp.raise_for_status()
        return {"id": resp.headers.get("x-restli-id")}

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 3000:
            return False, "Content exceeds LinkedIn's 3000 char limit"
        return True, "OK"
