"""
沙粒粒子数据模型
"""

from dataclasses import dataclass
from PyQt6.QtGui import QColor


@dataclass(slots=True)
class SandParticle:
    """沙粒粒子
    
    Attributes:
        x: 粒子X坐标
        y: 粒子Y坐标
        vx: X方向速度
        vy: Y方向速度
        size: 粒子大小
        color: 粒子颜色
        life: 生命周期（帧数）
    """
    x: float
    y: float
    vx: float
    vy: float
    size: float
    color: QColor
    life: int
