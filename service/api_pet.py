# pet_api.py
# 模拟宠物皮肤接口,后面改成真的后端接口

from typing import List, Dict

# 模拟数据库
fake_db = {
    "skins": [
        {
            "skin_id": 1,
            "name": "默认狗狗",
            "description": "初始皮肤",
            "gif_url": "dog1.gif",
            "unlock_level": 1,
            "owned": True,
            "current": True
        },
        {
            "skin_id": 3,
            "name": "金色狗狗",
            "description": "金色毛发的狗狗",
            "gif_url": "dog1.gif",
            "unlock_level": 3,
            "owned": True,
            "current": False
        },
        {
            "skin_id": 4,
            "name": "蓝色狗狗",
            "description": "蓝色毛发的狗狗",
            "gif_url": "dog1.gif",
            "unlock_level": 5,
            "owned": True,
            "current": False
        },
        {
            "skin_id": 5,
            "name": "紫色狗狗",
            "description": "紫色毛发的狗狗",
            "gif_url": "dog1.gif",
            "unlock_level": 8,
            "owned": True,
            "current": False
        },
        {
            "skin_id": 2,
            "name": "阳光狗狗",
            "description": "2级解锁",
            "gif_url": "dog2.gif",
            "unlock_level": 2,
            "owned": False,
            "current": False
        }
    ]
}

def get_user_skins(user_id: int) -> List[Dict]:
    # 这里只返回全部皮肤，忽略 user_id
    return fake_db["skins"]

def set_current_skin(user_id: int, skin_id: int) -> Dict:
    # 查找皮肤
    skin = next((s for s in fake_db["skins"] if s["skin_id"] == skin_id), None)
    if not skin:
        return {"success": False, "message": "皮肤不存在"}

    if not skin["owned"]:
        return {"success": False, "message": "该皮肤尚未解锁"}

    # 设置当前皮肤
    for s in fake_db["skins"]:
        s["current"] = False
    skin["current"] = True
    return {"success": True, "message": "皮肤切换成功"}