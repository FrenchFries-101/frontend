# service/api_petshow.py
import random

# 模拟数据库
_pet_db = {
    1: {
        "skin_id": 1,
        "name": "狗名字",
        "gif_url": "resources/icons/dog.gif",
        "vitality": 50
    }
}

_quotes_db = {
    1: { "low": ["我好饿", "我好累"],
         "medium": ["今天背单词了吗？"],
         "high": ["状态良好，继续努力"] }
}

def get_current_skin(user_id: int) -> dict:
    """获取当前宠物皮肤"""
    pet = _pet_db.get(user_id)
    if pet:
        return {
            "skin_id": pet["skin_id"],
            "name": pet["name"],
            "gif_url": pet["gif_url"]
        }
    return {}

def modify_pet_name(user_id: int, new_name: str) -> dict:
    """修改宠物名字"""
    pet = _pet_db.get(user_id)
    if pet:
        pet["name"] = new_name
        return {"success": True, "message": "名称修改成功"}
    return {"success": False, "message": "用户不存在"}

def get_pet_quote(user_id: int) -> dict:
    """根据活力值返回随机语录"""
    pet = _pet_db.get(user_id)
    if not pet:
        return {}
    vitality = pet["vitality"]
    if vitality < 30:
        zone = "low"
    elif vitality <= 70:
        zone = "medium"
    else:
        zone = "high"
    content = random.choice(_quotes_db[1][zone])
    return {
        "quote_id": random.randint(1, 100),
        "content": content,
        "vitality_zone": zone
    }