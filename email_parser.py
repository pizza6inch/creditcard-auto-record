import re

_TX_BLOCK = re.compile(r'<!--詳細內文 第一筆 -->(.*?)<!--詳細內文 第一筆end-->', re.DOTALL)
_DATE_IN_TD = re.compile(r'>(\d{4}/\d{2}/\d{2})<')
_AMOUNT_MERCHANT = re.compile(r'>NT\$([\d,]+)</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>', re.DOTALL)


def parse_transactions(body: str) -> list[dict]:
    """Parse a 國泰世華 消費彙整通知 HTML email body.

    Splits the email into per-transaction HTML blocks using the bank's own
    HTML comment markers, then extracts date, amount, and merchant from each.

    Returns:
        [{"date": "YYYY/MM/DD", "merchant": str, "amount": int}, ...]

    Raises:
        ValueError: if no transaction blocks are found, or a block is missing
                    a required field.
    """
    blocks = _TX_BLOCK.findall(body)
    if not blocks:
        raise ValueError("No transaction blocks found in email body")

    results = []
    for i, block in enumerate(blocks, start=1):
        date_m = _DATE_IN_TD.search(block)
        if not date_m:
            raise ValueError(f"Could not extract date from transaction block {i}")

        amt_m = _AMOUNT_MERCHANT.search(block)
        if not amt_m:
            raise ValueError(f"Could not extract amount/merchant from transaction block {i}")

        results.append({
            "date": date_m.group(1),
            "merchant": amt_m.group(2).strip(),
            "amount": int(amt_m.group(1).replace(",", "")),
        })

    return results
