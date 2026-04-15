"""
画笔类型定义
"""

from enum import Enum


class BrushType(Enum):
    """画笔工具类型枚举"""
    FINGER = "手指"
    PALM = "手掌"
    FIST = "拳头"
    RAKE = "耙子"
    COMB = "梳子"
    SPRAY = "喷洒"
    STAMP = "印章"
    ERASER = "添沙"
