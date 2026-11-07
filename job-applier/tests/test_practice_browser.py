import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from applier.browser import BrowserSession
from applier.practice import CAPTCHA_ID, COLOR_ID, SUCCESS_ID, PracticeSite
from applier.practice import practice_profile, practice_search
from applier.runner import RunHooks, execute
from applier.store import Store


class MemoryHooks(RunHooks):
    def __init__(self):
        self.lines = []
        self.items = []

    def log(self, message):
        self.lines.append(message)

    def inbox(self, item):
        self.items.append(item)

    def stopped(self):
        return False


def chromium_ready() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception:
        return False
    return True


@unittest.skipUnless(chromium_ready(), "Playwright Chromium is not installed")
class PracticeBrowserTests(unittest.TestCase):
    def test_practice_files_one_and_skips_the_rest(self):
        with tempfile.TemporaryDirectory() as directory:
            site = PracticeSite(Path(directory))
            site.start()
            try:
                hooks = MemoryHooks()
                store = Store(Path(directory) / "practice.db")
                profile = practice_profile(site.resume_path)
                stats = execute(
                    site.jobs(datetime(2026, 11, 7, 16, 0, tzinfo=timezone.utc)),
                    profile,
                    practice_search(),
                    submit=True,
                    allow_localhost=True,
                    max_age_days=14,
                    salary_floor=profile.salary_floor,
                    daily_cap=10,
                    pause_seconds=0,
                    cover_mode="template",
                    resume_path=site.resume_path,
                    store=store,
                    hooks=hooks,
                    browser_factory=lambda: BrowserSession(allow_localhost=True),
                    now=datetime(2026, 11, 7, 16, 0, tzinfo=timezone.utc),
                    inbox_for=lambda: {"title": "Software Engineer", "company": "Practice Co", **(site.inbox[-1] if site.inbox else {})},
                )
                self.assertEqual(stats.filed, 1, "\n".join(hooks.lines))
                self.assertEqual(stats.matched, 3, "\n".join(hooks.lines))
                self.assertEqual(site.views.count(SUCCESS_ID), 1)
                self.assertEqual(site.views.count(CAPTCHA_ID), 1)
                self.assertNotIn(COLOR_ID, site.views)
                self.assertNotIn("se-staff", site.views)
                self.assertNotIn("se-austin", site.views)
                self.assertNotIn("se-old", site.views)
                self.assertEqual(len(site.inbox), 1)
                filed = site.inbox[0]
                self.assertEqual(filed["first_name"], "Practice")
                self.assertEqual(filed["last_name"], "Applicant")
                self.assertEqual(filed["email"], "practice@example.com")
                self.assertEqual(filed["work_authorization"], "Yes")
                self.assertEqual(filed["sponsorship"], "No")
                self.assertEqual(filed["salary"], "80000")
                self.assertEqual(filed["school"], "Example State University")
                self.assertEqual(filed["veteran"], "I don't wish to answer")
                self.assertEqual(filed["privacy"], "on")
                self.assertTrue(filed["resume_filename"].endswith(".pdf"))
                self.assertGreater(filed["resume_bytes"], 0)
                self.assertIn("I am applying for Software Engineer", filed["cover"])
                self.assertIn("Practice Applicant", filed["cover"])
                self.assertTrue(any("favorite color" in line.lower() for line in hooks.lines))
                self.assertTrue(any("CAPTCHA" in line for line in hooks.lines))
            finally:
                site.stop()


if __name__ == "__main__":
    unittest.main()
