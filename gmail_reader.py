import imaplib
import email

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
CATHAY_SENDER = "cathaybk.com.tw"


def fetch_unread_transactions(gmail_address: str, app_password: str) -> list[dict]:
    """Connect to Gmail, fetch unseen 國泰世華 emails, return their bodies.

    Each email is marked as read immediately after fetching to prevent
    duplicate processing on the next run.

    Returns:
        [{"uid": bytes, "body": str}, ...]
    """
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as conn:
        conn.login(gmail_address, app_password)
        conn.select("INBOX")

        _, uids = conn.uid("search", None, f'FROM "@{CATHAY_SENDER}" UNSEEN')
        uid_list = [u for u in uids[0].split() if u]

        results = []
        for uid in uid_list:
            _, data = conn.uid("fetch", uid, "(RFC822)")
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            body = _extract_body(msg)
            results.append({"uid": uid, "body": body})
            conn.uid("store", uid, "+FLAGS", "\\Seen")

        return results


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
