import requests
import json
import time
import hmac
import hashlib
import base64
from urllib.parse import quote
from datetime import datetime
from typing import Optional, List
from .base import BaseSourceAdapter, BaseTargetAdapter, Post


class XSourceAdapter(BaseSourceAdapter):
    BASE_URL = "https://api.twitter.com/2"

    def _oauth1_sign(self, method: str, url: str, params: Optional[dict] = None) -> dict:
        oauth = {
            "oauth_consumer_key": self.config["api_key"],
            "oauth_nonce": str(int(time.time() * 1000)),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.config["access_token"],
            "oauth_version": "1.0"
        }
        all_params = {**oauth, **(params or {})}
        sorted_params = "&".join(f"{quote(k)}={quote(str(v))}" for k, v in sorted(all_params.items()))
        base_string = f"{method.upper()}&{quote(url)}&{quote(sorted_params)}"
        signing_key = f"{quote(self.config['api_secret'])}&{quote(self.config['access_token_secret'])}"
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        oauth["oauth_signature"] = signature
        return oauth

    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        url = f"{self.BASE_URL}/users/me/tweets"
        oauth = self._oauth1_sign("GET", url, {"max_results": "10"})
        headers = {"Authorization": f'OAuth ' + ", ".join(f'{k}="{quote(v)}"' for k, v in oauth.items())}

        resp = requests.get(url, headers=headers, params={"max_results": 10, "tweet.fields": "created_at,text"})
        resp.raise_for_status()

        posts = []
        for tweet in resp.json().get("data", []):
            created = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
            if since and created <= since:
                continue
            posts.append(Post(
                platform="x",
                post_id=tweet["id"],
                content=tweet["text"],
                url=f"https://x.com/i/status/{tweet['id']}",
                created_at=created
            ))
        return posts

    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        url = f"{self.BASE_URL}/tweets/{post_id}"
        oauth = self._oauth1_sign("GET", url)
        headers = {"Authorization": f'OAuth ' + ", ".join(f'{k}="{quote(v)}"' for k, v in oauth.items())}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        tweet = resp.json()["data"]
        return Post(
            platform="x",
            post_id=tweet["id"],
            content=tweet["text"],
            url=f"https://x.com/i/status/{tweet['id']}",
            created_at=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
        )


class XTargetAdapter(BaseTargetAdapter):
    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        provider = self.config.get("provider", "postpeer")

        if provider == "postpeer":
            return self._post_via_postpeer(content, title, url, tags)
        elif provider == "opentweet":
            return self._post_via_opentweet(content, title, url, tags)
        elif provider == "zernio":
            return self._post_via_zernio(content, title, url, tags)
        elif provider == "official":
            return self._post_via_official(content, title, url, tags)
        else:
            raise ValueError(f"Unknown X provider: {provider}")

    def _post_via_postpeer(self, content: str, title: Optional[str] = None,
                           url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        post_url = "https://api.postpeer.dev/v1/posts"
        headers = {
            "x-access-key": self.config["api_key"],
            "Content-Type": "application/json"
        }
        payload = {
            "content": content[:280],
            "platforms": [{"platform": "twitter", "accountId": self.config.get("account_id", "")}],
            "publishNow": True
        }
        resp = requests.post(post_url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _post_via_opentweet(self, content: str, title: Optional[str] = None,
                            url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        post_url = "https://api.opentweet.io/v1/tweets"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {"text": content[:280]}
        resp = requests.post(post_url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _post_via_zernio(self, content: str, title: Optional[str] = None,
                         url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        post_url = "https://api.zernio.com/v1/posts"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "content": content[:280],
            "platform": "twitter"
        }
        resp = requests.post(post_url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _post_via_official(self, content: str, title: Optional[str] = None,
                           url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        post_url = "https://api.twitter.com/2/tweets"
        oauth = self._oauth1_sign("POST", post_url)
        headers = {
            "Authorization": f'OAuth ' + ", ".join(f'{k}="{quote(v)}"' for k, v in oauth.items()),
            "Content-Type": "application/json"
        }
        payload = {"text": content[:280]}
        resp = requests.post(post_url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _oauth1_sign(self, method: str, url: str) -> dict:
        oauth = {
            "oauth_consumer_key": self.config["api_key"],
            "oauth_nonce": str(int(time.time() * 1000)),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.config["access_token"],
            "oauth_version": "1.0"
        }
        all_params = dict(oauth)
        sorted_params = "&".join(f"{quote(k)}={quote(str(v))}" for k, v in sorted(all_params.items()))
        base_string = f"{method.upper()}&{quote(url)}&{quote(sorted_params)}"
        signing_key = f"{quote(self.config['api_secret'])}&{quote(self.config['access_token_secret'])}"
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        oauth["oauth_signature"] = signature
        return oauth

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 280:
            return False, f"Content too long for X ({len(content)}/280)"
        return True, "OK"
