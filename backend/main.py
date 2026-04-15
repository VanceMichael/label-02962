#!/usr/bin/env python3
"""
沙画台 - Sand Art Table
一个模拟真实沙画创作的 Qt 应用程序

入口文件
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

from utils.logger import setup_logger
from windows.main_window import SandArtWindow


def main():
    """程序入口"""
    # 初始化日志系统
    logger = setup_logger(
        name="sand_art",
        level=logging.INFO,
        console_output=True
    )
    
    logger.info("=" * 50)
    logger.info("沙画台应用程序启动")
    logger.info("=" * 50)
    
    try:
        app = QApplication(sys.argv)
        logger.info("Qt 应用程序初始化成功")
        
        window = SandArtWindow()
        logger.info("主窗口创建成功")
        
        window.show()
        logger.info("主窗口已显示，进入事件循环")
        
        exit_code = app.exec()
        logger.info(f"应用程序退出，退出码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception(f"应用程序发生致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
