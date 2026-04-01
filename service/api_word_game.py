import requests

BASE = "http://127.0.0.1:8000/wordgame"


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