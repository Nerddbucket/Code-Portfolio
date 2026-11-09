from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from .models import ExtraAnswer, FormField, FormQuestion, Job, Option, Profile, Search

SUCCESS_ID = "se-remote"
COLOR_ID = "se-color"
CAPTCHA_ID = "se-captcha"


def minimal_pdf(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1", "replace")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n",
        b"4 0 obj<< /Length " + str(len(stream)).encode() + b" >>stream\n" + stream + b"\nendstream endobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(out)


def parse_multipart(content_type: str, body: bytes) -> dict[str, list[dict]]:
    header = f"MIME-Version: 1.0\r\nContent-Type: {content_type}\r\n\r\n".encode()
    message = BytesParser(policy=policy.default).parsebytes(header + body)
    fields: dict[str, list[dict]] = {}
    if not message.is_multipart():
        return fields
    for part in message.iter_parts():
        disposition = part.get("Content-Disposition", "")
        if "form-data" not in disposition:
            continue
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        data = part.get_payload(decode=True) or b""
        fields.setdefault(name, []).append(
            {
                "filename": filename,
                "data": data,
                "text": "" if filename else data.decode("utf-8", "replace"),
            }
        )
    return fields


def _text_question(label: str, name: str, required: bool = True, kind: str = "text") -> FormQuestion:
    return FormQuestion(label, required, (FormField(name, kind),))


def success_questions() -> tuple[FormQuestion, ...]:
    return (
        _text_question("First Name", "first_name"),
        _text_question("Last Name", "last_name"),
        _text_question("Email", "email"),
        _text_question("Phone", "phone", False),
        FormQuestion("Resume/CV", True, (FormField("resume", "file"), FormField("resume_text", "textarea"))),
        FormQuestion(
            "Are you authorized to work in the United States?",
            True,
            (FormField("work_auth", "select", (Option("Yes", "Yes"), Option("No", "No"))),),
        ),
        FormQuestion(
            "Will you now or in the future require sponsorship for a visa?",
            True,
            (
                FormField(
                    "sponsorship",
                    "select",
                    (
                        Option("No", "No"),
                        Option("Yes, Netherlands Highly Skilled Migrant Visa", "Yes, Netherlands Highly Skilled Migrant Visa"),
                    ),
                ),
            ),
        ),
        _text_question("Desired salary", "salary"),
        _text_question("What school did you attend?", "school"),
        FormQuestion("Cover Letter", False, (FormField("cover_letter", "textarea"),)),
        _text_question("Favorite snack", "snack", False),
        FormQuestion(
            "I agree to the processing of my application data",
            True,
            (FormField("privacy", "checkbox"),),
        ),
        FormQuestion(
            "Veteran Status",
            False,
            (
                FormField(
                    "veteran_status",
                    "select",
                    (
                        Option("I don't wish to answer", "I don't wish to answer"),
                        Option("I am not a protected veteran", "I am not a protected veteran"),
                    ),
                ),
            ),
        ),
    )


def practice_profile(resume_path: Path) -> Profile:
    return Profile(
        first_name="Practice",
        last_name="Applicant",
        email="practice@example.com",
        phone="919-555-0100",
        country="United States",
        city="Raleigh",
        linkedin="https://www.linkedin.com/in/practice",
        github="https://github.com/practice",
        portfolio="https://example.com/practice",
        work_authorization="yes",
        needs_sponsorship="no",
        salary_floor="80000",
        earliest_start_date="2026-12-01",
        veteran_status="decline",
        gender="decline",
        race="decline",
        disability="decline",
        privacy_consent=True,
        marketing_consent=False,
        certify_truth=True,
        resume_pdf=str(resume_path),
        extra_answers=(ExtraAnswer("school", "Example State University"), ExtraAnswer("aws", "")),
    )


def practice_search() -> Search:
    return Search(
        titles=("software engineer",),
        locations=("Remote", "North Carolina"),
        seniority=("entry", "mid"),
        include_unspecified_seniority=True,
        include_keywords=(),
        exclude_keywords=("unpaid",),
        companies={"practice": ("local",)},
    )


def _job(job_id: str, title: str, location: str, workplace: str, when: datetime, base: str, questions) -> Job:
    return Job(
        source="practice",
        company="Practice Co",
        job_id=job_id,
        title=title,
        location=location,
        workplace=workplace,
        url=f"{base}/apply/{job_id}",
        apply_url=f"{base}/apply/{job_id}",
        description="Build software.",
        published_at=when,
        questions=questions,
    )


def render_apply(job_id: str) -> str:
    if job_id == CAPTCHA_ID:
        return """<!doctype html><html><body>
        <h1>Verify you are human</h1>
        <div class="g-recaptcha" data-sitekey="practice"></div>
        </body></html>"""
    return """<!doctype html><html><body>
    <form method="post" enctype="multipart/form-data">
      <label for="first_name">First Name*</label><input id="first_name" name="first_name" required>
      <label for="last_name">Last Name*</label><input id="last_name" name="last_name" required>
      <label for="email">Email*</label><input id="email" name="email" required>
      <label for="phone">Phone</label><input id="phone" name="phone">
      <label for="resume">Resume/CV*</label><input id="resume" name="resume" type="file" required>
      <textarea name="resume_text"></textarea>
      <label for="work_auth">Are you authorized to work in the United States?*</label>
      <select id="work_auth" name="work_auth" required>
        <option value="">Select...</option>
        <option value="Yes">Yes</option>
        <option value="No">No</option>
      </select>
      <label for="sponsorship">Will you now or in the future require sponsorship for a visa?*</label>
      <select id="sponsorship" name="sponsorship" required>
        <option value="">Select...</option>
        <option value="No">No</option>
        <option value="Yes, Netherlands Highly Skilled Migrant Visa">Yes, Netherlands Highly Skilled Migrant Visa</option>
      </select>
      <label for="salary">Desired salary*</label><input id="salary" name="salary" required>
      <label for="school">What school did you attend?*</label><input id="school" name="school" required>
      <label for="cover_letter">Cover Letter</label><textarea id="cover_letter" name="cover_letter"></textarea>
      <label for="snack">Favorite snack</label><input id="snack" name="snack">
      <label for="privacy"><input id="privacy" name="privacy" type="checkbox" required> I agree to the processing of my application data</label>
      <div class="select">
        <label for="veteran_status">Veteran Status</label>
        <input id="veteran_status" name="veteran_status" class="select__input" role="combobox">
        <div class="select__single-value" id="veteran-chosen"></div>
        <div id="veteran_status-options">
          <div role="option">I don't wish to answer</div>
          <div role="option">I am not a protected veteran</div>
        </div>
      </div>
      <button type="submit">Submit application</button>
    </form>
    <script>
      const input = document.getElementById("veteran_status");
      const list = document.getElementById("veteran_status-options");
      list.hidden = true;
      input.addEventListener("focus", () => { list.hidden = false; });
      for (const opt of list.querySelectorAll("[role=option]")) {
        opt.addEventListener("click", () => {
          const value = opt.textContent.trim();
          input.value = value;
          input.dataset.selected = value;
          document.getElementById("veteran-chosen").textContent = value;
          list.hidden = true;
        });
      }
    </script>
    </body></html>"""


def filed_record(parts: dict[str, list[dict]]) -> dict:
    def text(name: str) -> str:
        values = parts.get(name) or []
        return values[0]["text"] if values else ""

    resume = (parts.get("resume") or [{}])[0]
    return {
        "first_name": text("first_name"),
        "last_name": text("last_name"),
        "email": text("email"),
        "phone": text("phone"),
        "salary": text("salary"),
        "school": text("school"),
        "work_authorization": text("work_auth"),
        "sponsorship": text("sponsorship"),
        "privacy": text("privacy"),
        "veteran": text("veteran_status"),
        "cover": text("cover_letter"),
        "resume_filename": resume.get("filename") or "",
        "resume_bytes": len(resume.get("data") or b""),
    }


class PracticeSite:
    def __init__(self, directory: Path):
        self.directory = directory
        self.inbox: list[dict] = []
        self.views: list[str] = []
        self.port = 0
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: Thread | None = None
        self.resume_path = directory / "practice-resume.pdf"

    def start(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.resume_path.write_bytes(minimal_pdf("Practice Applicant"))
        site = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                job_id = urlparse(self.path).path.rsplit("/", 1)[-1]
                if not self.path.startswith("/apply/"):
                    self.send_error(404)
                    return
                site.views.append(job_id)
                body = render_apply(job_id).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                parts = parse_multipart(self.headers.get("Content-Type", ""), body)
                record = filed_record(parts)
                site.inbox.append(record)
                payload = json.dumps(record)
                page = (
                    "<!doctype html><html><body><h1>Application received</h1>"
                    f"<script>window.__filed = {payload};</script></body></html>"
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)

            def log_message(self, fmt: str, *args) -> None:
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def jobs(self, now: datetime | None = None) -> list[Job]:
        moment = now or datetime.now(timezone.utc)
        base = self.base
        ready = success_questions()
        color = ready + (
            FormQuestion(
                "What is your favorite color?",
                True,
                (FormField("favorite_color", "select", (Option("Red", "Red"), Option("Blue", "Blue"))),),
            ),
        )
        return [
            _job(SUCCESS_ID, "Software Engineer", "Remote, United States", "remote", moment, base, ready),
            _job(COLOR_ID, "Software Engineer", "Remote, United States", "remote", moment, base, color),
            _job(CAPTCHA_ID, "Software Engineer", "Raleigh, North Carolina", "onsite", moment, base, ready),
            _job("se-staff", "Staff Software Engineer", "Remote, United States", "remote", moment, base, ready),
            _job("se-austin", "Software Engineer", "Austin, Texas", "onsite", moment - timedelta(days=1), base, ready),
            _job("se-old", "Software Engineer", "Remote, United States", "remote", moment - timedelta(days=40), base, ready),
        ]
