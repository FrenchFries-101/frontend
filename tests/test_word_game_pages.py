import sys
from PySide6.QtWidgets import QApplication
from pages.WordGamePages import BoardPage


class DummyParent:
    def goto(self, x):
        pass


def get_qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_gain_one_roll_blocked_when_daily_limit(monkeypatch):
    # 先确保 QApplication 存在
    app = get_qapp()

    # 先 mock 掉 BoardPage 初始化时可能调用到的东西
    monkeypatch.setattr(
        "pages.WordGamePages.safe_user_id",
        lambda: 1
    )

    monkeypatch.setattr(
        "pages.WordGamePages.status",
        lambda user_id: {
            "match": {
                "players": [
                    {
                        "user_id": 1,
                        "today_roll_contribute": 3
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

    called = {
        "quiz_opened": False,
        "gain_roll_called": False
    }

    class DummyQuiz:
        Accepted = 1

        def __init__(self, *args, **kwargs):
            called["quiz_opened"] = True

        def exec(self):
            return None

    monkeypatch.setattr(
        "pages.WordGamePages.QuizChallengeDialog",
        DummyQuiz
    )

    monkeypatch.setattr(
        "pages.WordGamePages.gain_roll",
        lambda user_id: {"message": "roll gained"}
    )

    board = BoardPage(DummyParent())

    # 调用被测逻辑
    board.gain_one_roll()

    # 关键断言：达到 3 次后，不应该再打开 quiz
    assert called["quiz_opened"] is False