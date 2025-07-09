from __future__ import annotations

import random
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer
import numpy as np


class Ball:
    def __init__(self, x: float, y: float, radius, color, speed_x, speed_y):
        self.position = np.array((x, y))
        self.radius = radius
        self.mass = radius * radius  # 质量
        self.velocity = np.array((speed_x, speed_y))
        self.color = color

    def move(self):
        self.position = self.position + self.velocity

    def collide_with_wall(self, width, height):
        if self.position[0] - self.radius <= 0:
            self.velocity[0] = -self.velocity[0]
            self.position[0] = 2 * self.radius - self.position[0]
        if self.position[0] + self.radius >= width:
            self.velocity[0] = -self.velocity[0]
            self.position[0] = 2 * width - 2 * self.radius - self.position[0]
        if self.position[1] - self.radius <= 0:
            self.velocity[1] = -self.velocity[1]
            self.position[1] = 2 * self.radius - self.position[1]
        if self.position[1] + self.radius >= height:
            self.velocity[1] = -self.velocity[1]
            self.position[1] = 2 * height - 2 * self.radius - self.position[1]

    def collide_with_ball(self, other: Ball):
        """
        弹性碰撞，无能量损失。
        双轴碰撞：两个小球球心连线方向上的速度满足动量守恒，垂直球心连线方向的速度保持不变
        当前用到了numpy进行向量计算

        当前算法的问题：
        1、当前位置并不是实际碰撞位置，而是属于碰撞后的小球继续沿碰撞前方向运动的的位置，
        球心连线方向并不等于实际碰撞时球心连线的方向，导致计算的碰撞后的速度与实际碰撞后速度不相同
        2、小球的当前位置不等于实际运动位置

        现象：两个小球连在一起，一直转圈圈，甚至完全重叠

        可选的解决方案：
        1、最优精确的解决方案：计算出两个小球的实际碰撞位置，先计算出到达碰撞位置所需时间，再计算碰撞位置，然后重新计算碰撞后的速度和位置
        2、当前解决方案：按照碰撞后的速度连续移动多次，直到两个小球无碰撞为止

        参考博客链接：https://www.kai666666.com/2020/07/28/Canvas%E7%B3%BB%E5%88%97%EF%BC%8814%EF%BC%89%EF%BC%9A%E5%AE%9E%E6%88%98-%E5%B0%8F%E7%90%83%E7%A2%B0%E6%92%9E/
        https://cloud.tencent.com/developer/article/1025993
        :param other: 另一个小球
        """
        distance = sum(np.power(self.position - other.position, 2))
        r = (self.radius + other.radius) ** 2
        if distance <= r:
            v1 = self.velocity
            v2 = other.velocity
            m1 = self.mass
            m2 = other.mass
            m = m1 + m2
            dm = m1 - m2
            wx = self.position - other.position
            wy = np.array((wx[1], -wx[0]))
            v1wx = np.dot(v1, wx) * wx  # 球1在球心连线方向上的速度
            v1wy = np.dot(v1, wy) * wy  # 球2
            v2wx = np.dot(v2, wx) * wx
            v2wy = np.dot(v2, wy) * wy

            u1wx = (dm * v1wx + 2 * m2 * v2wx) / m
            u2wx = v1wx - v2wx + u1wx

            self.velocity = (u1wx + v1wy) / distance
            other.velocity = (u2wx + v2wy) / distance

            while sum(np.power(self.position - other.position, 2)) < r:
                self.position = self.position + self.velocity
                other.position = other.position + other.velocity


class BallAnimation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ball Collision Simulation")
        self.resize(800, 600)

        self.balls = [
            # Ball(300, 300, 20, QColor(255, 0, 0), 0, random.randint(1, 5)),
            # Ball(300, 100, 20, QColor(0, 255, 0), 0, random.randint(1, 5)),
            # Ball(500, 150, 20, QColor(0, 0, 255), random.randint(1, 5), 0),
            # Ball(400, 150, 20, QColor(0, 255, 255), random.randint(1, 5), 0),
            # Ball(300, 500, 35, QColor(0, 0, 0), random.randint(0, 5), random.randint(0, 5)),
            # Ball(100, 100, 40, QColor(255, 255, 255), random.randint(0, 5), random.randint(0, 5)),
            # Ball(200, 200, 25, QColor(255, 0, 255), random.randint(0, 5), random.randint(0, 5)),
            Ball(500, 500, 25, QColor(255, 255, 0), 0, 5),
            Ball(500, 300, 100, QColor(255, 255, 255), 0, 0),
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event.key() == Qt.Key_Space:
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start(16)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        p0 = np.array((event.pos().x(), event.pos().y()))
        for ball in self.balls:
            if sum(np.power(ball.position - p0, 2)) <= ball.radius**2:
                if event.buttons() == Qt.LeftButton:
                    ball.velocity = ball.velocity * (2**0.5)  # 左键加速至2倍
                elif event.buttons() == Qt.RightButton:
                    ball.velocity = ball.velocity / (2**0.5)  # 右键减速至1/2
                break

    def update_animation(self):
        for ball in self.balls:
            ball.move()
            ball.collide_with_wall(self.width(), self.height())
        for i, ball in enumerate(self.balls):
            for j in range(i + 1, len(self.balls)):
                other_ball = self.balls[j]
                ball.collide_with_ball(other_ball)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        for ball in self.balls:
            painter.setBrush(ball.color)
            painter.drawEllipse(
                round(ball.position[0] - ball.radius),
                round(ball.position[1] - ball.radius),
                round(2 * ball.radius),
                round(2 * ball.radius),
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BallAnimation()
    window.show()
    sys.exit(app.exec_())
