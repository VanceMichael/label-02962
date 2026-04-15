"""
沙画画布组件 - 带粒子系统和物理效果
"""

import math
import random
import logging
from typing import Optional, List

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QPointF, QTimer
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QImage,
    QMouseEvent, QPaintEvent, QResizeEvent, QRadialGradient,
    QPolygonF, QPainterPath
)

from models.brush import BrushType
from models.particle import SandParticle
from utils.validators import (
    validate_brush_size, validate_stamp_pattern,
    validate_gravity, validate_friction,
    validate_particle_count, validate_color_value,
    validate_qcolor, validate_file_path,
    BRUSH_SIZE_MIN, BRUSH_SIZE_MAX,
    STAMP_PATTERN_MIN, STAMP_PATTERN_MAX,
)

logger = logging.getLogger("sand_art.canvas")


class SandCanvas(QWidget):
    """沙画画布 - 带粒子系统和物理效果"""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("初始化沙画画布组件")
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.canvas_image: Optional[QImage] = None
        self.sand_density: Optional[QImage] = None  # 沙子密度图

        # 颜色
        self.sand_color = QColor(194, 168, 128)
        self.light_color = QColor(255, 250, 235)

        # 画笔
        self.brush_type = BrushType.FINGER
        self._brush_size = 15

        # 状态
        self.drawing = False
        self.last_point: Optional[QPoint] = None

        # 历史
        self.history: List[QImage] = []
        self.history_index = -1

        # 粒子系统
        self.particles: List[SandParticle] = []
        self.max_particles = 500  # 粒子数量上限，防止无限增长导致掉帧
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self._update_particles)
        self.particle_timer.start(30)

        # 重力
        self._gravity = 0.3
        self._friction = 0.95

        # 印章图案
        self._stamp_pattern = 0  # 0=圆, 1=星, 2=心, 3=叶

        self.setMouseTracking(True)

    # ==================== 属性访问器（带校验） ====================

    @property
    def brush_size(self) -> int:
        """获取画笔大小"""
        return self._brush_size

    @brush_size.setter
    def brush_size(self, value: int):
        """设置画笔大小（带校验）"""
        self._brush_size = validate_brush_size(value)

    @property
    def stamp_pattern(self) -> int:
        """获取印章图案索引"""
        return self._stamp_pattern

    @stamp_pattern.setter
    def stamp_pattern(self, value: int):
        """设置印章图案索引（带校验）"""
        self._stamp_pattern = validate_stamp_pattern(value)

    @property
    def gravity(self) -> float:
        """获取重力值"""
        return self._gravity

    @gravity.setter
    def gravity(self, value: float):
        """设置重力值（带校验）"""
        self._gravity = validate_gravity(value)

    @property
    def friction(self) -> float:
        """获取摩擦系数"""
        return self._friction

    @friction.setter
    def friction(self, value: float):
        """设置摩擦系数（带校验）"""
        self._friction = validate_friction(value)

    def showEvent(self, event):
        super().showEvent(event)
        if self.canvas_image is None:
            self.init_canvas()

    def init_canvas(self):
        """初始化画布"""
        logger.info(f"初始化画布，尺寸: {self.size().width()}x{self.size().height()}")
        self.canvas_image = QImage(self.size(), QImage.Format.Format_ARGB32)
        self.sand_density = QImage(self.size(), QImage.Format.Format_Grayscale8)
        self.fill_with_sand()
        self.save_history()

    def fill_with_sand(self):
        """用沙子填充画布"""
        if not self.canvas_image:
            logger.warning("画布未初始化，无法填充沙子")
            return
        logger.debug(f"填充沙子，颜色: {self.sand_color.name()}")
        self.canvas_image.fill(self.sand_color)
        if self.sand_density:
            self.sand_density.fill(QColor(255, 255, 255))  # 满沙

        # 添加纹理
        painter = QPainter(self.canvas_image)
        w, h = self.canvas_image.width(), self.canvas_image.height()
        for _ in range(w * h // 10):
            x, y = random.randint(0, w-1), random.randint(0, h-1)
            noise = random.randint(-20, 20)
            color = QColor(
                max(0, min(255, self.sand_color.red() + noise)),
                max(0, min(255, self.sand_color.green() + noise)),
                max(0, min(255, self.sand_color.blue() + noise))
            )
            painter.setPen(color)
            painter.drawPoint(x, y)
        painter.end()
        self.update()

    def clear_canvas(self):
        """清空画布（移除所有沙子）"""
        logger.info("清空画布")
        if self.canvas_image:
            self.canvas_image.fill(QColor(255, 255, 255))
            if self.sand_density:
                self.sand_density.fill(QColor(0, 0, 0))  # 无沙
            self.save_history()
            self.update()

    def reset_canvas(self):
        """重置画布（重新铺满沙子）"""
        logger.info("重置画布")
        self.fill_with_sand()
        self.save_history()

    def save_history(self):
        """保存历史记录"""
        if not self.canvas_image:
            return
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(self.canvas_image.copy())
        if len(self.history) > 30:
            self.history.pop(0)
        self.history_index = len(self.history) - 1
        logger.debug(f"保存历史记录，当前索引: {self.history_index}, 总数: {len(self.history)}")

    def undo(self):
        """撤销"""
        if self.history_index > 0:
            self.history_index -= 1
            self.canvas_image = self.history[self.history_index].copy()
            logger.debug(f"撤销操作，历史索引: {self.history_index}")
            self.update()
        else:
            logger.debug("无法撤销，已到最早历史")

    def redo(self):
        """重做"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.canvas_image = self.history[self.history_index].copy()
            logger.debug(f"重做操作，历史索引: {self.history_index}")
            self.update()
        else:
            logger.debug("无法重做，已到最新历史")

    def resizeEvent(self, event: QResizeEvent):
        """处理窗口大小变化"""
        logger.debug(f"窗口大小变化: {event.oldSize().width()}x{event.oldSize().height()} -> {event.size().width()}x{event.size().height()}")
        if self.canvas_image:
            old = self.canvas_image
            self.canvas_image = QImage(event.size(), QImage.Format.Format_ARGB32)
            self.canvas_image.fill(self.sand_color)
            painter = QPainter(self.canvas_image)
            painter.drawImage(0, 0, old)
            painter.end()

            self.sand_density = QImage(event.size(), QImage.Format.Format_Grayscale8)
            self.sand_density.fill(QColor(255, 255, 255))
        super().resizeEvent(event)

    def paintEvent(self, event: QPaintEvent):
        """绑定绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        gradient = QRadialGradient(self.width()/2, self.height()/2, max(self.width(), self.height())/2)
        gradient.setColorAt(0, self.light_color)
        gradient.setColorAt(1, QColor(230, 220, 200))
        painter.fillRect(self.rect(), gradient)

        # 画布
        if self.canvas_image:
            painter.drawImage(0, 0, self.canvas_image)

        # 粒子 - 批量绘制优化：按颜色分组减少 QPainter 状态切换
        if self.particles:
            painter.setPen(Qt.PenStyle.NoPen)
            # 按颜色 rgba 分组
            color_groups: dict[int, list[SandParticle]] = {}
            for p in self.particles:
                key = p.color.rgba()
                if key not in color_groups:
                    color_groups[key] = []
                color_groups[key].append(p)

            for rgba, group in color_groups.items():
                painter.setBrush(QBrush(group[0].color))
                for p in group:
                    painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)

        # 画笔预览
        if self.underMouse() and not self.drawing:
            pos = self.mapFromGlobal(self.cursor().pos())
            self._draw_brush_preview(painter, pos)

    def _draw_brush_preview(self, painter: QPainter, pos: QPoint):
        """绘制画笔预览"""
        painter.setPen(QPen(QColor(80, 80, 80, 120), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.brush_type == BrushType.PALM:
            painter.drawEllipse(pos, self.brush_size * 2, int(self.brush_size * 1.3))
        elif self.brush_type == BrushType.FIST:
            painter.drawEllipse(pos, int(self.brush_size * 1.5), int(self.brush_size * 1.5))
        elif self.brush_type == BrushType.RAKE:
            for i in range(-2, 3):
                painter.drawEllipse(QPoint(pos.x() + i * 15, pos.y()), 6, 6)
        elif self.brush_type == BrushType.COMB:
            for i in range(-4, 5):
                painter.drawLine(pos.x() + i * 6, pos.y() - 15, pos.x() + i * 6, pos.y() + 15)
        elif self.brush_type == BrushType.SPRAY:
            painter.drawEllipse(pos, self.brush_size * 2, self.brush_size * 2)
        elif self.brush_type == BrushType.STAMP:
            self._draw_stamp_preview(painter, pos)
        else:
            painter.drawEllipse(pos, self.brush_size, self.brush_size)

    def _draw_stamp_preview(self, painter: QPainter, pos: QPoint):
        """绘制印章预览"""
        s = self.brush_size
        pattern = self._stamp_pattern
        if pattern == 0:  # 圆
            painter.drawEllipse(pos, s, s)
        elif pattern == 1:  # 星
            self._draw_star(painter, pos, s, preview=True)
        elif pattern == 2:  # 心
            self._draw_heart(painter, pos, s, preview=True)
        elif pattern == 3:  # 叶
            self._draw_leaf(painter, pos, s, preview=True)
        else:
            # 默认回退到圆形
            logger.warning(f"未知印章图案索引: {pattern}，使用默认圆形")
            painter.drawEllipse(pos, s, s)

    # ==================== 鼠标事件 ====================

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.draw_at(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.drawing and self.last_point:
            self.draw_line(self.last_point, event.pos())
            self.last_point = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.last_point = None
            self.save_history()

    # ==================== 绘制方法 ====================

    def draw_line(self, start: QPoint, end: QPoint):
        """绘制线条（插值）"""
        dx, dy = end.x() - start.x(), end.y() - start.y()
        dist = math.sqrt(dx*dx + dy*dy)
        steps = max(1, int(dist / max(3, self.brush_size // 5)))
        for i in range(steps + 1):
            t = i / steps
            pt = QPoint(int(start.x() + dx*t), int(start.y() + dy*t))
            self.draw_at(pt)

    def draw_at(self, point: QPoint):
        """在指定位置绘制"""
        if not self.canvas_image:
            return

        painter = QPainter(self.canvas_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.brush_type == BrushType.FINGER:
            self._draw_finger(painter, point)
        elif self.brush_type == BrushType.PALM:
            self._draw_palm(painter, point)
        elif self.brush_type == BrushType.FIST:
            self._draw_fist(painter, point)
        elif self.brush_type == BrushType.RAKE:
            self._draw_rake(painter, point)
        elif self.brush_type == BrushType.COMB:
            self._draw_comb(painter, point)
        elif self.brush_type == BrushType.SPRAY:
            self._draw_spray(painter, point)
        elif self.brush_type == BrushType.STAMP:
            self._draw_stamp(painter, point)
        elif self.brush_type == BrushType.ERASER:
            self._draw_sand(painter, point)

        painter.end()
        # 不在此处调用 self.update()
        # mouseMoveEvent 和 particle_timer 已负责触发重绘，避免重复刷新

    # ==================== 画笔实现 ====================

    def _draw_finger(self, painter: QPainter, pt: QPoint):
        """手指画笔"""
        gradient = QRadialGradient(pt.x(), pt.y(), self.brush_size)
        gradient.setColorAt(0, self.light_color)
        gradient.setColorAt(0.6, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 200))
        gradient.setColorAt(1, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(pt, self.brush_size, self.brush_size)
        self._spawn_particles(pt, 3)

    def _draw_palm(self, painter: QPainter, pt: QPoint):
        """手掌画笔"""
        sx, sy = self.brush_size * 2, int(self.brush_size * 1.3)
        gradient = QRadialGradient(pt.x(), pt.y(), sx)
        gradient.setColorAt(0, self.light_color)
        gradient.setColorAt(0.7, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 180))
        gradient.setColorAt(1, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(pt, sx, sy)
        self._spawn_particles(pt, 8)

    def _draw_fist(self, painter: QPainter, pt: QPoint):
        """拳头画笔"""
        s = int(self.brush_size * 1.5)
        gradient = QRadialGradient(pt.x(), pt.y(), s)
        gradient.setColorAt(0, self.light_color)
        gradient.setColorAt(0.5, self.light_color)
        gradient.setColorAt(1, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(pt, s, s)
        self._spawn_particles(pt, 10, strong=True)

    def _draw_rake(self, painter: QPainter, pt: QPoint):
        """耙子画笔"""
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(-2, 3):
            cx = pt.x() + i * 15
            gradient = QRadialGradient(cx, pt.y(), 8)
            gradient.setColorAt(0, self.light_color)
            gradient.setColorAt(1, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 0))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QPoint(cx, pt.y()), 8, 8)
        self._spawn_particles(pt, 5)

    def _draw_comb(self, painter: QPainter, pt: QPoint):
        """梳子画笔"""
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(-4, 5):
            cx = pt.x() + i * 6
            gradient = QRadialGradient(cx, pt.y(), 4)
            gradient.setColorAt(0, self.light_color)
            gradient.setColorAt(1, QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), 0))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QPoint(cx, pt.y()), 4, 20)
        self._spawn_particles(pt, 3)

    def _draw_spray(self, painter: QPainter, pt: QPoint):
        """喷洒画笔"""
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.brush_size * 2)
            x = pt.x() + r * math.cos(angle)
            y = pt.y() + r * math.sin(angle)
            size = random.uniform(1, 4)
            alpha = int(255 * (1 - r / (self.brush_size * 2)))
            painter.setBrush(QBrush(QColor(self.light_color.red(), self.light_color.green(), self.light_color.blue(), alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)
        self._spawn_particles(pt, 15, spray=True)

    def _draw_stamp(self, painter: QPainter, pt: QPoint):
        """印章画笔"""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.light_color))
        s = self.brush_size
        pattern = self._stamp_pattern
        if pattern == 0:
            painter.drawEllipse(pt, s, s)
        elif pattern == 1:
            self._draw_star(painter, pt, s)
        elif pattern == 2:
            self._draw_heart(painter, pt, s)
        elif pattern == 3:
            self._draw_leaf(painter, pt, s)
        else:
            # 默认回退到圆形
            painter.drawEllipse(pt, s, s)
        self._spawn_particles(pt, 8)

    def _draw_star(self, painter: QPainter, pt: QPoint, size: int, preview: bool = False):
        """绘制星形"""
        points = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            r = size if i % 2 == 0 else size * 0.4
            points.append(QPointF(pt.x() + r * math.cos(angle), pt.y() + r * math.sin(angle)))
        painter.drawPolygon(QPolygonF(points))

    def _draw_heart(self, painter: QPainter, pt: QPoint, size: int, preview: bool = False):
        """绘制心形"""
        path = QPainterPath()
        s = size * 0.8
        path.moveTo(pt.x(), pt.y() + s * 0.3)
        path.cubicTo(pt.x() - s, pt.y() - s * 0.5, pt.x() - s * 0.5, pt.y() - s, pt.x(), pt.y() - s * 0.3)
        path.cubicTo(pt.x() + s * 0.5, pt.y() - s, pt.x() + s, pt.y() - s * 0.5, pt.x(), pt.y() + s * 0.3)
        painter.drawPath(path)

    def _draw_leaf(self, painter: QPainter, pt: QPoint, size: int, preview: bool = False):
        """绘制叶形"""
        path = QPainterPath()
        s = size
        path.moveTo(pt.x(), pt.y() - s)
        path.quadTo(pt.x() + s * 0.8, pt.y(), pt.x(), pt.y() + s)
        path.quadTo(pt.x() - s * 0.8, pt.y(), pt.x(), pt.y() - s)
        painter.drawPath(path)

    def _draw_sand(self, painter: QPainter, pt: QPoint):
        """添沙画笔"""
        for _ in range(int(self.brush_size * 2)):
            dx = random.gauss(0, self.brush_size / 2.5)
            dy = random.gauss(0, self.brush_size / 2.5)
            x, y = int(pt.x() + dx), int(pt.y() + dy)
            if 0 <= x < self.canvas_image.width() and 0 <= y < self.canvas_image.height():
                noise = random.randint(-20, 20)
                color = QColor(
                    max(0, min(255, self.sand_color.red() + noise)),
                    max(0, min(255, self.sand_color.green() + noise)),
                    max(0, min(255, self.sand_color.blue() + noise))
                )
                self.canvas_image.setPixelColor(x, y, color)

    # ==================== 粒子系统 ====================

    def _spawn_particles(self, pt: QPoint, count: int, strong: bool = False, spray: bool = False):
        """生成沙粒粒子
        
        Args:
            pt: 生成位置
            count: 粒子数量
            strong: 是否强力（如拳头）
            spray: 是否喷洒模式
        """
        count = validate_particle_count(count)
        # 粒子数量上限保护：超出上限时跳过生成
        remaining = self.max_particles - len(self.particles)
        if remaining <= 0:
            return
        count = min(count, remaining)

        sand_r, sand_g, sand_b = self.sand_color.red(), self.sand_color.green(), self.sand_color.blue()
        px, py = pt.x(), pt.y()

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6) if strong else random.uniform(1, 3)
            if spray:
                speed = random.uniform(3, 8)

            # 粒子颜色基于沙子颜色，添加少量随机变化模拟自然纹理
            noise = random.randint(-10, 10)
            self.particles.append(SandParticle(
                x=px + random.uniform(-5, 5),
                y=py + random.uniform(-5, 5),
                vx=speed * math.cos(angle),
                vy=speed * math.sin(angle) - random.uniform(1, 3),
                size=random.uniform(1, 3),
                color=QColor(
                    validate_color_value(sand_r + noise),
                    validate_color_value(sand_g + noise),
                    validate_color_value(sand_b + noise),
                    220
                ),
                life=random.randint(30, 60)
            ))

    def _update_particles(self):
        """更新粒子物理（优化：单次遍历 + 原地过滤，避免 O(n²) 删除）"""
        alive = []
        gravity = self._gravity
        friction = self._friction
        w = self.width()
        h = self.height()
        canvas = self.canvas_image
        canvas_w = canvas.width() if canvas else 0

        for p in self.particles:
            # 重力 + 摩擦
            p.vy = (p.vy + gravity) * friction
            p.vx *= friction
            # 移动
            p.x += p.vx
            p.y += p.vy
            p.life -= 1

            # 出界或生命结束 → 丢弃
            if p.x < 0 or p.x > w or p.life <= 0:
                continue

            # 底部碰撞 - 沙子堆积
            if p.y >= h - p.size:
                p.y = h - p.size
                p.vy *= -0.3
                p.vx *= 0.8
                if abs(p.vy) < 0.5:
                    # 沙子落地，绘制到画布
                    px = int(p.x)
                    if canvas and 0 <= px < canvas_w:
                        canvas.setPixelColor(px, int(p.y), p.color)
                    continue  # 落地粒子不保留

            alive.append(p)

        self.particles = alive

        if self.particles:
            self.update()

    # ==================== 导出 ====================

    def save_image(self, path: str):
        """保存图像到文件"""
        if not self.canvas_image:
            logger.error("画布未初始化，无法保存")
            return False
        
        try:
            validated_path = validate_file_path(path)
            success = self.canvas_image.save(validated_path)
            if success:
                logger.info(f"图像保存成功: {validated_path}")
            else:
                logger.error(f"图像保存失败: {validated_path}")
            return success
        except Exception as e:
            logger.exception(f"保存图像时发生错误: {e}")
            return False
