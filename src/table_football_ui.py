import tkinter as tk
from table_football_logic import TableFootballGame


class GameMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Настольный футбол")

        # Увеличенная ширина
        self.root.geometry("600x400")

        # Кнопка "Игра" с увеличенным размером
        play_button = tk.Button(root, text="Игра", command=self.start_game, width=50, height=5)
        play_button.pack(pady=10)

        # Кнопка "Настройки" с увеличенным размером
        settings_button = tk.Button(root, text="Настройки", command=self.open_settings, width=50, height=5)
        settings_button.pack(pady=10)

        # Кнопка "Выход" с увеличенным размером
        exit_button = tk.Button(root, text="Выход", command=self.exit_game, width=50, height=5)
        exit_button.pack(pady=10)

    def start_game(self):
        # Очищаем текущий экран
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создаем объект игры
        game = TableFootballGame(self.root)
        game.move_ball()

        # Запускаем главный цикл Tkinter
        self.root.mainloop()

    def open_settings(self):
        # Очищает текущий экран и отображает страницу настроек
        for widget in self.root.winfo_children():
            widget.destroy()

        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=20)

        # Кнопка "Вернуться в меню" на странице настроек
        return_button = tk.Button(settings_frame, text="Вернуться в меню", command=self.return_to_menu, width=20)
        return_button.pack(pady=10)

    def return_to_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        menu = GameMenu(self.root)

    def exit_game(self):
        # Функция для выхода из игры
        self.root.destroy()
