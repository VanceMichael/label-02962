"""
沙画台主窗口
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QColorDialog, QFileDialog,
    QGroupBox, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

from models.brush import BrushType
from widgets.canvas import SandCanvas
from widgets.tool_button import ToolButton
from utils.validators import (
    validate_brush_size, validate_stamp_pattern,
    validate_color_string, validate_qcolor,
    ValidationError,
    BRUSH_SIZE_MIN, BRUSH_SIZE_MAX,
    STAMP_PATTERN_MIN, STAMP_PATTERN_MAX,
)

logger = logging.getLogger("sand_art.window")


class SandArtWindow(QMainWindow):
    """沙画台主窗口"""

    def __init__(self):
        super().__init__()
        logger.debug("初始化主窗口")
        self.setWindowTitle("沙画台 - Sand Art Table")
        self.setMinimumSize(950, 650)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 左侧面板
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # 画布
        self.canvas = SandCanvas()
        self.canvas.setStyleSheet("border: 2px solid #555; border-radius: 8px;")
        main_layout.addWidget(self.canvas, 1)

        # 右侧面板
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel)

        self.statusBar().showMessage("就绪 - 在画布上拖动鼠标绘制沙画")
        self._apply_style()

    def _create_left_panel(self) -> QWidget:
        """创建左侧工具面板"""
        panel = QFrame()
        panel.setFixedWidth(230)  # 增加宽度以容纳按钮
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)  # 面板本身无边距

        # 画笔工具 - 4x2网格
        tools_group = QGroupBox("画笔工具")
        tools_layout = QGridLayout(tools_group)
        tools_layout.setHorizontalSpacing(8)   # 水平间距
        tools_layout.setVerticalSpacing(8)     # 垂直间距
        tools_layout.setContentsMargins(16, 22, 16, 12)  # 左右边距一致（增大）

        self.tool_buttons = {}
        tools = [
            (BrushType.FINGER, "👆", "手指"),
            (BrushType.PALM, "🖐", "手掌"),
            (BrushType.FIST, "✊", "拳头"),
            (BrushType.RAKE, "🪥", "耙子"),
            (BrushType.COMB, "〰", "梳子"),
            (BrushType.SPRAY, "💨", "喷洒"),
            (BrushType.STAMP, "⭐", "印章"),
            (BrushType.ERASER, "✨", "添沙"),
        ]

        for i, (brush, icon, name) in enumerate(tools):
            btn = ToolButton(name, icon)
            btn.clicked.connect(lambda checked, b=brush: self._select_tool(b))
            self.tool_buttons[brush] = btn
            tools_layout.addWidget(btn, i // 4, i % 4)

        self.tool_buttons[BrushType.FINGER].setChecked(True)
        layout.addWidget(tools_group)

        # 印章图案
        stamp_group = QGroupBox("印章图案")
        stamp_layout = QHBoxLayout(stamp_group)
        stamp_layout.setSpacing(8)   # 按钮间距
        stamp_layout.setContentsMargins(16, 22, 16, 12)  # 左右边距一致

        self.stamp_buttons = []
        stamps = [("⚪", 0), ("⭐", 1), ("❤", 2), ("🍃", 3)]
        for icon, idx in stamps:
            btn = QPushButton(icon)
            btn.setFixedSize(44, 35)  # 固定尺寸与工具按钮一致
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self._select_stamp(i))
            self.stamp_buttons.append(btn)
            stamp_layout.addWidget(btn)
        self.stamp_buttons[0].setChecked(True)
        layout.addWidget(stamp_group)

        # 画笔大小（使用校验常量设置范围）
        size_group = QGroupBox(f"画笔大小 ({BRUSH_SIZE_MIN}-{BRUSH_SIZE_MAX})")
        size_layout = QVBoxLayout(size_group)
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(BRUSH_SIZE_MIN, BRUSH_SIZE_MAX)
        self.size_slider.setValue(15)
        self.size_slider.valueChanged.connect(self._on_size_change)
        self.size_label = QLabel("15")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        layout.addWidget(size_group)

        # 操作
        ops_group = QGroupBox("操作")
        ops_layout = QVBoxLayout(ops_group)
        for text, func in [("↩ 撤销", self._undo), ("↪ 重做", self._redo),
                           ("🗑 清空", self._clear), ("🔄 重铺", self._reset)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            ops_layout.addWidget(btn)
        layout.addWidget(ops_group)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        """创建右侧设置面板"""
        panel = QFrame()
        panel.setFixedWidth(160)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        # 沙子颜色
        sand_group = QGroupBox("沙子颜色")
        sand_layout = QVBoxLayout(sand_group)
        self.sand_preview = QFrame()
        self.sand_preview.setFixedHeight(30)
        self.sand_preview.setStyleSheet("background: #c2a880; border-radius: 4px;")
        sand_layout.addWidget(self.sand_preview)

        presets = QHBoxLayout()
        presets.setSpacing(6)
        for c in ["#c2a880", "#d4b896", "#a89070", "#e8d4b8"]:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background: {c}; border-radius: 4px; border: 1px solid #666;")
            btn.clicked.connect(lambda _, col=c: self._set_sand_color(col))
            presets.addWidget(btn)
        sand_layout.addLayout(presets)

        sand_btn = QPushButton("自定义")
        sand_btn.clicked.connect(self._choose_sand_color)
        sand_layout.addWidget(sand_btn)
        layout.addWidget(sand_group)

        # 画笔颜色
        light_group = QGroupBox("画笔颜色")
        light_layout = QVBoxLayout(light_group)
        self.light_preview = QFrame()
        self.light_preview.setFixedHeight(30)
        self.light_preview.setStyleSheet("background: #fffaeb; border-radius: 4px;")
        light_layout.addWidget(self.light_preview)

        light_presets = QHBoxLayout()
        light_presets.setSpacing(6)
        for c in ["#ffe4c4", "#ffffff", "#ffd4a0", "#d0e8ff"]:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background: {c}; border-radius: 4px; border: 1px solid #666;")
            btn.clicked.connect(lambda _, col=c: self._set_light_color(col))
            light_presets.addWidget(btn)
        light_layout.addLayout(light_presets)

        light_btn = QPushButton("自定义")
        light_btn.clicked.connect(self._choose_light_color)
        light_layout.addWidget(light_btn)
        layout.addWidget(light_group)

        # 导出
        save_group = QGroupBox("导出")
        save_layout = QVBoxLayout(save_group)
        save_btn = QPushButton("💾 保存图片")
        save_btn.clicked.connect(self._save_image)
        save_layout.addWidget(save_btn)
        layout.addWidget(save_group)

        layout.addStretch()
        return panel

    # ==================== 工具选择 ====================

    def _select_tool(self, brush: BrushType):
        """选择画笔工具"""
        logger.info(f"切换画笔工具: {brush.value}")
        for b, btn in self.tool_buttons.items():
            btn.setChecked(b == brush)
        self.canvas.brush_type = brush
        self.statusBar().showMessage(f"当前工具: {brush.value}")

    def _select_stamp(self, idx: int):
        """选择印章图案"""
        stamp_names = ["圆形", "星形", "心形", "叶形"]
        try:
            validated_idx = validate_stamp_pattern(idx)
            logger.debug(f"切换印章图案: {stamp_names[validated_idx]}")
            for i, btn in enumerate(self.stamp_buttons):
                btn.setChecked(i == validated_idx)
            self.canvas.stamp_pattern = validated_idx
        except ValidationError as e:
            logger.error(f"印章图案选择失败: {e}")

    def _on_size_change(self, val: int):
        """画笔大小变化"""
        try:
            validated_val = validate_brush_size(val)
            logger.debug(f"画笔大小调整: {validated_val}")
            self.size_label.setText(str(validated_val))
            self.canvas.brush_size = validated_val
        except ValidationError as e:
            logger.error(f"画笔大小设置失败: {e}")

    # ==================== 操作 ====================

    def _undo(self):
        """撤销"""
        self.canvas.undo()

    def _redo(self):
        """重做"""
        self.canvas.redo()

    def _clear(self):
        """清空画布"""
        self.canvas.clear_canvas()

    def _reset(self):
        """重置画布"""
        self.canvas.reset_canvas()

    # ==================== 颜色设置 ====================

    def _set_sand_color(self, color: str):
        """设置沙子颜色"""
        try:
            validated_color = validate_color_string(color)
            logger.info(f"设置沙子颜色: {validated_color}")
            qcolor = validate_qcolor(validated_color)
            self.canvas.sand_color = qcolor
            self.sand_preview.setStyleSheet(f"background: {validated_color}; border-radius: 4px;")
            self.canvas.fill_with_sand()
        except ValidationError as e:
            logger.error(f"沙子颜色设置失败: {e}")
            self.statusBar().showMessage(f"颜色设置失败: {e}")

    def _set_light_color(self, color: str):
        """设置画笔颜色"""
        try:
            validated_color = validate_color_string(color)
            logger.info(f"设置画笔颜色: {validated_color}")
            qcolor = validate_qcolor(validated_color)
            self.canvas.light_color = qcolor
            self.light_preview.setStyleSheet(f"background: {validated_color}; border-radius: 4px;")
        except ValidationError as e:
            logger.error(f"画笔颜色设置失败: {e}")
            self.statusBar().showMessage(f"颜色设置失败: {e}")

    def _choose_sand_color(self):
        """选择自定义沙子颜色"""
        dialog = QColorDialog(self.canvas.sand_color, self)
        dialog.setWindowTitle("选择沙子颜色")
        if dialog.exec():
            self._set_sand_color(dialog.currentColor().name())

    def _choose_light_color(self):
        """选择自定义画笔颜色"""
        dialog = QColorDialog(self.canvas.light_color, self)
        dialog.setWindowTitle("选择画笔颜色")
        if dialog.exec():
            self._set_light_color(dialog.currentColor().name())

    # ==================== 导出 ====================

    def _save_image(self):
        """保存图片"""
        logger.debug("打开保存图片对话框")
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", "sand_art.png", "PNG (*.png);;JPEG (*.jpg)")
        if path:
            logger.info(f"用户选择保存路径: {path}")
            self.canvas.save_image(path)
            self.statusBar().showMessage(f"已保存: {path}")
        else:
            logger.debug("用户取消保存操作")

    # ==================== 样式 ====================

    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow { background: #1e1e1e; }
            QGroupBox {
                color: #ddd; font-weight: bold;
                border: 1px solid #444; border-radius: 6px;
                margin-top: 10px; padding-top: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton {
                background: #3a3a3a; color: #eee;
                border: 1px solid #555; border-radius: 5px;
                padding: 6px 10px; font-size: 12px;
            }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:pressed { background: #2a2a2a; }
            QPushButton:checked { background: #5588bb; border-color: #6699cc; }
            QSlider::groove:horizontal { height: 6px; background: #333; border-radius: 3px; }
            QSlider::handle:horizontal { background: #5588bb; width: 14px; margin: -4px 0; border-radius: 7px; }
            QLabel { color: #ccc; font-size: 12px; }
            QStatusBar { background: #2a2a2a; color: #aaa; }
        """)
