import os
import pygame

from hex_settings import *

class SoundManager:

    def __init__(self, initial_music_vol, initial_sfx_vol):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        self.sounds = {}
        self.music_vol = initial_music_vol
        self.sfx_vol = initial_sfx_vol
        
        self._load_assets()

    def _load_assets(self):
        for name, path in SFX_PATHS.items():
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.sfx_vol)
                    self.sounds[name] = snd

                except pygame.error:
                    print(f"Error loading SFX: {name}")

        if os.path.exists(THEME_SONG):
            try:
                pygame.mixer.music.load(THEME_SONG)
                pygame.mixer.music.set_volume(self.music_vol)
                pygame.mixer.music.play(-1)

            except pygame.error:
                print("Error loading music")

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def set_music_volume(self, val):
        self.music_vol = val
        pygame.mixer.music.set_volume(self.music_vol)

    def set_sfx_volume(self, val):
        self.sfx_vol = val
        for snd in self.sounds.values():
            snd.set_volume(self.sfx_vol)
