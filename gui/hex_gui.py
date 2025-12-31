import pygame
from typing import Optional

from hex_settings import *

class UIElement:

    def draw(self, screen): pass
    def update(self, events) -> Optional[bool]: pass


class Label(UIElement):

    def __init__(self, text, x, y, font_size=FONT_SIZE, color=TEXT_COLOR):
        self.font = pygame.font.SysFont(FONT_NAME, font_size)
        self.surf = self.font.render(text, True, color)
        self.rect = self.surf.get_rect(topleft=(x, y))

    def draw(self, screen):
        screen.blit(self.surf, self.rect)


class Button(UIElement):

    def __init__(self, text, x, y, w, h, callback, font_size=FONT_SIZE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont(FONT_NAME, font_size)
        self.hovered = False

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my)
        
        clicked = False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.hovered:
                self.callback()
                clicked = True

        return clicked

    def draw(self, screen):
        color = HOVER_COLOR if self.hovered else PANEL_COLOR
        border = ACCENT_COLOR if self.hovered else BORDER_COLOR
        
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=8)
        
        txt_surf = self.font.render(self.text, True, TEXT_COLOR)
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

    def update(self, events):
        changed = False
        mx, my = pygame.mouse.get_pos()

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.handle_rect.collidepoint(mx, my) or self.rect.collidepoint(mx, my):
                    self.dragging = True
                    self._update_val_from_pos(mx)
                    changed = True

            elif e.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

            elif e.type == pygame.MOUSEMOTION and self.dragging:
                self._update_val_from_pos(mx)
                changed = True

        return changed

    def draw(self, screen):
        pygame.draw.rect(screen, BORDER_COLOR, self.rect, border_radius=5)
        fill_w = self.handle_rect.centerx - self.rect.x
        pygame.draw.rect(screen, ACCENT_COLOR, (self.rect.x, self.rect.y, fill_w, self.rect.height), border_radius=5)
        pygame.draw.rect(screen, TEXT_COLOR, self.handle_rect, border_radius=5)

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
        
        try: self.index = options.index(current_val)
        except ValueError: self.index = 0

        btn_w = 40
        self.btn_prev = Button("<", x, y, btn_w, h, self._prev)
        self.btn_next = Button(">", x + w - btn_w, y, btn_w, h, self._next)
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

    def update(self, events):
        click1 = self.btn_prev.update(events)
        click2 = self.btn_next.update(events)
        return click1 or click2

    def draw(self, screen):
        self.btn_prev.draw(screen)
        self.btn_next.draw(screen)
        
        txt = str(self.options[self.index])
        surf = self.font.render(txt, True, TEXT_COLOR)
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

    def update(self, events):
        pass

    def draw(self, screen):
        screen.blit(self.surf, self.rect)


class Background(UIElement):

    def __init__(self, image_path=BG_IMAGE_PATH):
        self.image = None
        self.loaded = False

        if os.path.exists(image_path):
            try:
                raw_img = pygame.image.load(image_path).convert()
                scaled_img = pygame.transform.smoothscale(raw_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                
                self.image = scaled_img.convert()
                self.loaded = True

            except pygame.error as e:
                print(f"Failed to load background: {e}")

        else:
            print(f"Background not found at {image_path}, using solid color.")

    def update(self, events) -> Optional[bool]:
        pass

    def draw(self, screen):
        if self.loaded and self.image:
            screen.blit(self.image, (0, 0))
        else:
            screen.fill(BG_COLOR)
