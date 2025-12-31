import pygame

import hexlib
import hex_game
from hex_defs import GameMode
from hex_config import hex_cfg
from hex_gui import Background, Button, Image, Label, Slider, Selector

class State:

    def __init__(self, app):
        self.app = app

    def handle_input(self, events):
        pass

    def update(self) -> None:
        pass

    def draw(self) -> None:
        pass


class UIState(State):

    def __init__(self, app):
        super().__init__(app)
        self.ui_elements = []
        self._header_font = pygame.font.SysFont(hex_cfg.get_system("font_name"), hex_cfg.get_system("header_size"))
        self._title_font = pygame.font.SysFont(hex_cfg.get_system("font_name"), 60)

    def _handle_ui(self, events):
        for el in self.ui_elements:
            if hasattr(el, "update"):
                clicked = el.update(events)
                if isinstance(el, Button) and clicked:
                    self.app.sound.play("click")

    def _draw_ui(self):
        for el in self.ui_elements:
            el.draw(self.app.screen)

    def _draw_title(self, text, y = 100, font = None):
        font = font or self._title_font
        surf = font.render(text, True, hex_cfg.get_color("accent"))
        rect = surf.get_rect(center=(hex_cfg.get_system("width") // 2, y))

        self.app.screen.blit(surf, rect)


class MenuState(UIState):

    def __init__(self, app):
        super().__init__(app)
        cx, cy = hex_cfg.get_system("width") // 2, hex_cfg.get_system("height") // 2
        btn_w, btn_h, gap = 250, 50, 70

        self.ui_elements = [
            Background(),

            Button("Play", cx - btn_w // 2, cy - 50, btn_w, btn_h,
                   lambda: self.app.change_state("play_menu")),

            Button("Settings", cx - btn_w // 2, cy - 50 + gap, btn_w, btn_h,
                   lambda: self.app.change_state("settings")),

            Button("Quit", cx - btn_w // 2, cy - 50 + gap * 2, btn_w, btn_h,
                   self.app.quit),
            
            Image(hex_cfg.get_image("logo"), cx - 100, 50, 200, 200),
        ]

    def handle_input(self, events):
        self._handle_ui(events)

    def draw(self) -> None:
        self._draw_ui()


class SettingsState(UIState):

    def __init__(self, app):
        super().__init__(app)
        cx = hex_cfg.get_system("width") // 2

        current_music = hex_cfg.get_default("music_volume")
        current_sfx = hex_cfg.get_default("sfx_volume")
        current_size = hex_cfg.get_default("board_size")

        self.slider_music = Slider(cx + 50, 285, 200, 20, 0.0, 1.0, current_music)
        self.slider_sfx = Slider(cx + 50, 345, 200, 20, 0.0, 1.0, current_sfx)
        self.selector_size = Selector(cx + 50, 195, 200, 40,
                                      [7, 9, 11, 13, 15],
                                      current_size,
                                      self._set_size)

        self.ui_elements = [
            Background(),
            Label("Board Size:", cx - 150, 200),
            Label("Music:", cx - 150, 280),
            Label("SFX:", cx - 150, 340),
            self.selector_size,
            self.slider_music,
            self.slider_sfx,
            Button("Back", cx - 100, 500, 200, 50,
                   lambda: app.change_state("main_menu")),
        ]

    def handle_input(self, events):
        self._handle_ui(events)

    def update(self):
        current_music = hex_cfg.get_default("music_volume")
        current_sfx = hex_cfg.get_default("sfx_volume")

        if self.slider_music.val != current_music:
            hex_cfg.update_setting("defaults", "music_volume", self.slider_music.val)
            self.app.sound.set_music_volume(self.slider_music.val)

        if self.slider_sfx.val != current_sfx:
            hex_cfg.update_setting("defaults", "sfx_volume", self.slider_sfx.val)
            self.app.sound.set_sfx_volume(self.slider_sfx.val)

        super().update()

    def draw(self):
        self._draw_ui()
        self._draw_title("Settings", hex_cfg.get_system("header_size"))

    def _set_size(self, val):
        hex_cfg.update_setting("defaults", "board_size", val)


class PlayMenuState(UIState):

    def __init__(self, app):
        super().__init__(app)

        self.cx, self.cy = hex_cfg.get_system("width") // 2, hex_cfg.get_system("height") // 2

        self.show_modes()

    def show_modes(self):
        self.ui_elements = [
            Background(),

            Button("Player vs Player", self.cx - 125, self.cy - 60, 250, 50,
                   lambda: self.app.change_state("game", mode=GameMode.PVP)),
        
            Button("Player vs AI", self.cx - 125, self.cy + 10, 250, 50,
                   self.show_difficulties),

            Button("Back", self.cx - 125, self.cy + 150, 250, 50,
                   lambda: self.app.change_state("main_menu")),
        ]

    def show_difficulties(self):
        self.ui_elements = [
            Background(),

            Button("Easy", self.cx - 125, self.cy - 60, 250, 50,
                   lambda: self._start_ai_game(hexlib.Difficulty.EASY)),

            Button("Medium", self.cx - 125, self.cy + 10, 250, 50,
                   lambda: self._start_ai_game(hexlib.Difficulty.MEDIUM)),

            Button("Hard", self.cx - 125, self.cy + 80, 250, 50,
                   lambda: self._start_ai_game(hexlib.Difficulty.HARD)),

            Button("Back", self.cx - 125, self.cy + 180, 250, 50,
                   self.show_modes),
        ]

    def handle_input(self, events: list[pygame.event.Event]) -> None:
        self._handle_ui(events)

    def draw(self) -> None:
        self._draw_ui()
        self._draw_title("Select Mode", 100)

    def _start_ai_game(self, diff):
        self.app.change_state("game", mode=GameMode.PVAI, diff=hexlib.Difficulty(diff))


class GameState(State):

    def __init__(self, app, mode=GameMode.PVP, diff=hexlib.Difficulty.EASY):
        super().__init__(app)

        board_size = hex_cfg.get_default("board_size")
        
        self.manager = hex_game.HexGameManager(
            app.screen, app.sound, board_size, mode, diff
        )

    def handle_input(self, events):
        if self.manager.handle_input(events) == "main_menu":
            self.app.change_state("main_menu")

    def update(self):
        self.manager.update()

    def draw(self):
        self.manager.draw()


STATE_MAP = {
    "main_menu": MenuState,
    "settings": SettingsState,
    "play_menu": PlayMenuState,
    "game": GameState
}
