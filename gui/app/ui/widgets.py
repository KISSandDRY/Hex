import os
import pygame
from typing import Optional

from app.config import hex_cfg


class UIElement:

    def draw(self, screen): 
        pass

    def update(self) -> Optional[bool]: 
        pass

    def handle_event(self, event) -> Optional[bool]: 
        return False


class Label(UIElement):

    def __init__(self, text, x, y, font_size=hex_cfg.get_system("font_size"), color=hex_cfg.get_color("text")):
        self.font = pygame.font.SysFont(hex_cfg.get_system("font_name"), font_size)
        self.surf = self.font.render(text, True, color)
        self.rect = self.surf.get_rect(topleft=(x, y))

    def draw(self, screen):
        screen.blit(self.surf, self.rect)


class Button(UIElement):

    def __init__(self, text, font_size, x, y, w, h, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont(hex_cfg.get_system("font_name"), font_size)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True

        return False

    def update(self):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen):
        color = hex_cfg.get_color("hover") if self.hovered else hex_cfg.get_color("panel")
        border = hex_cfg.get_color("accent") if self.hovered else hex_cfg.get_color("border")
        
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)
        
        txt_surf = self.font.render(self.text, True, hex_cfg.get_color("text"))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)


class Slider(UIElement):

    def __init__(self, x, y, w, h, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.val = initial_val
        
        self.handle_w = 20
        self.handle_rect = pygame.Rect(x, y - 5, self.handle_w, h + 10)
        self.dragging = False
        self._update_handle_pos()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_val_from_pos(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_val_from_pos(event.pos[0])
            return True
            
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, hex_cfg.get_color("border"), self.rect, border_radius=5)
        fill_w = self.handle_rect.centerx - self.rect.x
        pygame.draw.rect(screen, hex_cfg.get_color("accent"), (self.rect.x, self.rect.y, fill_w, self.rect.height), border_radius=5)
        pygame.draw.rect(screen, hex_cfg.get_color("text"), self.handle_rect, border_radius=5)

    def _update_handle_pos(self):
        ratio = (self.val - self.min) / (self.max - self.min)
        center_x = self.rect.x + (self.rect.width * ratio)
        self.handle_rect.centerx = int(center_x)

    def _update_val_from_pos(self, x):
        ratio = (x - self.rect.x) / self.rect.width
        ratio = max(0, min(1, ratio))
        self.val = self.min + ratio * (self.max - self.min)
        self._update_handle_pos()


class Selector(UIElement):

    def __init__(self, x, y, w, h, options, current_val, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.callback = callback
        
        try: 
            self.index = options.index(current_val)
        except ValueError: 
            self.index = 0

        btn_w = 40
        self.btn_prev = Button("<", hex_cfg.get_system("font_size"), x, y, btn_w, h, self._prev)
        self.btn_next = Button(">", hex_cfg.get_system("font_size"), x + w - btn_w, y, btn_w, h, self._next)
        self.font = pygame.font.SysFont(hex_cfg.get_system("font_name"), hex_cfg.get_system("font_size"))

    def handle_event(self, event):
        click1 = self.btn_prev.handle_event(event)
        click2 = self.btn_next.handle_event(event)
        return click1 or click2

    def update(self):
        self.btn_prev.update()
        self.btn_next.update()

    def draw(self, screen):
        self.btn_prev.draw(screen)
        self.btn_next.draw(screen)
        
        txt = str(self.options[self.index])
        surf = self.font.render(txt, True, hex_cfg.get_color("text"))
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

    def _prev(self):
        self.index = (self.index - 1) % len(self.options)
        self.callback(self.options[self.index])

    def _next(self):
        self.index = (self.index + 1) % len(self.options)
        self.callback(self.options[self.index])


class Image(UIElement):

    def __init__(self, path, x, y, w=None, h=None, center=False):
        self.path = path
        
        try:
            raw_surf = pygame.image.load(path).convert_alpha()

        except (FileNotFoundError, pygame.error):
            print(f"Warning: Could not load image '{path}'. Using placeholder.")
            raw_surf = pygame.Surface((50, 50))
            raw_surf.fill((200, 50, 50)) 

        if w and h:
            self.surf = pygame.transform.smoothscale(raw_surf, (w, h))
        elif w:
            ratio = w / raw_surf.get_width()
            h = int(raw_surf.get_height() * ratio)
            self.surf = pygame.transform.smoothscale(raw_surf, (w, h))
        elif h:
            ratio = h / raw_surf.get_height()
            w = int(raw_surf.get_width() * ratio)
            self.surf = pygame.transform.smoothscale(raw_surf, (w, h))
        else:
            self.surf = raw_surf

        self.rect = self.surf.get_rect()
        if center:
            self.rect.center = (x, y)
        else:
            self.rect.topleft = (x, y)

    def draw(self, screen):
        screen.blit(self.surf, self.rect)


class Background(UIElement):

    def __init__(self, image_path=hex_cfg.get_image("bg")):
        self.image = None
        self.loaded = False

        if os.path.exists(image_path):
            try:
                raw_img = pygame.image.load(image_path).convert()
                scaled_img = pygame.transform.smoothscale(raw_img, (hex_cfg.get_system("width"), hex_cfg.get_system("height")))
                
                self.image = scaled_img.convert()
                self.loaded = True

            except pygame.error as e:
                print(f"Failed to load background: {e}")

        else:
            print(f"Background not found at {image_path}, using solid color.")

    def update(self) -> Optional[bool]:
        pass

    def draw(self, screen):
        if self.loaded and self.image:
            screen.blit(self.image, (0, 0))
        else:
            screen.fill(hex_cfg.get_color("bg"))
