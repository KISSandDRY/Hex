import random
import pygame
import threading

from app.defs import *
from app.ui.renderer import *
from app.engine import hexlib
from app.ui.widgets import Button


class HexGameManager:

    def __init__(self, renderer, sound, board_size, mode, difficulty):
        self.renderer = renderer 
        self.sound = sound
        self.mode = mode
        self.difficulty = difficulty
        self.board_size = board_size

        self.board = hexlib.HexBoard(board_size, board_size)
        self.turn = PLAYER_1
        self.last_move = None
        self.winner = EMPTY
        self.winning_path = []

        self.thinking = False
        self.ai_move = -1

        if mode == GameMode.PVAI:
            self.human_player = random.choice([PLAYER_1, PLAYER_2])
        else:
            self.human_player = EMPTY

        self.exit_to_menu = False

        self.menu_btn = Button("Menu", hex_cfg.get_system("font_size"), 20, 20, 100, 40, self._menu_callback)

    def handle_event(self, event):
        if self.exit_to_menu:
            return "main_menu"

        if self.menu_btn.handle_event(event):
            self.sound.play("click")
            return

        if self.winner != EMPTY or self.thinking:
            return

        can_play = (self.mode == GameMode.PVP or self.turn == self.human_player)

        if can_play and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            grid_pos = self.renderer.pixel_to_grid(event.pos)
            if grid_pos:
                self._attempt_move(*grid_pos)

    def update(self):
        self.menu_btn.update()

        if self.winner == EMPTY and self.mode == GameMode.PVAI and self.turn != self.human_player:
            if not self.thinking:
                self.thinking = True
                threading.Thread(target=self._run_ai).start()

            if self.ai_move != -1:
                r, c = self.board.get_coord(self.ai_move)
                self._attempt_move(r, c)
                self.ai_move = -1
                self.thinking = False

    def draw(self):
        self.renderer.draw_game(
            self.board, 
            self.turn, 
            self.last_move, 
            self.winner,
            self.thinking,
            self.mode,
            self.human_player
        )
        self.menu_btn.draw(self.renderer.screen)

    def _run_ai(self):
        self.ai_move = hexlib.HexAI.get_move(self.board, self.turn, self.difficulty)

    def _attempt_move(self, r, c):
        if self.board.make_move(r, c, self.turn):
            self.sound.play("move")
            self.last_move = (r, c)
            
            winner = self.board.check_win()
            if winner != EMPTY:
                self.winner = winner
                is_win = (self.mode == GameMode.PVP) or (winner == self.human_player)
                self.sound.play("win" if is_win else "lose")
            else:
                self.turn = PLAYER_2 if self.turn == PLAYER_1 else PLAYER_1

    def _menu_callback(self):
        self.exit_to_menu = True
