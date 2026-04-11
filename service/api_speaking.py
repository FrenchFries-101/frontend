import requests

#BASE_URL = "http://127.0.0.1:8000"
BASE_URL="http://124.223.33.28:8787"

def health_check():
    try:
        res = requests.get(f"{BASE_URL}/api/health", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Speaking health check failed:", e)
        return {}


def get_sample_topics():
    try:
        res = requests.get(f"{BASE_URL}/api/topics/sample", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Get speaking topics failed:", e)
        return {}


def start_speaking(student_id, topic, think_seconds=15, answer_seconds=60):
    try:
        payload = {
            "student_id": str(student_id),
            "topic": topic,
            "think_seconds": think_seconds,
            "answer_seconds": answer_seconds,
        }
        res = requests.post(
            f"{BASE_URL}/api/speaking/start",
            json=payload,
            timeout=15
        )
        res.raise_for_status()
        return res.json()
    except requests.HTTPError as e:
        detail = ""
        try:
            detail = e.response.text
        except Exception:
            detail = str(e)
        print("Start speaking session failed:", detail)
        return {"error": detail}
    except Exception as e:
        print("Start speaking session failed:", e)
        return {"error": str(e)}


def finalize_speaking(session_id, audio_path):
    try:
        with open(audio_path, "rb") as f:
            files = {
                "audio": ("answer.wav", f, "audio/wav")
            }
            data = {
                "session_id": session_id
            }
            res = requests.post(
                f"{BASE_URL}/api/speaking/finalize",
                data=data,
                files=files,
                timeout=180
            )

        # 关键：先打印失败详情
        if not res.ok:
            print("Finalize speaking failed:")
            print("status_code =", res.status_code)
            print("response_text =", res.text)
            try:
                return {"error": res.json()}
            except Exception:
                return {"error": res.text}

        return res.json()

    except Exception as e:
        print("Finalize speaking failed:", e)
        return {"error": str(e)}


def abort_speaking(session_id):
    try:
        res = requests.post(
            f"{BASE_URL}/api/speaking/abort",
            json={"session_id": session_id},
            timeout=10
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Abort speaking failed:", e)
        return {}


def get_speaking_session(session_id):
    try:
        res = requests.get(
            f"{BASE_URL}/api/speaking/session/{session_id}",
            timeout=10
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Get speaking session failed:", e)
        return {}


def get_speaking_result(session_id):
    try:
        res = requests.get(
            f"{BASE_URL}/api/speaking/session/{session_id}/result",
            timeout=10
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("Get speaking result failed:", e)
        return {}