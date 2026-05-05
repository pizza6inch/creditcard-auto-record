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
