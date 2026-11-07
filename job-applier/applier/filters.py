from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .models import Job, Search, norm

SENIORITY = (
    ("intern", re.compile(r"\bintern(ship)?\b", re.I)),
    ("manager", re.compile(r"\b(manager|director|vp|head of)\b", re.I)),
    ("staff", re.compile(r"\b(staff|principal|distinguished)\b", re.I)),
    ("senior", re.compile(r"\b(senior|sr\.?)\b", re.I)),
    ("entry", re.compile(r"\b(junior|jr\.?|entry[- ]level|new grad|associate)\b", re.I)),
    ("mid", re.compile(r"\b(mid[- ]level|intermediate)\b", re.I)),
)
NC = re.compile(
    r"\b(north carolina|raleigh|durham|charlotte|cary|chapel hill|winston-salem|greensboro|nc)\b",
    re.I,
)


def infer_seniority(title: str) -> str:
    for name, pattern in SENIORITY:
        if pattern.search(title or ""):
            return name
    return "unspecified"


def _plain(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", text).strip()


def location_matches(job: Job, phrases: tuple[str, ...]) -> bool:
    blob = job.location or ""
    remote = job.workplace == "remote" or re.search(r"\bremote\b", blob, re.I) is not None
    for phrase in phrases:
        wanted = phrase.strip()
        if not wanted:
            continue
        if wanted.lower() == "remote":
            if remote:
                return True
            continue
        if norm(wanted) in {"nc", "north carolina"}:
            if NC.search(blob):
                return True
            continue
        if re.search(rf"\b{re.escape(wanted)}\b", blob, re.I):
            return True
    return False


def reject_reason(job: Job, search: Search, now: datetime, salary_floor: str, max_age_days: int) -> str:
    titles = [title.strip() for title in search.titles if title.strip()]
    if not titles:
        return "no job titles are configured"
    if not any(title.lower() in (job.title or "").lower() for title in titles):
        return "title does not match"
    if not location_matches(job, search.locations):
        return "location does not match"
    band = infer_seniority(job.title)
    allowed = {norm(item) for item in search.seniority if item.strip()}
    if band == "unspecified":
        if not search.include_unspecified_seniority:
            return "seniority is not stated on the title"
    elif allowed and band not in allowed:
        return f"seniority is {band}"
    haystack = f"{job.title} {_plain(job.description)}".lower()
    for phrase in search.exclude_keywords:
        if phrase.strip() and phrase.strip().lower() in haystack:
            return f"excluded keyword: {phrase.strip()}"
    includes = [phrase.strip().lower() for phrase in search.include_keywords if phrase.strip()]
    if includes and not any(phrase in haystack for phrase in includes):
        return "none of the include keywords matched"
    if job.published_at is not None:
        moment = job.published_at
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        age = now - moment.astimezone(timezone.utc)
        if age > timedelta(days=max_age_days):
            return "listing is older than the age limit"
    if job.deadline is not None:
        deadline = job.deadline if job.deadline.tzinfo else job.deadline.replace(tzinfo=timezone.utc)
        if deadline < now:
            return "application deadline has passed"
    digits = re.sub(r"[^0-9]", "", salary_floor or "")
    if digits and job.salary_currency == "USD" and job.salary_max is not None:
        if job.salary_max < int(digits):
            return "posted pay is below the salary floor"
    return ""
