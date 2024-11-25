import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPainter, QPen
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
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(200)  # Update every 100ms

    def update_game(self):
        new_grid = [[False] * self.grid_width for _ in range(self.grid_height)]
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                neighbors = self.count_neighbors(i, j)
                if self.grid[i][j]:
                    if neighbors == 2 or neighbors == 3:
                        new_grid[i][j] = True
                else:
                    if neighbors == 3:
                        new_grid[i][j] = True
        self.grid = new_grid
        self.update()

    def count_neighbors(self, x, y):
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_height and 0 <= ny < self.grid_width:
                    count += self.grid[nx][ny]
        return count

    def mousePressEvent(self, event):
        x, y = event.pos().x() // self.cell_size, event.pos().y() // self.cell_size
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.grid[y][x] = not self.grid[y][x]
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        x, y = event.pos().x() // self.cell_size, event.pos().y() // self.cell_size
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            if event.buttons() == Qt.LeftButton:
                self.grid[y][x] = True
            elif event.buttons() == Qt.RightButton:
                self.grid[y][x] = False
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBackground(Qt.white)
        painter.setPen(QPen(Qt.gray, 2))
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                painter.drawRect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size)
                if self.grid[i][j]:
                    painter.fillRect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size, Qt.black)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conway's Game of Life")
        self.setGeometry(100, 100, 800, 600)
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
            self.central_widget.speed = max(50,self.central_widget.speed-50)
            self.central_widget.timer.setInterval(self.central_widget.speed)
        elif event.key() == Qt.Key_C:
            self.central_widget.speed += 50
            self.central_widget.timer.setInterval(self.central_widget.speed)
        self.update()
        return super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
