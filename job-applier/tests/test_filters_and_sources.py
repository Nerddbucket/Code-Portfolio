import json
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from io import BytesIO

from applier.filters import infer_seniority, reject_reason
from applier.models import Job, Search
from applier.sources import HttpSource, job_from_ashby, job_from_greenhouse, job_from_lever, questions_from_greenhouse


NOW = datetime(2026, 11, 7, 16, 0, tzinfo=timezone.utc)


def search(**overrides) -> Search:
    data = dict(
        titles=("software engineer",),
        locations=("Remote", "North Carolina"),
        seniority=("entry", "mid"),
        include_unspecified_seniority=True,
        include_keywords=(),
        exclude_keywords=("unpaid",),
        companies={},
    )
    data.update(overrides)
    return Search(**data)


def job(**overrides) -> Job:
    data = dict(
        source="greenhouse",
        company="acme",
        job_id="1",
        title="Software Engineer",
        location="Remote, United States",
        workplace="remote",
        url="https://job-boards.greenhouse.io/acme/jobs/1",
        apply_url="https://job-boards.greenhouse.io/acme/jobs/1",
        description="Build APIs.",
        published_at=NOW - timedelta(days=2),
    )
    data.update(overrides)
    return Job(**data)


class FilterTests(unittest.TestCase):
    def test_remote_and_north_carolina_match(self):
        self.assertEqual(reject_reason(job(), search(), NOW, "", 14), "")
        raleigh = job(location="Raleigh, North Carolina", workplace="onsite")
        self.assertEqual(reject_reason(raleigh, search(), NOW, "", 14), "")

    def test_staff_austin_old_unpaid_and_low_pay_are_rejected(self):
        self.assertIn("seniority", reject_reason(job(title="Staff Software Engineer"), search(), NOW, "", 14))
        self.assertEqual(infer_seniority("Senior Engineering Manager"), "manager")
        self.assertIn("location", reject_reason(job(location="Austin, Texas", workplace="onsite"), search(), NOW, "", 14))
        self.assertIn("older", reject_reason(job(published_at=NOW - timedelta(days=40)), search(), NOW, "", 14))
        self.assertIn("unpaid", reject_reason(job(description="This is an unpaid role"), search(), NOW, "", 14))
        low = job(salary_max=60000, salary_currency="USD")
        self.assertIn("salary floor", reject_reason(low, search(), NOW, "80000", 14))
        euro = job(salary_max=1000, salary_currency="EUR")
        self.assertEqual(reject_reason(euro, search(), NOW, "80000", 14), "")

    def test_deadline_passed(self):
        expired = job(deadline=NOW - timedelta(days=1))
        self.assertIn("deadline", reject_reason(expired, search(), NOW, "", 14))


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return json.dumps(self.payload).encode()


class SourceTests(unittest.TestCase):
    def test_parsers_keep_public_fields(self):
        greenhouse = job_from_greenhouse(
            "gitlab",
            {
                "id": 5,
                "title": "Backend Engineer",
                "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/5",
                "location": {"name": "Remote, United States"},
                "first_published": "2026-11-06T15:25:07-05:00",
            },
        )
        self.assertEqual(greenhouse.workplace, "remote")
        self.assertEqual(greenhouse.apply_url, "https://job-boards.greenhouse.io/gitlab/jobs/5")
        lever = job_from_lever(
            "spotify",
            {
                "id": "abc",
                "text": "Software Engineer",
                "categories": {"location": "New York, NY"},
                "workplaceType": "hybrid",
                "hostedUrl": "https://jobs.lever.co/spotify/abc",
                "applyUrl": "https://jobs.lever.co/spotify/abc/apply",
                "createdAt": 1792767640768,
                "salaryRange": {"min": 100000, "max": 150000, "currency": "USD"},
                "descriptionPlain": "Build things",
            },
        )
        self.assertEqual(lever.salary_max, 150000)
        self.assertEqual(lever.workplace, "hybrid")
        self.assertIsNotNone(lever.published_at)
        ashby = job_from_ashby(
            "ashby",
            {
                "id": "job-1",
                "title": "Engineer",
                "location": "Remote",
                "workplaceType": "Remote",
                "applyUrl": "https://jobs.ashbyhq.com/ashby/job-1/application",
                "isListed": True,
                "publishedAt": "2026-11-01T00:00:00.000+00:00",
                "compensation": {
                    "compensationTiers": [
                        {"components": [{"compensationType": "Salary", "currencyCode": "EUR", "maxValue": 250000}]}
                    ]
                },
            },
        )
        self.assertIsNone(ashby.salary_max)
        questions = questions_from_greenhouse(
            {
                "questions": [
                    {"required": True, "label": "First Name", "fields": [{"name": "first_name", "type": "input_text"}]}
                ],
                "compliance": [
                    {
                        "type": "eeoc",
                        "questions": [
                            {
                                "required": False,
                                "label": "VeteranStatus",
                                "fields": [
                                    {
                                        "name": "veteran_status",
                                        "type": "multi_value_single_select",
                                        "values": [{"label": "I don't wish to answer", "value": "3"}],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        self.assertEqual(questions[1].label, "VeteranStatus")
        self.assertEqual(questions[1].fields[0].options[0].label, "I don't wish to answer")

    def test_http_source_uses_only_fixed_hosts_and_continues_after_404(self):
        seen = []

        def opener(request, timeout=30):
            seen.append(request.full_url)
            if "missing" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 404, "missing", hdrs=None, fp=BytesIO(b""))
            if "greenhouse" in request.full_url:
                return Response({"jobs": [{"id": 1, "title": "Software Engineer", "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/1", "location": {"name": "Remote"}}]})
            return Response({"jobs": []})

        logs = []
        source = HttpSource(opener=opener, sleeper=lambda _seconds: None)
        search_for = search(companies={"greenhouse": ("acme", "missing"), "ashby": ("ashby",)})
        jobs = source.list_jobs(search_for, logs.append, lambda: False)
        self.assertEqual(len(jobs), 1)
        self.assertTrue(any("HTTP 404" in line for line in logs))
        self.assertTrue(all(url.startswith("https://boards-api.greenhouse.io/") or url.startswith("https://api.ashbyhq.com/") for url in seen))
        self.assertNotIn("..", "".join(seen))


if __name__ == "__main__":
    unittest.main()
