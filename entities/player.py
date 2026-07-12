import pygame
import math
import random
from utils.constants import WIZARD_X, WIZARD_Y, WIZARD_MAX_HP, WIZARD_RADIUS, Colors

class Player:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        self.x = WIZARD_X
        self.y = WIZARD_Y
        self.max_hp = WIZARD_MAX_HP
        self.hp = self.max_hp
        self.score = 0
        
        # Animations
        self.hover_angle = 0.0
        self.hover_amplitude = 6.0
        self.hover_speed = 0.05
        
        self.cast_timer = 0.0
        self.cast_duration = 0.3  # cast frame length
        self.is_casting = False
        self.last_cast_spell = None
        
        self.hurt_timer = 0.0
        self.hurt_duration = 0.25
        
        # Load sprite (supports fallback)
        self.sprite = self.asset_manager.get_image(
            "sprites", "wizard.png", 
            width=WIZARD_RADIUS*2, 
            height=WIZARD_RADIUS*2, 
            color=Colors.WIZARD_COLOR
        )

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.hurt_timer = self.hurt_duration
        
    def add_score(self, amount):
        self.score += amount

    def start_cast(self, spell_name):
        self.is_casting = True
        self.cast_timer = self.cast_duration
        self.last_cast_spell = spell_name

    def update(self, dt):
        # Hover animation (sinusoidal vertical float)
        self.hover_angle += self.hover_speed
        
        # Update animation timers
        if self.cast_timer > 0:
            self.cast_timer -= dt
            if self.cast_timer <= 0:
                self.is_casting = False
                
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def draw(self, surface, animation_effects):
        # Calculate current vertical position based on hover offset
        offset_y = math.sin(self.hover_angle) * self.hover_amplitude
        draw_y = self.y + offset_y
        
        # Render Glow around the Wizard
        glow_radius = WIZARD_RADIUS + 8
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        
        # Adjust glow color based on status (hurt vs normal/casting)
        if self.hurt_timer > 0:
            glow_color = (255, 50, 50, 100)
        elif self.is_casting and self.last_cast_spell:
            # Glow color corresponds to cast spell
            spell_color = Colors.FIRE if self.last_cast_spell == "fire" else \
                          Colors.ICE if self.last_cast_spell == "ice" else \
                          Colors.LIGHTNING if self.last_cast_spell == "lightning" else Colors.WIND
            glow_color = (spell_color[0], spell_color[1], spell_color[2], 120)
        else:
            glow_color = (Colors.WIZARD_COLOR[0], Colors.WIZARD_COLOR[1], Colors.WIZARD_COLOR[2], 60)
            
        pygame.draw.circle(glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (self.x - glow_radius, int(draw_y) - glow_radius))

        # Draw Staff / Weapon
        staff_x = self.x + 24
        staff_y = draw_y - 10
        if self.is_casting:
            # Staff points forward to cast
            pygame.draw.line(surface, Colors.GOLD, (self.x, draw_y), (staff_x + 10, staff_y - 5), 4)
            # Draw magic sparkle at tip of staff
            spell_color = Colors.FIRE if self.last_cast_spell == "fire" else \
                          Colors.ICE if self.last_cast_spell == "ice" else \
                          Colors.LIGHTNING if self.last_cast_spell == "lightning" else Colors.WIND
            pygame.draw.circle(surface, spell_color, (staff_x + 10, int(staff_y - 5)), 8)
            pygame.draw.circle(surface, Colors.TEXT_MAIN, (staff_x + 10, int(staff_y - 5)), 4)
        else:
            # Staff held upright
            pygame.draw.line(surface, Colors.GOLD, (self.x - 5, draw_y + 15), (staff_x - 5, staff_y - 20), 4)
            pygame.draw.circle(surface, Colors.WIZARD_COLOR, (staff_x - 5, int(staff_y - 20)), 6)
            
        # Draw Main Sprite
        sprite_rect = self.sprite.get_rect(center=(self.x, int(draw_y)))
        
        # If hurt, flash sprite red
        if self.hurt_timer > 0:
            hurt_surf = self.sprite.copy()
            # Overlay red
            hurt_surf.fill((255, 50, 50, 150), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(hurt_surf, sprite_rect)
        else:
            surface.blit(self.sprite, sprite_rect)

        # Spawning idle/casting sparks around player
        if self.is_casting and random.random() < 0.3:
            spell_color = Colors.FIRE if self.last_cast_spell == "fire" else \
                          Colors.ICE if self.last_cast_spell == "ice" else \
                          Colors.LIGHTNING if self.last_cast_spell == "lightning" else Colors.WIND
            animation_effects.add_particle_burst(
                self.x + 20, int(draw_y - 10), 
                [spell_color, Colors.TEXT_MAIN], 
                count=2, 
                speed_range=(0.5, 2.0), 
                size_range=(2, 4), 
                lifetime_range=(10, 20)
            )
            
    def get_hitbox(self):
        # Returns wizard's circle bounding region
        return pygame.Rect(self.x - WIZARD_RADIUS, self.y - WIZARD_RADIUS, WIZARD_RADIUS*2, WIZARD_RADIUS*2)
