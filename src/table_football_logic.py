import tensorflow as tf
import tkinter as tk
from tkinter import messagebox
import random
import numpy as np
from ai import NeuralNetwork
from sklearn.preprocessing import LabelEncoder
from keras.utils import to_categorical



class TableFootballGame:
    def __init__(self, master):
        self.master = master
        self.goal_scored_flag = False
        self.paused = False
        self.root = master.winfo_toplevel()
        self.master.title("Table Football Game")
        self.canvas = tk.Canvas(self.master, width=600, height=400, bg="green")
        self.canvas.pack()
        self.draw_field()

        self.epochs = 1000  # You can adjust the value based on your needs

        # Create an instance of NeuralNetwork
        self.ball = self.canvas.create_oval(290, 190, 310, 210, fill="white", outline="white")
        self.paddles_team1 = self.create_team_of_paddles("red", 50, 590)
        self.paddles_team2 = self.create_team_of_paddles("blue", 570, 10)
        input_size = len(self.get_current_state())
        output_size = 3  # Adjust the output size based on your AI actions
        self.neural_network = NeuralNetwork(input_size, output_size)

        self.goal1 = self.canvas.create_rectangle(0, 120, 10, 280, fill="red", outline="red", tags="goal")
        self.goal2 = self.canvas.create_rectangle(590, 120, 600, 280, fill="blue", outline="blue", tags="goal")
        self.active_team1_row = 0
        self.active_team2_row = 0
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.focus_set()

        self.ball_speed = [4, 2]

        self.player1_score = 0
        self.player2_score = 0
        self.MAX_GOALS = 5

        self.score_label = tk.Label(self.master, text="Score: 0 - 0", font=("Helvetica", 12))
        self.score_label.pack()

        self.master.bind("<KeyRelease-Tab>", self.toggle_game_pause)
        self.master.bind("<KeyRelease-BackSpace>", self.reset_game)
        self.master.bind("<KeyRelease-Escape>", self.return_to_menu)

        self.training_data = {
            'features': [],
            'labels': []
        }
        self.neural_network = NeuralNetwork(len(self.get_current_state()), 3)  # Adjust output size based on actions

        self.move_ball()

    def create_team_of_paddles(self, color, x_coord, goal_x_coord):
        paddles = []
        columns = [1, 4, 3, 3]

        paddle_width = 20
        paddle_height = 35
        vertical_spacing = (400 - len(columns) * paddle_height) / (len(columns) + 1)

        goal_height = 160

        for col, num_paddles in enumerate(columns):
            if goal_x_coord < x_coord:
                start_y = (400 - num_paddles * paddle_height - (num_paddles - 1) * vertical_spacing) / 2
                direction = 1
            else:
                start_y = (400 - num_paddles * paddle_height - (num_paddles - 1) * vertical_spacing) / 2
                direction = -1

            paddles_in_column = []
            for row in range(num_paddles):
                y_coord = start_y + row * (paddle_height + vertical_spacing)
                x_offset = col * (paddle_width + 130) * direction
                paddle = self.canvas.create_rectangle(x_coord - x_offset - paddle_width, y_coord,
                                                      x_coord - x_offset, y_coord + paddle_height,
                                                      fill=color, outline=color, tags="paddle")
                paddles_in_column.append(paddle)
            paddles.append(paddles_in_column)

        return paddles

    def draw_field(self):
        self.canvas.create_line(0, 0, 600, 0, width=2, fill="white")
        self.canvas.create_line(0, 400, 600, 400, width=2, fill="white")
        self.canvas.create_line(300, 0, 300, 400, width=2, fill="white")
        self.canvas.create_oval(280, 180, 320, 220, outline="white", width=2)

    def on_key_press(self, event):
        if not self.paused:
            if event.char.lower() == "w":
                self.move_active_row(self.paddles_team1, -20, self.active_team1_row)
            elif event.char.lower() == "s":
                self.move_active_row(self.paddles_team1, 20, self.active_team1_row)
            elif event.char.lower() == "i":
                self.move_active_row(self.paddles_team2, -20, self.active_team2_row)
            elif event.char.lower() == "k":
                self.move_active_row(self.paddles_team2, 20, self.active_team2_row)
            elif event.char.lower() == "a":
                self.active_team1_row = (self.active_team1_row - 1) % len(self.paddles_team1)
            elif event.char.lower() == "d":
                self.active_team1_row = (self.active_team1_row + 1) % len(self.paddles_team1)
            elif event.char.lower() == "j":
                self.active_team2_row = (self.active_team2_row - 1) % len(self.paddles_team2)
            elif event.char.lower() == "l":
                self.active_team2_row = (self.active_team2_row + 1) % len(self.paddles_team2)

            # Запись обучающих данных при нажатии клавиши
            self.record_training_data("some_action")

    def move_active_row(self, team, dy, active_row):
        can_move = True
        for idx, paddle in enumerate(team[active_row]):
            current_pos = self.canvas.coords(paddle)
            if not (0 < current_pos[1] + dy < 400) or not (0 < current_pos[3] + dy < 400):
                can_move = False
                break

        if can_move:
            for idx, paddle in enumerate(team[active_row]):
                self.move_paddle(paddle, dy)

    def move_paddle(self, paddle, dy):
        current_pos = self.canvas.coords(paddle)
        if 0 < current_pos[1] + dy < 400:
            self.canvas.move(paddle, 0, dy)

    def move_ball(self):
        if not self.paused:
            self.canvas.move(self.ball, self.ball_speed[0], self.ball_speed[1])
            ball_pos = self.canvas.coords(self.ball)

            if ball_pos[1] <= 0 or ball_pos[3] >= 400:
                self.ball_speed[1] = -self.ball_speed[1]

            if ball_pos[0] <= 0:
                if self.check_goal(ball_pos, self.goal2):
                    self.goal_scored("Player2")
                else:
                    self.ball_speed[0] = -self.ball_speed[0]

            if ball_pos[2] >= 600:
                if self.check_goal(ball_pos, self.goal1):
                    self.goal_scored("Player1")
                else:
                    self.ball_speed[0] = -self.ball_speed[0]

            if self.check_collision(ball_pos, self.paddles_team1) or self.check_collision(ball_pos, self.paddles_team2):
                self.ball_speed[0] = -self.ball_speed[0]

            if self.player1_score == self.MAX_GOALS or self.player2_score == self.MAX_GOALS:
                self.game_over()

            self.master.after(20, self.move_ball)

    def check_goal(self, ball_pos, goal):
        goal_coords = self.canvas.coords(goal)
        ball_radius = 10

        overlapping_items = self.canvas.find_overlapping(*ball_pos)

        for item in overlapping_items:
            item_tags = self.canvas.gettags(item)
            if item_tags and "goal" in item_tags and item != goal:
                return True

        return False

    def check_collision(self, ball_pos, paddles):
        ball_center = [(ball_pos[0] + ball_pos[2]) / 2, (ball_pos[1] + ball_pos[3]) / 2]

        for paddle_row in paddles:
            for paddle in paddle_row:
                paddle_coords = self.canvas.coords(paddle)
                if paddle_coords[0] < ball_center[0] < paddle_coords[2] and paddle_coords[1] < ball_center[1] < \
                        paddle_coords[3]:
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
            self.master.after(2000, self.reset_goal_scored_flag)

    def reset_goal_scored_flag(self):
        self.goal_scored_flag = False

    def reset_ball(self):
        self.canvas.coords(self.ball, 290, 190, 310, 210)
        self.ball_speed = [random.choice([-4, 4]), random.choice([-2, 2])]

    def update_score(self):
        self.score_label.config(text=f"Score: {self.player1_score} - {self.player2_score}")

    def game_over(self):
        winner = "Player 1" if self.player1_score == self.MAX_GOALS else "Player 2"
        messagebox.showinfo("Game Over", f"{winner} wins!\nFinal Score: {self.player1_score} - {self.player2_score}")
        self.master.quit()

    def toggle_game_pause(self, event):
        self.paused = not self.paused

        if self.paused:
            self.master.after_cancel(self.move_ball)
        else:
            self.move_ball()

    def return_to_menu(self, event):
        # Import GameMenu here to break the circular dependency
        from table_football_ui import GameMenu

        for widget in self.root.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        menu = GameMenu(self.root)

    def reset_game(self, event):
        self.paused = False
        self.reset_goal_scored_flag()
        self.reset_ball()
        self.update_score()

    def record_training_data(self, action):
        # Здесь записывайте текущее состояние и действие противника в обучающие данные
        features = self.get_current_state()

        # Добавьте текущее состояние и действие в обучающие данные
        self.training_data['features'].append(features)
        self.training_data['labels'].append(action)

        # Преобразуйте метки в числовой формат
        label_encoder = LabelEncoder()
        labels_encoded = label_encoder.fit_transform(self.training_data['labels'])

        # Обучите нейронную сеть
        self.train_neural_network(features, labels_encoded)

    def get_current_state(self):
        # Получите координаты мяча
        ball_coords = self.canvas.coords(self.ball)

        # Получите координаты ракеток
        paddles_team1_coords = [self.canvas.coords(paddle) for row in self.paddles_team1 for paddle in row]
        paddles_team2_coords = [self.canvas.coords(paddle) for row in self.paddles_team2 for paddle in row]

        # Преобразуйте координаты в одномерный массив
        features = np.array([
            ball_coords[0], ball_coords[1], ball_coords[2], ball_coords[3]
        ])

        # Добавьте координаты ракеток, если они существуют
        if paddles_team1_coords:
            features = np.concatenate((features, paddles_team1_coords[0]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        if len(paddles_team1_coords) > 1:
            features = np.concatenate((features, paddles_team1_coords[1]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        if len(paddles_team1_coords) > 2:
            features = np.concatenate((features, paddles_team1_coords[2]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        if paddles_team2_coords:
            features = np.concatenate((features, paddles_team2_coords[0]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        if len(paddles_team2_coords) > 1:
            features = np.concatenate((features, paddles_team2_coords[1]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        if len(paddles_team2_coords) > 2:
            features = np.concatenate((features, paddles_team2_coords[2]))
        else:
            features = np.concatenate((features, [0, 0, 0, 0]))

        return features

    def train_neural_network(self, features, labels):
        unique_classes = np.unique(labels)
        num_classes = len(unique_classes)
        labels_one_hot = to_categorical(labels, num_classes=num_classes)
        self.neural_network.model.fit(features.reshape(-1, 28), labels_one_hot, epochs=self.epochs)




if __name__ == "__main__":
    root = tk.Tk()
    game = TableFootballGame(root)
    root.mainloop()
