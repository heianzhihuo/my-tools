import random
import tkinter as tk


class SnakeGame:
    def __init__(self) -> None:
        self.direction = "right"
        self.head = [30, 30]
        self.body = [tuple(self.head)]
        self.food = ()
        self.score = 0
        self.speed = 300
        self.speed_ = None
        self.path = []

        self.generate_food()

        self.window = tk.Tk()
        self.window.title("Snake Game")
        self.canvas = tk.Canvas(self.window, width=700, height=610)
        self.canvas.pack()
        self.window.bind("<Key>", self.on_key_press)
        self.window.bind("<KeyPress-space>", self.speed_up)
        self.window.bind("<KeyRelease-space>", self.speed_down)
        self.running = True
        self.auto_path = False
        self.update()
        self.window.mainloop()

    def reset(self, event):
        self.window.unbind("<Return>")
        self.window.unbind("<Escape>")
        self.direction = "right"
        self.head = [30, 30]
        self.body = [tuple(self.head)]
        self.food = []
        self.score = 0
        self.speed = 300
        self.generate_food()
        self.running = True
        self.update()

    def update(self):
        if self.running:
            self.window.after(self.speed, self.update)  # speed时间后，update.
        self.move_snake()
        self.check_food()
        self.check_collisions()
        self.draw()

    def over(self, event):
        self.window.destroy()

    def speed_up(self, event=None):
        if event and not self.speed_:
            self.speed_ = self.speed
            self.speed = self.speed // 2
        if not event:
            if self.speed_:
                self.speed_ = max(20, self.speed_ - 10)
                self.speed = self.speed_ // 2
            else:
                self.speed = max(20, self.speed - 10)

    def speed_down(self, event):
        if self.speed_:
            self.speed = self.speed_
            self.speed_ = None

    def on_key_press(self, event):
        if event.keysym in ("Up", "W", "w") and self.direction != "down":
            self.direction = "up"
        elif event.keysym in ("Down", "S", "s") and self.direction != "up":
            self.direction = "down"
        elif event.keysym in ("Left", "A", "a") and self.direction != "right":
            self.direction = "left"
        elif event.keysym in ("Right", "D", "d") and self.direction != "left":
            self.direction = "right"
        elif event.keysym == "P" or event.keysym == "p":
            self.running = not self.running
        elif event.keysym in {"K", "k"}:
            self.auto_path = not self.auto_path
            if not self.auto_path:
                self.speed = 100
                self.path = []

    def move_snake(self):
        if self.auto_path and not self.path:
            self.path = find_path(self.body, self.food, 60, 60)
        if self.path:
            self.direction = self.path.pop()
        if self.direction == "up":
            self.head[1] -= 1
        elif self.direction == "down":
            self.head[1] += 1
        elif self.direction == "left":
            self.head[0] -= 1
        elif self.direction == "right":
            self.head[0] += 1
        if len(self.body) > 0:
            self.tail = self.body.pop()
        self.body.insert(0, tuple(self.head))

    def check_food(self):
        if self.head == self.food:
            self.score += 1
            self.body.append(tuple(self.tail))
            self.generate_food()
            if self.score % 10 == 0:
                self.speed_up()

    def check_collisions(self):
        if self.head[0] < 0 or self.head[0] >= 60 or self.head[1] < 0 or self.head[1] >= 60:
            self.running = False
        if tuple(self.head) in self.body[1:]:
            self.running = False

    def generate_food(self):
        while True:
            x = random.randint(0, 59)
            y = random.randint(0, 59)
            if (x, y) not in self.body and [x, y] != self.head:
                self.food = [x, y]
                break

    def draw(self):
        self.canvas.delete("all")  # 清空后重画
        self.canvas.create_rectangle(5, 5, 605, 605)
        if not self.running:
            del self.body[0]
            self.body.append(list(self.tail))
        for segment in self.body:
            self.canvas.create_rectangle(
                segment[0] * 10 + 5,
                segment[1] * 10 + 5,
                (segment[0] + 1) * 10 + 5,
                (segment[1] + 1) * 10 + 5,
                fill="green",
            )
        self.canvas.create_rectangle(
            self.food[0] * 10 + 5,
            self.food[1] * 10 + 5,
            (self.food[0] + 1) * 10 + 5,
            (self.food[1] + 1) * 10 + 5,
            fill="red",
        )
        self.canvas.create_text(
            655, 550, text=f"Score: {self.score}\nSpeed: {self.speed}\n\nKey Map:\nPause/Start: P", justify="left"
        )
        if not self.running:
            self.canvas.create_text(300, 300, text=f"Game Over! Your Score is {self.score}!", fill="red")
            self.canvas.create_text(300, 320, text="Press Enter to Reset", fill="red")
            self.canvas.create_text(300, 340, text="Press Esc to Quit", fill="red")
            self.window.bind("<Return>", self.reset)
            self.window.bind("<Escape>", self.over)


def DFS(body, food, m, n, k=10):
    x, y = body[0]
    if x < 0 or x >= m or y < 0 or y >= n or (x, y) in body[1:]:
        return -100, []
    if (x, y) == tuple(food):
        return 20, []
    if k <= 0:
        return 1, []
    up_ans = DFS([(x, y - 1)] + body[:-1], food, m, n, k - 1)
    down_ans = DFS([(x, y + 1)] + body[:-1], food, m, n, k - 1)
    left_ans = DFS([(x - 1, y)] + body[:-1], food, m, n, k - 1)
    right_ans = DFS([(x + 1, y)] + body[:-1], food, m, n, k - 1)
    ans = max(up_ans[0], down_ans[0], left_ans[0], right_ans[0])
    if ans == up_ans[0]:
        return ans + 1, up_ans[1] + ["up"]
    elif ans == down_ans[0]:
        return ans + 1, down_ans[1] + ["down"]
    elif ans == left_ans[0]:
        return ans + 1, left_ans[1] + ["left"]
    else:
        return ans + 1, right_ans[1] + ["right"]


def find_path(body, food, m, n, visited=set()):
    queue = [body[0]]
    visited = {body[0]}
    food = tuple(food)
    parent = {}
    while queue:
        x, y = queue.pop(0)
        if (x, y) == food:
            break
        if (x, y - 1) not in body and (x, y - 1) not in visited and y - 1 >= 0:
            queue.append((x, y - 1))
            visited.add((x, y - 1))
            parent[(x, y - 1)] = ((x, y), "up")
        if (x, y + 1) not in body and (x, y + 1) not in visited and y + 1 < m:
            queue.append((x, y + 1))
            visited.add((x, y + 1))
            parent[(x, y + 1)] = ((x, y), "down")
        if (x - 1, y) not in body and (x - 1, y) not in visited and x - 1 >= 0:
            queue.append((x - 1, y))
            visited.add((x - 1, y))
            parent[(x - 1, y)] = ((x, y), "left")
        if (x + 1, y) not in body and (x + 1, y) not in visited and x + 1 < n:
            queue.append((x + 1, y))
            visited.add((x + 1, y))
            parent[(x + 1, y)] = ((x, y), "right")
    path = []
    while food in parent:
        food, direction = parent[food]
        path.append(direction)
    if not path:
        ans = DFS(body, food, m, n)
        print(ans)
        path = ans[1]
    return path


if __name__ == "__main__":
    SnakeGame()
