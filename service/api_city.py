# service/api_city.py
# 城市卡片模块 —— 天气 & 景点 API

import requests
from typing import Dict, List

from service.api import BASE_URL

CITY_BASE_URL = f"{BASE_URL}/api/city"


def get_weather(month: str = None) -> Dict:
    """获取天气信息 GET /api/city/weather?month=April"""
    try:
        params = {}
        if month:
            params["month"] = month
        res = requests.get(f"{CITY_BASE_URL}/weather", params=params)
        res.raise_for_status()
        data = res.json()
        print(f"[CityAPI] GET /weather → {data}")
        return data
    except Exception as e:
        print(f"[CityAPI] 获取天气失败: {e}")
        return {"month": "", "description": "Weather data unavailable", "icon": ""}


def get_sights() -> List:
    """获取景点列表 GET /api/city/sights"""
    try:
        res = requests.get(f"{CITY_BASE_URL}/sights")
        res.raise_for_status()
        data = res.json()
        print(f"[CityAPI] GET /sights → {data}")
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[CityAPI] 获取景点失败: {e}")
        return []
