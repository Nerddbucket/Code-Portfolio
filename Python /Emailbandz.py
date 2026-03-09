import argparse
import getpass
import imaplib
import os
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
            created_at TEXT NOT NULL
        )
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


def log_email(conn, direction, message):
    conn.execute(
        """
        INSERT INTO email_traffic (
            direction, message_id, subject, from_addr, to_addr, date_header, snippet, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            direction,
            message.get("Message-ID"),
            message.get("Subject"),
            message.get("From"),
            message.get("To"),
            message.get("Date"),
            extract_text_snippet(message),
            datetime.utcnow().isoformat(timespec="seconds") + "Z",
        ),
    )
    conn.commit()

def read_recent_emails(conn, limit=5):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, APP_PASS)
    mail.select("inbox")

    _, data = mail.search(None, "ALL")
    ids = data[0].split()[-limit:]

    for num in ids:
        _, msg_data = mail.fetch(num, "(RFC822)")
        raw = msg_data[0][1]
        message = BytesParser(policy=policy.default).parsebytes(raw)
        log_email(conn, "inbound", message)
        print(f"Message {num.decode()}:")
        print(raw[:200].decode(errors="ignore"))
        print("-" * 60)

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
