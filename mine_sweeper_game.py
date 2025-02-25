import random
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QDialogButtonBox,
                             QGridLayout, QHBoxLayout, QLabel, QMainWindow,
                             QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
                             QWidget, qApp)


class Board:

    def __init__(self, width=9, height=9, mine_count=10):
        self.width, self.height, self.mine_count = width, height, mine_count
        self.reset()

    def reset(self):
        self.board = [[0] * self.width for _ in range(self.height)]  # 雷区标记
        self.revealed = [[False] * self.width for _ in range(self.height)]  # 是否点击
        self.flags = [[False] * self.width for _ in range(self.height)]  # 是否标记为雷
        self.mine_left = self.mine_count  # 剩余未标记的雷数
        self.game_over = False
        self.game_win = False
        self.first_click = True

    def place_mines(self, exclude=None):
        # Place mines randomly on the board
        all_positions = [(x, y) for x in range(self.width) for y in range(self.height)]
        if exclude is not None:
            all_positions.remove(exclude)
        mines = random.sample(all_positions, self.mine_count)
        for x, y in mines:
            self.board[y][x] = -1
        self.calculate_numbers()

    def calculate_numbers(self):
        # Calculate the number of adjacent mines for each cell
        for y in range(self.height):
            for x in range(self.width):
                if self.board[y][x] == -1:
                    continue
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height and self.board[ny][nx] == -1:
                            self.board[y][x] += 1

    def reveal_around(self, x, y):
        if not self.revealed[y][x]:
            return
        if self.board[y][x] <= 0:
            return
        z = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.flags[ny][nx]:
                    z += 1
        if z == self.board[y][x]:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    self.reveal_area(x + dx, y + dy)
        self.game_win = self.width * self.height - self.mine_count == sum(row.count(True) for row in self.revealed)

    def reveal(self, x, y):
        if self.game_over or self.revealed[y][x] or self.flags[y][x]:
            return
        if self.first_click:
            self.place_mines(exclude=(x, y))  # 第一次点击后随机生成雷区
            self.first_click = False
        self.reveal_area(x, y)
        self.game_win = self.width * self.height - self.mine_count == sum(row.count(True) for row in self.revealed)

    def reveal_area(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height) or self.revealed[y][x] or self.flags[y][x]:
            return
        self.revealed[y][x] = True
        if self.board[y][x] == -1:
            self.game_over = True
            return
        if self.board[y][x] > 0:
            return
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    self.reveal_area(x + dx, y + dy)

    def toggle_flag(self, x, y):
        if self.revealed[y][x]:
            return
        self.flags[y][x] = not self.flags[y][x]
        self.mine_left = self.mine_count - sum(row.count(True) for row in self.flags)


class DoubleClickButton(QPushButton):
    # 自定义双击信号
    double_clicked = pyqtSignal()

    def __init__(self, text):
        super().__init__(text)

    # 重写鼠标双击事件
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()  # 发送双击信号
        super().mouseDoubleClickEvent(event)  # 保留原事件逻辑


class CustomDifficultyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("自定义难度")
        
        layout = QVBoxLayout(self)
        
        self.width_spinbox = QSpinBox(self)
        self.width_spinbox.setMinimum(1)
        self.width_spinbox.setMaximum(100)
        self.width_spinbox.setValue(9)
        layout.addWidget(QLabel("宽度:"))
        layout.addWidget(self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setMinimum(1)
        self.height_spinbox.setMaximum(100)
        self.height_spinbox.setValue(9)
        layout.addWidget(QLabel("高度:"))
        layout.addWidget(self.height_spinbox)

        self.mine_count_spinbox = QSpinBox()
        self.mine_count_spinbox.setMinimum(1)
        self.mine_count_spinbox.setMaximum(999)  # 最大值可以根据实际情况调整
        self.mine_count_spinbox.setValue(10)
        layout.addWidget(QLabel("地雷数:"))
        layout.addWidget(self.mine_count_spinbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.grabKeyboard()

    def get_values(self):
        return self.width_spinbox.value(), self.height_spinbox.value(), self.mine_count_spinbox.value()

class MineSweeper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扫雷")
        self.difficulty = "初级"  # 默认难度
        self.board = Board()  # 默认使用初级难度的设置
        self.buttons = []
        self.init_ui()
        self.create_menu()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time = 0
        self.select_button = None

    def init_ui(self):
        layout = QVBoxLayout()

        # 创建顶部布局用于放置时间和剩余地雷数标签
        top_layout = QHBoxLayout()

        # 剩余地雷数标签
        self.mine_left_label = QLabel(str(self.board.mine_left))
        # 设置字体颜色为蓝色，字体大小为24pt
        self.mine_left_label.setStyleSheet("QLabel { color: red; font-size: 24pt; }")
        # 将剩余地雷数标签添加到顶部布局中并设置对其方式为左对齐
        top_layout.addWidget(self.mine_left_label, alignment=Qt.AlignLeft)

        self.time_label = QLabel("0")
        self.time_label.setStyleSheet("QLabel { color: red; font-size: 24pt; }")  # 设置字体颜色为红色，字体大小为24pt
        top_layout.addStretch()  # 增加一个伸缩因子，使时间标签靠右对齐
        top_layout.addWidget(
            self.time_label, alignment=Qt.AlignRight
        )  # 将时间标签添加到顶部布局中并设置对其方式为右对齐
        layout.addLayout(top_layout)  # 将顶部布局添加到主布局中

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        layout.addLayout(self.grid_layout)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)
        self.init_board()
        self.grabKeyboard()

    def init_board(self):
        for row in self.buttons:
            for btn in row:
                self.grid_layout.removeWidget(btn)
        self.buttons = []
        for y in range(self.board.height):
            row = []
            for x in range(self.board.width):
                btn = DoubleClickButton(self)
                btn.setFixedSize(30, 30)
                btn.setContentsMargins(0, 0, 0, 0)
                btn.setStyleSheet("QPushButton {background-color:gray;} ")
                # 使用lambda表达式时，通过默认参数固定x, y的值
                btn.clicked.connect(lambda _, x=x, y=y: self.on_click(x, y))
                btn.double_clicked.connect(lambda x=x, y=y: self.on_double_click(x, y))
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda _, x=x, y=y: self.on_right_click(x, y))
                self.grid_layout.addWidget(btn, y, x)
                row.append(btn)
            self.buttons.append(row)
        QTimer().singleShot(0, lambda: self.resize(10, 10))  # 作用：使得窗口大小随着width*height变化，原理未知

    def create_menu(self):
        # 创建菜单栏
        menu_bar = self.menuBar()
        # 创建“游戏”菜单
        game_menu = menu_bar.addMenu("游戏")
        # 新游戏动作
        new_game_action = QAction("新游戏", self)
        new_game_action.triggered.connect(self.start_new_game)
        game_menu.addAction(new_game_action)

        difficulty_menu = game_menu.addMenu("难度")
        self.difficulty_actions = []
        for diff in ["初级", "中级", "高级","自定义"]:
            action = difficulty_menu.addAction(diff)
            action.triggered.connect(lambda checked, d=diff: self.change_difficulty(d))
            action.setCheckable(True)
            self.difficulty_actions.append(action)
        self.difficulty_actions[0].setChecked(True)

        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(qApp.quit)
        game_menu.addAction(exit_action)

        # 创建“帮助”菜单
        help_menu = menu_bar.addMenu("帮助")

        # 显示帮助信息动作
        help_action = menu_bar.addAction("关于")
        help_action.triggered.connect(self.show_help)

    def start_new_game(self):
        # 重置游戏状态
        self.time = 0
        self.board.reset()
        self.init_board()
        self.timer.stop()
        self.time_label.setText(str(self.time))
        self.update_mines_left_label()
        self.update_board()

    def change_difficulty(self, difficulty):
        self.difficulty = difficulty
        for action in self.difficulty_actions:
            action.setChecked(False)
        if difficulty == "初级":
            self.difficulty_actions[0].setChecked(True)
            self.board = Board(width=9, height=9, mine_count=10)
        elif difficulty == "中级":
            self.difficulty_actions[1].setChecked(True)
            self.board = Board(width=16, height=16, mine_count=40)
        elif difficulty == "高级":
            self.difficulty_actions[2].setChecked(True)
            self.board = Board(width=30, height=16, mine_count=99)
        elif difficulty == "自定义":
            self.difficulty_actions[3].setChecked(True)
            dialog = CustomDifficultyDialog(self)
            if dialog.exec_():
                width, height, mine_count = dialog.get_values()
                self.board = Board(width=width, height=height, mine_count=mine_count)
        self.start_new_game()

    def on_double_click(self, x, y):
        if self.board.game_over or self.board.game_win:
            return
        self.board.reveal_around(x, y)
        self.update_board()
        if self.board.game_over or self.board.game_win:
            self.timer.stop()
        if self.board.game_over:
            self.show_game_over()
        elif self.board.game_win:
            self.show_game_win()

    def on_click(self, x, y):
        if self.board.game_over or self.board.game_win:
            return
        if self.board.first_click:
            self.start_timer()
        self.board.reveal(x, y)
        self.update_board()
        if self.board.game_over or self.board.game_win:
            self.timer.stop()
        if self.board.game_over:
            self.show_game_over()
        elif self.board.game_win:
            self.show_game_win()

    def on_right_click(self, x, y):
        self.board.toggle_flag(x, y)
        self.update_board()
        self.update_mines_left_label()

    def keyPressEvent(self, event: QKeyEvent):
        dir_keys = (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D, Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left)
        if event.key() in dir_keys and self.select_button is None:
            self.select_button = [self.board.width // 2, self.board.height // 2]
        select_button = self.select_button
        if select_button is None:
            return super().keyPressEvent(event)
        select_style = "QPushButton {border:1px solid rgb(230,230,0)}"
        btn = self.buttons[select_button[0]][select_button[1]]
        btn.setStyleSheet(btn.styleSheet().replace(select_style, ""))

        if event.key() in (Qt.Key_W, Qt.Key_Up):
            select_button[0] = (select_button[0] - 1) % self.board.height
        elif event.key() in (Qt.Key_S, Qt.Key_Down):
            select_button[0] = (select_button[0] + 1) % self.board.height
        elif event.key() in (Qt.Key_A, Qt.Key_Left):
            select_button[1] = (select_button[1] - 1) % self.board.width
        elif event.key() in (Qt.Key_D, Qt.Key_Right):
            select_button[1] = (select_button[1] + 1) % self.board.width
        elif event.key() == Qt.Key_Q:
            self.on_click(select_button[1], select_button[0])
        elif event.key() == Qt.Key_X:
            self.on_right_click(select_button[1], select_button[0])
        elif event.key() == Qt.Key_C:
            self.on_double_click(select_button[1], select_button[0])
        btn = self.buttons[select_button[0]][select_button[1]]
        btn.setStyleSheet(f"{btn.styleSheet()} {select_style}")
        return super().keyPressEvent(event)

    def start_timer(self):
        self.timer.start(1000)  # 定时器每1000毫秒（即1秒）触发一次

    def update_mines_left_label(self):
        # 更新剩余地雷数标签
        self.mine_left_label.setText(str(self.board.mine_left))

    def update_timer(self):
        self.time += 1
        self.time_label.setText(str(self.time))

    def update_board(self):
        for y in range(self.board.height):
            for x in range(self.board.width):
                btn = self.buttons[y][x]
                num = self.board.board[y][x]
                btn_text = ""
                btn_style = "QPushButton {background-color:gray;} "
                if self.board.flags[y][x]:
                    btn_text = "🚩"
                    if num != -1 and self.board.game_over:
                        # btn_text = "X"
                        btn_style = "QPushButton {background-color:red;} "
                elif self.board.revealed[y][x] or self.board.game_over:
                    # btn.setEnabled(False)
                    btn_style = ""
                    if num == -1:
                        btn_text = "💣"
                        if self.board.revealed[y][x]:
                            btn_style = "QPushButton {background-color:red;} "
                    elif num > 0:
                        btn_text = str(num)
                        colors = [
                            "#0000FF",
                            "#008200",
                            "#FF0000",
                            "#000084",
                            "#840000",
                            "#008284",
                            "#000000",
                            "#840084",
                        ]
                        btn_style = f"QPushButton {{ color: {colors[num-1]}}}"
                btn.setText(btn_text)
                btn.setStyleSheet(btn_style)

    def show_game_over(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("你输了！游戏结束！")
        msg_box.exec_()

    def show_game_win(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"你赢了，总用时：{self.time}s")
        msg_box.exec_()

    def show_help(self):
        # 简单的帮助对话框
        help_text = "这是一个简单的扫雷游戏。\n点击方块以翻开它们，右键点击标记地雷。\n祝你好运！"
        QMessageBox.information(self, "关于", help_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sweeper = MineSweeper()
    sweeper.show()
    sys.exit(app.exec_())
