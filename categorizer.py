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
    Returns '其他' if no keyword matches or merchant is empty.
    """
    if not merchant.strip():
        return "其他"
    categories = _load_categories()
    merchant_lower = merchant.lower()
    for category, keywords in categories.items():
        if not keywords:
            continue
        for keyword in keywords:
            if keyword.lower() in merchant_lower:
                return category
    return "其他"
