import random
import tkinter as tk


class SnakeGame:
    def __init__(self) -> None:
        self.body = []
        self.direction = "right"
        self.head = [30, 30]
        self.food = []
        self.score = 0
        self.speed = 200

        self.generate_food()

        self.window = tk.Tk()
        self.window.title("Snake Game")
        self.canvas = tk.Canvas(self.window, width=700, height=610)
        self.canvas.pack()
        self.window.bind("<Key>", self.on_key_press)
        self.running = True
        self.update()
        self.window.mainloop()

    def over(self, event):
        self.window.destroy()

    def on_key_press(self, event):
        if event.keysym == "Up" and self.direction != "down":
            self.direction = "up"
        elif event.keysym == "Down" and self.direction != "up":
            self.direction = "down"
        elif event.keysym == "Left" and self.direction != "right":
            self.direction = "left"
        elif event.keysym == "Right" and self.direction != "left":
            self.direction = "right"
        elif event.keysym == "P" or event.keysym == "p":
            self.running = not self.running

    def reset(self, event):
        self.window.unbind("<Return>")
        self.window.unbind("<Escape>")
        self.body = []
        self.direction = "right"
        self.head = [30, 30]
        self.food = []
        self.score = 0
        self.speed = 200
        self.generate_food()
        self.running = True
        self.update()

    def update(self):
        self.window.after(self.speed, self.update)  # speed时间后，执行play
        if not self.running:
            return
        self.move_snake()
        self.check_food()
        self.check_collisions()
        self.draw()

    def move_snake(self):
        if len(self.path) > 0:
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
        self.body.insert(0, list(self.head))

    def check_food(self):
        if self.head == self.food:
            self.score += 1
            self.body.append(list(self.tail))
            self.generate_food()
            if self.speed > 10:
                self.speed -= 10

    def check_collisions(self):
        if self.head[0] < 0 or self.head[0] > 59 or self.head[1] < 0 or self.head[1] > 59:
            self.running = False
        for segment in self.body[1:]:
            if self.head == segment:
                self.running = False

    def generate_food(self):
        while True:
            x = random.randint(0, 59)
            y = random.randint(0, 59)
            self.food = [x, y]
            if self.food not in self.body and self.food != self.head:
                break
        self.path = find_path(self.body, self.head, self.food, 60, 60)

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(5, 5, 605, 605)
        if not self.running:
            del self.body[0]
            self.body.append(list(self.tail))
        for segment in self.body:
            self.canvas.create_rectangle(segment[0] * 10 + 5, segment[1] * 10 + 5,
                                         (segment[0] + 1) * 10 + 5, (segment[1] + 1) * 10+5, fill="green")
        self.canvas.create_rectangle(self.food[0] * 10+5, self.food[1] * 10+5,
                                     (self.food[0] + 1) * 10+5, (self.food[1] + 1) * 10+5, fill="red")
        self.canvas.create_text(
            655, 550, text=f"Score: {self.score}\nSpeed: {self.speed}\n\nKey Map:\nPause/Start: P", justify="left")
        if not self.running:
            self.canvas.create_text(300, 300, text=f"Game Over! Your Score is {self.score}!", fill="red")
            self.canvas.create_text(300, 320, text="Press Enter to Reset", fill="red")
            self.canvas.create_text(300, 340, text="Press Esc to Quit", fill="red")
            self.window.bind("<Return>", self.reset)
            self.window.bind("<Escape>", self.over)


def find_path(body, head, food, m, n, visited=set()):
    queue = [tuple(head)]
    visited = {tuple(head)}
    food = tuple(food)
    parent = {}
    while len(queue) > 0:
        x, y = queue.pop(0)
        if (x, y) == food:
            break
        if [x, y-1] not in body and (x, y-1) not in visited and y-1 >= 0:
            queue.append((x, y-1))
            visited.add((x, y-1))
            parent[(x, y-1)] = ((x, y), "up")
        if [x, y+1] not in body and (x, y+1) not in visited and y+1 < m:
            queue.append((x, y+1))
            visited.add((x, y+1))
            parent[(x, y+1)] = ((x, y), "down")
        if [x-1, y] not in body and (x-1, y) not in visited and x-1 >= 0:
            queue.append((x-1, y))
            visited.add((x-1, y))
            parent[(x-1, y)] = ((x, y), "left")
        if [x+1, y] not in body and (x+1, y) not in visited and x+1 < n:
            queue.append((x+1, y))
            visited.add((x+1, y))
            parent[(x+1, y)] = ((x, y), "right")
    path = []
    while food in parent:
        food, direction = parent[food]
        path.append(direction)
    return path


if __name__ == "__main__":
    SnakeGame()
