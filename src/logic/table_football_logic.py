import tkinter as tk
from tkinter import messagebox
import random

class TableFootballLogic:
    def __init__(self, gui, paddle1, paddle2):
        self.gui = gui
        self.goal_scored_flag = False
        self.ball_speed = [4, 2]
        self.player1_score = 0
        self.player2_score = 0
        self.MAX_GOALS = 5  # Set the maximum number of goals to win
        self.paddle1 = paddle1
        self.paddle2 = paddle2

    def init_gui_elements(self, canvas):
        self.canvas = canvas
        self.draw_field()  # Добавляем разметку поля

        self.ball = self.canvas.create_oval(290, 190, 310, 210, fill="white", outline="white")
        self.goal1 = self.canvas.create_rectangle(0, 120, 10, 280, fill="red", outline="red", tags="goal")
        self.goal2 = self.canvas.create_rectangle(590, 120, 600, 280, fill="blue", outline="blue", tags="goal")

        # Add players for team 1
        for i in range(11):
            y_position = 40 + i * 30
            self.canvas.create_rectangle(10, y_position, 30, y_position + 20, fill="red", outline="red", tags="player")

        # Add players for team 2
        for i in range(11):
            y_position = 40 + i * 30
            self.canvas.create_rectangle(570, y_position, 590, y_position + 20, fill="blue", outline="blue",
                                         tags="player")

    def draw_field(self):
        # Рисуем верхнюю и нижнюю границу поля
        self.canvas.create_line(0, 0, 600, 0, width=2, fill="white")
        self.canvas.create_line(0, 400, 600, 400, width=2, fill="white")

        # Рисуем центральную линию
        self.canvas.create_line(300, 0, 300, 400, width=2, fill="white")

        # Рисуем центральный круг
        self.canvas.create_oval(280, 180, 320, 220, outline="white", width=2)

    def on_key_press(self, event):
        if event.char.lower() == "w":
            self.move_paddle(self.paddle1, -20)
        elif event.char.lower() == "s":
            self.move_paddle(self.paddle1, 20)
        elif event.char.lower() == "i":
            self.move_paddle(self.paddle2, -20)
        elif event.char.lower() == "k":
            self.move_paddle(self.paddle2, 20)

    def move_paddle(self, paddle, dy):
        current_pos = self.canvas.coords(paddle)
        if 0 < current_pos[1] + dy < 400:
            self.canvas.move(paddle, 0, dy)

    def move_ball(self):
        self.canvas.move(self.ball, self.ball_speed[0], self.ball_speed[1])
        ball_pos = self.canvas.coords(self.ball)

        # Проверка столкновения с верхней и нижней границей поля
        if ball_pos[1] <= 0 or ball_pos[3] >= 400:
            self.ball_speed[1] = -self.ball_speed[1]

        # Проверка столкновения с левой границей (гол для player2)
        if ball_pos[0] <= 0:
            if self.check_goal(ball_pos, self.goal2):
                self.goal_scored("Player2")
            else:
                self.ball_speed[0] = -self.ball_speed[0]  # изменение направления на противоположное

        # Проверка столкновения с правой границей (гол для player1)
        if ball_pos[2] >= 600:
            if self.check_goal(ball_pos, self.goal1):
                self.goal_scored("Player1")
            else:
                self.ball_speed[0] = -self.ball_speed[0]  # изменение направления на противоположное

        # Проверка столкновения с ракетками
        if self.check_collision(ball_pos, self.paddle1) or self.check_collision(ball_pos, self.paddle2):
            self.ball_speed[0] = -self.ball_speed[0]

        if self.player1_score == self.MAX_GOALS or self.player2_score == self.MAX_GOALS:
            self.game_over()

        self.gui.master.after(20, self.move_ball)

    def check_goal(self, ball_pos, goal):
        goal_coords = self.canvas.coords(goal)
        ball_radius = 10  # радиус мяча

        overlapping_items = self.canvas.find_overlapping(*ball_pos)

        for item in overlapping_items:
            item_tags = self.canvas.gettags(item)
            if item_tags and "goal" in item_tags and item != goal:
                return True

        return False

    def check_collision(self, ball_pos, paddle):
        overlapping_items = self.canvas.find_overlapping(*ball_pos)

        for item in overlapping_items:
            item_tags = self.canvas.gettags(item)
            if item == paddle or ("paddle" in item_tags and "player" in item_tags):
                return True

        return False

    def goal_scored(self, player):
        if not self.goal_scored_flag:
            self.goal_scored_flag = True
            self.reset_ball()
            if player == "Player1":
                self.player1_score += 1
            elif player == "Player2":
                self.player2_score += 1
            self.update_score()
            self.gui.master.after(2000, self.reset_goal_scored_flag)  # Ждем 2 секунды перед включением проверки гола

    def reset_goal_scored_flag(self):
        self.goal_scored_flag = False

    def reset_ball(self):
        self.canvas.coords(self.ball, 290, 190, 310, 210)
        self.ball_speed = [random.choice([-4, 4]), random.choice([-2, 2])]

    def update_score(self):
        self.gui.score_label.config(text=f"Score: {self.player1_score} - {self.player2_score}")

    def game_over(self):
        winner = "Player 1" if self.player1_score == self.MAX_GOALS else "Player 2"
        messagebox.showinfo("Game Over", f"{winner} wins!\nFinal Score: {self.player1_score} - {self.player2_score}")
        self.gui.master.quit()
