import pygame
import random
import math
from utils.constants import Colors

def draw_text_with_outline(surface, text, font, color, outline_color, pos, outline_width=2):
    """
    Renders text with a thick border outline for readability over complex backgrounds.
    """
    x, y = pos
    # Render outline by offset rendering
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                outline_surf = font.render(text, True, outline_color)
                surface.blit(outline_surf, (x + dx, y + dy))
                
    # Main text
    main_surf = font.render(text, True, color)
    surface.blit(main_surf, (x, y))

def draw_health_bar(surface, x, y, width, height, val, max_val, bar_color=Colors.HP_BAR_FILL, bg_color=Colors.HP_BAR_EMPTY):
    """
    Draws a stylized, segmented health bar with a border and subtle highlights.
    """
    # Clamp value
    val = max(0, min(val, max_val))
    ratio = val / max_val
    
    # Outer Border
    border_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, Colors.SHADOW, border_rect, border_radius=4)
    
    # Background
    bg_rect = border_rect.inflate(-2, -2)
    pygame.draw.rect(surface, bg_color, bg_rect, border_radius=3)
    
    if val > 0:
        # Filled part
        fill_width = int(bg_rect.width * ratio)
        fill_rect = pygame.Rect(bg_rect.x, bg_rect.y, fill_width, bg_rect.height)
        pygame.draw.rect(surface, bar_color, fill_rect, border_radius=3)
        
        # Draw small inner highlight for premium look
        highlight_rect = pygame.Rect(bg_rect.x, bg_rect.y, fill_width, bg_rect.height // 3)
        highlight_color = tuple(min(255, c + 40) for c in bar_color)
        pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=2)

class Particle:
    """
    Individual visual particle for spell effects, walk dust, and impact flashes.
    """
    def __init__(self, x, y, vx, vy, color, size, lifetime, shrink=True, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.start_size = size
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.shrink = shrink
        self.gravity = gravity

    def update(self, dt=1.0):
        self.lifetime -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        
        if self.shrink:
            self.size = max(0.1, self.start_size * (self.lifetime / self.max_lifetime))
            
    def draw(self, surface):
        if self.lifetime <= 0 or self.size < 0.5:
            return
            
        # Draw soft glowing circle by blending
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Check if color is RGB
        c = self.color
        if len(c) == 3:
            glow_color = (c[0], c[1], c[2], alpha)
        else:
            glow_color = c
            
        # Draw antialiased circle or fallback transparent surface
        target_size = int(self.size)
        if target_size > 0:
            surf = pygame.Surface((target_size * 2, target_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, glow_color, (target_size, target_size), target_size)
            surface.blit(surf, (int(self.x - target_size), int(self.y - target_size)))

class FloatingText:
    """
    Text that rises up, grows, shakes, and fades out when damage/effects happen.
    """
    def __init__(self, text, x, y, color, font, duration=1.0, is_damage=True):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.duration = duration
        self.time_alive = 0.0
        self.is_damage = is_damage
        self.vx = random.uniform(-1.0, 1.0) if is_damage else 0
        self.vy = random.uniform(-2.0, -1.0)

    def update(self, dt):
        self.time_alive += dt
        self.x += self.vx
        self.y += self.vy
        
        # Slowly decelerate horizontal movement
        self.vx *= 0.95

    def draw(self, surface):
        alpha = int(255 * (1.0 - (self.time_alive / self.duration)))
        if alpha <= 0:
            return
            
        # Custom color with alpha
        c = self.color
        text_color = (c[0], c[1], c[2], alpha)
        
        # Render text with soft shadow
        shadow_surf = self.font.render(self.text, True, (0, 0, 0, alpha))
        main_surf = self.font.render(self.text, True, text_color)
        
        # Blit shadow slightly offset
        surface.blit(shadow_surf, (int(self.x) + 2, int(self.y) + 2))
        surface.blit(main_surf, (int(self.x), int(self.y)))
