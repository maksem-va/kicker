import tkinter as tk
from tkinter import messagebox
import random

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

class PPO(nn.Module):
    def __init__(self, input_size, output_size):
        super(PPO, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return F.softmax(x, dim=-1)

class AIController:
    def __init__(self, game):
        self.game = game
        self.input_size = 26  # 8 coordinates (ball + 2 coordinates per paddle)
        self.output_size = 2
        self.model = PPO(self.input_size, self.output_size)
        self.input_data = np.zeros(self.input_size)
        self.goal_scored_flag = False
        self.episode_data = {'states': [], 'actions': [], 'rewards': []}

    def get_input_data(self):
        ball_coords = self.game.get_ball_coords()
        paddle_coords = []

        # Проверяем, есть ли активные ракетки в команде 2
        if self.game.paddles_team2:
            # Используем координаты всех ракеток команды 2
            for row in self.game.paddles_team2:
                paddle_coords.extend([self.game.canvas.coords(paddle) for paddle in row])

            input_data = []

            if paddle_coords:
                # Обновляем input_data с учетом координат мяча и ракеток
                input_data.extend(ball_coords)
                for coords in paddle_coords:
                    input_data.extend(coords[:2])

                # Нормализуем input_data
                normalized_input_data = (np.array(input_data) - np.mean(input_data)) / (np.std(input_data) + 1e-8)

                # Добавим размерность (батч) 1x26
                normalized_input_data = normalized_input_data.reshape(1, -1)

                return normalized_input_data

        # Возвращаем некоторое значение по умолчанию в случае отсутствия ракеток
        return np.zeros(self.input_size)

    def get_action(self):
        input_data = self.get_input_data()
        input_tensor = torch.tensor(input_data, dtype=torch.float32)
        output_tensor = self.model(input_tensor)
        action = torch.multinomial(output_tensor, 1).item()
        log_probability = torch.log(output_tensor[0, action])
        return action, log_probability

    def update(self):
        if not self.game.paused:
            action, log_probability = self.get_action()
            if action == 0:
                self.game.move_active_rows(self.game.paddles_team2, -20)
            elif action == 1:
                self.game.move_active_rows(self.game.paddles_team2, 20)

            ball_deflection_reward = self.check_ball_deflection()
            if ball_deflection_reward != 0:
                self.episode_data['rewards'].append(ball_deflection_reward)
                self.update_neural_network()

    def check_ball_deflection(self):
        ball_pos = self.game.get_ball_coords()
        paddle_coords = []

        # Проверяем, есть ли активные ракетки в команде 2
        if self.game.paddles_team2:
            # Используем координаты всех ракеток команды 2
            for row in self.game.paddles_team2:
                paddle_coords.extend([self.game.canvas.coords(paddle) for paddle in row])

            for coords in paddle_coords:
                if self.is_point_inside_rect(ball_pos[0], ball_pos[1], coords) or \
                   self.is_point_inside_rect(ball_pos[2], ball_pos[3], coords):
                    return 0.1  # Positive reward for successful ball deflection

        return 0

    def is_point_inside_rect(self, x, y, rect_coords):
        return rect_coords[0] <= x <= rect_coords[2] and rect_coords[1] <= y <= rect_coords[3]

    def update_neural_network(self):
        if not self.episode_data['states'] or not self.episode_data['actions'] or not self.episode_data['rewards']:
            return  # Избегаем обновления нейросети, если данные эпизода пусты

        input_data = self.get_input_data()
        self.episode_data['states'].append(input_data)
        action, log_probability = self.get_action()

        if self.game.goal_scored_flag:
            reward = 1  # Награда за забитый гол
        else:
            reward = 0

        self.episode_data['actions'].append(action)
        self.episode_data['rewards'].append(reward)

        if self.game.goal_scored_flag:
            self.game.reset_goal_scored_flag()

            # Обучение нейросети по эпизоду
            states_tensor = torch.tensor(self.episode_data['states'], dtype=torch.float32)
            actions_tensor = torch.tensor(self.episode_data['actions'], dtype=torch.long)
            rewards_tensor = torch.tensor(self.episode_data['rewards'], dtype=torch.float32)

            optimizer = optim.SGD(self.model.parameters(), lr=0.001)

            output_tensor = self.model(states_tensor)
            action_probabilities = F.softmax(output_tensor, dim=1)
            chosen_probabilities = torch.gather(action_probabilities, 1, actions_tensor.view(-1, 1))
            loss = -torch.sum(torch.log(chosen_probabilities) * rewards_tensor)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Сброс данных эпизода
            self.episode_data = {'states': [], 'actions': [], 'rewards': []}



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

        self.ball_radius = 10  # Выберите желаемый размер

        self.ball = self.canvas.create_oval(300 - self.ball_radius, 200 - self.ball_radius,
                                            300 + self.ball_radius, 200 + self.ball_radius,
                                            fill="white", outline="white")

        self.goal1 = self.canvas.create_rectangle(0, 120, 10, 280, fill="red", outline="red", tags="goal")
        self.goal2 = self.canvas.create_rectangle(590, 120, 600, 280, fill="blue", outline="blue", tags="goal")
        self.paddles_team1 = self.create_team_of_paddles("red", 50, 590)
        self.paddles_team2 = self.create_team_of_paddles("blue", 570, 10)
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

        self.ai_controller = AIController(self)
        self.ai_controller.update()

    def create_team_of_paddles(self, color, x_coord, goal_x_coord):
        paddles = []
        columns = [1, 4, 3, 3]

        paddle_width = 20
        paddle_height = 25
        vertical_spacing = (400 - len(columns) * paddle_height) / (len(columns) + 1)

        goal_height = 160

        for col, num_paddles in enumerate(columns):
            vertical_spacing = (400/num_paddles)/2
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
                self.move_active_rows(self.paddles_team1, -20)
            elif event.char.lower() == "s":
                self.move_active_rows(self.paddles_team1, 20)
            elif event.char.lower() == "i":
                self.move_active_rows(self.paddles_team2, -20)
            elif event.char.lower() == "k":
                self.move_active_rows(self.paddles_team2, 20)

    def move_row(self, row, dy):
        for paddle in row:
            self.move_paddle(paddle, dy)

    def move_active_rows(self, team, dy):
        can_move = True
        for row in team:
            for paddle in row:
                current_pos = self.canvas.coords(paddle)
                if not (0 < current_pos[1] + dy < 400) or not (0 < current_pos[3] + dy < 400):
                    can_move = False
                    break
        if can_move:
            for row in team:
                self.move_row(row, dy)

    def move_paddle(self, paddle, dy):
        current_pos = self.canvas.coords(paddle)
        if 0 < current_pos[1] + dy < 400 and 0 < current_pos[3] + dy < 400:
            self.canvas.move(paddle, 0, dy)

    def move_ball(self):
        if not self.paused:
            self.ai_controller.update()  # Add this line to update the AI
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

    def get_ball_coords(self):
        return self.canvas.coords(self.ball)

    def check_goal(self, ball_pos, goal):
        goal_coords = self.canvas.coords(goal)
        if ball_pos[1] >= goal_coords[1] and (ball_pos[3] <= goal_coords[3]):
            self.goal_scored_flag = True
            return True
        return False

    def check_collision(self, ball_pos, paddles):
        ball_center = [(ball_pos[0] + ball_pos[2]) / 2, (ball_pos[1] + ball_pos[3]) / 2]

        for paddle_row in paddles:
            for paddle in paddle_row:
                paddle_coords = self.canvas.coords(paddle)
                if paddle_coords[0] < ball_center[0] < paddle_coords[2] and paddle_coords[1] < ball_center[1] < paddle_coords[3]:
                    return True

        return False

    def goal_scored(self, player):
        if self.goal_scored_flag:
            self.goal_scored_flag = False
            self.reset_ball()
            if player == "Player1":
                self.player1_score += 1
                reward = 1  # Награда за забитый гол
            elif player == "Player2":
                self.player2_score += 1
                reward = -1  # Штраф за пропущенный гол
            self.update_score()
            return True, reward  # Возвращаем флаг и награду
        self.ai_controller.goal_scored_flag = False
        return False, 0  # Возвращаем флаг и нулевую награду


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