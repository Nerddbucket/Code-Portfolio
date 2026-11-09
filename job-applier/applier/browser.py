from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .htmlform import questions_from_html
from .models import Answer, FormQuestion

ALLOWED_HOSTS = {
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "boards.eu.greenhouse.io",
    "job-boards.eu.greenhouse.io",
    "jobs.lever.co",
    "jobs.eu.lever.co",
    "jobs.ashbyhq.com",
}
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,80}$")


def allowed_apply_url(url: str, *, allow_localhost: bool) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if allow_localhost and host in {"127.0.0.1", "localhost"} and parsed.scheme == "http":
        return True
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return False
    if parsed.port not in (None, 443):
        return False
    return host in ALLOWED_HOSTS


def blocking_captcha(html: str) -> bool:
    text = html or ""
    lowered = text.lower()
    if "verify you are human" in lowered or "i'm not a robot" in lowered or "i’m not a robot" in lowered:
        return True
    if "cf-turnstile" in lowered or "challenges.cloudflare.com" in lowered:
        return True
    if re.search(r"class=['\"][^'\"]*h-captcha", lowered):
        return True
    for match in re.finditer(r"<[^>]*class=['\"][^'\"]*g-recaptcha[^'\"]*['\"][^>]*>", lowered):
        tag = match.group(0)
        if "data-size='invisible'" in tag or 'data-size="invisible"' in tag:
            continue
        return True
    if "recaptcha/api2/bframe" in lowered:
        return True
    return False


def blocking_login(html: str) -> bool:
    return re.search(r"<input\b[^>]*type=['\"]password['\"]", html or "", re.I) is not None


def blocking_email_code(visible_text: str) -> bool:
    lowered = (visible_text or "").lower()
    cues = (
        "enter the verification code",
        "we emailed you a code",
        "check your email for a code",
        "one-time code",
    )
    return any(cue in lowered for cue in cues)


@dataclass(frozen=True)
class FileResult:
    filed: bool
    reason: str
    captured: dict | None = None


MISSING_JS = """
() => {
  const missing = [];
  const controls = [...document.querySelectorAll("input, select, textarea")];
  for (const el of controls) {
    if (el.disabled || el.type === "hidden" || el.type === "submit" || el.type === "button") continue;
    const required = el.required || el.getAttribute("aria-required") === "true";
    if (!required) continue;
    let filled = false;
    if (el.type === "checkbox" || el.type === "radio") filled = el.checked;
    else if (el.type === "file") filled = el.files && el.files.length > 0;
    else if (el.classList.contains("select__input")) {
      const shell = el.closest(".select");
      const chosen = shell && shell.querySelector(".select__single-value");
      filled = !!(chosen && chosen.textContent.trim()) || el.dataset.selected;
    } else filled = !!(el.value && el.value.trim());
    if (!filled) {
      const label = document.querySelector(`label[for="${el.id}"]`);
      missing.push((label && label.innerText) || el.name || el.id || "required field");
    }
  }
  return missing;
}
"""

CONFIRM_JS = """
([name, label, kind]) => {
  const el = document.querySelector(`[name="${name}"]`) || document.getElementById(name);
  if (!el) return false;
  if (kind === "file") return !!(el.files && el.files.length);
  if (kind === "checkbox") return !!el.checked;
  if (el.tagName === "SELECT") {
    const option = el.selectedOptions && el.selectedOptions[0];
    return !!(option && (option.label === label || option.value === label));
  }
  if (el.classList.contains("select__input") || el.getAttribute("role") === "combobox") {
    return el.dataset.selected === label;
  }
  return (el.value || "").trim() === label;
}
"""


class BrowserSession:
    def __init__(self, allow_localhost: bool = False):
        self.allow_localhost = allow_localhost
        self._playwright = None
        self._browser = None

    def __enter__(self) -> "BrowserSession":
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def file_application(
        self,
        url: str,
        plan_answers: tuple[Answer, ...],
        resume_path: Path | None,
        cover_path: Path | None,
        stop,
        profile=None,
        cover_text: str = "",
        known_questions: tuple[FormQuestion, ...] | None = None,
    ) -> FileResult:
        if not allowed_apply_url(url, allow_localhost=self.allow_localhost):
            return FileResult(False, "Skipped: the application link is not a Greenhouse, Lever, or Ashby page")
        if self._browser is None:
            raise RuntimeError("Browser is not open")
        page = self._browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if not allowed_apply_url(page.url, allow_localhost=self.allow_localhost):
                return FileResult(False, "Skipped: the page left the application site")
            html = page.content()
            if blocking_captcha(html):
                return FileResult(False, "Skipped: a visible CAPTCHA is on the page")
            if blocking_login(html):
                return FileResult(False, "Skipped: the page asks for a login")
            visible = page.inner_text("body")
            if blocking_email_code(visible):
                return FileResult(False, "Skipped: the page wants an email verification code")
            questions = known_questions
            if questions is None:
                questions = questions_from_html(html)
                if not questions:
                    return FileResult(False, "Skipped: the application form could not be read")
                if profile is None:
                    return FileResult(False, "Skipped: profile was missing")
                from .questions import plan_application as build_plan

                built = build_plan(questions, profile, cover_text)
                if not built.ok:
                    return FileResult(False, built.reason)
                plan_answers = built.answers
            if stop():
                return FileResult(False, "Stopped before sending")
            for answer in plan_answers:
                if not SAFE_NAME.match(answer.name):
                    return FileResult(False, f"Skipped: form field {answer.name} is not safe to fill")
                self._fill(page, answer, resume_path, cover_path)
                confirmed = page.evaluate(CONFIRM_JS, [answer.name, answer.value if answer.kind != "file" else answer.value, answer.kind])
                if answer.kind == "file":
                    confirmed = page.evaluate(CONFIRM_JS, [answer.name, "", "file"])
                if answer.kind == "textarea":
                    confirmed = page.evaluate(
                        """([name, value]) => {
                            const el = document.querySelector(`[name="${name}"]`);
                            return !!el && el.value.trim() === value.trim();
                        }""",
                        [answer.name, answer.value],
                    )
                if not confirmed:
                    return FileResult(False, f"Skipped: could not confirm the answer for {answer.label}")
            missing = page.evaluate(MISSING_JS)
            if missing:
                return FileResult(False, "Skipped: a required field is still empty: " + "; ".join(missing[:4]))
            if stop():
                return FileResult(False, "Stopped before sending")
            page.get_by_role("button", name=re.compile(r"submit", re.I)).click(timeout=5000)
            page.get_by_text(re.compile(r"application received|thank you|application has been submitted", re.I)).wait_for(timeout=8000)
            after = page.content()
            if blocking_captcha(after) and "application received" not in after.lower() and "thank you" not in after.lower():
                return FileResult(False, "Skipped: a CAPTCHA appeared and the application was not confirmed")
            captured = page.evaluate("() => window.__filed || null")
            return FileResult(True, "Filed", captured)
        except Exception as exc:
            return FileResult(False, f"Skipped: the form could not be sent ({exc.__class__.__name__}: {exc})"[:300])
        finally:
            page.close()

    def _fill(self, page, answer: Answer, resume_path: Path | None, cover_path: Path | None) -> None:
        name = answer.name
        if answer.kind == "file":
            if resume_path is None:
                raise RuntimeError("resume missing")
            page.locator(f"input[type=file][name='{name}']").set_input_files(str(resume_path))
            return
        if answer.kind == "cover_file":
            if cover_path is None:
                raise RuntimeError("cover letter missing")
            page.locator(f"input[type=file][name='{name}']").set_input_files(str(cover_path))
            return
        if answer.kind == "checkbox":
            page.locator(f"input[type=checkbox][name='{name}']").check()
            return
        select = page.locator(f"select[name='{name}']")
        if answer.kind == "select" and select.count():
            select.select_option(label=answer.value)
            return
        if answer.kind == "select":
            box = page.locator(f"[name='{name}']")
            box.click()
            option = page.get_by_role("option", name=answer.value, exact=True)
            option.first.wait_for(state="visible", timeout=3000)
            option.click(timeout=3000)
            return
        page.locator(f"[name='{name}']").fill(answer.value)
