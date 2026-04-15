"""
工具按钮组件
"""

from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtGui import QFont


class ToolButton(QPushButton):
    """工具按钮 - 带图标和文字的可选中按钮"""
    
    def __init__(self, text: str, icon: str, parent=None):
        """初始化工具按钮
        
        Args:
            text: 按钮文字
            icon: 按钮图标（emoji）
            parent: 父组件
        """
        super().__init__(parent)
        self.setText(f"{icon}\n{text}")
        self.setCheckable(True)
        self.setFixedSize(44, 50)  # 固定尺寸确保一致性
        self.setFont(QFont("Arial", 9))
