from __future__ import annotations

import re
from datetime import datetime

from .models import Answer, FormField, FormQuestion, Option, Plan, Profile, norm

DECLINE_PHRASES = (
    "decline to",
    "prefer not",
    "do not wish",
    "dont wish",
    "choose not",
    "not to answer",
    "not disclose",
)
COUNTRY_ALIASES = {
    "us": "united states",
    "usa": "united states",
    "u s": "united states",
    "united states of america": "united states",
    "uk": "united kingdom",
    "u k": "united kingdom",
    "great britain": "united kingdom",
}
COUNTRY_DISPLAY = {
    "united states": "United States",
    "united kingdom": "United Kingdom",
}
AUTH_PHRASES = (
    "authorized to work",
    "authorised to work",
    "legally authorized",
    "legally authorised",
    "eligible to work",
    "right to work",
    "work authorization",
    "work authorisation",
)
YES_NO = {"yes", "y", "true", "no", "n", "false"}


def wants_decline(value: str) -> bool:
    text = norm(value)
    if text in {"decline", "prefer not", "prefer not to answer", "decline to answer"}:
        return True
    return any(phrase in text for phrase in DECLINE_PHRASES)


def yes_no(value: str) -> bool | None:
    text = norm(value)
    if text in {"yes", "y", "true"}:
        return True
    if text in {"no", "n", "false"}:
        return False
    return None


def canon_country(value: str) -> str:
    text = norm(value)
    text = re.sub(r"^the ", "", text)
    return COUNTRY_ALIASES.get(text, text)


def _visible(question: FormQuestion) -> FormField | None:
    for item in question.fields:
        if item.kind != "hidden":
            return item
    return None


def _option_named(options: tuple[Option, ...], *names: str) -> Option | None:
    wanted = set(names)
    hits = [option for option in options if norm(option.label) in wanted]
    if len(hits) == 1:
        return hits[0]
    return None


def _decline_option(options: tuple[Option, ...]) -> Option | None:
    hits = []
    for option in options:
        text = norm(option.label)
        if any(phrase in text for phrase in DECLINE_PHRASES):
            hits.append(option)
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        return hits[0]
    return None


def _exact_option(options: tuple[Option, ...], wanted: str) -> Option | None:
    text = norm(wanted)
    hits = [option for option in options if norm(option.label) == text]
    if len(hits) == 1:
        return hits[0]
    return None


def _choice(question: FormQuestion, label: str, option: Option | None) -> Answer | None:
    field = _visible(question)
    if field is None:
        return None
    if field.kind in {"select", "multiselect"}:
        if field.options and option is None:
            return None
        shown = option.label if option else label
        return Answer(
            field.name,
            "select",
            shown,
            question.label,
            option.value if option else "",
        )
    if field.kind in {"text", "textarea"}:
        return Answer(field.name, field.kind, label, question.label)
    return None


def _yes_no_answer(question: FormQuestion, answer: bool) -> Answer | None:
    field = _visible(question)
    if field is None:
        return None
    word = "Yes" if answer else "No"
    if field.kind in {"select", "multiselect"}:
        if field.options:
            option = _option_named(field.options, word.lower(), "y" if answer else "n", "true" if answer else "false")
            if option is None:
                return None
            return _choice(question, option.label, option)
        return _choice(question, word, None)
    if field.kind in {"text", "textarea"}:
        return Answer(field.name, field.kind, word, question.label)
    return None


def _eeo(question: FormQuestion, value: str) -> Answer | None:
    field = _visible(question)
    if field is None or field.kind not in {"select", "multiselect"}:
        return None
    if wants_decline(value):
        if not field.options:
            return _choice(question, "I don't wish to answer", None)
        return _choice(question, "", _decline_option(field.options))
    if not value.strip():
        return None
    if not field.options:
        return _choice(question, value.strip(), None)
    return _choice(question, value, _exact_option(field.options, value))


def _words(value: str) -> set[str]:
    return set(norm(value).split())


def _is_privacy(label: str) -> bool:
    text = norm(label)
    if any(word in text for word in ("newsletter", "marketing", "promotional")):
        return False
    return any(word in text for word in ("privacy", "personal data", "processing", "process my", "store my"))


def _is_marketing(label: str) -> bool:
    text = norm(label)
    return any(word in text for word in ("newsletter", "marketing email", "promotional", "future job alerts", "similar jobs"))


def _is_certify(label: str) -> bool:
    text = norm(label)
    return any(
        phrase in text
        for phrase in (
            "certify",
            "information provided is true",
            "information is accurate",
            "answers are true",
            "information is true",
        )
    )


def _salary_digits(value: str) -> str:
    return re.sub(r"[^0-9]", "", value or "")


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _extra(question: FormQuestion, profile: Profile) -> Answer | None:
    label = norm(question.label)
    field = _visible(question)
    if field is None:
        return None
    hits: list[tuple[int, str]] = []
    for extra in profile.extra_answers:
        phrase = norm(extra.match)
        if len(phrase) < 3 or not extra.answer.strip():
            continue
        if re.search(rf"\b{re.escape(phrase)}\b", label):
            hits.append((len(phrase), extra.answer.strip()))
    if not hits:
        return None
    answer = max(hits)[1]
    if field.kind in {"select", "multiselect"}:
        if field.options:
            option = _exact_option(field.options, answer)
            return _choice(question, answer, option)
        return _choice(question, answer, None)
    if field.kind in {"text", "textarea"}:
        return Answer(field.name, field.kind, answer, question.label)
    return None


def _country_option(question: FormQuestion, country: str) -> Option | None:
    field = _visible(question)
    if field is None:
        return None
    wanted = canon_country(country)
    if not wanted:
        return None
    hits = []
    for option in field.options:
        if canon_country(option.label) == wanted:
            hits.append(option)
    if len(hits) == 1:
        return hits[0]
    return None


def answer_question(question: FormQuestion, profile: Profile, cover_text: str) -> Answer | None:
    field = _visible(question)
    if field is None:
        return None
    label = norm(question.label)
    words = _words(question.label)
    names = {item.name for item in question.fields}

    if "resume" in words or "cv" in words or "resume" in names:
        if not profile.resume_pdf:
            return None
        file_field = next((item for item in question.fields if item.kind == "file"), None)
        if file_field is None:
            return None
        filename = profile.resume_pdf.rsplit("/", 1)[-1] or "resume.pdf"
        return Answer(file_field.name, "file", filename, question.label)

    if "cover letter" in label:
        if not cover_text.strip():
            return None
        text_field = next((item for item in question.fields if item.kind == "textarea"), None)
        if text_field is not None:
            return Answer(text_field.name, "textarea", cover_text.strip(), question.label)
        file_field = next((item for item in question.fields if item.kind == "file"), None)
        if file_field is not None:
            return Answer(file_field.name, "cover_file", "cover-letter.txt", question.label)
        if field.kind in {"text", "textarea"}:
            return Answer(field.name, field.kind, cover_text.strip(), question.label)
        return None

    if label in {"first name", "firstname", "given name", "legal first name"}:
        if not profile.first_name.strip():
            return None
        return Answer(field.name, field.kind if field.kind in {"text", "textarea"} else "text", profile.first_name.strip(), question.label)

    if label in {"last name", "lastname", "family name", "surname", "legal last name"}:
        if not profile.last_name.strip():
            return None
        return Answer(field.name, field.kind if field.kind in {"text", "textarea"} else "text", profile.last_name.strip(), question.label)

    if label in {"name", "full name", "legal name", "your name"}:
        if not profile.first_name.strip() or not profile.last_name.strip():
            return None
        return Answer(field.name, field.kind if field.kind in {"text", "textarea"} else "text", profile.full_name, question.label)

    if "email" in words or label in {"e mail", "email address"}:
        if not profile.email.strip():
            return None
        return Answer(field.name, "text", profile.email.strip(), question.label)

    if words & {"phone", "mobile", "telephone", "tel"}:
        if not profile.phone.strip():
            return None
        return Answer(field.name, "text", profile.phone.strip(), question.label)

    compact = label.replace(" ", "")
    if "linkedin" in compact or "linked in" in label:
        if not profile.linkedin.strip():
            return None
        return Answer(field.name, "text", profile.linkedin.strip(), question.label)
    if "github" in compact or "git hub" in label:
        if not profile.github.strip():
            return None
        return Answer(field.name, "text", profile.github.strip(), question.label)
    if any(phrase in label for phrase in ("portfolio", "personal site", "personal website", "your website")) or label in {"website", "web site", "url"}:
        if not profile.portfolio.strip():
            return None
        return Answer(field.name, "text", profile.portfolio.strip(), question.label)

    if "sponsor" in label or "visa" in label:
        answer = yes_no(profile.needs_sponsorship)
        if answer is None:
            return None
        return _yes_no_answer(question, answer)

    if any(phrase in label for phrase in AUTH_PHRASES):
        answer = yes_no(profile.work_authorization)
        if answer is None:
            return None
        return _yes_no_answer(question, answer)

    if any(phrase in label for phrase in ("salary expectation", "desired salary", "expected salary", "compensation expectation", "pay expectation", "salary requirement")):
        if any(phrase in label for phrase in ("current", "history", "previous")):
            return None
        digits = _salary_digits(profile.salary_floor)
        if not digits or field.kind in {"select", "multiselect"}:
            return None
        if field.kind in {"text", "textarea"}:
            return Answer(field.name, field.kind, digits, question.label)
        return None

    if any(phrase in label for phrase in ("earliest start", "start date", "when can you start", "date available", "available to start")):
        if any(phrase in label for phrase in ("graduation", "birth", "end date")):
            return None
        if not _valid_date(profile.earliest_start_date):
            return None
        if field.kind in {"text", "textarea"}:
            return Answer(field.name, field.kind, profile.earliest_start_date, question.label)
        return None

    if "country" in words and field.kind in {"select", "multiselect"}:
        if field.options:
            option = _country_option(question, profile.country)
            return _choice(question, profile.country, option)
        display = COUNTRY_DISPLAY.get(canon_country(profile.country), profile.country.strip())
        if not display:
            return None
        return _choice(question, display, None)

    reside = re.search(r"\breside in\b(.+)$", label)
    if reside and field.kind in {"select", "multiselect"} and _option_named(field.options or (), "yes") and _option_named(field.options or (), "no"):
        country = canon_country(profile.country)
        if not country:
            return None
        places = []
        for part in reside.group(1).split(" or "):
            places.append(re.sub(r"^the ", "", part).strip(" ?"))
        living_there = any(canon_country(place) == country for place in places)
        return _yes_no_answer(question, living_there)

    if "veteran" in words:
        return _eeo(question, profile.veteran_status)
    if "gender" in words or "sex" in words:
        return _eeo(question, profile.gender)
    if "race" in words or "ethnicity" in words or "racial" in words:
        return _eeo(question, profile.race)
    if "disability" in words or "disabled" in words:
        return _eeo(question, profile.disability)

    if field.kind == "checkbox":
        if _is_marketing(question.label):
            if not profile.marketing_consent:
                return None
            return Answer(field.name, "checkbox", "yes", question.label)
        if _is_privacy(question.label):
            if not profile.privacy_consent:
                return None
            return Answer(field.name, "checkbox", "yes", question.label)
        if _is_certify(question.label):
            if not profile.certify_truth:
                return None
            return Answer(field.name, "checkbox", "yes", question.label)
        return None

    if label in {"location", "city", "your location", "current location", "city of residence"}:
        if not profile.city.strip():
            return None
        if field.kind in {"select", "multiselect"}:
            if field.options:
                return _choice(question, profile.city, _exact_option(field.options, profile.city))
            return _choice(question, profile.city.strip(), None)
        if field.kind in {"text", "textarea"}:
            return Answer(field.name, field.kind, profile.city.strip(), question.label)
        return None

    return _extra(question, profile)


def plan_application(questions: tuple[FormQuestion, ...] | list[FormQuestion], profile: Profile, cover_text: str) -> Plan:
    answers: list[Answer] = []
    for question in questions:
        if question.fields and all(item.kind == "hidden" for item in question.fields):
            continue
        if not question.fields:
            if question.required:
                return Plan(False, (), f"Skipped: required question is not in the config: {question.label}")
            continue
        answer = answer_question(question, profile, cover_text)
        if answer is None:
            if question.required:
                return Plan(False, (), f"Skipped: required question is not in the config: {question.label}")
            continue
        answers.append(answer)
    return Plan(True, tuple(answers), "")
