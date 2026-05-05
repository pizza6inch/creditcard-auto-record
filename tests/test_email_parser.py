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


def test_parse_merchant_at_end_no_trailing_newline():
    body = "消費日期：2024/01/15\n消費金額：新台幣 100 元\n消費特店：某商店"
    result = parse_transaction(body)
    assert result["merchant"] == "某商店"


def test_parse_html_body():
    html_body = (
        "<html><body>\n"
        "<tr><td>消費日期：2024/02/14</td></tr>\n"
        "<tr><td>消費特店：麥當勞</td></tr>\n"
        "<tr><td>消費金額：NT$199</td></tr>\n"
        "</body></html>"
    )
    result = parse_transaction(html_body)
    assert result["date"] == "2024/02/14"
    assert result["merchant"] == "麥當勞"
    assert result["amount"] == 199
