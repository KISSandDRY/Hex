import os
import sys
import pygame

from hex_settings import *
from hex_sfx import SoundManager
from hex_states import STATE_MAP


class Hex:

    def __init__(self):
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(CAPTION)
        if os.path.exists(ICON_PATH):
            pygame.display.set_icon(pygame.image.load(ICON_PATH))

        self.config = DEFAULT_CONFIG.copy()
        self.sound = SoundManager(self.config['music_volume'], self.config['sfx_volume'])
        self.clock = pygame.time.Clock()

        # Start with main menu state
        self.change_state("main_menu")

    def change_state(self, state_name, **kwargs):
        state = STATE_MAP.get(state_name)

        if not state:
            raise ValueError(f"Unknown state: {state_name}")
        
        self.state = state(self, **kwargs)

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.quit()
            
            if self.state:
                self.state.handle_input(events)
                self.state.update()
                self.state.draw()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Hex()
    game.run()
