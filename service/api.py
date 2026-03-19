import requests

BASE_URL = "http://124.223.33.28:8787"
#BASE_URL="http://127.0.0.1:8000"

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


def get_sections(cambridge_id, test_id):
    res = requests.get(
        f"{BASE_URL}/listening/sections",
        params={
            "cambridge_id": cambridge_id,
            "test_id": test_id
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
    url = f"{BASE_URL}/register"

    data = {
        "username": username,
        "email": email,
        "password": password
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.json()["detail"])


# ----------------------
# 登录（重点：form-data）
# ----------------------
def login(username, password):
    url = f"{BASE_URL}/login"

    data = {
        "username": username,
        "password": password
    }

    # ⚠️ FastAPI OAuth2 必须用 form data
    response = requests.post(url, data=data)

    if response.status_code == 200:
        return response.json()  # {access_token, token_type}
    else:
        raise Exception(response.json()["detail"])


# ----------------------
# 获取当前用户
# ----------------------
def get_current_user(token):
    url = f"{BASE_URL}/users/me"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.json()["detail"])