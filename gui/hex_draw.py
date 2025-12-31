import math
import pygame
import pygame.gfxdraw
from functools import lru_cache

from hex_config import hex_cfg
from hex_defs import PLAYER_1, PLAYER_2

@lru_cache(maxsize=256)
def get_hex_corners(center_x, center_y, size):
    # Get (x, y) corners of hex
    # Order: [TopRight, BottomRight, Bottom, BottomLeft, TopLeft, Top]

    points = []

    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)

        points.append((
            center_x + size * math.cos(angle_rad),
            center_y + size * math.sin(angle_rad)
        ))

    return points 

def grid_to_pixel(r, c, size, offset_x, offset_y):
    # (row, col) to (x, y)
    # Pointy Top, Odd-Row offset

    width = size * math.sqrt(3)
    height = size * 2

    x = (c + (r % 2) / 2.0) * width
    y = r * (height * 0.75)

    return int(x + offset_x), int(y + offset_y)

def draw_hex_top_border(surface, points, color, width=4):
    draw_points = [points[0], points[5], points[4]]
    draw_thick_aalines(surface, color, draw_points, width)

def draw_hex_bottom_border(surface, points, color, width=4):
    draw_points = [points[3], points[2], points[1]]
    draw_thick_aalines(surface, color, draw_points, width)

def draw_hex_left_border(surface, points, r, color, width=4):
    if r & 1: 
        draw_points = [points[4], points[3]]
    else: 
        draw_points = [points[5], points[4], points[3], points[2]]

    draw_thick_aalines(surface, color, draw_points, width)

def draw_hex_right_border(surface, points, r, color, width=4):
    if r & 1: 
        draw_points = [points[5], points[0], points[1], points[2]]
    else: 
        draw_points = [points[0], points[1]]

    draw_thick_aalines(surface, color, draw_points, width)

def draw_border(surface, rows, cols, size, off_x, off_y, current_turn):
    p1_border_color = hex_cfg.get_color("p1") if current_turn == PLAYER_1 else hex_cfg.get_color("inactive_border")
    p2_border_color = hex_cfg.get_color("p2") if current_turn == PLAYER_2 else hex_cfg.get_color("inactive_border")

    for r in range(rows):
        cx, cy = grid_to_pixel(r, 0, size, off_x, off_y)
        points = get_hex_corners(cx, cy, size)
        draw_hex_left_border(surface, points, r, p1_border_color, 3)

    for r in range(rows):
        cx, cy = grid_to_pixel(r, cols-1, size, off_x, off_y)
        points = get_hex_corners(cx, cy, size)
        draw_hex_right_border(surface, points, r, p1_border_color, 3)

    for c in range(cols):
        cx, cy = grid_to_pixel(0, c, size, off_x, off_y)
        points = get_hex_corners(cx, cy, size)
        draw_hex_top_border(surface, points, p2_border_color, 3)

    for c in range(cols):
        cx, cy = grid_to_pixel(rows-1, c, size, off_x, off_y)
        points = get_hex_corners(cx, cy, size)
        draw_hex_bottom_border(surface, points, p2_border_color, 3)

def draw_board(surface, board, screen_config, current_turn, last_move=None):
    rows, cols = board.rows, board.cols
    off_x, off_y  = screen_config["offset_x"], screen_config["offset_y"]
    size = screen_config["tile_size"]

    for r in range(rows):
        for c in range(cols):
            val = board.get_cell(r, c)
            cx, cy = grid_to_pixel(r, c, size, off_x, off_y)
            points = get_hex_corners(cx, cy, size)

            color = hex_cfg.get_color("empty_hex")
            width = 1
            if val == PLAYER_1:
                color = hex_cfg.get_color("p1")
                width = 0
            elif val == PLAYER_2:
                color = hex_cfg.get_color("p2")
                width = 0

            pygame.draw.polygon(surface, color, points, width)
            pygame.draw.aalines(surface, hex_cfg.get_color("border"), True, points)

            if last_move and last_move == (r, c):
                highlight_size = size * 0.6 
                highlight_points = get_hex_corners(cx, cy, highlight_size)
                pygame.gfxdraw.filled_polygon(surface, highlight_points, (255, 255, 255, 100))

    draw_border(surface, rows, cols, size, off_x, off_y, current_turn)

def draw_winning_path(surface, board, winner, screen_config):
    path_indices = board.get_winning_path(winner)

    if not path_indices:
        return

    points = []
    size = screen_config["tile_size"]
    off_x, off_y = screen_config["offset_x"], screen_config["offset_y"]

    for idx in path_indices:
        coord = board.get_coord(idx)
        px, py = grid_to_pixel(coord[0], coord[1], size, off_x, off_y)
        points.append((px, py))

    draw_thick_aalines(surface, hex_cfg.get_color("win_path"), points, width=5)

def draw_thick_aalines(surface, color, points, width=6):
    if len(points) > 1:
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i+1]

            draw_thick_aaline(surface, color, start, end, width)

def draw_thick_aaline(surface, color, start_pos, end_pos, width):
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
    
    pygame.gfxdraw.filled_polygon(surface, points, color)
    pygame.gfxdraw.aapolygon(surface, points, color)
