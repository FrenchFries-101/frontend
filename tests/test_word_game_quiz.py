from pages.WordGameQuiz import normalize_answer


def test_normalize_answer_basic():
    assert normalize_answer("apple") == "apple"


def test_normalize_answer_strip_spaces():
    assert normalize_answer("  apple  ") == "apple"


def test_normalize_answer_case_insensitive():
    assert normalize_answer("Apple") == "apple"


def test_normalize_answer_multiple_spaces():
    assert normalize_answer("apple   pie") == "apple pie"


def test_normalize_answer_empty():
    assert normalize_answer("") == ""


def test_normalize_answer_none():
    assert normalize_answer(None) == ""


def test_normalize_answer_with_newline():
    assert normalize_answer("apple\npie") == "apple pie"


def test_normalize_answer_with_tabs():
    assert normalize_answer("apple\t\tpie") == "apple pie"