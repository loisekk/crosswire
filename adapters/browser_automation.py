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

        storage_file = self.STATE_DIR / f"{self.__class__.__name__}_state.json"
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
        storage_file = self.STATE_DIR / f"{self.__class__.__name__}_state.json"
        await context.storage_state(path=str(storage_file))

    async def _human_delay(self, page, min_ms=500, max_ms=2000):
        import random
        delay = random.randint(min_ms, max_ms) / 1000
        await page.wait_for_timeout(int(delay * 1000))


class IndeedTargetAdapter(BaseTargetAdapter, BrowserAutomationMixin):
    LOGIN_URL = "https://secure.indeed.com/auth"
    POST_URL = "https://employers.indeed.com/post"

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 4000:
            return False, "Content too long for Indeed"
        return True, "OK"

    async def _login(self, page):
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await self._human_delay(page)

        email_input = page.locator('input[name="email"], input#email-input')
        if await email_input.count() > 0:
            await email_input.fill(self.config["email"])
            await self._human_delay(page)

            password_input = page.locator('input[name="password"], input#password-input')
            await password_input.fill(self.config["password"])
            await self._human_delay(page)

            submit_btn = page.locator('button[type="submit"], button[data-testid="login-submit"]')
            await submit_btn.click()
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

            title_input = page.locator('input[name="title"], textarea[name="title"], #job-title')
            if await title_input.count() > 0:
                await title_input.fill(title or "Cross-posted Position")
                await self._human_delay(page)

            desc_input = page.locator('textarea[name="description"], div[contenteditable="true"], #job-description')
            if await desc_input.count() > 0:
                await desc_input.fill(content)
                await self._human_delay(page)

            if url:
                url_input = page.locator('input[name="url"], input[name="job-url"]')
                if await url_input.count() > 0:
                    await url_input.fill(url)
                    await self._human_delay(page)

            submit_btn = page.locator('button[type="submit"], button:has-text("Post"), button:has-text("Submit")')
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await page.wait_for_load_state("networkidle")
                await self._human_delay(page, 3000, 7000)

            await self._save_state(context)
            return {
                "status": "posted",
                "platform": "indeed",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await browser.close()
            await pw.stop()


class NaukriTargetAdapter(BaseTargetAdapter, BrowserAutomationMixin):
    LOGIN_URL = "https://www.naukri.com/nlogin/login"
    POST_URL = "https://www.naukri.com/jobapi/v3/createjob"

    def validate_content(self, content: str) -> tuple[bool, str]:
        if len(content) > 4000:
            return False, "Content too long for Naukri"
        return True, "OK"

    async def _login(self, page):
        await page.goto(self.LOGIN_URL, wait_until="networkidle")
        await self._human_delay(page)

        email_input = page.locator('input[name="username"], input[type="email"], #emailField')
        if await email_input.count() > 0:
            await email_input.fill(self.config["email"])
            await self._human_delay(page)

            password_input = page.locator('input[name="password"], input[type="password"], #passwordField')
            await password_input.fill(self.config["password"])
            await self._human_delay(page)

            submit_btn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            await self._human_delay(page, 2000, 5000)

    async def post(self, content: str, title: Optional[str] = None,
                   url: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
        pw, browser, context = await self._get_browser_context()
        try:
            page = await context.new_page()
            await self._login(page)
            await self._save_state(context)

            await page.goto("https://www.naukri.com/post-a-job", wait_until="networkidle")
            await self._human_delay(page)

            title_input = page.locator('input[name="title"], textarea[name="title"], #jobTitle')
            if await title_input.count() > 0:
                await title_input.fill(title or "Cross-posted Position")
                await self._human_delay(page)

            desc_input = page.locator('textarea[name="description"], div[contenteditable="true"], #jobDescription')
            if await desc_input.count() > 0:
                await desc_input.fill(content)
                await self._human_delay(page)

            if url:
                url_input = page.locator('input[name="url"], input[name="job-url"], #jobUrl')
                if await url_input.count() > 0:
                    await url_input.fill(url)
                    await self._human_delay(page)

            submit_btn = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Post")')
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await page.wait_for_load_state("networkidle")
                await self._human_delay(page, 3000, 7000)

            await self._save_state(context)
            return {
                "status": "posted",
                "platform": "naukri",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await browser.close()
            await pw.stop()


def run_async(coro):
    return asyncio.run(coro)
