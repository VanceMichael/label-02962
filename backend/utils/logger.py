"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 全局日志器缓存
_loggers: dict = {}


def setup_logger(
    name: str = "sand_art",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """设置并返回日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        console_output: 是否输出到控制台
        
    Returns:
        配置好的日志器
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 防止重复添加处理器
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def get_logger(name: str = "sand_art") -> logging.Logger:
    """获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)
