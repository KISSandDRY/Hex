import os
import pygame

from app.config import hex_cfg

class SoundManager:

    def __init__(self, initial_music_vol, initial_sfx_vol):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        self.sounds = {}
        self.music_vol = initial_music_vol
        self.sfx_vol = initial_sfx_vol
        
        self.sounds = {}
        self._load_assets()

    def _load_assets(self):
        if "audio" in hex_cfg.data and "sfx" in hex_cfg.data["audio"]:
            sfx_data = hex_cfg.data["audio"]["sfx"]

            for name in sfx_data:
                try:
                    path = hex_cfg.get_sound(name)

                    if os.path.exists(path):
                        snd = pygame.mixer.Sound(path)
                        snd.set_volume(self.sfx_vol)
                        self.sounds[name] = snd
                    else:
                        print(f"Warning: SFX file not found: {path}")

                except (pygame.error, KeyError) as e:
                    print(f"Error loading SFX '{name}': {e}")

        try:
            theme_path = hex_cfg.get_sound("theme_song")

            if os.path.exists(theme_path):
                pygame.mixer.music.load(theme_path)
                pygame.mixer.music.set_volume(self.music_vol)
                pygame.mixer.music.play(-1)
            else:
                 print(f"Warning: Music file not found: {theme_path}")

        except (pygame.error, KeyError) as e:
            print(f"Error loading music: {e}")

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
