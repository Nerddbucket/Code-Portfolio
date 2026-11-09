from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def norm(value: str) -> str:
    text = value or ""
    text = text.replace("'", "").replace("’", "")
    lowered = []
    for index, char in enumerate(text):
        if index and char.isupper() and text[index - 1].islower():
            lowered.append(" ")
        lowered.append(char.lower())
    cleaned = "".join(lowered)
    out = []
    for char in cleaned:
        out.append(char if char.isalnum() else " ")
    return " ".join("".join(out).split())


@dataclass(frozen=True)
class Option:
    value: str
    label: str


@dataclass(frozen=True)
class FormField:
    name: str
    kind: str
    options: tuple[Option, ...] = ()


@dataclass(frozen=True)
class FormQuestion:
    label: str
    required: bool
    fields: tuple[FormField, ...]
    group: str = "application"


@dataclass(frozen=True)
class Answer:
    name: str
    kind: str
    value: str
    label: str
    option_value: str = ""


@dataclass(frozen=True)
class Plan:
    ok: bool
    answers: tuple[Answer, ...]
    reason: str


@dataclass(frozen=True)
class ExtraAnswer:
    match: str
    answer: str


@dataclass(frozen=True)
class Profile:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    city: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    work_authorization: str = ""
    needs_sponsorship: str = ""
    salary_floor: str = ""
    earliest_start_date: str = ""
    veteran_status: str = "decline"
    gender: str = "decline"
    race: str = "decline"
    disability: str = "decline"
    privacy_consent: bool = False
    marketing_consent: bool = False
    certify_truth: bool = False
    resume_pdf: str = ""
    extra_answers: tuple[ExtraAnswer, ...] = ()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass(frozen=True)
class Search:
    titles: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    seniority: tuple[str, ...] = ()
    include_unspecified_seniority: bool = True
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    companies: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    submit: bool
    daily_cap: int
    max_age_days: int
    pause_seconds: float
    cover_letters: str
    profile: Profile
    search: Search
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Job:
    source: str
    company: str
    job_id: str
    title: str
    location: str
    workplace: str
    url: str
    apply_url: str
    description: str = ""
    published_at: datetime | None = None
    deadline: datetime | None = None
    salary_max: int | None = None
    salary_currency: str = ""
    questions: tuple[FormQuestion, ...] | None = None

    @property
    def key(self) -> str:
        return f"{self.source}:{self.company}:{self.job_id}"
