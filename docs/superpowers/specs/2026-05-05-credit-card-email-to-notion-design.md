# Design: Credit Card Email to Notion Auto-Bookkeeping

**Date:** 2026-05-05
**Status:** Approved

## Overview

A GitHub Actions cron job that reads Cathay United Bank (國泰世華) credit card spending notification emails from Gmail via IMAP, parses transaction details, applies a keyword-based category mapping, and writes records to a Notion database.

---

## Architecture

```
GitHub Actions (daily cron)
        │
        ▼
  main.py
  ├── 1. Gmail IMAP connection
  │       └── Search unseen emails from 國泰世華
  ├── 2. Parse each email
  │       └── Extract: date, merchant name, amount
  ├── 3. Category mapping
  │       └── categories.yml (keyword → category)
  ├── 4. Write to Notion Database
  │       └── Notion API (create page per transaction)
  └── 5. Mark emails as processed
          └── Mark as read to prevent duplicate writes
```

### Secrets (stored in GitHub repository secrets)

| Secret | Description |
|---|---|
| `GMAIL_ADDRESS` | Gmail account address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not account password) |
| `NOTION_API_KEY` | Notion Integration token |
| `NOTION_DATABASE_ID` | Target Notion database ID |

---

## Email Parsing

- **Search filter:** `FROM:cathaybk.com.tw UNSEEN`
- **Extraction:** regex on HTML/text body to pull date, merchant name, and amount
- **Error handling:** if a single email fails to parse, log a warning and skip it — do not abort the run
- **Note:** regex patterns must be verified against a real notification email before first use; this is handled during implementation

---

## Category Mapping

Managed via `categories.yml`. Each category maps to a list of keyword strings. Matching is case-insensitive; first match wins. Transactions with no keyword match are assigned the `其他` (Other) category.

```yaml
餐飲:
  - 麥當勞
  - 肯德基
  - 星巴克
  - 85度C
  - 鼎泰豐

超市/量販:
  - 全聯
  - 家樂福
  - 好市多
  - 大潤發

交通:
  - 台鐵
  - 高鐵
  - 捷運
  - Uber
  - 統聯

購物:
  - 蝦皮
  - Momo
  - PChome
  - UNIQLO
  - Zara

醫療:
  - 診所
  - 藥局
  - 藥妝

其他: []
```

---

## Notion Database Schema

The script creates (or writes into) a database with the following properties:

| Field | Type | Notes |
|---|---|---|
| 名稱 | Title | Merchant name |
| 日期 | Date | Transaction date |
| 金額 | Number | Amount (numeric for filtering/summing) |
| 分類 | Select | Category from mapping |
| 建立時間 | Created time | Auto-set by Notion |

### Duplicate prevention

Before writing each record, query the database for an existing entry matching all three of: date + merchant name + amount. If a match exists, skip the write.

---

## GitHub Actions Workflow

**File:** `.github/workflows/sync.yml`

- **Schedule:** daily at 18:00 UTC (02:00 Taiwan time, UTC+8)
- **Manual trigger:** `workflow_dispatch` enabled
- **Steps:** checkout → install Python deps → run `main.py`
- **Failure notification:** Actions marks the run failed and sends a GitHub email notification on non-zero exit

### Project structure

```
/
├── .github/workflows/sync.yml
├── main.py
├── categories.yml
├── requirements.txt
└── README.md
```

### Dependencies (`requirements.txt`)

- `requests` — Notion API calls
- `pyyaml` — parse `categories.yml`
- Standard library: `imaplib`, `email`, `re`, `datetime`

---

## One-Time Setup

A `setup.py` script handles first-time initialization:
1. Uses the Notion API to create the database under a user-specified parent page
2. Prints the new `NOTION_DATABASE_ID` for the user to store in GitHub Secrets
3. Run locally once before the cron job is activated

---

## Out of Scope

- Multi-bank support (only 國泰世華)
- AI-based category inference
- Historical email backfill (only processes unseen/unread emails)
