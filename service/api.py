import requests

BASE_URL = "http://124.223.33.28:8787"

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