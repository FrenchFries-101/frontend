# service/api_restaurant.py
# 美食推荐模块 —— 对接后端真实 API

import requests
from typing import Dict, List

from service.api import BASE_URL

RESTAURANT_BASE_URL = f"{BASE_URL}/api/restaurant"


def get_filters() -> Dict:
    """获取筛选条件 GET /api/restaurant/filters"""
    try:
        res = requests.get(f"{RESTAURANT_BASE_URL}/filters")
        res.raise_for_status()
        data = res.json()
        print(f"[RestaurantAPI] GET /filters → {data}")
        return data
    except Exception as e:
        print(f"[RestaurantAPI] 获取筛选条件失败: {e}")
        return {"locations": [], "cuisines": [], "spice_levels": []}


def get_recommend(location: str = None, cuisine: str = None, spice_level: str = None) -> Dict:
    """随机推荐 GET /api/restaurant/recommend"""
    try:
        params = {}
        if location:
            params["location"] = location
        if cuisine:
            params["cuisine"] = cuisine
        if spice_level:
            params["spice_level"] = spice_level
        res = requests.get(f"{RESTAURANT_BASE_URL}/recommend", params=params)
        res.raise_for_status()
        data = res.json()
        print(f"[RestaurantAPI] GET /recommend → {data}")
        return data
    except Exception as e:
        print(f"[RestaurantAPI] 推荐失败: {e}")
        # 返回包含错误信息的数据结构
        return {
            "error": True,
            "message": "No matching restaurant found, please try other filters"
        }


def get_refresh(location: str = None, cuisine: str = None, spice_level: str = None) -> Dict:
    """刷新推荐 GET /api/restaurant/refresh"""
    try:
        params = {}
        if location:
            params["location"] = location
        if cuisine:
            params["cuisine"] = cuisine
        if spice_level:
            params["spice_level"] = spice_level
        res = requests.get(f"{RESTAURANT_BASE_URL}/refresh", params=params)
        res.raise_for_status()
        data = res.json()
        print(f"[RestaurantAPI] GET /refresh → {data}")
        return data
    except Exception as e:
        print(f"[RestaurantAPI] 刷新失败: {e}")
        return {
            "error": True,
            "message": "No matching restaurant found, please try other filters"
        }
