import pygame

from .widgets import *
from .renderer import HexRenderer
from app.defs import GameMode, Difficulty
from app.config import hex_cfg
from app.engine.manager import HexGameManager


class State:

    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
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

    def handle_event(self, event):
        for el in self.ui_elements:
            if el.handle_event(event):
                if isinstance(el, Button):
                     self.app.sound.play("click")
                return 

    def update(self):
        for el in self.ui_elements:
            el.update()

    def _draw_ui(self):
        for el in self.ui_elements:
            el.draw(self.app.screen)

    def _draw_title(self, text, y, font = None):
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

            Button("Play", hex_cfg.get_system("font_size"), cx - btn_w // 2, cy - 50, btn_w, btn_h,
                   lambda: self.app.set_state(PlayMenuState)),

            Button("Settings", hex_cfg.get_system("font_size"), cx - btn_w // 2, cy - 50 + gap, btn_w, btn_h,
                   lambda: self.app.set_state(SettingsState)),

            Button("Quit", hex_cfg.get_system("font_size"), cx - btn_w // 2, cy - 50 + gap * 2, btn_w, btn_h,
                   self.app.quit),
            
            Image(hex_cfg.get_image("logo"), cx - 100, 50, 200, 200),
        ]

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
            Button("Back", hex_cfg.get_system("font_size"), cx - 100, 500, 200, 50,
                   lambda: app.set_state(MenuState)),
        ]

    def update(self):
        super().update()

        current_music = hex_cfg.get_default("music_volume")
        current_sfx = hex_cfg.get_default("sfx_volume")

        if self.slider_music.val != current_music:
            hex_cfg.update_setting("defaults", "music_volume", self.slider_music.val)
            self.app.sound.set_music_volume(self.slider_music.val)

        if self.slider_sfx.val != current_sfx:
            hex_cfg.update_setting("defaults", "sfx_volume", self.slider_sfx.val)
            self.app.sound.set_sfx_volume(self.slider_sfx.val)

    def draw(self):
        self._draw_ui()
        self._draw_title("Settings", 100)

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

            Button("Player vs Player", hex_cfg.get_system("font_size"), self.cx - 125, self.cy - 60, 250, 50,
                   lambda: self.app.set_state(GameState, mode=GameMode.PVP)),

            Button("Player vs AI", hex_cfg.get_system("font_size"), self.cx - 125, self.cy + 10, 250, 50,
                   self.show_difficulties),

            Button("Back", hex_cfg.get_system("font_size"), self.cx - 125, self.cy + 150, 250, 50,
                   lambda: self.app.set_state(MenuState)),
        ]

    def show_difficulties(self):
        self.ui_elements = [
            Background(),
            Button("Easy", hex_cfg.get_system("font_size"), self.cx - 125, self.cy - 60, 250, 50,
                   lambda: self._start_ai_game(Difficulty.EASY)),

            Button("Medium", hex_cfg.get_system("font_size"), self.cx - 125, self.cy + 10, 250, 50,
                   lambda: self._start_ai_game(Difficulty.MEDIUM)),

            Button("Hard", hex_cfg.get_system("font_size"), self.cx - 125, self.cy + 80, 250, 50,
                   lambda: self._start_ai_game(Difficulty.HARD)),
            
            Button("Back", hex_cfg.get_system("font_size"), self.cx - 125, self.cy + 180, 250, 50,
                   self.show_modes),
        ]

    def draw(self) -> None:
        self._draw_ui()
        self._draw_title("Select Mode", 100)

    def _start_ai_game(self, diff):
        self.app.set_state(GameState, mode=GameMode.PVAI, diff=diff)


class GameState(State):

    def __init__(self, app, mode=GameMode.PVP, diff=Difficulty.EASY):
        super().__init__(app)

        board_size = hex_cfg.get_default("board_size")
        
        self.renderer = HexRenderer(app.screen, board_size)
        self.manager = HexGameManager(
            self.renderer, 
            app.sound, 
            board_size, 
            mode, 
            diff
        )

        self.menu_btn = Button(
            "Menu", 
            hex_cfg.get_system("font_size"), 
            20, 20, 100, 40, 
            lambda: self.app.set_state(MenuState)
        )

    def handle_event(self, event):
        if self.menu_btn.handle_event(event):
            self.app.sound.play("click")
            return

        self.manager.handle_event(event)

    def update(self):
        self.menu_btn.update()
        self.manager.update()

    def draw(self):
        self.manager.draw()
        self.menu_btn.draw(self.app.screen)
