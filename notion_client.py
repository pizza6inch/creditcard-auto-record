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
    data = resp.json()
    if "id" not in data:
        raise ValueError(f"Unexpected Notion response (missing 'id'): {data}")
    return data["id"]


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
    data = resp.json()
    if "results" not in data:
        raise ValueError(f"Unexpected Notion response (missing 'results'): {data}")
    return len(data["results"]) > 0


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
