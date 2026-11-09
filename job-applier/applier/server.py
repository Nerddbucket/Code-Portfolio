from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from urllib.parse import urlparse

from .browser import BrowserSession
from .config import absolute_resume, config_problems, load_config
from .practice import PracticeSite, practice_profile, practice_search
from .runner import RunHooks, RunStats, execute
from .sources import HttpSource
from .store import Store, now_et

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("APPLIER_CONFIG", ROOT / "config.json"))
DATA_DIR = Path(os.environ.get("APPLIER_DATA", ROOT / "data"))
INDEX = Path(__file__).with_name("index.html")


class State:
    def __init__(self) -> None:
        self.lock = Lock()
        self.running = False
        self.mode = "idle"
        self.lines: list[str] = []
        self.stats = RunStats()
        self.inbox: list[dict] = []
        self.note = "Idle"
        self._stop = False

    def snapshot(self) -> dict:
        config, problems, filing = _describe_config()
        with self.lock:
            label = "Start"
            if config is not None and config.submit and not config_problems(config, filing=True):
                label = "Start filing"
            elif config is not None:
                label = "Start dry run"
            return {
                "running": self.running,
                "mode": self.mode,
                "note": self.note,
                "log": list(self.lines[-200:]),
                "stats": self.stats.__dict__,
                "inbox": self.inbox[-5:],
                "problems": problems,
                "start_label": label,
                "submit": bool(config and config.submit),
                "config_path": str(CONFIG_PATH),
            }

    def add(self, message: str) -> None:
        stamp = now_et().strftime("%Y-%m-%d %I:%M %p ET")
        with self.lock:
            self.lines.append(f"{stamp}  {message}")

    def set_stats(self, stats: RunStats) -> None:
        with self.lock:
            self.stats = stats


STATE = State()


def _describe_config():
    if not CONFIG_PATH.is_file():
        return None, ["Copy config.example.json to config.json and fill it in."], False
    try:
        config = load_config(CONFIG_PATH)
    except Exception as exc:
        return None, [f"Config could not be read: {exc}"], False
    filing = config.submit
    return config, config_problems(config, filing=filing), filing


def _playwright_ready() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


class Hooks(RunHooks):
    def log(self, message: str) -> None:
        STATE.add(message)

    def stats(self, stats: RunStats) -> None:
        STATE.set_stats(stats)

    def inbox(self, item: dict) -> None:
        safe = {key: value for key, value in item.items() if isinstance(value, (str, int, float))}
        with STATE.lock:
            STATE.inbox.append(safe)

    def stopped(self) -> bool:
        with STATE.lock:
            return STATE._stop


def _run_config() -> None:
    config, problems, filing = _describe_config()
    if config is None or problems:
        for problem in problems:
            STATE.add(problem)
        return
    for warning in config.warnings:
        STATE.add(warning)
    if filing and not _playwright_ready():
        STATE.add("Playwright is not installed. Run: python -m pip install -r requirements.txt && python -m playwright install chromium")
        return
    resume = absolute_resume(config)
    source = HttpSource()
    store = Store(DATA_DIR / "applications.db")
    STATE.add("Dry run. Nothing will be sent." if not filing else "Filing is on. Matching applications will be sent.")
    execute(
        source.list_jobs(config.search, STATE.add, Hooks().stopped),
        config.profile,
        config.search,
        submit=filing,
        allow_localhost=False,
        max_age_days=config.max_age_days,
        salary_floor=config.profile.salary_floor,
        daily_cap=config.daily_cap,
        pause_seconds=config.pause_seconds,
        cover_mode=config.cover_letters,
        resume_path=resume,
        store=store,
        hooks=Hooks(),
        browser_factory=lambda: BrowserSession(allow_localhost=False),
        load_questions=source.load_questions,
    )


def _run_practice() -> None:
    if not _playwright_ready():
        STATE.add("Playwright is not installed. Run: python -m pip install -r requirements.txt && python -m playwright install chromium")
        return
    site = PracticeSite(DATA_DIR / "practice")
    site.start()
    try:
        profile = practice_profile(site.resume_path)
        search = practice_search()
        STATE.add("Practice run. Applications stay on this computer and are not sent to employers.")
        practice_db = DATA_DIR / "practice.db"
        if practice_db.exists():
            practice_db.unlink()
        store = Store(practice_db)
        execute(
            site.jobs(),
            profile,
            search,
            submit=True,
            allow_localhost=True,
            max_age_days=14,
            salary_floor=profile.salary_floor,
            daily_cap=10,
            pause_seconds=0,
            cover_mode="template",
            resume_path=site.resume_path,
            store=store,
            hooks=Hooks(),
            browser_factory=lambda: BrowserSession(allow_localhost=True),
            inbox_for=lambda: site.inbox[-1] if site.inbox else None,
        )
    finally:
        site.stop()


def _start(mode: str) -> tuple[int, dict]:
    with STATE.lock:
        if STATE.running:
            return 409, {"error": "A run is already going."}
        STATE.running = True
        STATE._stop = False
        STATE.mode = mode
        STATE.lines = []
        STATE.stats = RunStats()
        STATE.inbox = []
        STATE.note = "Practice" if mode == "practice" else "Running"
    target = _run_practice if mode == "practice" else _run_config

    def wrap() -> None:
        try:
            target()
        except Exception as exc:
            STATE.add(f"Run failed: {exc}")
        finally:
            with STATE.lock:
                STATE.running = False
                STATE.note = "Idle"
                STATE.mode = "idle"

    Thread(target=wrap, daemon=True).start()
    return 202, {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(200, STATE.snapshot())
            return
        if path in {"/", "/index.html"}:
            body = INDEX.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "Expected JSON."})
            return
        if path == "/api/stop":
            with STATE.lock:
                STATE._stop = True
            STATE.add("Stop requested. The current form will not be submitted.")
            self._json(200, {"ok": True})
            return
        if path == "/api/start":
            mode = payload.get("mode") or "config"
            if mode not in {"config", "practice"}:
                self._json(400, {"error": "Unknown mode."})
                return
            if mode == "config":
                config, problems, _filing = _describe_config()
                if config is None:
                    STATE.add("Start did not run. " + " ".join(problems))
                    self._json(400, {"error": " ".join(problems)})
                    return
                filing_problems = config_problems(config, filing=config.submit)
                if filing_problems:
                    STATE.add("Start did not run. " + " ".join(filing_problems))
                    self._json(400, {"error": " ".join(filing_problems)})
                    return
            status, body = _start(mode)
            self._json(status, body)
            return
        self.send_error(404)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> None:
    port = int(os.environ.get("APPLIER_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Job applier at http://127.0.0.1:{port}", flush=True)
    server.serve_forever()
