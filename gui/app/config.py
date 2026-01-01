import os
import json


class HexConfig:

    _instance = None

    DEFAULT_PATH = os.path.join("../resources", "settings.json")
    USER_PATH = "../resources/user_settings.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HexConfig, cls).__new__(cls)
            cls._instance._load()

        return cls._instance

    def _load(self):
        self.data = {}
        
        try:
            with open(self.DEFAULT_PATH, 'r') as f:
                self.data = json.load(f)

        except FileNotFoundError:
            raise RuntimeError(f"{self.DEFAULT_PATH} not found!")

        if os.path.exists(self.USER_PATH):
            try:
                with open(self.USER_PATH, 'r') as f:
                    user_data = json.load(f)
                    self._deep_update(self.data, user_data)

            except json.JSONDecodeError:
                print("User settings corrupted. Reverting to defaults.")

        self.audio_dir = self.data["audio"]["audio_dir"]
        self.images_dir = self.data["images"]["images_dir"]

    def save(self):
        save_data = {
            "defaults": self.data["defaults"],
        }

        try:
            with open(self.USER_PATH, 'w') as f:
                json.dump(save_data, f, indent=4)
                
        except IOError as e:
            print(f"Failed to save settings: {e}")

    def update_setting(self, section, key, value):
        if section in self.data and key in self.data[section]:
            self.data[section][key] = value
        else:
            print(f"Warning: Key {key} not found in section {section}")

    def _deep_update(self, original, update):
        for key, value in update.items():
            if isinstance(value, dict) and key in original:
                self._deep_update(original[key], value)
            else:
                original[key] = value

    def get_color(self, name):
        return tuple(self.data["colors"][name])

    def get_system(self, name):
        return self.data["system"][name]

    def get_default(self, name):
        return self.data["defaults"][name]

    def get_image(self, name):
        filename = self.data["images"][name]
        return os.path.join(self.images_dir, filename)

    def get_sound(self, name):
        audio_block = self.data["audio"]
        
        if "sfx" in audio_block and name in audio_block["sfx"]:
            filename = audio_block["sfx"][name]
        
        elif name in audio_block:
            filename = audio_block[name]
            
        else:
            raise KeyError(f"Sound '{name}' not found in settings.")
            
        return os.path.join(self.audio_dir, filename)

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]

        raise AttributeError(f"'HexConfig' object has no attribute '{name}'")


hex_cfg = HexConfig()
