import requests

BASE = "http://124.223.33.28:8787/wordgame"


# =========================
# Multiplayer
# =========================
def join(user_id):
    return requests.post(f"{BASE}/join", params={"user_id": user_id}).json()


def cancel(user_id):
    return requests.post(f"{BASE}/cancel", params={"user_id": user_id}).json()


def status(user_id):
    return requests.get(f"{BASE}/status", params={"user_id": user_id}).json()


def gain_roll(user_id):
    return requests.post(f"{BASE}/gain-roll", params={"user_id": user_id}).json()


def roll(user_id):
    return requests.post(f"{BASE}/roll", params={"user_id": user_id}).json()


def get_quiz_question(user_id):
    return requests.get(f"{BASE}/quiz-question", params={"user_id": user_id}).json()


# =========================
# Single Player
# =========================
def single_start(user_id):
    resp = requests.post(f"{BASE}/single/start", params={"user_id": user_id})
    try:
        return resp.json()
    except Exception:
        raise Exception(f"HTTP {resp.status_code}: {resp.text}")


def single_status(user_id):
    return requests.get(f"{BASE}/single/status", params={"user_id": user_id}).json()


def single_gain_roll(user_id):
    return requests.post(f"{BASE}/single/gain-roll", params={"user_id": user_id}).json()


def single_roll(user_id):
    return requests.post(f"{BASE}/single/roll", params={"user_id": user_id}).json()


def single_get_quiz_question(user_id):
    return requests.get(f"{BASE}/single/quiz-question", params={"user_id": user_id}).json()
