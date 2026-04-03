import requests

# BASE_URL = "http://124.233.33.28:8787"
BASE_URL = "http://127.0.0.1:8000"
#BASE_URL = "http://124.233.33.28:8787"

# Pet 模块后端路由前缀
# PET_BASE_URL = BASE_URL
PET_BASE_URL = f"{BASE_URL}/pet_module"

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


def get_user_rank(user_id):
    try:
        res = requests.get(f"{BASE_URL}/rank/user/{user_id}")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取用户排名失败:", e)
        return {"rank": 0, "points": 0}


# ---- Group Plaza ----


def get_groups(search=None, page=1, page_size=20):
    try:
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        res = requests.get(f"{BASE_URL}/groups", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取小组列表失败:", e)
        return {"groups": [], "total_count": 0}


def create_group(group_name, max_members, group_icon=None, password=None, user_id=None):
    try:
        payload = {
            "group_name": group_name,
            "max_members": max_members,
        }
        if group_icon:
            payload["group_icon"] = group_icon
        if password:
            payload["password"] = password
        if user_id is not None:
            payload["user_id"] = user_id

        res = requests.post(f"{BASE_URL}/groups/create", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("创建小组失败:", e)
        return {"success": False, "message": "创建小组失败"}



def join_group(group_id, password=None, user_id=None):
    try:
        payload = {
            "group_id": group_id,
            "password": password or "",
        }
        if user_id is not None:
            payload["user_id"] = user_id
        res = requests.post(f"{BASE_URL}/groups/join", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("加入小组失败:", e)
        return {"success": False, "message": "加入小组失败"}



def get_group_members(group_id):
    try:
        res = requests.get(f"{BASE_URL}/groups/{group_id}/members")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取小组成员失败:", e)
        return {"members": []}


def upload_group_icon(group_id, image_path=None, image_base64=None):
    try:
        if image_path:
            with open(image_path, "rb") as f:
                files = {"image": (image_path.split("/")[-1].split("\\")[-1], f, "application/octet-stream")}
                res = requests.post(f"{BASE_URL}/groups/{group_id}/icon", files=files)
        elif image_base64:
            res = requests.post(
                f"{BASE_URL}/groups/{group_id}/icon",
                data={"image_base64": image_base64}
            )
        else:
            return {"success": False, "message": "未选择图片"}

        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("上传小组头像失败:", e)
        return {"success": False, "message": "上传小组头像失败"}


