import asyncio
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from .base import BaseTargetAdapter, Post

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


class BrowserAutomationMixin:
    STATE_DIR = Path.home() / ".crosspost"

    async def _get_browser_context(self):
        if async_playwright is None:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install")

        self.STATE_DIR.mkdir(exist_ok=True)
        pw = await async_playwright().start()

        storage_file = self.STATE_DIR / f"MediumTargetAdapter_state.json"
        context_args = {
            "viewport": {"width": 1280, "height": 800},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if storage_file.exists():
            context_args["storage_state"] = str(storage_file)

        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(**context_args)
        return pw, browser, context

    async def _save_state(self, context):
        storage_file = self.STATE_DIR / f"MediumTargetAdapter_state.json"
        await context.storage_state(path=str(storage_file))

    async def _human_delay(self, page, min_ms=500, max_ms=2000):
        import random
        delay = random.randint(min_ms, max_ms) / 1000
        await page.wait_for_timeout(int(delay * 1000))


class MediumTargetAdapter(BaseTargetAdapter, BrowserAutomationMixin):
    LOGIN_URL = "https://medium.com/m/signin"
    POST_URL = "https://medium.com/new-story"

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 50000:
            return False, "Content too long for Medium (max 50000 chars)"
        if len(content) < 100:
            return False, "Content too short for Medium (min 100 chars)"
        return True, "OK"

    async def _login(self, page):
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await self._human_delay(page)

        email_input = page.locator('input[name="email"], input[type="email"]')
        if await email_input.count() > 0:
            await email_input.fill(self.config["email"])
            await self._human_delay(page)

            continue_btn = page.locator('button:has-text("Continue"), button[type="submit"]')
            await continue_btn.click()
            await self._human_delay(page, 1000, 2000)

            password_input = page.locator('input[name="password"], input[type="password"]')
            if await password_input.count() > 0:
                await password_input.fill(self.config["password"])
                await self._human_delay(page)

                sign_in_btn = page.locator('button:has-text("Sign in"), button[type="submit"]')
                await sign_in_btn.click()
                await page.wait_for_load_state("networkidle")
                await self._human_delay(page, 2000, 5000)

    async def post(self, content: str, title: Optional[str] = None,
                   url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        pw, browser, context = await self._get_browser_context()
        try:
            page = await context.new_page()
            await self._login(page)
            await self._save_state(context)

            await page.goto(self.POST_URL, wait_until="networkidle")
            await self._human_delay(page)

            title_input = page.locator('h1[placeholder], div[contenteditable="true"][data-placeholder="Title"], textarea[name="title"]')
            if await title_input.count() > 0:
                await title_input.fill(title or "Cross-posted Article")
                await self._human_delay(page)

            story_input = page.locator('div[contenteditable="true"][data-placeholder="Tell your story..."], div.section-content')
            if await story_input.count() > 0:
                await story_input.click()
                await self._human_delay(page)

                paragraphs = content.split('\n')
                for para in paragraphs:
                    if para.strip():
                        await page.keyboard.type(para)
                        await page.keyboard.press("Enter")
                        await self._human_delay(page, 100, 300)

            publish_btn = page.locator('button:has-text("Publish"), button:has-text("Ready to publish")')
            if await publish_btn.count() > 0:
                await publish_btn.click()
                await self._human_delay(page, 1000, 2000)

                confirm_btn = page.locator('button:has-text("Publish now"), button:has-text("Publish")')
                if await confirm_btn.count() > 0:
                    await confirm_btn.click()
                    await page.wait_for_load_state("networkidle")
                    await self._human_delay(page, 3000, 7000)

            await self._save_state(context)
            return {
                "status": "posted",
                "platform": "medium",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await browser.close()
            await pw.stop()


def run_async(coro):
    return asyncio.run(coro)
