# service/api_pet_task.py
# 宠物任务模块 —— 对接后端真实 API

import requests
from typing import Dict

from service.api import PET_BASE_URL


def complete_task(user_id: int, task_type: str) -> Dict:
    """完成任务 POST /task/complete"""
    try:
        res = requests.post(
            f"{PET_BASE_URL}/task/complete",
            json={
                "user_id": str(user_id),
                "task_type": task_type
            }
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("完成任务失败:", e)
        return {"success": False, "points_earned": 0, "message": f"请求失败: {e}"}


def get_daily_progress(user_id: int) -> Dict:
    """获取每日任务进度 GET /task/daily_progress?user_id={user_id}"""
    try:
        res = requests.get(
            f"{PET_BASE_URL}/task/daily_progress",
            params={"user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("获取每日进度失败:", e)
        return {
            "date": "",
            "tasks": [],
            "total_earned_today": 0,
            "daily_cap": 50,
            "remaining_cap": 50
        }
