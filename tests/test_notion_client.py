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
