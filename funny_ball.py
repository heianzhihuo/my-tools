from __future__ import annotations

import random
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QKeyEvent, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer
import numpy as np


class Ball:
    def __init__(self, x: float, y: float, radius, color, speed_x, speed_y):
        self.position = np.array((x, y))
        self.radius = radius
        self.mass = radius*radius  # 质量
        self.velocity = np.array((speed_x, speed_y))
        self.color = color

    def move(self):
        self.position = self.position + self.velocity
        

    def collide_with_wall(self, width, height):
        if self.position[0] - self.radius <= 0:
            self.velocity[0] = -self.velocity[0]
            self.position[0] = 2*self.radius-self.position[0]
        if self.position[0] + self.radius >= width:
            self.velocity[0] = -self.velocity[0]
            self.position[0] = 2*width-2*self.radius-self.position[0]
        if self.position[1] - self.radius <= 0:
            self.velocity[1] = -self.velocity[1]
            self.position[1] = 2*self.radius - self.position[1]
        if self.position[1] + self.radius >= height:
            self.velocity[1] = -self.velocity[1]
            self.position[1] = 2*height-2*self.radius-self.position[1]

    def collide_with_ball(self, other: Ball):
        distance = sum(np.power(self.position-other.position, 2))
        if distance <= (self.radius + other.radius)**2:
            v1 = self.velocity
            v2 = other.velocity
            m1 = self.mass
            m2 = other.mass
            m = m1 + m2
            dm = m1 - m2
            wx = self.position - other.position
            wy = np.array((wx[1], -wx[0]))
            v1wx = np.dot(v1, wx)*wx
            v1wy = np.dot(v1, wy)*wy
            v2wx = np.dot(v2, wx)*wx
            v2wy = np.dot(v2, wy)*wy

            self.velocity = ((dm*v1wx + 2*m2*v2wx)/m + v1wy)/distance
            other.velocity = ((-dm*v2wx + 2*m1*v1wx)/m + v2wy)/distance


class BallAnimation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Ball Collision Simulation')
        self.resize(800, 600)

        self.balls = [
            Ball(300, 300, 20, QColor(255, 0, 0), 0, random.randint(1, 4)),
            Ball(300, 100, 20, QColor(0, 255, 0), 0, random.randint(1, 5)),
            Ball(500, 150, 20, QColor(0, 0, 255), random.randint(0, 4), random.randint(0, 5)),
            Ball(400, 150, 20, QColor(0, 255, 255), random.randint(0, 4), random.randint(0, 5)),
            Ball(300, 250, 20, QColor(0, 0, 0), random.randint(0, 4), random.randint(0, 5)),
            Ball(100, 100, 80, QColor(255, 255, 255), random.randint(0, 4), random.randint(0, 5)),
            Ball(200, 200, 20, QColor(255, 0, 255), random.randint(0, 4), random.randint(0, 5)),
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # Approximately 60 FPS

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event.key() == Qt.Key_Space:
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start(16)

    def update_animation(self):
        for ball in self.balls:
            ball.move()
            ball.collide_with_wall(self.width(), self.height())

        for i, ball in enumerate(self.balls):
            for j in range(i+1, len(self.balls)):
                other_ball = self.balls[j]
                ball.collide_with_ball(other_ball)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        for ball in self.balls:
            painter.setBrush(ball.color)
            painter.drawEllipse(round(ball.position[0] - ball.radius),
                                round(ball.position[1] - ball.radius),
                                round(2 * ball.radius), round(2 * ball.radius))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BallAnimation()
    window.show()
    sys.exit(app.exec_())
