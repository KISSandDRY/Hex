import os
import hexlib

PLAYER_1 = hexlib.PLAYER_1
PLAYER_2 = hexlib.PLAYER_2
EMPTY = hexlib.EMPTY

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 720
FPS = 60
CAPTION = "Hex"
HEX_TILE_SIZE = 30

# Resources
LOGO_PATH = "../resources/logo.png"
ICON_PATH = LOGO_PATH
BG_IMAGE_PATH = "../resources/bg.png"
AUDIO_DIR = "../resources/audio"
THEME_SONG = os.path.join(AUDIO_DIR, "theme.mp3")

# Sound Effects Map
SFX_PATHS = {
    "click": os.path.join(AUDIO_DIR, "click.mp3"),
    "win":   os.path.join(AUDIO_DIR, "win.mp3"),
    "lose":  os.path.join(AUDIO_DIR, "lose.mp3"),
    "move":  os.path.join(AUDIO_DIR, "click.mp3")
}

# Fonts
FONT_NAME = "Bahnschrift" 
HEADER_SIZE = 60
FONT_SIZE = 30

# Colors
BG_COLOR = (30, 32, 40)
PANEL_COLOR = (45, 48, 55)
TEXT_COLOR = (240, 240, 240)
ACCENT_COLOR = (100, 180, 255)
HOVER_COLOR = (60, 100, 200)
BORDER_COLOR = (80, 80, 90)

P1_COLOR = (255, 80, 80)
P2_COLOR = (50, 100, 255)
INACTIVE_BORDER_COLOR = (60, 60, 70)

EMPTY_HEX_COLOR = (60, 60, 65)
HEX_BORDER = (100, 100, 100)
WIN_PATH_COLOR = (255, 215, 0)

class GameMode:
    PVP = 0
    PVAI = 1

DEFAULT_CONFIG = {
    'board_size': 11,
    'music_volume': 0.5,
    'sfx_volume': 0.7
}
