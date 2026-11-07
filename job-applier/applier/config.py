from __future__ import annotations

import json
import re
from pathlib import Path

from .models import AppConfig, ExtraAnswer, Profile, Search, norm

MAX_DAILY_CAP = 50
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BAD_EMAIL_HOSTS = ("example.com", "example.org", "example.net", "localhost")
BAD_NAMES = {
    "",
    "todo",
    "changeme",
    "your name",
    "firstname",
    "lastname",
    "first",
    "last",
    "name",
    "example",
}


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return default


def _phrases(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _slugs(value: object, warnings: list[str], source: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    kept: list[str] = []
    for item in value:
        slug = _text(item)
        if not slug:
            continue
        if not SLUG.match(slug):
            warnings.append(f"Ignored {source} board {slug!r}. Use the board name only, not a URL.")
            continue
        if slug not in kept:
            kept.append(slug)
    return tuple(kept)


def load_config(path: Path) -> AppConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config must be a JSON object")
    warnings: list[str] = []
    profile_raw = raw.get("profile") if isinstance(raw.get("profile"), dict) else {}
    eeo = profile_raw.get("eeo") if isinstance(profile_raw.get("eeo"), dict) else {}
    extras = []
    for item in profile_raw.get("extra_answers") or []:
        if not isinstance(item, dict):
            continue
        extras.append(ExtraAnswer(_text(item.get("match")), _text(item.get("answer"))))
    profile = Profile(
        first_name=_text(profile_raw.get("first_name")),
        last_name=_text(profile_raw.get("last_name")),
        email=_text(profile_raw.get("email")),
        phone=_text(profile_raw.get("phone")),
        country=_text(profile_raw.get("country")),
        city=_text(profile_raw.get("city")),
        linkedin=_text(profile_raw.get("linkedin")),
        github=_text(profile_raw.get("github")),
        portfolio=_text(profile_raw.get("portfolio")),
        work_authorization=_text(profile_raw.get("work_authorization")).lower(),
        needs_sponsorship=_text(profile_raw.get("needs_sponsorship")).lower(),
        salary_floor=_text(profile_raw.get("salary_floor")),
        earliest_start_date=_text(profile_raw.get("earliest_start_date")),
        veteran_status=_text(eeo.get("veteran_status") or profile_raw.get("veteran_status") or "decline"),
        gender=_text(eeo.get("gender") or "decline"),
        race=_text(eeo.get("race") or "decline"),
        disability=_text(eeo.get("disability") or "decline"),
        privacy_consent=_bool(profile_raw.get("privacy_consent"), False),
        marketing_consent=_bool(profile_raw.get("marketing_consent"), False),
        certify_truth=_bool(profile_raw.get("certify_truth"), False),
        resume_pdf=_text(profile_raw.get("resume_pdf")),
        extra_answers=tuple(extras),
    )
    search_raw = raw.get("search") if isinstance(raw.get("search"), dict) else {}
    companies_raw = search_raw.get("companies") if isinstance(search_raw.get("companies"), dict) else {}
    companies = {
        "greenhouse": _slugs(companies_raw.get("greenhouse"), warnings, "greenhouse"),
        "lever": _slugs(companies_raw.get("lever"), warnings, "lever"),
        "ashby": _slugs(companies_raw.get("ashby"), warnings, "ashby"),
    }
    try:
        cap = int(raw.get("daily_cap", 10))
    except (TypeError, ValueError):
        cap = 10
        warnings.append("daily_cap was not a number, so 10 is used.")
    if cap < 1:
        cap = 1
        warnings.append("daily_cap was raised to 1.")
    if cap > MAX_DAILY_CAP:
        warnings.append(f"daily_cap was limited to {MAX_DAILY_CAP} so one click cannot send more than that.")
        cap = MAX_DAILY_CAP
    try:
        age = int(raw.get("max_age_days", 14))
    except (TypeError, ValueError):
        age = 14
    age = min(180, max(1, age))
    try:
        pause = float(raw.get("pause_seconds", 5))
    except (TypeError, ValueError):
        pause = 5
    pause = min(60.0, max(2.0, pause))
    cover = _text(raw.get("cover_letters") or "template").lower()
    if cover not in {"template", "claude"}:
        warnings.append("cover_letters must be template or claude. Template will be used.")
        cover = "template"
    search = Search(
        titles=_phrases(search_raw.get("titles")),
        locations=_phrases(search_raw.get("locations")),
        seniority=_phrases(search_raw.get("seniority")),
        include_unspecified_seniority=_bool(search_raw.get("include_unspecified_seniority"), True),
        include_keywords=_phrases(search_raw.get("include_keywords")),
        exclude_keywords=_phrases(search_raw.get("exclude_keywords")),
        companies=companies,
    )
    return AppConfig(
        submit=_bool(raw.get("submit"), False),
        daily_cap=cap,
        max_age_days=age,
        pause_seconds=pause,
        cover_letters=cover,
        profile=profile,
        search=search,
        warnings=tuple(warnings),
    )


def _bad_name(value: str) -> bool:
    text = norm(value)
    return text in BAD_NAMES or text.startswith("your ")


def config_problems(config: AppConfig, *, filing: bool) -> list[str]:
    problems: list[str] = []
    profile = config.profile
    if not config.search.titles:
        problems.append("Add at least one job title.")
    if not config.search.locations:
        problems.append("Add at least one location, such as Remote or North Carolina.")
    companies = [slug for names in config.search.companies.values() for slug in names]
    if not companies:
        problems.append("Add at least one Greenhouse, Lever, or Ashby board name.")
    if len(companies) > 100:
        problems.append("Use 100 company boards or fewer per run.")
    if not filing:
        return problems
    if _bad_name(profile.first_name) or _bad_name(profile.last_name):
        problems.append("Fill in your first and last name.")
    if not EMAIL.match(profile.email) or profile.email.lower().split("@")[-1] in BAD_EMAIL_HOSTS:
        problems.append("Fill in your email address.")
    if not profile.phone.strip():
        problems.append("Fill in your phone number.")
    if not profile.country.strip():
        problems.append("Fill in your country.")
    if profile.work_authorization not in {"yes", "no"}:
        problems.append("Set work_authorization to yes or no.")
    if profile.needs_sponsorship not in {"yes", "no"}:
        problems.append("Set needs_sponsorship to yes or no.")
    resume = Path(profile.resume_pdf)
    if profile.resume_pdf and not resume.is_absolute():
        resume = Path.cwd() / resume
    if not profile.resume_pdf or resume.suffix.lower() != ".pdf" or not resume.is_file() or resume.stat().st_size <= 0:
        problems.append("Set resume_pdf to a PDF on this computer.")
    elif resume.stat().st_size > 10 * 1024 * 1024:
        problems.append("Resume PDF must be 10 MB or smaller.")
    return problems


def absolute_resume(config: AppConfig) -> Path | None:
    if not config.profile.resume_pdf:
        return None
    path = Path(config.profile.resume_pdf)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path
