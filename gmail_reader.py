import base64
import imaplib
import email
import logging

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
CATHAY_SENDER = "cathaybk.com.tw"
LABEL = "cathaybk/已處理"

log = logging.getLogger(__name__)


def fetch_unread_transactions(gmail_address: str, app_password: str) -> list[dict]:
    """Connect to Gmail, fetch unseen 國泰世華 消費彙整通知 emails, return their bodies.

    Each email is marked as read and labelled ``cathaybk/已處理`` immediately
    after fetching to prevent duplicate processing. If either operation fails a
    warning is logged; the email will be retried on the next run (downstream
    duplicate detection prevents double-writes to Notion).

    Returns:
        [{"uid": bytes, "body": str}, ...]
    """
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as conn:
        conn.login(gmail_address, app_password)
        _ensure_label(conn, LABEL)
        conn.select("INBOX")

        _, uids = conn.uid("search", None, f'FROM "@{CATHAY_SENDER}" UNSEEN')
        uid_list = [u for u in uids[0].split() if u]

        results = []
        for uid in uid_list:
            _, data = conn.uid("fetch", uid, "(RFC822)")
            if not data or not isinstance(data[0], tuple):
                log.warning(f"Unexpected fetch response for uid {uid}, skipping")
                continue
            raw = data[0][1]
            msg = email.message_from_bytes(raw)

            # Only process 消費彙整通知 emails; skip login notifications etc.
            subject = _decode_header(msg.get("Subject", ""))
            if "消費彙整通知" not in subject:
                log.info(f"Skipping non-transaction email: {subject!r}")
                continue

            body = _extract_body(msg)
            results.append({"uid": uid, "body": body})

            try:
                conn.uid("store", uid, "+FLAGS", "\\Seen")
            except Exception:
                log.warning(f"Failed to mark uid {uid} as read — will be retried next run")

            try:
                conn.uid("copy", uid, _encode_mbox(LABEL))
            except Exception:
                log.warning(f"Failed to apply label '{LABEL}' to uid {uid}")

        return results


def _encode_mbox(name: str) -> str:
    """Encode a mailbox name in IMAP Modified UTF-7 (RFC 3501).

    ASCII printable characters (except '&') are kept as-is. Non-ASCII runs
    are encoded as &<base64 of UTF-16-BE>-.
    """
    result = []
    buf = []

    def flush():
        if buf:
            utf16 = "".join(buf).encode("utf-16-be")
            b64 = base64.b64encode(utf16).decode("ascii").rstrip("=")
            result.append(f"&{b64}-")
            buf.clear()

    for ch in name:
        if ch == "&":
            flush()
            result.append("&-")
        elif "\x20" <= ch <= "\x7e":
            flush()
            result.append(ch)
        else:
            buf.append(ch)

    flush()
    return "".join(result)


def _ensure_label(conn: imaplib.IMAP4_SSL, label: str) -> None:
    """Create the Gmail label if it does not already exist."""
    encoded = _encode_mbox(label)
    try:
        status, mailboxes = conn.list()
        if status != "OK":
            return
        existing = b"".join(m for m in mailboxes if m) if mailboxes else b""
        if encoded.encode("ascii") not in existing:
            result, _ = conn.create(encoded)
            if result == "OK":
                log.info(f"Created Gmail label: {label}")
            else:
                log.warning(f"Could not create Gmail label '{label}'")
    except Exception as e:
        log.warning(f"Could not ensure Gmail label '{label}': {e}")


def _decode_header(header: str) -> str:
    parts = email.header.decode_header(header)
    out = []
    for b, enc in parts:
        if isinstance(b, bytes):
            out.append(b.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(b)
    return "".join(out)


def _extract_body(msg: email.message.Message) -> str:
    """Extract the first text/plain or text/html part from an email."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return ""
