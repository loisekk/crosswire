import requests
from datetime import datetime
from typing import Optional, List
from .base import BaseSourceAdapter, BaseTargetAdapter, Post


class HashnodeSourceAdapter(BaseSourceAdapter):
    API_URL = "https://api.hashnode.com"

    def fetch_new_posts(self, since: Optional[datetime] = None) -> List[Post]:
        publication_host = self.config.get("publication_host", "your-publication.hashnode.dev")
        query = f"""
        query GetPosts {{
            publication(host: "{publication_host}") {{
                posts(first: 10) {{
                    edges {{
                        node {{
                            id
                            title
                            brief
                            slug
                            publishedAt
                            tags {{ name }}
                        }}
                    }}
                }}
            }}
        }}
        """
        headers = {"Authorization": self.config["api_key"]}
        resp = requests.post(self.API_URL, json={"query": query}, headers=headers)
        resp.raise_for_status()

        posts = []
        edges = resp.json().get("data", {}).get("publication", {}).get("posts", {}).get("edges", [])
        for edge in edges:
            node = edge["node"]
            published = datetime.fromisoformat(node["publishedAt"].replace("Z", "+00:00"))
            if since and published <= since:
                continue

            posts.append(Post(
                platform="hashnode",
                post_id=node["id"],
                content=node.get("brief", ""),
                title=node.get("title"),
                url=f"https://{publication_host}/{node['slug']}",
                tags=[t["name"] for t in node.get("tags", [])],
                created_at=published
            ))
        return posts

    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        query = """
        query GetPost($id: String!) {
            post(id: $id) {
                id title brief slug publishedAt
                tags { name }
            }
        }
        """
        headers = {"Authorization": self.config["api_key"]}
        resp = requests.post(self.API_URL, json={"query": query, "variables": {"id": post_id}}, headers=headers)
        resp.raise_for_status()
        post = resp.json().get("data", {}).get("post")
        if not post:
            return None
        publication_host = self.config.get("publication_host", "your-publication.hashnode.dev")
        return Post(
            platform="hashnode",
            post_id=post["id"],
            content=post.get("brief", ""),
            title=post.get("title"),
            url=f"https://{publication_host}/{post['slug']}",
            tags=[t["name"] for t in post.get("tags", [])],
            created_at=datetime.fromisoformat(post["publishedAt"].replace("Z", "+00:00"))
        )


class HashnodeTargetAdapter(BaseTargetAdapter):
    API_URL = "https://api.hashnode.com"

    def post(self, content: str, title: Optional[str] = None,
             url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        query = """
        mutation CreatePost($input: CreatePostInput!) {
            createPost(input: $input) {
                post { id title }
            }
        }
        """
        payload = {
            "title": title or "Cross-posted Article",
            "contentMarkdown": content,
            "tags": [{"name": t} for t in (tags or [])[:5]],
            "publicationId": self.config["publication_id"]
        }
        headers = {"Authorization": self.config["api_key"]}
        resp = requests.post(self.API_URL, json={"query": query, "variables": {"input": payload}}, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) < 10:
            return False, "Content too short for Hashnode"
        return True, "OK"
