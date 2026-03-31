# service/api_pet_service.py
# 宠物服务模块假接口（后续替换为真实后端接口）

import time
from typing import Dict, List

# ============ 模拟数据库 ============

# 服务分类
_categories = [
    {"category_id": 1, "name": "食物"},
    {"category_id": 2, "name": "清洁"},
    {"category_id": 3, "name": "陪玩"},
]

# 分类下的服务列表
_services = {
    1: [  # 食物
        {"service_id": 1, "name": "投喂水", "vitality_effect": 3,
         "points_cost": 1, "gif_url": "water.gif", "cooldown_seconds": 60},
        {"service_id": 2, "name": "投喂萝卜", "vitality_effect": 6,
         "points_cost": 2, "gif_url": "carrot.gif", "cooldown_seconds": 120},
        {"service_id": 3, "name": "投喂烤鸡", "vitality_effect": 10,
         "points_cost": 5, "gif_url": "chicken.gif", "cooldown_seconds": 300},
    ],
    2: [  # 清洁
        {"service_id": 4, "name": "洗澡", "vitality_effect": 5,
         "points_cost": 3, "gif_url": "bath.gif", "cooldown_seconds": 180},
        {"service_id": 5, "name": "梳毛", "vitality_effect": 2,
         "points_cost": 1, "gif_url": "brush.gif", "cooldown_seconds": 90},
    ],
    3: [  # 陪玩
        {"service_id": 6, "name": "抛接球", "vitality_effect": 4,
         "points_cost": 2, "gif_url": "ball.gif", "cooldown_seconds": 120},
        {"service_id": 7, "name": "散步", "vitality_effect": 8,
         "points_cost": 4, "gif_url": "walk.gif", "cooldown_seconds": 240},
    ],
}

# 模拟用户数据（积分、冷却记录）
_user_data = {
    1: {"points": 500, "vitality": 50}
}

# 冷却记录: {(user_id, service_id): 上次使用的时间戳}
_cooldowns: Dict[tuple, float] = {}


# ============ 接口函数 ============

def get_service_categories() -> List[Dict]:
    """
    获取所有服务分类列表
    对应 GET /pet/service_categories
    """
    return _categories.copy()


def get_services_by_category(category_id: int) -> List[Dict]:
    """
    获取某分类下的所有服务
    对应 GET /pet/services?category_id={category_id}

    返回的每条记录额外附带 remaining_cooldown（剩余冷却秒数）
    """
    return _services.get(category_id, []).copy()


def apply_service(user_id: int, service_id: int) -> Dict:
    """
    使用服务：消耗积分，提升活力值，进入冷却
    对应 POST /pet/apply_service

    请求体: {"user_id": int, "service_id": int}
    成功返回: {"success": True, "new_vitality": float, "new_points": int,
              "vitality_gained": int, "points_spent": int}
    失败返回: {"success": False, "message": str}
    """
    user = _user_data.get(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}

    # 查找服务
    service = None
    for services in _services.values():
        for s in services:
            if s["service_id"] == service_id:
                service = s
                break
        if service:
            break
    if not service:
        return {"success": False, "message": "服务不存在"}

    # 校验冷却
    now = time.time()
    key = (user_id, service_id)
    last_use = _cooldowns.get(key, 0)
    remaining = int(service["cooldown_seconds"] - (now - last_use))
    if remaining > 0:
        return {"success": False, "message": f"服务冷却中，请等待 {remaining} 秒"}

    # 校验积分
    cost = service["points_cost"]
    if user["points"] < cost:
        return {"success": False, "message": "积分不足"}

    # 执行服务
    user["points"] -= cost
    user["vitality"] = min(100, user["vitality"] + service["vitality_effect"])
    _cooldowns[key] = now

    return {
        "success": True,
        "new_vitality": user["vitality"],
        "new_points": user["points"],
        "vitality_gained": service["vitality_effect"],
        "points_spent": cost,
    }


def get_remaining_cooldown(user_id: int, service_id: int) -> int:
    """
    获取某个服务的剩余冷却秒数
    """
    service = None
    for services in _services.values():
        for s in services:
            if s["service_id"] == service_id:
                service = s
                break
        if service:
            break
    if not service:
        return 0

    key = (user_id, service_id)
    last_use = _cooldowns.get(key, 0)
    remaining = int(service["cooldown_seconds"] - (time.time() - last_use))
    return max(0, remaining)


def get_user_points(user_id: int) -> int:
    """获取用户积分（测试用）"""
    user = _user_data.get(user_id)
    return user["points"] if user else 0
