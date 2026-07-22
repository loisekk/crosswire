import json
import logging
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PLATFORM_PROMPTS = {
    "linkedin": """Transform this content for LinkedIn. Rules:
- Professional, authoritative tone
- Start with a hook (question, bold statement, or insight)
- Use line breaks for readability (1-2 sentences per line)
- Add 3-5 relevant hashtags at the end
- Include a call-to-action (ask a question, invite comments)
- Max 3000 characters
- Showcase expertise and learning journey""",

    "x": """Transform this content for X (Twitter). Rules:
- Max 280 characters total
- Punchy, concise, impactful
- Use emojis sparingly for emphasis
- No hashtags (or max 1-2)
- End with a hook or question
- Strip all formatting, keep only the core message""",

    "reddit": """Transform this content for Reddit. Rules:
- Casual, conversational tone (like talking to a friend)
- No hashtags, no corporate speak
- Start with context (what you built/learned and why)
- Ask for feedback or share a lesson learned
- Be genuine, avoid self-promotion tone
- Include technical details other devs would care about
- Max 40000 characters""",

    "devto": """Transform this content for Dev.to. Rules:
- Technical, tutorial-style tone
- Use markdown formatting (headings, code blocks, lists)
- Include what you built, how it works, lessons learned
- Add a "Key Takeaways" section
- Use tags: programming, webdev, or relevant tech
- Be educational, help others learn from your experience
- Max 40000 characters""",

    "hashnode": """Transform this content for Hashnode blog. Rules:
- Long-form, detailed blog post style
- Use markdown with proper headings (##, ###)
- Include code examples if relevant
- Add sections: Introduction, What I Built, How It Works, Challenges, Conclusion
- SEO-friendly title
- Be detailed and thorough
- Max 50000 characters""",

    "medium": """Transform this content for Medium. Rules:
- Storytelling narrative style
- Start with a compelling opening line
- Use subheadings to break up content
- Include personal anecdotes and reflections
- Be vulnerable about challenges faced
- End with a forward-looking conclusion
- Use formatting: bold, italics, blockquotes
- Max 50000 characters""",

    "indeed": """Transform this content for Indeed job posting. Rules:
- Professional job description format
- Highlight skills and technologies used
- Include role, responsibilities, and achievements
- Use bullet points for key skills
- Mention impact and results
- Keep it concise and job-focused""",

    "naukri": """Transform this content for Naukri job profile. Rules:
- Professional summary format
- Highlight technical skills and projects
- Include achievements with metrics
- Use industry keywords
- Be concise and impactful""",

    "glassdoor": """Transform this content for Glassdoor. Rules:
- Company review / job posting style
- Be honest and balanced
- Highlight work culture and growth
- Include specific examples
- Professional but authentic tone""",

    "ziprecruiter": """Transform this content for ZipRecruiter. Rules:
- Job posting format
- Clear job title and description
- Required skills and qualifications
- Benefits and perks
- Call to action to apply""",

    "shine": """Transform this content for Shine.com. Rules:
- Professional job posting format
- Indian job market focused
- Include relevant skills and experience
- Use clear, concise language
- Highlight career growth opportunities""",

    "timesjobs": """Transform this content for TimesJobs. Rules:
- Professional job listing format
- Include job title, department, location
- List key responsibilities
- Required qualifications and skills
- Application instructions""",

    "apna": """Transform this content for Apna app. Rules:
- Short, punchy job posting
- Focus on key skills needed
- Include salary range if possible
- Simple, easy to read format
- Hindi-English mix is OK""",

    "iimjobs": """Transform this content for IIMJobs. Rules:
- Executive-level job posting format
- Focus on leadership and management skills
- Include industry and function
- Highlight career progression
- Professional and authoritative tone"""
}


class AITransformer:
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._check_connection()

    def _check_connection(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                logger.info(f"Ollama connected. Model: {self.model}")
            else:
                logger.warning(f"Ollama responded with status {resp.status_code}")
        except requests.ConnectionError:
            logger.error("Cannot connect to Ollama. Make sure 'ollama serve' is running.")
            raise ConnectionError("Ollama not reachable at " + self.base_url)

    def transform(self, content: str, title: str = "", platform: str = "linkedin",
                  source_platform: str = "linkedin") -> Dict[str, Any]:
        prompt = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS["linkedin"])

        system_prompt = f"""You are a content transformation expert. You transform posts from one social media platform to another.

Source platform: {source_platform}
Target platform: {platform}

{prompt}

Original content:
Title: {title}
Content: {content}

Transform this content for {platform}. Return ONLY the transformed content, nothing else."""

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1024
                    }
                },
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
            transformed = result.get("response", "").strip()

            if not transformed:
                logger.warning(f"Empty response from Ollama for {platform}")
                return {"content": content, "title": title, "transformed": False}

            return {
                "content": transformed,
                "title": title,
                "transformed": True,
                "platform": platform
            }

        except requests.Timeout:
            logger.error(f"Ollama timeout for {platform}")
            return {"content": content, "title": title, "transformed": False}
        except Exception as e:
            logger.error(f"AI transformation error for {platform}: {e}")
            return {"content": content, "title": title, "transformed": False}

    def transform_for_all(self, content: str, title: str = "",
                          platforms: Optional[List[str]] = None, source_platform: str = "linkedin") -> Dict[str, Dict[str, Any]]:
        if platforms is None:
            platforms = list(PLATFORM_PROMPTS.keys())

        results = {}
        for platform in platforms:
            if platform == source_platform:
                results[platform] = {"content": content, "title": title, "transformed": False, "original": True}
                continue

            logger.info(f"Transforming for {platform}...")
            results[platform] = self.transform(content, title, platform, source_platform)

        return results


def transform_for_n8n(content: str, title: str = "", platforms: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    transformer = AITransformer()
    return transformer.transform_for_all(content, title, platforms)
