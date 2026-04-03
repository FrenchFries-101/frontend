import requests

# BASE_URL = "http://124.233.33.28:8787"
BASE_URL = "http://127.0.0.1:8000"
#BASE_URL = "http://124.233.33.28:8787"

# Pet 模块后端路由前缀
PET_BASE_URL = BASE_URL
# PET_BASE_URL = f"{BASE_URL}/pet_module"

def get_cambridge_list():
    res = requests.get(f"{BASE_URL}/listening/cambridge")
    return res.json()


def get_tests(cambridge_id, user_id):
    res = requests.get(
        f"{BASE_URL}/listening/tests",
        params={
            "cambridge_id": cambridge_id,
            "user_id": user_id
        }
    )
    return res.json()


def get_sections(test_id, user_id):
    res = requests.get(
        f"{BASE_URL}/listening/sections",
        params={
            "test_id": test_id,
            "user_id": user_id
        }
    )
    return res.json()


def get_listening_material(cambridge_id, test_id, section_id):
    res = requests.get(
        f"{BASE_URL}/listening/material",
        params={
            "cambridge_id": cambridge_id,
            "test_id": test_id,
            "section_id": section_id
        }
    )
    return res.json()


def submit_score(data):
    res = requests.post(
        f"{BASE_URL}/listening/submit",
        json=data
    )
    return res.json()

def get_categories():
    """
    获取一级分类
    return: ["Academic Subject", "Academic English"]
    """
    try:
        res = requests.get(f"{BASE_URL}/word/categories")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取分类失败:", e)
        return []


def get_subcategories(category):
    """
    获取二级分类
    param: category (str)
    """
    try:
        res = requests.get(
            f"{BASE_URL}/word/subcategories",
            params={"category": category}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取子分类失败:", e)
        return []


def get_words(category, subcategory):
    """
    获取单词列表
    return:
    [
        {"english": "derivative", "chinese": "..."},
        ...
    ]
    """
    try:
        res = requests.get(
            f"{BASE_URL}/word/words",
            params={
                "category": category,
                "subcategory": subcategory
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取单词失败:", e)
        return []

def register(username, email, password):
    try:
        res = requests.post(
            f"{BASE_URL}/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        return res.json()
    except Exception as e:
        print("注册失败:", e)
        return None
def login(username, password):
    try:
        res = requests.post(
            f"{BASE_URL}/login",
            data={
                "username": username,
                "password": password
            }
        )
        return res.json()
    except Exception as e:
        print("登录失败:", e)
        return None
def get_current_user(token):
    try:
        res = requests.get(
            f"{BASE_URL}/users/me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        return res.json()
    except Exception as e:
        print("获取用户失败:", e)
        return None

# ---- TED ----

def get_ted_talks():
    try:
        res = requests.get(f"{BASE_URL}/ted/talks")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取TED talks失败:", e)
        return []


def get_ted_questions(talk_id):
    try:
        res = requests.get(f"{BASE_URL}/ted/questions", params={"talk_id": talk_id})
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取TED题目失败:", e)
        return None


def submit_ted_answer(user_id, talk_id, answer_list):
    try:
        res = requests.post(
            f"{BASE_URL}/ted/submit",
            json={"user_id": user_id, "talk_id": talk_id, "answer_list": answer_list}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("提交TED答案失败:", e)
        return None


def get_ted_analysis(talk_id, question_id):
    try:
        res = requests.get(
            f"{BASE_URL}/ted/analysis",
            params={"talk_id": talk_id, "question_id": question_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取TED解析失败:", e)
        return None

def get_rank_list():
    try:
        res = requests.get(f"{BASE_URL}/rank/list")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取排行榜失败:", e)
        return []
