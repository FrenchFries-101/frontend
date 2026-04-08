# service/api_petshow.py
# 宠物展示相关接口 —— 对接后端真实 API

import requests

from service.api import PET_BASE_URL


def get_current_skin(user_id: int) -> dict:
    """获取当前宠物皮肤 GET /pet/current_skin?user_id={user_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/pet/current_skin",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取当前皮肤失败:", e)
        return {}

def modify_pet_name(user_id: int, new_name: str) -> dict:
    """修改宠物名字 POST /pet/modify_name"""
    try:
        res = requests.post(
            f"{PET_BASE_URL}/pet/modify_name",
            json={
                "user_id": str(user_id),
                "name": new_name
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("修改宠物名称失败:", e)
        return {"success": False, "message": f"请求失败: {e}"}


def get_pet_name(user_id: int) -> dict:
    """获取宠物名字 GET /pet_module/pet/name?user_id={user_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/pet/name",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取宠物名字失败:", e)
        return {}


def get_pet_quote(user_id: int) -> dict:
    """获取语录 GET /pet/quote?user_id={user_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/pet/quote",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取语录失败:", e)
        return {}


def get_level_config() -> list:
    """获取所有等级配置 GET /pet/level_config"""
    try:
        res = requests.get(f"{PET_BASE_URL}/pet/level_config")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取等级配置失败:", e)
        return []


def get_pet_types() -> list:
    """获取所有宠物类型 GET /pet/types"""
    try:
        res = requests.get(f"{PET_BASE_URL}/pet/types")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取宠物类型失败:", e)
        return []