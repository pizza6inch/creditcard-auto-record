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
