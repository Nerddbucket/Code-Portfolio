from __future__ import annotations

import json
import os
import urllib.request

from .models import Job, Profile

DEFAULT_MODEL = "claude-sonnet-4-5"


def template_letter(profile: Profile, job: Job) -> str:
    links = [item for item in (profile.linkedin, profile.github, profile.portfolio) if item.strip()]
    link_line = f"Links: {', '.join(links)}" if links else ""
    lines = [
        "Hello,",
        "",
        f"I am applying for {job.title} at {job.company}. My resume is attached.",
    ]
    if link_line:
        lines.extend(["", link_line])
    lines.extend(["", "Thank you,", profile.full_name or "Applicant"])
    return "\n".join(lines).strip()


def _claude_letter(profile: Profile, job: Job, opener) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    facts = {
        "name": profile.full_name,
        "title": job.title,
        "company": job.company,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "portfolio": profile.portfolio,
        "city": profile.city,
        "country": profile.country,
    }
    prompt = (
        "Write a cover letter of at most 120 words. Use only the facts in the JSON. "
        "Do not invent employers, degrees, certifications, years, or skills. "
        "If a fact is empty, leave it out.\n"
        + json.dumps(facts)
    )
    body = json.dumps(
        {
            "model": os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    parts = payload.get("content") or []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text.strip():
        raise RuntimeError("Claude returned an empty letter")
    return text.strip()


def make_letter(profile: Profile, job: Job, mode: str, log, opener=None) -> str:
    fallback = template_letter(profile, job)
    if mode != "claude":
        return fallback
    try:
        return _claude_letter(profile, job, opener or urllib.request.urlopen)
    except Exception as exc:
        log(f"Cover letter used the template because Claude was unavailable: {exc}")
        return fallback
