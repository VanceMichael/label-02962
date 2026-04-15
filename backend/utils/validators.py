"""
参数校验模块
"""

import re
import logging
from typing import Union, Optional
from PyQt6.QtGui import QColor

logger = logging.getLogger("sand_art.validators")


class ValidationError(Exception):
    """参数校验异常"""
    pass


# ==================== 常量定义 ====================

# 画笔大小范围
BRUSH_SIZE_MIN = 1
BRUSH_SIZE_MAX = 100

# 印章图案索引范围
STAMP_PATTERN_MIN = 0
STAMP_PATTERN_MAX = 3

# 物理参数范围
GRAVITY_MIN = 0.0
GRAVITY_MAX = 2.0
FRICTION_MIN = 0.0
FRICTION_MAX = 1.0

# 粒子参数范围
PARTICLE_COUNT_MIN = 0
PARTICLE_COUNT_MAX = 100
PARTICLE_LIFE_MIN = 1
PARTICLE_LIFE_MAX = 200

# 历史记录最大数量
HISTORY_MAX_SIZE = 50

# 颜色值范围
COLOR_VALUE_MIN = 0
COLOR_VALUE_MAX = 255


# ==================== 校验函数 ====================

def validate_brush_size(size: int) -> int:
    """校验画笔大小
    
    Args:
        size: 画笔大小
        
    Returns:
        校验后的画笔大小（自动修正到有效范围）
        
    Raises:
        ValidationError: 如果输入类型不正确
    """
    if not isinstance(size, (int, float)):
        logger.error(f"画笔大小类型错误: {type(size)}, 期望 int")
        raise ValidationError(f"画笔大小必须是数字，收到: {type(size).__name__}")
    
    size = int(size)
    if size < BRUSH_SIZE_MIN:
        logger.warning(f"画笔大小 {size} 小于最小值 {BRUSH_SIZE_MIN}，已修正")
        return BRUSH_SIZE_MIN
    if size > BRUSH_SIZE_MAX:
        logger.warning(f"画笔大小 {size} 大于最大值 {BRUSH_SIZE_MAX}，已修正")
        return BRUSH_SIZE_MAX
    
    return size


def validate_stamp_pattern(pattern: int) -> int:
    """校验印章图案索引
    
    Args:
        pattern: 印章图案索引
        
    Returns:
        校验后的索引（自动修正到有效范围）
        
    Raises:
        ValidationError: 如果输入类型不正确
    """
    if not isinstance(pattern, (int, float)):
        logger.error(f"印章图案索引类型错误: {type(pattern)}")
        raise ValidationError(f"印章图案索引必须是数字，收到: {type(pattern).__name__}")
    
    pattern = int(pattern)
    if pattern < STAMP_PATTERN_MIN:
        logger.warning(f"印章图案索引 {pattern} 小于最小值 {STAMP_PATTERN_MIN}，已修正")
        return STAMP_PATTERN_MIN
    if pattern > STAMP_PATTERN_MAX:
        logger.warning(f"印章图案索引 {pattern} 大于最大值 {STAMP_PATTERN_MAX}，已修正")
        return STAMP_PATTERN_MAX
    
    return pattern


def validate_gravity(gravity: float) -> float:
    """校验重力值
    
    Args:
        gravity: 重力值
        
    Returns:
        校验后的重力值
    """
    if not isinstance(gravity, (int, float)):
        logger.error(f"重力值类型错误: {type(gravity)}")
        raise ValidationError(f"重力值必须是数字，收到: {type(gravity).__name__}")
    
    gravity = float(gravity)
    if gravity < GRAVITY_MIN:
        logger.warning(f"重力值 {gravity} 小于最小值 {GRAVITY_MIN}，已修正")
        return GRAVITY_MIN
    if gravity > GRAVITY_MAX:
        logger.warning(f"重力值 {gravity} 大于最大值 {GRAVITY_MAX}，已修正")
        return GRAVITY_MAX
    
    return gravity


def validate_friction(friction: float) -> float:
    """校验摩擦系数
    
    Args:
        friction: 摩擦系数
        
    Returns:
        校验后的摩擦系数
    """
    if not isinstance(friction, (int, float)):
        logger.error(f"摩擦系数类型错误: {type(friction)}")
        raise ValidationError(f"摩擦系数必须是数字，收到: {type(friction).__name__}")
    
    friction = float(friction)
    if friction < FRICTION_MIN:
        logger.warning(f"摩擦系数 {friction} 小于最小值 {FRICTION_MIN}，已修正")
        return FRICTION_MIN
    if friction > FRICTION_MAX:
        logger.warning(f"摩擦系数 {friction} 大于最大值 {FRICTION_MAX}，已修正")
        return FRICTION_MAX
    
    return friction


def validate_particle_count(count: int) -> int:
    """校验粒子数量
    
    Args:
        count: 粒子数量
        
    Returns:
        校验后的粒子数量
    """
    if not isinstance(count, (int, float)):
        logger.error(f"粒子数量类型错误: {type(count)}")
        raise ValidationError(f"粒子数量必须是数字，收到: {type(count).__name__}")
    
    count = int(count)
    if count < PARTICLE_COUNT_MIN:
        return PARTICLE_COUNT_MIN
    if count > PARTICLE_COUNT_MAX:
        logger.warning(f"粒子数量 {count} 大于最大值 {PARTICLE_COUNT_MAX}，已修正")
        return PARTICLE_COUNT_MAX
    
    return count


def validate_color_string(color: str) -> str:
    """校验颜色字符串格式
    
    Args:
        color: 颜色字符串（支持 #RRGGBB 或 #RGB 格式）
        
    Returns:
        校验后的颜色字符串
        
    Raises:
        ValidationError: 如果颜色格式不正确
    """
    if not isinstance(color, str):
        logger.error(f"颜色值类型错误: {type(color)}")
        raise ValidationError(f"颜色值必须是字符串，收到: {type(color).__name__}")
    
    color = color.strip()
    
    # 支持 #RRGGBB 或 #RGB 格式
    pattern = r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$'
    if not re.match(pattern, color):
        logger.error(f"颜色格式无效: {color}")
        raise ValidationError(f"颜色格式无效: {color}，期望格式: #RRGGBB 或 #RGB")
    
    return color


def validate_color_value(value: int) -> int:
    """校验单个颜色分量值 (0-255)
    
    Args:
        value: 颜色分量值
        
    Returns:
        校验后的颜色值
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"颜色分量必须是数字，收到: {type(value).__name__}")
    
    value = int(value)
    return max(COLOR_VALUE_MIN, min(COLOR_VALUE_MAX, value))


def validate_qcolor(color: Union[QColor, str, None]) -> Optional[QColor]:
    """校验并转换为 QColor
    
    Args:
        color: 颜色值（QColor、字符串或 None）
        
    Returns:
        QColor 对象或 None
        
    Raises:
        ValidationError: 如果颜色无效
    """
    if color is None:
        return None
    
    if isinstance(color, QColor):
        if not color.isValid():
            logger.error("QColor 对象无效")
            raise ValidationError("无效的 QColor 对象")
        return color
    
    if isinstance(color, str):
        validated_str = validate_color_string(color)
        qcolor = QColor(validated_str)
        if not qcolor.isValid():
            logger.error(f"无法创建有效的 QColor: {color}")
            raise ValidationError(f"无法创建有效的颜色: {color}")
        return qcolor
    
    logger.error(f"不支持的颜色类型: {type(color)}")
    raise ValidationError(f"不支持的颜色类型: {type(color).__name__}")


def validate_file_path(path: str, allowed_extensions: tuple = ('.png', '.jpg', '.jpeg')) -> str:
    """校验文件路径
    
    Args:
        path: 文件路径
        allowed_extensions: 允许的文件扩展名
        
    Returns:
        校验后的文件路径
        
    Raises:
        ValidationError: 如果路径无效
    """
    if not isinstance(path, str):
        logger.error(f"文件路径类型错误: {type(path)}")
        raise ValidationError(f"文件路径必须是字符串，收到: {type(path).__name__}")
    
    path = path.strip()
    if not path:
        logger.error("文件路径为空")
        raise ValidationError("文件路径不能为空")
    
    # 检查扩展名
    lower_path = path.lower()
    if not any(lower_path.endswith(ext) for ext in allowed_extensions):
        logger.warning(f"文件扩展名不在允许列表中: {path}")
        # 不抛出异常，只记录警告
    
    return path


def validate_positive_int(value: int, name: str = "参数") -> int:
    """校验正整数
    
    Args:
        value: 要校验的值
        name: 参数名称（用于错误信息）
        
    Returns:
        校验后的正整数
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name}必须是数字，收到: {type(value).__name__}")
    
    value = int(value)
    if value < 0:
        logger.warning(f"{name} {value} 为负数，已修正为 0")
        return 0
    
    return value
