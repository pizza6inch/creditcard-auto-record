# Credit Card Email to Notion Auto-Bookkeeping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A GitHub Actions daily cron job that reads 國泰世華 credit card spending emails from Gmail via IMAP and records transactions into a Notion database.

**Architecture:** `main.py` orchestrates the pipeline: fetch unseen emails from Gmail via IMAP, parse each body with regex, map the merchant to a category via `categories.yml`, check for duplicates in Notion, then write new records. A one-time `setup.py` creates the Notion database. GitHub Actions runs `main.py` daily on a schedule.

**Tech Stack:** Python 3.11, `imaplib` (stdlib), `email` (stdlib), `requests`, `pyyaml`, `requests-mock` (tests), Notion API v1, Gmail IMAP

---

## File Structure

| File | Responsibility |
|---|---|
| `main.py` | Orchestrates the full pipeline |
| `gmail_reader.py` | IMAP connection, fetch unseen emails, mark as read |
| `email_parser.py` | Regex extraction of date/merchant/amount from email body |
| `categorizer.py` | Keyword-to-category matching from `categories.yml` |
| `notion_client.py` | Notion API: create database, check duplicates, write record |
| `setup.py` | One-time: creates Notion database and prints its ID |
| `categories.yml` | User-editable keyword → category mapping |
| `requirements.txt` | Python dependencies |
| `.github/workflows/sync.yml` | Daily cron workflow |
| `tests/test_email_parser.py` | Unit tests for email parsing |
| `tests/test_categorizer.py` | Unit tests for category mapping |
| `tests/test_notion_client.py` | Unit tests for Notion API calls (mocked HTTP) |

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `categories.yml`

- [ ] **Step 1: Create `requirements.txt`**

```
requests==2.31.0
pyyaml==6.0.1
pytest==7.4.0
requests-mock==1.11.0
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
.venv/
venv/
```

- [ ] **Step 3: Create `categories.yml`**

```yaml
餐飲:
  - 麥當勞
  - 肯德基
  - 星巴克
  - 85度C
  - 鼎泰豐
  - 摩斯漢堡
  - subway
  - 7-ELEVEN
  - 全家

超市/量販:
  - 全聯
  - 家樂福
  - 好市多
  - 大潤發
  - 愛買

交通:
  - 台鐵
  - 高鐵
  - 捷運
  - Uber
  - 統聯
  - 客運
  - 停車

購物:
  - 蝦皮
  - Momo
  - PChome
  - UNIQLO
  - Zara
  - H&M
  - 誠品

醫療:
  - 診所
  - 藥局
  - 藥妝
  - 健保

其他: []
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 5: Initialise git and commit**

```bash
git init
git add requirements.txt .gitignore categories.yml
git commit -m "chore: project scaffold"
```

---

### Task 2: Email Parser

**Files:**
- Create: `email_parser.py`
- Create: `tests/test_email_parser.py`

The parser extracts three fields from an email body string using regex. 國泰世華 notification emails contain lines such as:

```
消費日期：2024/01/15
消費特店：全聯福利中心
消費金額：新台幣 350 元
```

If any field cannot be extracted, `parse_transaction` raises `ValueError`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_email_parser.py`:

```python
import pytest
from email_parser import parse_transaction

SAMPLE_BODY = """
親愛的持卡人您好，

您的信用卡有以下消費紀錄：

消費日期：2024/01/15
消費特店：全聯福利中心
消費金額：新台幣 350 元

如有疑問請洽客服。
"""

ALT_FORMAT_BODY = """
消費日期：2024-03-22
消費特店：麥當勞
消費金額：NT$129
"""


def test_parse_standard_format():
    result = parse_transaction(SAMPLE_BODY)
    assert result["date"] == "2024/01/15"
    assert result["merchant"] == "全聯福利中心"
    assert result["amount"] == 350


def test_parse_alt_date_and_amount_format():
    result = parse_transaction(ALT_FORMAT_BODY)
    assert result["date"] == "2024-03-22"
    assert result["merchant"] == "麥當勞"
    assert result["amount"] == 129


def test_parse_amount_with_commas():
    body = "消費日期：2024/06/01\n消費特店：Apple Store\n消費金額：新台幣 1,299 元"
    result = parse_transaction(body)
    assert result["amount"] == 1299


def test_raises_on_missing_date():
    body = "消費特店：全聯\n消費金額：新台幣 100 元"
    with pytest.raises(ValueError, match="date"):
        parse_transaction(body)


def test_raises_on_missing_merchant():
    body = "消費日期：2024/01/15\n消費金額：新台幣 100 元"
    with pytest.raises(ValueError, match="merchant"):
        parse_transaction(body)


def test_raises_on_missing_amount():
    body = "消費日期：2024/01/15\n消費特店：全聯"
    with pytest.raises(ValueError, match="amount"):
        parse_transaction(body)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_email_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'email_parser'`

- [ ] **Step 3: Implement `email_parser.py`**

```python
import re

DATE_PATTERN = re.compile(r'消費日期[：:]\s*(\d{4}[/\-]\d{2}[/\-]\d{2})')
MERCHANT_PATTERN = re.compile(r'消費特店[：:]\s*(.+?)[\n\r<]')
AMOUNT_PATTERN = re.compile(r'消費金額[：:]\s*(?:新台幣\s*)?(?:NT\$\s*)?([\d,]+)')


def parse_transaction(body: str) -> dict:
    """Parse a 國泰世華 spending notification email body.

    Returns:
        {"date": str, "merchant": str, "amount": int}

    Raises:
        ValueError: if any required field cannot be extracted.
    """
    date_match = DATE_PATTERN.search(body)
    if not date_match:
        raise ValueError("Could not extract date from email body")

    merchant_match = MERCHANT_PATTERN.search(body)
    if not merchant_match:
        raise ValueError("Could not extract merchant from email body")

    amount_match = AMOUNT_PATTERN.search(body)
    if not amount_match:
        raise ValueError("Could not extract amount from email body")

    return {
        "date": date_match.group(1),
        "merchant": merchant_match.group(1).strip(),
        "amount": int(amount_match.group(1).replace(",", "")),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_email_parser.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add email_parser.py tests/test_email_parser.py
git commit -m "feat: email parser with regex extraction"
```

> **Important — verify against a real email before first production run.** Forward a real 國泰世華 消費通知 email to a `.txt` file, then run `python -c "from email_parser import parse_transaction; print(parse_transaction(open('sample.txt').read()))"`. If it raises `ValueError`, the field labels in your actual email may differ (e.g. `消費商店` instead of `消費特店`). Adjust the regex constants at the top of `email_parser.py` accordingly.

---

### Task 3: Categorizer

**Files:**
- Create: `categorizer.py`
- Create: `tests/test_categorizer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_categorizer.py`:

```python
from categorizer import categorize


def test_exact_keyword_match():
    assert categorize("全聯福利中心") == "超市/量販"


def test_partial_keyword_match():
    assert categorize("台北捷運板南線") == "交通"


def test_case_insensitive():
    assert categorize("UNIQLO 信義店") == "購物"


def test_fallback_to_other():
    assert categorize("某不知名小店") == "其他"


def test_first_match_wins():
    # "7-ELEVEN" is in 餐飲 — should not fall through to 其他
    assert categorize("7-ELEVEN 台北信義店") == "餐飲"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_categorizer.py -v
```

Expected: `ModuleNotFoundError: No module named 'categorizer'`

- [ ] **Step 3: Implement `categorizer.py`**

```python
import yaml
from pathlib import Path

_CATEGORIES: dict | None = None
_CATEGORIES_FILE = Path(__file__).parent / "categories.yml"


def _load_categories() -> dict:
    global _CATEGORIES
    if _CATEGORIES is None:
        with open(_CATEGORIES_FILE, encoding="utf-8") as f:
            _CATEGORIES = yaml.safe_load(f)
    return _CATEGORIES


def categorize(merchant: str) -> str:
    """Return the category for a merchant name.

    Matches case-insensitively against keywords in categories.yml.
    Returns '其他' if no keyword matches.
    """
    categories = _load_categories()
    merchant_lower = merchant.lower()
    for category, keywords in categories.items():
        if not keywords:
            continue
        for keyword in keywords:
            if keyword.lower() in merchant_lower:
                return category
    return "其他"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_categorizer.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add categorizer.py tests/test_categorizer.py
git commit -m "feat: keyword-based categorizer"
```

---

### Task 4: Notion Client

**Files:**
- Create: `notion_client.py`
- Create: `tests/test_notion_client.py`

Three operations:
1. `create_database(parent_page_id, api_key)` — creates the DB schema (used by `setup.py`)
2. `record_exists(database_id, date, merchant, amount, api_key)` — duplicate check
3. `create_record(database_id, date, merchant, amount, category, api_key)` — writes a row

All HTTP goes to `https://api.notion.com/v1/`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_notion_client.py`:

```python
from notion_client import create_database, record_exists, create_record

API_KEY = "secret_test"
DB_ID = "db-123"
PARENT_ID = "page-456"


def test_create_database_calls_correct_endpoint(requests_mock):
    requests_mock.post(
        "https://api.notion.com/v1/databases",
        json={"id": "new-db-id"},
    )
    result = create_database(PARENT_ID, API_KEY)
    assert result == "new-db-id"
    assert requests_mock.last_request.headers["Authorization"] == f"Bearer {API_KEY}"


def test_record_exists_returns_true_when_found(requests_mock):
    requests_mock.post(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        json={"results": [{"id": "existing-page"}]},
    )
    assert record_exists(DB_ID, "2024/01/15", "全聯", 350, API_KEY) is True


def test_record_exists_returns_false_when_empty(requests_mock):
    requests_mock.post(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        json={"results": []},
    )
    assert record_exists(DB_ID, "2024/01/15", "全聯", 350, API_KEY) is False


def test_create_record_posts_correct_payload(requests_mock):
    requests_mock.post(
        "https://api.notion.com/v1/pages",
        json={"id": "new-page-id"},
    )
    create_record(DB_ID, "2024/01/15", "全聯", 350, "超市/量販", API_KEY)
    body = requests_mock.last_request.json()
    props = body["properties"]
    assert props["名稱"]["title"][0]["text"]["content"] == "全聯"
    assert props["金額"]["number"] == 350
    assert props["分類"]["select"]["name"] == "超市/量販"
    assert props["日期"]["date"]["start"] == "2024-01-15"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_notion_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'notion_client'`

- [ ] **Step 3: Implement `notion_client.py`**

```python
import requests

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _normalise_date(date: str) -> str:
    """Convert 2024/01/15 → 2024-01-15 (ISO 8601, required by Notion)."""
    return date.replace("/", "-")


def create_database(parent_page_id: str, api_key: str) -> str:
    """Create the bookkeeping database under parent_page_id.

    Returns the new database ID.
    """
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "信用卡消費紀錄"}}],
        "properties": {
            "名稱": {"title": {}},
            "日期": {"date": {}},
            "金額": {"number": {"format": "number"}},
            "分類": {"select": {}},
            "建立時間": {"created_time": {}},
        },
    }
    resp = requests.post(f"{BASE_URL}/databases", json=payload, headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()["id"]


def record_exists(
    database_id: str, date: str, merchant: str, amount: int, api_key: str
) -> bool:
    """Return True if a record with the same date + merchant + amount already exists."""
    payload = {
        "filter": {
            "and": [
                {"property": "日期", "date": {"equals": _normalise_date(date)}},
                {"property": "名稱", "title": {"equals": merchant}},
                {"property": "金額", "number": {"equals": amount}},
            ]
        }
    }
    resp = requests.post(
        f"{BASE_URL}/databases/{database_id}/query",
        json=payload,
        headers=_headers(api_key),
    )
    resp.raise_for_status()
    return len(resp.json()["results"]) > 0


def create_record(
    database_id: str,
    date: str,
    merchant: str,
    amount: int,
    category: str,
    api_key: str,
) -> None:
    """Write a new transaction record to the Notion database."""
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "名稱": {"title": [{"text": {"content": merchant}}]},
            "日期": {"date": {"start": _normalise_date(date)}},
            "金額": {"number": amount},
            "分類": {"select": {"name": category}},
        },
    }
    resp = requests.post(f"{BASE_URL}/pages", json=payload, headers=_headers(api_key))
    resp.raise_for_status()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_notion_client.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add notion_client.py tests/test_notion_client.py
git commit -m "feat: Notion API client with duplicate detection"
```

---

### Task 5: Gmail Reader

**Files:**
- Create: `gmail_reader.py`

Connects to Gmail via IMAP SSL, searches for unseen emails from `@cathaybk.com.tw`, returns their body text, and marks each email as read immediately to prevent re-processing on the next run. Uses only stdlib — no unit tests (requires a live IMAP connection), but logic is intentionally minimal.

- [ ] **Step 1: Create `gmail_reader.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add gmail_reader.py
git commit -m "feat: Gmail IMAP reader"
```

---

### Task 6: Main Orchestrator

**Files:**
- Create: `main.py`

Reads environment variables, calls each module in sequence. Exits with code 1 on unexpected errors so GitHub Actions marks the run as failed.

- [ ] **Step 1: Create `main.py`**

```python
import os
import sys
import logging

from gmail_reader import fetch_unread_transactions
from email_parser import parse_transaction
from categorizer import categorize
from notion_client import record_exists, create_record

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
    gmail_address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    notion_api_key = os.environ["NOTION_API_KEY"]
    database_id = os.environ["NOTION_DATABASE_ID"]

    emails = fetch_unread_transactions(gmail_address, app_password)
    log.info(f"Fetched {len(emails)} unseen email(s)")

    written = 0
    skipped = 0

    for item in emails:
        try:
            tx = parse_transaction(item["body"])
        except ValueError as e:
            log.warning(f"Skipping unparseable email: {e}")
            continue

        if record_exists(database_id, tx["date"], tx["merchant"], tx["amount"], notion_api_key):
            log.info(f"Duplicate, skipping: {tx['date']} {tx['merchant']} {tx['amount']}")
            skipped += 1
            continue

        category = categorize(tx["merchant"])
        create_record(
            database_id, tx["date"], tx["merchant"], tx["amount"], category, notion_api_key
        )
        log.info(f"Recorded: {tx['date']} | {tx['merchant']} | {tx['amount']} | {category}")
        written += 1

    log.info(f"Done. Written: {written}, Skipped duplicates: {skipped}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)
```

- [ ] **Step 2: Run all tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: 15 passed

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main orchestrator"
```

---

### Task 7: Setup Script

**Files:**
- Create: `setup.py`

Run once locally to create the Notion database and print its ID for copying into GitHub Secrets.

- [ ] **Step 1: Create `setup.py`**

```python
"""One-time setup: creates the Notion bookkeeping database.

Usage:
    NOTION_API_KEY=secret_... NOTION_PARENT_PAGE_ID=<page-id> python setup.py

Prints NOTION_DATABASE_ID to stdout. Copy it into your GitHub Secrets.
"""
import os
import sys
from notion_client import create_database


def main():
    api_key = os.environ.get("NOTION_API_KEY")
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")

    if not api_key or not parent_page_id:
        print("Error: set NOTION_API_KEY and NOTION_PARENT_PAGE_ID environment variables")
        sys.exit(1)

    db_id = create_database(parent_page_id, api_key)
    print("\nNotion database created successfully!")
    print(f"NOTION_DATABASE_ID={db_id}")
    print("\nAdd this as a GitHub Secret named NOTION_DATABASE_ID")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add setup.py
git commit -m "feat: one-time Notion database setup script"
```

---

### Task 8: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/sync.yml`

- [ ] **Step 1: Create `.github/workflows/sync.yml`**

```yaml
name: Sync credit card transactions to Notion

on:
  schedule:
    - cron: '0 18 * * *'   # Daily at 02:00 Taiwan time (UTC+8 = UTC 18:00)
  workflow_dispatch:         # Allow manual trigger from the GitHub Actions UI

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run sync
        env:
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
        run: python main.py
```

- [ ] **Step 2: Create a GitHub repository**

Go to https://github.com/new and create a new repository (can be private).

- [ ] **Step 3: Push**

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

- [ ] **Step 4: Commit workflow file and push**

```bash
git add .github/workflows/sync.yml
git commit -m "feat: GitHub Actions daily cron workflow"
git push
```

---

### Task 9: Configure Secrets and First Run

All steps in this task happen in the GitHub, Google, and Notion UIs — no code to write.

- [ ] **Step 1: Enable Gmail IMAP**

Gmail → Settings (gear icon) → See all settings → Forwarding and POP/IMAP tab → Enable IMAP → Save Changes.

- [ ] **Step 2: Create a Gmail App Password**

Google Account (myaccount.google.com) → Security → 2-Step Verification → App passwords → Create an app password → name it "信用卡記帳" → copy the 16-character password.

- [ ] **Step 3: Create a Notion Integration**

Go to https://www.notion.so/profile/integrations → New integration → name it "信用卡記帳" → Internal → Submit → copy the **Internal Integration Secret**.

- [ ] **Step 4: Share your Notion parent page with the integration**

Open the Notion page where you want the database to live → click `•••` (top right) → Connections → search for "信用卡記帳" → confirm.

- [ ] **Step 5: Run `setup.py` to create the database**

```bash
NOTION_API_KEY=secret_... NOTION_PARENT_PAGE_ID=<32-char-page-id> python setup.py
```

The page ID is the last part of the Notion page URL: `notion.so/<workspace>/<page-id>`.

Copy the printed `NOTION_DATABASE_ID`.

- [ ] **Step 6: Add four GitHub Secrets**

GitHub repo → Settings → Secrets and variables → Actions → New repository secret. Add:

| Name | Value |
|---|---|
| `GMAIL_ADDRESS` | your Gmail address |
| `GMAIL_APP_PASSWORD` | the 16-char app password from Step 2 |
| `NOTION_API_KEY` | the integration secret from Step 3 |
| `NOTION_DATABASE_ID` | the ID printed by `setup.py` |

- [ ] **Step 7: Trigger a manual run**

GitHub repo → Actions tab → "Sync credit card transactions to Notion" → Run workflow → Run workflow.

Verify the run completes green and a record appears in your Notion database.
