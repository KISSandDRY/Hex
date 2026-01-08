import os
import sys
import pygame

from app.ui import MenuState
from app.config import hex_cfg
from app.utils import SoundManager


class Hex:

    def __init__(self):
        pygame.init()
        
        self.screen = pygame.display.set_mode((hex_cfg.get_system("width"), hex_cfg.get_system("height")))
        pygame.display.set_caption(hex_cfg.get_system("caption"))

        icon_path = hex_cfg.get_image("logo")

        if os.path.exists(icon_path):
            pygame.display.set_icon(pygame.image.load(icon_path))

        self.sound = SoundManager(hex_cfg.get_default("music_volume"), hex_cfg.get_default("sfx_volume"))
        self.clock = pygame.time.Clock()

        # Start with main menu state
        self.set_state(MenuState)

    def set_state(self, state, **kwargs):
        self.state = state(self, **kwargs)

    def quit(self):
        hex_cfg.save()
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            
                if self.state:
                    self.state.handle_event(event)

            if self.state:
                self.state.update()

            if self.state:
                self.state.draw()

            pygame.display.flip()
            self.clock.tick(hex_cfg.get_system("fps"))


if __name__ == "__main__":
    game = Hex()
    game.run()
