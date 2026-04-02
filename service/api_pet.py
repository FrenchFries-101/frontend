# pet_api.py
# 宠物皮肤接口 —— 对接后端真实 API

import requests
from typing import List, Dict

from service.api import PET_BASE_URL


def get_user_skins(user_id: int) -> List[Dict]:
    """获取用户皮肤列表 GET /pet/skins?user_id={user_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/pet/skins",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取皮肤列表失败:", e)
        return []


def set_current_skin(user_id: int, skin_id: int) -> Dict:
    """设置当前皮肤 POST /pet/current_skin"""
    try:
        res = requests.post(
            f"{PET_BASE_URL}/pet/current_skin",
            json={
                "user_id": str(user_id),
                "skin_id": skin_id
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("设置当前皮肤失败:", e)
        return {"success": False, "message": f"请求失败: {e}"}