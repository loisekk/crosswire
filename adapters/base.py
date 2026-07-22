from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List
import hashlib


@dataclass
class Post:
    platform: str
    post_id: str
    content: str
    title: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    raw_data: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.md5(f"{self.platform}:{self.post_id}:{self.content}".encode()).hexdigest()


class BaseSourceAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        pass

    @abstractmethod
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        pass


class BaseTargetAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> Any:
        pass

    @abstractmethod
    def validate_content(self, content: str) -> tuple[bool, str]:
        pass

    def transform_content(self, post: Post, transform_config: dict) -> tuple[str, List[str]]:
        content = post.content
        tags = post.tags.copy()

        if transform_config.get("truncate_to"):
            max_len = transform_config["truncate_to"]
            if transform_config.get("add_linkback") and post.url:
                max_len -= len(post.url) - 5
            content = content[:max_len]

        if transform_config.get("add_linkback") and post.url:
            content = f"{content}\n\n{post.url}"

        if transform_config.get("hashtags") and tags:
            hashtag_str = " ".join(f"#{t}" for t in tags[:5])
            content = f"{content}\n\n{hashtag_str}"

        return content, tags
