import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from applier.browser import FileResult, allowed_apply_url, blocking_captcha, blocking_email_code, blocking_login
from applier.config import config_problems, load_config
from applier.models import Job
from applier.practice import practice_profile, practice_search, success_questions
from applier.runner import RunHooks, execute
from applier.store import Store


NOW = datetime(2026, 11, 7, 16, 0, tzinfo=timezone.utc)


class MemoryHooks(RunHooks):
    def __init__(self):
        self.lines = []
        self.items = []
        self.flag = False

    def log(self, message):
        self.lines.append(message)

    def inbox(self, item):
        self.items.append(item)

    def stopped(self):
        return self.flag


class FakeBrowser:
    def __init__(self, hooks=None):
        self.urls = []
        self.hooks = hooks

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def file_application(self, url, plan_answers, resume_path, cover_path, stop, **kwargs):
        if stop():
            return FileResult(False, "Stopped before sending")
        self.urls.append(url)
        if self.hooks is not None:
            self.hooks.flag = True
        return FileResult(True, "Filed", {"url": url})


def good_job(job_id, **overrides):
    data = dict(
        source="greenhouse",
        company="acme",
        job_id=job_id,
        title="Software Engineer",
        location="Remote, United States",
        workplace="remote",
        url=f"https://job-boards.greenhouse.io/acme/jobs/{job_id}",
        apply_url=f"https://job-boards.greenhouse.io/acme/jobs/{job_id}",
        description="Build software.",
        published_at=NOW,
        questions=success_questions(),
    )
    data.update(overrides)
    return Job(**data)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.resume = Path(self.directory.name) / "resume.pdf"
        self.resume.write_bytes(b"%PDF-1.4 practice")
        self.store = Store(Path(self.directory.name) / "applications.db")
        self.profile = practice_profile(self.resume)

    def tearDown(self):
        self.directory.cleanup()

    def test_dry_run_does_not_open_a_browser(self):
        hooks = MemoryHooks()

        def factory():
            raise AssertionError("browser should stay closed")

        stats = execute(
            [good_job("1"), good_job("2", title="Staff Software Engineer"), good_job("3", location="Austin, Texas", workplace="onsite")],
            self.profile,
            practice_search(),
            submit=False,
            allow_localhost=False,
            max_age_days=14,
            salary_floor="80000",
            daily_cap=10,
            pause_seconds=0,
            cover_mode="template",
            resume_path=self.resume,
            store=self.store,
            hooks=hooks,
            browser_factory=factory,
            now=NOW,
        )
        self.assertEqual(stats.dry_run, 1)
        self.assertEqual(stats.filed, 0)
        self.assertTrue(any("Would file" in line for line in hooks.lines))
        self.assertTrue(any("Dry run did not send" in line for line in hooks.lines))

    def test_unknown_question_is_not_sent(self):
        from applier.models import FormField, FormQuestion, Option

        color = good_job(
            "9",
            questions=success_questions()
            + (
                FormQuestion(
                    "What is your favorite color?",
                    True,
                    (FormField("favorite_color", "select", (Option("Red", "Red"),)),),
                ),
            ),
        )
        hooks = MemoryHooks()
        browser = FakeBrowser()
        execute(
            [color],
            self.profile,
            practice_search(),
            submit=True,
            allow_localhost=False,
            max_age_days=14,
            salary_floor="",
            daily_cap=10,
            pause_seconds=0,
            cover_mode="template",
            resume_path=self.resume,
            store=self.store,
            hooks=hooks,
            browser_factory=lambda: browser,
            now=NOW,
        )
        self.assertEqual(browser.urls, [])
        self.assertTrue(any("favorite color" in line.lower() for line in hooks.lines))

    def test_stop_prevents_the_next_submit(self):
        hooks = MemoryHooks()
        browser = FakeBrowser(hooks)
        stats = execute(
            [good_job("1"), good_job("2")],
            self.profile,
            practice_search(),
            submit=True,
            allow_localhost=False,
            max_age_days=14,
            salary_floor="",
            daily_cap=10,
            pause_seconds=0,
            cover_mode="template",
            resume_path=self.resume,
            store=self.store,
            hooks=hooks,
            browser_factory=lambda: browser,
            now=NOW,
        )
        self.assertEqual(browser.urls, [good_job("1").apply_url])
        self.assertEqual(stats.filed, 1)
        self.assertTrue(any(line == "Stopped." for line in hooks.lines))

    def test_offsite_link_is_not_opened(self):
        hooks = MemoryHooks()
        browser = FakeBrowser()
        evil = good_job("4", apply_url="https://evil.example/apply", url="https://evil.example/apply")
        execute(
            [evil],
            self.profile,
            practice_search(),
            submit=True,
            allow_localhost=False,
            max_age_days=14,
            salary_floor="",
            daily_cap=10,
            pause_seconds=0,
            cover_mode="template",
            resume_path=self.resume,
            store=self.store,
            hooks=hooks,
            browser_factory=lambda: browser,
            now=NOW,
        )
        self.assertEqual(browser.urls, [])
        self.assertTrue(any("not an allowed board" in line for line in hooks.lines))

    def test_daily_cap_blocks_a_second_filing(self):
        self.store.record("seed", "Old", "acme", "https://job-boards.greenhouse.io/acme/jobs/0", "filed", "filed")
        hooks = MemoryHooks()
        browser = FakeBrowser()
        execute(
            [good_job("8")],
            self.profile,
            practice_search(),
            submit=True,
            allow_localhost=False,
            max_age_days=14,
            salary_floor="",
            daily_cap=1,
            pause_seconds=0,
            cover_mode="template",
            resume_path=self.resume,
            store=self.store,
            hooks=hooks,
            browser_factory=lambda: browser,
            now=NOW,
        )
        self.assertEqual(browser.urls, [])
        self.assertTrue(any("Daily cap" in line for line in hooks.lines))


class GuardTests(unittest.TestCase):
    def test_captcha_login_and_email_code_detection(self):
        invisible = '<script>window.ENV = {"GOOGLE_RECAPTCHA_INVISIBLE_KEY":"6Lf"}</script>'
        self.assertFalse(blocking_captcha(invisible))
        self.assertTrue(blocking_captcha('<div class="g-recaptcha" data-sitekey="x"></div>'))
        self.assertFalse(blocking_captcha('<div class="g-recaptcha" data-size="invisible" data-sitekey="x"></div>'))
        self.assertTrue(blocking_login('<input type="password" name="password">'))
        self.assertTrue(blocking_email_code("Enter the verification code we sent"))
        self.assertTrue(allowed_apply_url("https://jobs.lever.co/spotify/abc/apply", allow_localhost=False))
        self.assertTrue(allowed_apply_url("https://jobs.ashbyhq.com/ashby/1/application", allow_localhost=False))
        self.assertFalse(allowed_apply_url("https://evil.example/apply", allow_localhost=False))
        self.assertFalse(allowed_apply_url("http://127.0.0.1:9/apply/1", allow_localhost=False))
        self.assertTrue(allowed_apply_url("http://127.0.0.1:9/apply/1", allow_localhost=True))

    def test_live_config_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = json.loads(Path("config.example.json").read_text(encoding="utf-8"))
            config["submit"] = True
            config["search"]["titles"] = ["software engineer"]
            config["search"]["companies"]["greenhouse"] = ["gitlab"]
            config["profile"].update(
                {
                    "first_name": "YOUR NAME",
                    "last_name": "Example",
                    "email": "person@example.com",
                    "phone": "919-555-0100",
                    "country": "United States",
                    "work_authorization": "yes",
                    "needs_sponsorship": "no",
                    "resume_pdf": "missing.pdf",
                }
            )
            path.write_text(json.dumps(config), encoding="utf-8")
            loaded = load_config(path)
            problems = " ".join(config_problems(loaded, filing=True)).lower()
            self.assertIn("name", problems)
            self.assertIn("email", problems)
            self.assertIn("resume", problems)
            self.assertEqual(loaded.daily_cap, 10)
            loaded_cap = load_config(path)
            raw = json.loads(path.read_text())
            raw["daily_cap"] = 500
            path.write_text(json.dumps(raw))
            capped = load_config(path)
            self.assertEqual(capped.daily_cap, 50)
            self.assertTrue(any("50" in warning for warning in capped.warnings))
            self.assertIsNotNone(loaded_cap)


if __name__ == "__main__":
    unittest.main()
