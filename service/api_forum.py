import requests

# BASE_URL = "http://124.223.33.28:8787/forum"
BASE_URL = "http://127.0.0.1:8000/forum"

# =========================
# 获取帖子列表
# =========================
def get_posts(page=1, page_size=20):
    try:
        res = requests.get(
            f"{BASE_URL}/posts",
            params={
                "page": page,
                "page_size": page_size
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取帖子失败:", e)
        return {}


# =========================
# 搜索帖子
# =========================
def search_posts(keyword, page=1, page_size=20):
    try:
        res = requests.get(
            f"{BASE_URL}/posts/search",
            params={
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("搜索帖子失败:", e)
        return {}


# =========================
# 获取帖子详情
# =========================
def get_post_detail(post_id):
    try:
        res = requests.get(f"{BASE_URL}/posts/{post_id}")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取帖子详情失败:", e)
        return {}


# =========================
# 获取回复列表
# =========================
def get_replies(post_id):
    try:
        res = requests.get(f"{BASE_URL}/posts/{post_id}/replies")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取回复失败:", e)
        return []


# =========================
# 创建帖子
# =========================
def create_post(title, content, user_id):
    try:
        res = requests.post(
            f"{BASE_URL}/posts",
            json={
                "title": title,
                "content": content,
                "user_id": user_id
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("创建帖子失败:", e)
        return {}


# =========================
# 回复帖子
# =========================
def reply_post(post_id, content, user_id):
    try:
        res = requests.post(
            f"{BASE_URL}/posts/{post_id}/reply",
            json={
                "content": content,
                "user_id": user_id
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("回复失败:", e)
        return {}


# =========================
# 点赞帖子
# =========================
def like_post(post_id, user_id):
    try:
        res = requests.post(
            f"{BASE_URL}/posts/{post_id}/like",
            json={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("点赞失败:", e)
        return {}


# =========================
# 点赞回复
# =========================
def like_reply(reply_id, user_id):
    try:
        res = requests.post(
            f"{BASE_URL}/replies/{reply_id}/like",
            json={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("回复点赞失败:", e)
        return {}


def is_post_liked(post_id, user_id):
    try:
        res = requests.get(
            f"{BASE_URL}/posts/{post_id}/is-liked",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json().get("liked", False)
    except Exception as e:
        print("判断帖子点赞失败:", e)
        return False

def is_reply_liked(reply_id, user_id):
    try:
        res = requests.get(
            f"{BASE_URL}/replies/{reply_id}/is-liked",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json().get("liked", False)
    except Exception as e:
        print("判断回复点赞失败:", e)
        return False