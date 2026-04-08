import sys
from PySide6.QtWidgets import QApplication
from pages.WordGamePages import BoardPage, SingleBoardPage


class DummyParent:
    def goto(self, x):
        pass


def get_qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_gain_one_roll_blocked_when_daily_limit(monkeypatch):
    app = get_qapp()

    monkeypatch.setattr("pages.WordGamePages.safe_user_id", lambda: 1)

    monkeypatch.setattr(
        "pages.WordGamePages.status",
        lambda user_id: {
            "match": {
                "players": [
                    {
                        "user_id": 1,
                        "today_roll_contribute": 3,
                        "team": "red"
                    }
                ],
                "status": "active",
                "red_position": 0,
                "blue_position": 0,
                "total_cells": 84,
                "red_available_rolls": 0,
                "blue_available_rolls": 0
            },
            "last_match": None
        }
    )

    monkeypatch.setattr(
        "pages.WordGamePages.current_player",
        lambda match, user_id: match["players"][0]
    )

    monkeypatch.setattr(
        "pages.WordGamePages.show_light_message",
        lambda *args, **kwargs: None
    )

    called = {"quiz_opened": False}

    class DummyQuiz:
        Accepted = 1

        def __init__(self, *args, **kwargs):
            called["quiz_opened"] = True

        def exec(self):
            return None

    monkeypatch.setattr("pages.WordGamePages.QuizChallengeDialog", DummyQuiz)
    monkeypatch.setattr("pages.WordGamePages.gain_roll", lambda user_id: {"message": "roll gained"})

    board = BoardPage(DummyParent())
    board.gain_one_roll()

    assert called["quiz_opened"] is False


def test_single_gain_one_roll_blocked_when_daily_limit(monkeypatch):
    app = get_qapp()

    monkeypatch.setattr("pages.WordGamePages.safe_user_id", lambda: 1)

    monkeypatch.setattr(
        "pages.WordGamePages.single_status",
        lambda user_id: {
            "game": {
                "status": "active",
                "today_roll_gained": 3,
                "current_position": 0,
                "available_rolls": 0,
                "current_day": 1,
                "pending_reward_points": 0,
                "total_cells": 84
            },
            "last_game": None
        }
    )

    monkeypatch.setattr(
        "pages.WordGamePages.show_light_message",
        lambda *args, **kwargs: None
    )

    called = {"quiz_opened": False}

    class DummyQuiz:
        Accepted = 1

        def __init__(self, *args, **kwargs):
            called["quiz_opened"] = True

        def exec(self):
            return None

    monkeypatch.setattr("pages.WordGamePages.QuizChallengeDialog", DummyQuiz)
    monkeypatch.setattr("pages.WordGamePages.single_gain_roll", lambda user_id: {"message": "roll gained"})

    page = SingleBoardPage(DummyParent())
    page.gain_one_roll()

    assert called["quiz_opened"] is False