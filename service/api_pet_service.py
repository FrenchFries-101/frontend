# service/api_pet_service.py
# 宠物服务模块 —— 对接后端真实 API

import time
import requests
from typing import Dict, List

from service.api import PET_BASE_URL

# 本地服务缓存（用于组件查找服务信息）
_services_cache: Dict[int, dict] = {}

# 本地冷却记录: {(user_id, service_id): 上次使用的时间戳}
_cooldowns: Dict[tuple, float] = {}

# 内部固定冷却时间（秒）
COOLDOWN_SECONDS = 20


def get_service_categories() -> List[Dict]:
    """获取服务分类列表 GET /pet/service_categories"""
    try:
        res = requests.get(f"{PET_BASE_URL}/pet/service_categories")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取服务分类失败:", e)
        return []


def get_services_by_category(category_id: int) -> List[Dict]:
    """获取某分类下的服务 GET /pet/services?category_id={category_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/pet/services",
            params={"category_id": category_id}
        )
        res.raise_for_status()
        services = res.json()
        # 缓存服务数据，供冷却刷新时查找
        for s in services:
            _services_cache[s["service_id"]] = s
        return services
    except Exception as e:
        print("获取服务列表失败:", e)
        return []


def apply_service(user_id: int, service_id: int) -> Dict:
    """使用服务 POST /pet/apply_service"""
    try:
        res = requests.post(
            f"{PET_BASE_URL}/pet/apply_service",
            json={
                "user_id": str(user_id),
                "service_id": service_id
            }
        )
        res.raise_for_status()
        result = res.json()
        # 成功后记录冷却起始时间
        if result.get("success"):
            _cooldowns[(user_id, service_id)] = time.time()
        return result
    except Exception as e:
        print("应用服务失败:", e)
        return {"success": False, "message": f"请求失败: {e}"}


def get_remaining_cooldown(user_id: int, service_id: int) -> int:
    """获取某个服务的剩余冷却秒数（内部固定 20 秒）"""
    key = (user_id, service_id)
    last_use = _cooldowns.get(key, 0)
    remaining = int(COOLDOWN_SECONDS - (time.time() - last_use))
    return max(0, remaining)
