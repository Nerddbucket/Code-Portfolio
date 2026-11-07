from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .browser import FileResult, allowed_apply_url
from .cover import make_letter
from .filters import reject_reason
from .models import Job, Profile, Search
from .questions import plan_application


@dataclass
class RunStats:
    seen: int = 0
    matched: int = 0
    skipped: int = 0
    dry_run: int = 0
    filed: int = 0
    errors: int = 0


class RunHooks:
    def log(self, message: str) -> None:
        return

    def stats(self, stats: RunStats) -> None:
        return

    def inbox(self, item: dict) -> None:
        return

    def stopped(self) -> bool:
        return False


def _publish_key(job: Job) -> datetime:
    moment = job.published_at
    if moment is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def execute(
    jobs: list[Job],
    profile: Profile,
    search: Search,
    *,
    submit: bool,
    allow_localhost: bool,
    max_age_days: int,
    salary_floor: str,
    daily_cap: int,
    pause_seconds: float,
    cover_mode: str,
    resume_path: Path | None,
    store,
    hooks: RunHooks,
    browser_factory,
    load_questions=None,
    inspect_limit: int = 40,
    now: datetime | None = None,
    inbox_for=None,
) -> RunStats:
    moment = now or datetime.now(timezone.utc)
    stats = RunStats(seen=len(jobs))
    matched: list[Job] = []
    grouped: dict[tuple[str, str], list[Job]] = {}
    for job in jobs:
        grouped.setdefault((job.source, job.company), []).append(job)
    for (source, company), rows in grouped.items():
        kept = [
            job
            for job in rows
            if not reject_reason(job, search, moment, salary_floor, max_age_days)
        ]
        hooks.log(f"{source} {company}: {len(rows)} listed, {len(kept)} match the search.")
        matched.extend(kept)
    matched.sort(key=_publish_key, reverse=True)
    stats.matched = len(matched)
    hooks.stats(stats)
    browser = None
    filed_now = 0
    inspected = 0
    wait = 0 if allow_localhost else max(2.0, pause_seconds)
    try:
        for job in matched:
            if hooks.stopped():
                hooks.log("Stopped.")
                break
            if store.filed_today() >= daily_cap or filed_now >= daily_cap:
                hooks.log(f"Daily cap of {daily_cap} is reached. Nothing else will be sent.")
                break
            if inspected >= inspect_limit:
                hooks.log(f"Stopped after checking {inspect_limit} matching jobs.")
                break
            inspected += 1
            if store.already_filed(job.key):
                stats.skipped += 1
                hooks.log(f"Skipped {job.title} at {job.company}: already filed.")
                hooks.stats(stats)
                continue
            questions = job.questions
            description = job.description
            if questions is None and load_questions is not None:
                questions, description = load_questions(job)
                if description and description != job.description:
                    job = replace(job, description=description)
                    reason = reject_reason(job, search, moment, salary_floor, max_age_days)
                    if reason:
                        stats.skipped += 1
                        hooks.log(f"Skipped {job.title} at {job.company}: {reason}.")
                        store.record(job.key, job.title, job.company, job.url, "skipped", reason)
                        hooks.stats(stats)
                        continue
            cover = make_letter(profile, job, cover_mode, hooks.log)
            if questions is None:
                if not submit:
                    stats.dry_run += 1
                    hooks.log(
                        f"Dry run {job.title} at {job.company}: the feed has no form questions, so the page was not opened."
                    )
                    store.record(job.key, job.title, job.company, job.url, "dry_run", "form not in feed")
                    hooks.stats(stats)
                    continue
                plan_answers = ()
                known = None
            else:
                plan = plan_application(questions, profile, cover)
                if not plan.ok:
                    stats.skipped += 1
                    hooks.log(f"{job.title} at {job.company}: {plan.reason}")
                    store.record(job.key, job.title, job.company, job.url, "skipped", plan.reason)
                    hooks.stats(stats)
                    continue
                if not submit:
                    stats.dry_run += 1
                    hooks.log(f"Would file {job.title} at {job.company}. Dry run did not send it.")
                    for answer in plan.answers:
                        shown = answer.value.replace("\n", " ")
                        if len(shown) > 90:
                            shown = shown[:90] + "..."
                        hooks.log(f"  {answer.label}: {shown}")
                    store.record(job.key, job.title, job.company, job.url, "dry_run", "ready")
                    hooks.stats(stats)
                    continue
                plan_answers = plan.answers
                known = questions
            if any(answer.kind == "file" for answer in plan_answers) and (resume_path is None or not resume_path.is_file()):
                stats.skipped += 1
                hooks.log(f"Skipped {job.title}: the resume PDF is missing.")
                hooks.stats(stats)
                continue
            if not allowed_apply_url(job.apply_url, allow_localhost=allow_localhost):
                stats.skipped += 1
                hooks.log(f"Skipped {job.title}: the application link is not an allowed board.")
                store.record(job.key, job.title, job.company, job.url, "skipped", "url not allowed")
                hooks.stats(stats)
                continue
            if hooks.stopped():
                hooks.log("Stopped before sending.")
                break
            if browser is None:
                try:
                    browser = browser_factory()
                    browser.__enter__()
                except Exception as exc:
                    stats.errors += 1
                    hooks.log(
                        "Chromium could not start. Run: python -m pip install -r requirements.txt "
                        f"&& python -m playwright install chromium. ({exc.__class__.__name__}: {exc})"
                    )
                    hooks.stats(stats)
                    break
            cover_path = None
            result: FileResult = browser.file_application(
                url=job.apply_url,
                plan_answers=plan_answers,
                resume_path=resume_path,
                cover_path=cover_path,
                stop=hooks.stopped,
                profile=profile,
                cover_text=cover,
                known_questions=known,
            )
            if result.filed:
                filed_now += 1
                stats.filed += 1
                store.record(job.key, job.title, job.company, job.url, "filed", "filed")
                hooks.log(f"Filed {job.title} at {job.company}.")
                item = {"title": job.title, "company": job.company, "url": job.url}
                if inbox_for is not None:
                    extra = inbox_for()
                    if isinstance(extra, dict):
                        item.update(extra)
                elif result.captured:
                    item.update(result.captured)
                hooks.inbox(item)
                if wait and filed_now < daily_cap:
                    import time

                    time.sleep(wait)
            else:
                if "could not be sent" in result.reason:
                    stats.errors += 1
                stats.skipped += 1
                hooks.log(f"{job.title} at {job.company}: {result.reason}")
                store.record(job.key, job.title, job.company, job.url, "skipped", result.reason)
            hooks.stats(stats)
    finally:
        if browser is not None:
            browser.__exit__(None, None, None)
    if stats.filed:
        hooks.log(f"Done. Filed {stats.filed}. Skipped {stats.skipped}.")
    else:
        hooks.log(f"Done. Filed 0. Skipped {stats.skipped}. Dry run {stats.dry_run}.")
    hooks.stats(stats)
    return stats
