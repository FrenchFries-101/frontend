from service import api_word_game


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_join_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"message": "ok"})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.join(19)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/join"
    assert called["params"] == {"user_id": 19}
    assert result == {"message": "ok"}


def test_status_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_get(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"in_match": True})

    monkeypatch.setattr(api_word_game.requests, "get", fake_get)

    result = api_word_game.status(7)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/status"
    assert called["params"] == {"user_id": 7}
    assert result == {"in_match": True}


def test_gain_roll_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"message": "roll gained"})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.gain_roll(8)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/gain-roll"
    assert called["params"] == {"user_id": 8}
    assert result == {"message": "roll gained"}


def test_roll_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"step": 4})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.roll(8)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/roll"
    assert called["params"] == {"user_id": 8}
    assert result == {"step": 4}


def test_get_quiz_question_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_get(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"question": "test"})

    monkeypatch.setattr(api_word_game.requests, "get", fake_get)

    result = api_word_game.get_quiz_question(11)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/quiz-question"
    assert called["params"] == {"user_id": 11}
    assert result == {"question": "test"}


def test_single_start_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"game": {"id": 1}})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.single_start(21)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/single/start"
    assert called["params"] == {"user_id": 21}
    assert result == {"game": {"id": 1}}


def test_single_status_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_get(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"game": {"current_position": 0}})

    monkeypatch.setattr(api_word_game.requests, "get", fake_get)

    result = api_word_game.single_status(21)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/single/status"
    assert called["params"] == {"user_id": 21}
    assert result == {"game": {"current_position": 0}}


def test_single_gain_roll_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"message": "roll gained"})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.single_gain_roll(21)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/single/gain-roll"
    assert called["params"] == {"user_id": 21}
    assert result == {"message": "roll gained"}


def test_single_roll_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_post(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"step": 3, "current_position": 3})

    monkeypatch.setattr(api_word_game.requests, "post", fake_post)

    result = api_word_game.single_roll(21)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/single/roll"
    assert called["params"] == {"user_id": 21}
    assert result == {"step": 3, "current_position": 3}


def test_single_get_quiz_question_calls_correct_endpoint(monkeypatch):
    called = {}

    def fake_get(url, params=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse({"question": "single test"})

    monkeypatch.setattr(api_word_game.requests, "get", fake_get)

    result = api_word_game.single_get_quiz_question(21)

    assert called["url"] == "http://124.223.33.28:8787/wordgame/single/quiz-question"
    assert called["params"] == {"user_id": 21}
    assert result == {"question": "single test"}