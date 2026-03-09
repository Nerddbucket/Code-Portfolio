import argparse
import getpass
import imaplib
import os
import re
import smtplib
import sqlite3
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser

# ── CONFIG ────────────────────────────────────────────────
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL = "ndorleus@gmail.com"
APP_PASS = os.environ.get("EMAIL_APP_PASS", "")
DISPLAY_NAME = "Bandz Express"
DB_PATH = "/Volumes/Code bag/Database Bag/email_traffic.db"
ENABLE_IMAP = True
UID_PATTERN = re.compile(rb"UID (\d+)")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS email_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT NOT NULL,
            message_id TEXT,
            subject TEXT,
            from_addr TEXT,
            to_addr TEXT,
            date_header TEXT,
            snippet TEXT,
            imap_uid INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(email_traffic)")}
    if "imap_uid" not in columns:
        conn.execute("ALTER TABLE email_traffic ADD COLUMN imap_uid INTEGER")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_email_traffic_direction_uid
        ON email_traffic(direction, imap_uid)
        """
    )
    conn.commit()
    return conn


def extract_text_snippet(message, limit=200):
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                text = part.get_content()
                return text[:limit]
        return ""
    return message.get_content()[:limit]


def log_email(conn, direction, message, imap_uid=None, auto_commit=True):
    conn.execute(
        """
        INSERT OR IGNORE INTO email_traffic (
            direction, message_id, subject, from_addr, to_addr, date_header, snippet, imap_uid, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            direction,
            message.get("Message-ID"),
            message.get("Subject"),
            message.get("From"),
            message.get("To"),
            message.get("Date"),
            extract_text_snippet(message),
            imap_uid,
            datetime.utcnow().isoformat(timespec="seconds") + "Z",
        ),
    )
    if auto_commit:
        conn.commit()


def get_last_seen_uid(conn):
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = 'last_seen_imap_uid'"
    ).fetchone()
    if not row:
        return None
    try:
        return int(row[0])
    except ValueError:
        return None


def set_last_seen_uid(conn, uid):
    conn.execute(
        """
        INSERT INTO app_state(key, value)
        VALUES('last_seen_imap_uid', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (str(uid),),
    )


def extract_uid(fetch_row):
    if not fetch_row or not fetch_row[0]:
        return None
    meta = fetch_row[0][0]
    if not isinstance(meta, bytes):
        return None
    match = UID_PATTERN.search(meta)
    if not match:
        return None
    return int(match.group(1))

def read_recent_emails(conn, limit=5):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, APP_PASS)
    status, mailbox_data = mail.select("inbox")
    if status != "OK":
        mail.logout()
        return

    try:
        message_count = int(mailbox_data[0])
    except (TypeError, ValueError, IndexError):
        message_count = 0

    last_seen_uid = get_last_seen_uid(conn)
    fetch_mode = "sequence"
    ids = []

    if last_seen_uid is None:
        if message_count > 0:
            start = max(1, message_count - limit + 1)
            ids = [str(i).encode() for i in range(start, message_count + 1)]
    else:
        status, data = mail.uid("search", None, f"UID {last_seen_uid + 1}:*")
        if status == "OK" and data and data[0]:
            ids = data[0].split()
            fetch_mode = "uid"

    if not ids:
        mail.close()
        mail.logout()
        return

    max_seen_uid = last_seen_uid or 0
    conn.execute("BEGIN")
    try:
        for current_id in ids:
            if fetch_mode == "uid":
                status, msg_data = mail.uid("fetch", current_id, "(UID RFC822)")
            else:
                status, msg_data = mail.fetch(current_id, "(UID RFC822)")

            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0][1]
            message = BytesParser(policy=policy.default).parsebytes(raw)
            message_uid = extract_uid(msg_data)
            if message_uid:
                max_seen_uid = max(max_seen_uid, message_uid)

            log_email(
                conn,
                "inbound",
                message,
                imap_uid=message_uid,
                auto_commit=False,
            )
            print(f"Message {current_id.decode()}:")
            print(raw[:200].decode(errors="ignore"))
            print("-" * 60)

        if max_seen_uid > (last_seen_uid or 0):
            set_last_seen_uid(conn, max_seen_uid)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        mail.close()
        mail.logout()


def send_email(conn, to_address, subject, body):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{DISPLAY_NAME} <{EMAIL}>"
    message["To"] = to_address
    message.set_content(body)

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(EMAIL, APP_PASS)
        server.send_message(message)

    log_email(conn, "outbound", message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email client with DB logging.")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send an email after collecting inbound mail.",
    )
    args = parser.parse_args()

    conn = init_db()
    if not APP_PASS:
        APP_PASS = getpass.getpass("Enter Gmail App Password: ")
    if ENABLE_IMAP:
        try:
            read_recent_emails(conn, limit=5)
        except imaplib.IMAP4.error as exc:
            print(f"IMAP login failed, skipping inbound: {exc}")
    if args.send:
        send_email(
            conn,
            "nerddbucket@outlook.com",
            "Watch for the update",
            "My fault twin",
        )
    conn.close()
    if args.send:
        print("Email sent.")
