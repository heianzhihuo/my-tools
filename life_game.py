import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPainter, QPen, QResizeEvent
from PyQt5.QtCore import Qt, QTimer


class LifeGame(QWidget):
    def __init__(self):
        super().__init__()
        self.width = 1810
        self.height = 1000
        self.cell_size = 10
        self.grid_width = 180
        self.grid_height = 100
        self.speed = 200
        self.grid = [[False] * self.grid_width for _ in range(self.grid_height)]
        self.lives = set()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(200)  # Update every 100ms

    def update_game(self):
        neighbor_cnt = {}
        for x, y in self.lives:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor_cnt[(x + dx, y + dy)] = neighbor_cnt.get((x + dx, y + dy), 0) + 1
        new_lives = set()
        for key, cnt in neighbor_cnt.items():
            if cnt == 3:
                new_lives.add(key)
            elif cnt == 2 and key in self.lives:
                new_lives.add(key)
        self.lives = new_lives
        self.update()

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        print(event.size(), "in")

    def mousePressEvent(self, event):
        x, y = event.pos().x() // self.cell_size, event.pos().y() // self.cell_size
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.change_status(y, x)
            self.update()

    def change_status(self, x: int, y: int):
        if (x, y) in self.lives:
            self.lives.discard((x, y))
        else:
            self.lives.add((x, y))

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        x, y = event.pos().x() // self.cell_size, event.pos().y() // self.cell_size
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            if event.buttons() == Qt.LeftButton:
                self.lives.add((y, x))
            elif event.buttons() == Qt.RightButton:
                self.lives.discard((y, x))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBackground(Qt.white)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawText(0,0,self.cell_size,self.cell_size,1,"0")
        for i, j in self.lives:
            painter.fillRect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size, Qt.black)
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                painter.drawRect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conway's Game of Life")
        self.setGeometry(0, 0, 1840, 1000)
        self.central_widget = LifeGame()
        self.setCentralWidget(self.central_widget)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event.key() == Qt.Key_Space:
            self.central_widget.timer.stop()
            self.central_widget.update()
            self.central_widget.repaint()
        elif event.key() == Qt.Key_Return:
            self.central_widget.timer.start(200)
            self.central_widget.update()
            self.central_widget.repaint()
        elif event.key() == Qt.Key_X:
            self.central_widget.speed = max(5, self.central_widget.speed - 5)
            self.central_widget.timer.setInterval(self.central_widget.speed)
        elif event.key() == Qt.Key_C:
            self.central_widget.speed += 5
            self.central_widget.timer.setInterval(self.central_widget.speed)
        self.update()
        return super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

