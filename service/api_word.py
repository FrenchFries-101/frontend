import requests

# BASE_URL = "http://124.223.33.28:8787"
BASE_URL = "http://127.0.0.1:8004"


def get_categories():
    """
    获取一级分类
    return:
    [
        {"category_id": 1, "category_name": "Academic Disciplines"},
        {"category_id": 2, "category_name": "Academic English"}
    ]
    """
    try:
        res = requests.get(f"{BASE_URL}/word/categories")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取分类失败:", e)
        return []


def get_subcategories(category_id):
    """
    获取二级分类（必须传 category_id）
    return:
    [
        {"subcategory_id": 6, "subcategory_name": "..."},
        ...
    ]
    """
    try:
        res = requests.get(
            f"{BASE_URL}/word/subcategories",
            params={"category_id": category_id}   # ✅ 关键改动
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取子分类失败:", e)
        return []


def get_words(subcategory_id):
    """
    获取单词列表（必须传 subcategory_id）
    return:
    [
        {"english": "syntax", "chinese": "..."},
        ...
    ]
    """
    try:
        res = requests.get(
            f"{BASE_URL}/word/words",
            params={"subcategory_id": subcategory_id}   # ✅ 关键改动
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取单词失败:", e)
        return []