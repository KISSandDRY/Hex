import math
import pygame
import pygame.gfxdraw
from functools import lru_cache

from app.defs import *
from app.config import hex_cfg

class HexRenderer:

    def __init__(self, screen, board_size):
        self.screen = screen
        self.board_size = board_size
        self.font = pygame.font.SysFont(
            hex_cfg.get_system("font_name"), 
            hex_cfg.get_system("font_size")
        )

        self._recalculate_layout()

    def draw_game(self, board, turn, last_move=None, winner=None, thinking=False, mode=None, human_player=None):
        self.screen.fill(hex_cfg.get_color("bg"))
        self._draw_board(board, turn, last_move)
        
        if winner:
            self._draw_winning_path(board, winner)
            self._draw_overlay_text(f"{'Red' if winner == PLAYER_1 else 'Blue'} Wins!", 50, hex_cfg.get_color("win_path"))
        else:
            self._draw_turn_info(turn, thinking, mode, human_player)

    def pixel_to_grid(self, pos):
        mx, my = pos
        hex_radius_sq = self.tile_size ** 2
        
        best_dist = hex_radius_sq
        best_coord = None

        for r in range(self.board_size):
            for c in range(self.board_size):
                cx, cy = self.grid_to_pixel(r, c)
                dist_sq = (cx - mx)**2 + (cy - my)**2
                
                if dist_sq < best_dist:
                    best_dist = dist_sq
                    best_coord = (r, c)
        
        return best_coord

    def grid_to_pixel(self, r, c):
        # (row, col) to (x, y)
        # Pointy Top, Odd-Row offset

        width = self.tile_size * math.sqrt(3)
        height = self.tile_size * 2

        x = (c + (r % 2) / 2.0) * width
        y = r * (height * 0.75)

        return int(x + self.off_x), int(y + self.off_y)

    def _recalculate_layout(self):
        self.tile_size = hex_cfg.get_system("tile_size")

        if self.board_size > 15: 
            self.tile_size -= 12
        elif self.board_size > 11: 
            self.tile_size -= 8

        hex_w, hex_h = self.tile_size * math.sqrt(3), self.tile_size * 2

        board_px_w = 0.75 * hex_w * self.board_size + hex_w
        board_px_h = hex_h * self.board_size

        self.off_x = int((hex_cfg.get_system("width") - board_px_w) // 2)
        self.off_y = (hex_cfg.get_system("height") - board_px_h) // 2 + 100

    @lru_cache(maxsize=256)
    def _get_hex_corners(self, cx, cy, size=None):
        # Get (x, y) corners of hex
        # Order: [TopRight, BottomRight, Bottom, BottomLeft, TopLeft, Top]

        if size is None: 
            size = self.tile_size

        points = []

        for i in range(6):
            deg = 60 * i - 30
            rad = math.radians(deg)

            points.append((
                cx + size * math.cos(rad),
                cy + size * math.sin(rad)
            ))

        return points 


    def _draw_turn_info(self, turn, thinking, mode, human_player):
        if thinking:
            color = hex_cfg.get_color("text") 
        else:
            color = hex_cfg.get_color("p1") if turn == PLAYER_1 else hex_cfg.get_color("p2")

        p_name = "Red" if turn == PLAYER_1 else "Blue"
        
        if thinking:
            text = "Thinking..."
        else:
            text = f"Turn: {p_name}"
            
            if mode == GameMode.PVAI and human_player is not None:
                is_human = (turn == human_player)
                text += " (You)" if is_human else " (AI)"

        surf = self.font.render(text, True, color)
        self.screen.blit(surf, (140, 25))

    def _draw_overlay_text(self, text, font_size, color):
        cx, cy = hex_cfg.get_system("width") // 2, hex_cfg.get_system("height") // 2
        font = pygame.font.SysFont(hex_cfg.get_system("font_name"), font_size)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(cx, cy))
        bg = rect.inflate(20, 20)

        pygame.draw.rect(self.screen, (20, 25, 40), bg)
        pygame.draw.rect(self.screen, color, bg, 2)

        self.screen.blit(surf, rect)

    def _draw_board_top_border(self, points, color, width=4):
        draw_points = [points[0], points[5], points[4]]
        self._draw_thick_aalines(color, draw_points, width)

    def _draw_board_bottom_border(self, points, color, width=4):
        draw_points = [points[3], points[2], points[1]]
        self._draw_thick_aalines(color, draw_points, width)

    def _draw_board_left_border(self, points, r, color, width=4):
        if r & 1: 
            draw_points = [points[4], points[3]]
        else: 
            draw_points = [points[5], points[4], points[3], points[2]]

        self._draw_thick_aalines(color, draw_points, width)

    def _draw_board_right_border(self, points, r, color, width=4):
        if r & 1: 
            draw_points = [points[5], points[0], points[1], points[2]]
        else: 
            draw_points = [points[0], points[1]]

        self._draw_thick_aalines(color, draw_points, width)

    def _draw_border(self, rows, cols, turn):
        p1_border_color = hex_cfg.get_color("p1") if turn == PLAYER_1 else hex_cfg.get_color("inactive_border")
        p2_border_color = hex_cfg.get_color("p2") if turn == PLAYER_2 else hex_cfg.get_color("inactive_border")

        for r in range(rows):
            cx, cy = self.grid_to_pixel(r, 0)
            points = self._get_hex_corners(cx, cy)
            self._draw_board_left_border(points, r, p1_border_color, 3)

        for r in range(rows):
            cx, cy = self.grid_to_pixel(r, cols-1)
            points = self._get_hex_corners(cx, cy)
            self._draw_board_right_border(points, r, p1_border_color, 3)

        for c in range(cols):
            cx, cy = self.grid_to_pixel(0, c)
            points = self._get_hex_corners(cx, cy)
            self._draw_board_top_border(points, p2_border_color, 3)

        for c in range(cols):
            cx, cy = self.grid_to_pixel(rows-1, c)
            points = self._get_hex_corners(cx, cy)
            self._draw_board_bottom_border(points, p2_border_color, 3)

    def _draw_board(self, board, turn, last_move):
        rows, cols = board.rows, board.cols

        for r in range(rows):
            for c in range(cols):
                val = board.get_cell(r, c)
                cx, cy = self.grid_to_pixel(r, c)
                points = self._get_hex_corners(cx, cy, self.tile_size)

                color = hex_cfg.get_color("empty_hex")
                width = 1
                if val == PLAYER_1:
                    color = hex_cfg.get_color("p1")
                    width = 0
                elif val == PLAYER_2:
                    color = hex_cfg.get_color("p2")
                    width = 0

                pygame.draw.polygon(self.screen, color, points, width)
                pygame.draw.aalines(self.screen, hex_cfg.get_color("border"), True, points)

                if last_move == (r, c):
                    highlight_size = self.tile_size * 0.6 
                    highlight_points = self._get_hex_corners(cx, cy, highlight_size)
                    pygame.gfxdraw.filled_polygon(self.screen, highlight_points, (255, 255, 255, 100))

        self._draw_border(rows, cols, turn)

    def _draw_winning_path(self, board, winner):
        path_indices = board.get_winning_path(winner)

        if not path_indices:
            return

        points = []
        for idx in path_indices:
            r, c = board.get_coord(idx)
            points.append(self.grid_to_pixel(r, c))

        self._draw_thick_aalines(hex_cfg.get_color("win_path"), points, width=5)

    def _draw_thick_aalines(self, color, points, width=6):
        if len(points) > 1:
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i+1]

                self._draw_thick_aaline(color, start, end, width)

    def _draw_thick_aaline(self, color, start_pos, end_pos, width):
        # https://stackoverflow.com/questions/30578068/pygame-draw-anti-aliased-thick-line
        # Idea: replace line with rotated rectangle with rotation matrix
        # since pygame can draw antialiased rectangles by
        # drawing filled polygon with antialiased outline

        x0, y0 = start_pos
        x1, y1 = end_pos
        
        center_x = (x0 + x1) / 2.0
        center_y = (y0 + y1) / 2.0
        length = math.hypot(x1 - x0, y1 - y0)
        
        angle = math.atan2(y0 - y1, x0 - x1)
        
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        
        half_len = length / 2.0
        half_thick = width / 2.0
        
        ul = ( center_x + (half_len * cos_a) - (half_thick * sin_a),
               center_y + (half_thick * cos_a) + (half_len * sin_a))
        
        ur = ( center_x - (half_len * cos_a) - (half_thick * sin_a),
               center_y + (half_thick * cos_a) - (half_len * sin_a))
        
        bl = ( center_x + (half_len * cos_a) + (half_thick * sin_a),
               center_y - (half_thick * cos_a) + (half_len * sin_a))
        
        br = ( center_x - (half_len * cos_a) + (half_thick * sin_a),
               center_y - (half_thick * cos_a) - (half_len * sin_a))
        
        points = [ul, ur, br, bl]
        
        pygame.gfxdraw.filled_polygon(self.screen, points, color)
        pygame.gfxdraw.aapolygon(self.screen, points, color)
