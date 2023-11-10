import tkinter as tk
from src.logic.table_football_logic import TableFootballLogic

class TableFootballGUI:
    def __init__(self, master, game_logic):
        self.master = master
        self.game_logic = TableFootballLogic(self, self.paddle1, self.paddle2)
        self.master.title("Table Football Game")

        self.canvas = tk.Canvas(self.master, width=600, height=400, bg="green")
        self.canvas.pack()

        self.game_logic.init_gui_elements(self.canvas)

        self.canvas.bind("<KeyPress>", self.game_logic.on_key_press)
        self.canvas.focus_set()

        self.score_label = tk.Label(self.master, text="Score: 0 - 0", font=("Helvetica", 12))
        self.score_label.pack()
