import math
import random
import pygame
import threading

import hexlib
import hex_draw
from hex_gui import Button
from hex_config import hex_cfg
from hex_defs import PLAYER_1, PLAYER_2, EMPTY, GameMode


class HexGameManager:

    def __init__(self, screen, sound, board_size, mode, difficulty):
        self.screen = screen
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
        self.ai_thread = None
        self.ai_move = -1

        self.human_player = self._assign_human_player()
        self.exit_to_menu = False

        self.menu_btn = Button("Menu", 20, 20, 100, 40, self._menu_callback)
        self.render_cfg = self._init_render_config()

        self._calc_offset()

    def handle_input(self, events):
        if self.menu_btn.update(events):
            self.sound.play("click")

        if self.exit_to_menu:
            return "main_menu"

        if self.winner != EMPTY or self.thinking:
            return

        if not self._is_ai_turn():
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._on_click(pygame.mouse.get_pos())

    def update(self):
        if self.mode == GameMode.PVAI and self.winner == EMPTY:
            if self._is_ai_turn():
                self._start_ai_thread_if_needed()
                self._apply_ai_move_if_ready()

    def draw(self):
        self.screen.fill(hex_cfg.get_color("bg"))
        hex_draw.draw_board(self.screen, self.board, self.render_cfg, self.turn, self.last_move)

        if self.winner != EMPTY:
            hex_draw.draw_winning_path(self.screen, self.board, self.winner, self.render_cfg)
            self._draw_winner_text()
        else:
            self._draw_turn_label()

        self.menu_btn.draw(self.screen)

    def _assign_human_player(self):
        return random.choice([PLAYER_1, PLAYER_2]) if self.mode == GameMode.PVAI else EMPTY

    def _init_render_config(self):
        tile_size = hex_cfg.get_system("tile_size")

        if self.board_size > 15:
            tile_size -= 12

        elif self.board_size > 11:
            tile_size -= 8

        return {"tile_size": tile_size, "offset_x": 0, "offset_y": 0}

    def _draw_turn_label(self):
        p_name = "Red" if self.turn == PLAYER_1 else "Blue"
        txt = "Thinking..." if self.thinking else f"Turn: {p_name}"
        color = hex_cfg.get_color("text") if self.thinking else (hex_cfg.get_color("p1") if self.turn == PLAYER_1 else hex_cfg.get_color("p2"))
        
        if self.mode == GameMode.PVAI:
            txt += " (You)" if self.turn == self.human_player else " (AI)"

        self._draw_text(txt, color, (140, 25), hex_cfg.get_system("font_size"))

    def _draw_winner_text(self):
        winner_name = "Red" if self.winner == PLAYER_1 else "Blue"
        msg = f"{winner_name} wins!"
        self._draw_centered_boxed_text(msg, hex_cfg.get_color("win_path"), 50)

    def _is_ai_turn(self):
        return self.mode == GameMode.PVAI and self.turn != self.human_player

    def _start_ai_thread_if_needed(self):
        if not self.thinking:
            self.thinking = True
            self.ai_thread = threading.Thread(target=self._run_ai)
            self.ai_thread.start()

    def _apply_ai_move_if_ready(self):
        if self.ai_move != -1:
            self._apply_move_index(self.ai_move)
            self.ai_move = -1
            self.thinking = False

    def _run_ai(self):
        move = -1
        move = hexlib.HexAI.get_move(self.board, self.turn, self.difficulty)
        self.ai_move = move

    def _on_click(self, pos):
        # Identifying what hexagon was clicked by measuring distance 

        size = self.render_cfg["tile_size"]
        off_x, off_y = self.render_cfg["offset_x"], self.render_cfg["offset_y"]
        mx, my = pos

        best_dist = 1e9
        best_move = None

        for idx in self.board.get_legal_moves():
            r, c = self.board.get_coord(idx)
            px, py = hex_draw.grid_to_pixel(r, c, size, off_x, off_y)
            dist = (px - mx) ** 2 + (py - my) ** 2

            if dist < size**2 and dist < best_dist:
                best_dist = dist
                best_move = (r, c)

        if best_move:
            self._apply_move(*best_move)

    def _apply_move(self, r, c):
        if not self.board.make_move(r, c, self.turn):
            return

        self.last_move = (r, c)
        self.sound.play("move")
        self._check_for_winner_or_continue()

    def _apply_move_index(self, index):
        r, c = self.board.get_coord(index)
        self._apply_move(r, c)

    def _check_for_winner_or_continue(self):
        winner = self.board.check_win()

        if winner != EMPTY:
            self.winner = winner
            human_won = self.mode == GameMode.PVP or self.winner == self.human_player
            self.sound.play("win" if human_won else "lose")
        else:
            self.turn = PLAYER_2 if self.turn == PLAYER_1 else PLAYER_1

    def _menu_callback(self):
        self.exit_to_menu = True

    def _calc_offset(self):
        size = self.render_cfg["tile_size"]
        hex_w, hex_h = size * math.sqrt(3), size * 2

        board_px_w = 0.75 * hex_w * self.board_size + hex_w
        board_px_h = hex_h * self.board_size

        self.render_cfg["offset_x"] = int((hex_cfg.get_system("width") - board_px_w) // 2)
        self.render_cfg["offset_y"] = (hex_cfg.get_system("height") - board_px_h) // 2 + 100

    def _draw_text(self, text, color, pos, size):
        font = pygame.font.SysFont(hex_cfg.get_system("font_name"), size)
        surf = font.render(text, True, color)

        self.screen.blit(surf, pos)

    def _draw_centered_boxed_text(self, msg, color, font_size):
        font = pygame.font.SysFont(hex_cfg.get_system("font_name"), font_size)
        surf = font.render(msg, True, color)
        rect = surf.get_rect(center=(hex_cfg.get_system("width") // 2, hex_cfg.get_system("height") // 2))
        bg_rect = rect.inflate(20, 20)

        pygame.draw.rect(self.screen, (20, 25, 40), bg_rect)
        pygame.draw.rect(self.screen, color, bg_rect, 3)

        self.screen.blit(surf, rect)
