from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from .models import FormField, FormQuestion, Job, Option, Search

USER_AGENT = "personal-job-applier/1.0"
Opener = Callable[..., object]


def _parse_time(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        number = float(value)
        if number > 10_000_000_000:
            number = number / 1000.0
        return datetime.fromtimestamp(number, timezone.utc)
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            return None
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment
    return None


def workplace_of(type_hint: str, location: str) -> str:
    hint = (type_hint or "").lower().replace("_", "-")
    if hint in {"remote", "hybrid"}:
        return hint
    if hint in {"onsite", "on-site"}:
        return "onsite"
    blob = (location or "").lower()
    if "remote" in blob:
        return "remote"
    if "hybrid" in blob:
        return "hybrid"
    return "unknown"


def _field(raw: dict) -> FormField:
    kind = {
        "input_text": "text",
        "textarea": "textarea",
        "input_file": "file",
        "input_hidden": "hidden",
        "multi_value_single_select": "select",
        "multi_value_multi_select": "multiselect",
    }.get(str(raw.get("type") or ""), "text")
    options = tuple(
        Option(str(item.get("value")), str(item.get("label")))
        for item in (raw.get("values") or [])
        if isinstance(item, dict) and item.get("label") is not None
    )
    return FormField(str(raw.get("name") or ""), kind, options)


def _question(raw: dict, group: str) -> FormQuestion:
    fields = tuple(_field(item) for item in (raw.get("fields") or []) if isinstance(item, dict))
    return FormQuestion(str(raw.get("label") or ""), bool(raw.get("required")), fields, group)


def questions_from_greenhouse(payload: dict) -> tuple[FormQuestion, ...]:
    found: list[FormQuestion] = []
    for raw in payload.get("questions") or []:
        if isinstance(raw, dict):
            found.append(_question(raw, "application"))
    for raw in payload.get("location_questions") or []:
        if isinstance(raw, dict):
            found.append(_question(raw, "location"))
    for block in payload.get("compliance") or []:
        if not isinstance(block, dict):
            continue
        for raw in block.get("questions") or []:
            if isinstance(raw, dict):
                found.append(_question(raw, "compliance"))
    demo = payload.get("demographic_questions") or {}
    if isinstance(demo, dict):
        for raw in demo.get("questions") or []:
            if not isinstance(raw, dict):
                continue
            options = tuple(
                Option(str(item.get("id")), str(item.get("label")))
                for item in (raw.get("answer_options") or [])
                if isinstance(item, dict) and item.get("label") is not None
            )
            kind = "multiselect" if raw.get("type") == "multi_value_multi_select" else "select"
            found.append(
                FormQuestion(
                    str(raw.get("label") or ""),
                    bool(raw.get("required")),
                    (FormField(str(raw.get("id") or raw.get("label") or "demographic"), kind, options),),
                    "demographic",
                )
            )
    return tuple(found)


def _usd_max_from_ashby(job: dict) -> tuple[int | None, str]:
    compensation = job.get("compensation") or {}
    tiers = compensation.get("compensationTiers") or []
    best: int | None = None
    currency = ""
    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        for component in tier.get("components") or []:
            if not isinstance(component, dict):
                continue
            if component.get("compensationType") != "Salary":
                continue
            code = str(component.get("currencyCode") or "")
            maximum = component.get("maxValue")
            if code == "USD" and isinstance(maximum, (int, float)):
                best = int(maximum) if best is None else max(best, int(maximum))
                currency = "USD"
    return best, currency


def job_from_greenhouse(board: str, raw: dict) -> Job:
    location = raw.get("location") or {}
    location_name = location.get("name") if isinstance(location, dict) else str(location or "")
    return Job(
        source="greenhouse",
        company=board,
        job_id=str(raw.get("id")),
        title=str(raw.get("title") or ""),
        location=str(location_name or ""),
        workplace=workplace_of("", str(location_name or "")),
        url=str(raw.get("absolute_url") or ""),
        apply_url=str(raw.get("absolute_url") or ""),
        description="",
        published_at=_parse_time(raw.get("first_published") or raw.get("updated_at")),
        deadline=_parse_time(raw.get("application_deadline")),
    )


def job_from_lever(board: str, raw: dict) -> Job:
    categories = raw.get("categories") or {}
    location = str(categories.get("location") or "") if isinstance(categories, dict) else ""
    salary = raw.get("salaryRange") or {}
    maximum = None
    currency = ""
    if isinstance(salary, dict) and str(salary.get("currency") or "").upper() == "USD":
        if isinstance(salary.get("max"), (int, float)):
            maximum = int(salary["max"])
            currency = "USD"
    return Job(
        source="lever",
        company=board,
        job_id=str(raw.get("id") or ""),
        title=str(raw.get("text") or ""),
        location=location,
        workplace=workplace_of(str(raw.get("workplaceType") or ""), location),
        url=str(raw.get("hostedUrl") or ""),
        apply_url=str(raw.get("applyUrl") or raw.get("hostedUrl") or ""),
        description=str(raw.get("descriptionPlain") or ""),
        published_at=_parse_time(raw.get("createdAt")),
        salary_max=maximum,
        salary_currency=currency,
    )


def job_from_ashby(board: str, raw: dict) -> Job:
    location = str(raw.get("location") or "")
    maximum, currency = _usd_max_from_ashby(raw)
    return Job(
        source="ashby",
        company=board,
        job_id=str(raw.get("id") or ""),
        title=str(raw.get("title") or ""),
        location=location,
        workplace=workplace_of(str(raw.get("workplaceType") or ""), location),
        url=str(raw.get("jobUrl") or ""),
        apply_url=str(raw.get("applyUrl") or raw.get("jobUrl") or ""),
        description=str(raw.get("descriptionPlain") or ""),
        published_at=_parse_time(raw.get("publishedAt")),
        salary_max=maximum,
        salary_currency=currency,
    )


def greenhouse_jobs_url(slug: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


def greenhouse_questions_url(slug: str, job_id: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}?questions=true"


def lever_jobs_url(slug: str, skip: int) -> str:
    return f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=100&skip={skip}"


def ashby_jobs_url(slug: str) -> str:
    return f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"


class HttpSource:
    def __init__(self, opener: Opener | None = None, sleeper: Callable[[float], None] | None = None):
        self.opener = opener or urllib.request.urlopen
        self.sleeper = sleeper or time.sleep

    def _get_json(self, url: str) -> object:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with self.opener(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_jobs(self, search: Search, log: Callable[[str], None], stop: Callable[[], bool]) -> list[Job]:
        jobs: list[Job] = []
        companies = [(source, slug) for source, slugs in search.companies.items() for slug in slugs]
        if len(companies) > 100:
            companies = companies[:100]
            log("Only the first 100 company boards are read.")
        for source, slug in companies:
            if stop():
                break
            try:
                jobs.extend(self._list_one(source, slug))
                log(f"Read {source} board {slug}.")
            except urllib.error.HTTPError as exc:
                log(f"Could not read {source} board {slug}: HTTP {exc.code}.")
            except Exception as exc:
                log(f"Could not read {source} board {slug}: {exc}.")
            self.sleeper(0.4)
        return jobs

    def _list_one(self, source: str, slug: str) -> list[Job]:
        if source == "greenhouse":
            payload = self._get_json(greenhouse_jobs_url(slug))
            rows = payload.get("jobs") if isinstance(payload, dict) else []
            return [job_from_greenhouse(slug, row) for row in rows or [] if isinstance(row, dict)]
        if source == "lever":
            found: list[Job] = []
            for page in range(10):
                payload = self._get_json(lever_jobs_url(slug, page * 100))
                if not isinstance(payload, list) or not payload:
                    break
                found.extend(job_from_lever(slug, row) for row in payload if isinstance(row, dict))
                if len(payload) < 100:
                    break
            return found
        if source == "ashby":
            payload = self._get_json(ashby_jobs_url(slug))
            rows = payload.get("jobs") if isinstance(payload, dict) else []
            kept = []
            for row in rows or []:
                if isinstance(row, dict) and row.get("isListed", True):
                    kept.append(job_from_ashby(slug, row))
            return kept
        return []

    def load_questions(self, job: Job) -> tuple[tuple[FormQuestion, ...] | None, str]:
        if job.source != "greenhouse":
            return None, job.description
        payload = self._get_json(greenhouse_questions_url(job.company, job.job_id))
        if not isinstance(payload, dict):
            return None, job.description
        return questions_from_greenhouse(payload), str(payload.get("content") or job.description)
