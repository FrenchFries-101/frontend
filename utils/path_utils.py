# utils/path_utils.py

import os
import sys

def resource_path(relative_path):
    """
    兼容：
    - 本地运行
    - PyInstaller 打包
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # 项目根目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)