import pytest
from email_parser import parse_transactions

# Minimal HTML that matches the bank's actual comment + table structure
def _make_tx_html(date: str, amount: str, merchant: str) -> str:
    return (
        f'<!--詳細內文 第一筆 -->'
        f'<td>PLACEHOLDER</td>'
        f'<td>{date}</td>'
        f'<!--詳細內文 第一筆end-->'
        # The amount/merchant row is inside the same block — rebuild realistic:
    )


def _tx_block(date: str, amount_raw: str, merchant: str) -> str:
    """Build one realistic transaction block as the bank sends it."""
    return (
        f'<!--詳細內文 第一筆 -->'
        f'<td class="style_item">{date}</td>'
        f'<td class="style_item_head">NT${amount_raw}</td>'
        f'<td class="style_item">{merchant}</td>'
        f'<!--詳細內文 第一筆end-->'
    )


SINGLE_TX_HTML = _tx_block("2026/05/03", "116", "全聯福利中心－中山南京")

MULTI_TX_HTML = (
    _tx_block("2026/04/23", "45", "統一超商－鑫東一")
    + _tx_block("2026/04/23", "65", "統一超商－圓武")
)

AMOUNT_WITH_COMMA = _tx_block("2026/01/01", "1,299", "Apple Store")


def test_parse_single_transaction():
    result = parse_transactions(SINGLE_TX_HTML)
    assert len(result) == 1
    assert result[0] == {"date": "2026/05/03", "merchant": "全聯福利中心－中山南京", "amount": 116}


def test_parse_multiple_transactions():
    result = parse_transactions(MULTI_TX_HTML)
    assert len(result) == 2
    assert result[0] == {"date": "2026/04/23", "merchant": "統一超商－鑫東一", "amount": 45}
    assert result[1] == {"date": "2026/04/23", "merchant": "統一超商－圓武", "amount": 65}


def test_parse_amount_with_commas():
    result = parse_transactions(AMOUNT_WITH_COMMA)
    assert result[0]["amount"] == 1299


def test_raises_when_no_blocks():
    with pytest.raises(ValueError, match="No transaction blocks"):
        parse_transactions("<html>some unrelated content</html>")


def test_raises_when_block_missing_date():
    bad = (
        '<!--詳細內文 第一筆 -->'
        '<td class="style_item_head">NT$100</td>'
        '<td class="style_item">SomeMerchant</td>'
        '<!--詳細內文 第一筆end-->'
    )
    with pytest.raises(ValueError, match="date"):
        parse_transactions(bad)


def test_raises_when_block_missing_amount_merchant():
    bad = (
        '<!--詳細內文 第一筆 -->'
        '<td class="style_item">2026/01/01</td>'
        '<!--詳細內文 第一筆end-->'
    )
    with pytest.raises(ValueError, match="amount/merchant"):
        parse_transactions(bad)
