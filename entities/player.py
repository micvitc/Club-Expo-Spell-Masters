import pygame
import math
import random
from utils.constants import WIZARD_X, WIZARD_Y, WIZARD_MAX_HP, WIZARD_RADIUS, Colors
from utils.helpers import draw_text_with_outline

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
        self.cast_duration = 1.0  # increased cast frame length to make stance visible
        self.is_casting = False
        self.last_cast_spell = None
        
        self.hurt_timer = 0.0
        self.hurt_duration = 0.25
        
        # Load sprite (supports fallback)
        self.sprite = self.asset_manager.get_image(
            "sprites", "wizard.png", 
            width=WIZARD_RADIUS*2.5, 
            height=WIZARD_RADIUS*2.5, 
            color=Colors.WIZARD_COLOR
        )
        self.sprite_casting = self.asset_manager.get_image(
            "sprites", "wizard_casting.png", 
            width=WIZARD_RADIUS*2.5, 
            height=WIZARD_RADIUS*2.5, 
            color=Colors.WIZARD_COLOR
        )

    def take_damage(self, amount):
        if hasattr(self, 'shield_active') and self.shield_active and getattr(self, 'shield_hp', 0) > 0:
            # Shield absorbs damage
            self.shield_hp -= amount
            self.hurt_timer = self.hurt_duration * 0.5
            if self.shield_hp <= 0:
                self.shield_active = False
                self.shield_timer = 0.0
            return
        self.hp = max(0, self.hp - amount)
        self.hurt_timer = self.hurt_duration
        
    def add_score(self, amount):
        self.score += amount

    def start_cast(self, spell_name, target_pos=None):
        self.is_casting = True
        self.cast_timer = self.cast_duration
        self.last_cast_spell = spell_name
        self.last_cast_target_pos = target_pos

    def activate_shield(self, duration, hp=30):
        self.shield_active = True
        self.shield_timer = duration
        self.shield_hp = hp # Shield HP is reset on cast (not stackable)

    def update(self, dt):
        # Hover animation (sinusoidal vertical float)
        self.hover_angle += self.hover_speed
        
        # Update shield timer in seconds
        if hasattr(self, 'shield_timer') and self.shield_timer > 0:
            self.shield_timer -= dt / 60.0
            if self.shield_timer <= 0:
                self.shield_active = False
                
        # Update animation timers
        if self.cast_timer > 0:
            self.cast_timer -= dt / 60.0
            if self.cast_timer <= 0:
                self.is_casting = False
                
        if self.hurt_timer > 0:
            self.hurt_timer -= dt / 60.0

    def draw(self, surface, animation_effects):
        from utils.constants import SPELLS
        
        # Ensure shield properties are initialized
        if not hasattr(self, 'shield_active'):
            self.shield_active = False
            self.shield_timer = 0.0
            self.last_cast_target_pos = None

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
            spell_color = SPELLS.get(self.last_cast_spell, {}).get("color", Colors.WIZARD_COLOR)
            glow_color = (spell_color[0], spell_color[1], spell_color[2], 120)
        else:
            glow_color = (Colors.WIZARD_COLOR[0], Colors.WIZARD_COLOR[1], Colors.WIZARD_COLOR[2], 60)
            
        pygame.draw.circle(glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
        #surface.blit(glow_surf, (self.x - glow_radius, int(draw_y) - glow_radius))

        # Draw spinning magic circle beneath player
        ticks = pygame.time.get_ticks()
        circle_radius = WIZARD_RADIUS + 10
        circle_surf = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
        pulse_alpha = int(40 + 20 * math.sin(ticks * 0.005))
        
        if self.is_casting and self.last_cast_spell:
            c = SPELLS.get(self.last_cast_spell, {}).get("color", Colors.WIZARD_COLOR)
        else:
            c = Colors.WIZARD_COLOR
            
        pygame.draw.circle(circle_surf, (c[0], c[1], c[2], pulse_alpha), (circle_radius, circle_radius), circle_radius, width=2)
        pygame.draw.circle(circle_surf, (c[0], c[1], c[2], pulse_alpha // 2), (circle_radius, circle_radius), circle_radius - 8, width=1)
        
        for i in range(4):
            angle = i * (math.pi / 4) + ticks * 0.001
            sx = circle_radius + math.cos(angle) * (circle_radius - 2)
            sy = circle_radius + math.sin(angle) * (circle_radius - 2)
            ex = circle_radius - math.cos(angle) * (circle_radius - 2)
            ey = circle_radius - math.sin(angle) * (circle_radius - 2)
            pygame.draw.line(circle_surf, (c[0], c[1], c[2], pulse_alpha // 3), (sx, sy), (ex, ey), 1)
            
        surface.blit(circle_surf, (self.x - circle_radius, int(draw_y) + 12 - circle_radius))

        # Draw Staff / Weapon
        if self.is_casting and getattr(self, 'last_cast_target_pos', None):
            # Calculate angle pointing to the target
            tx, ty = self.last_cast_target_pos
            dx = tx - self.x
            dy = ty - draw_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                ux, uy = dx / dist, dy / dist
            else:
                ux, uy = 1.0, 0.0
            
            # Draw staff pointing to target
            staff_len = 35
            staff_end_x = self.x + ux * staff_len
            staff_end_y = draw_y + uy * staff_len
            pygame.draw.line(surface, Colors.GOLD, (self.x, draw_y), (staff_end_x, staff_end_y), 4)
            
            # Draw magic sparkle at tip of staff
            spell_color = SPELLS.get(self.last_cast_spell, {}).get("color", Colors.WIZARD_COLOR)
            pygame.draw.circle(surface, spell_color, (int(staff_end_x), int(staff_end_y)), 8)
            pygame.draw.circle(surface, Colors.TEXT_MAIN, (int(staff_end_x), int(staff_end_y)), 4)
        else:
            # Staff held upright
            staff_x = self.x + 24
            staff_y = draw_y - 10
            pygame.draw.line(surface, Colors.GOLD, (self.x - 5, draw_y + 15), (staff_x - 5, staff_y - 20), 4)
            pygame.draw.circle(surface, Colors.WIZARD_COLOR, (staff_x - 5, int(staff_y - 20)), 6)
            
        # Determine which sprite to use
        current_sprite = self.sprite_casting if self.is_casting else self.sprite
        
        # Draw Main Sprite
        sprite_rect = current_sprite.get_rect(center=(self.x, int(draw_y)))
        
        # If hurt, flash sprite red
        if self.hurt_timer > 0 and not self.shield_active:
            hurt_surf = current_sprite.copy()
            # Overlay red
            hurt_surf.fill((255, 50, 50, 150), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(hurt_surf, sprite_rect)
        else:
            surface.blit(current_sprite, sprite_rect)

        # Draw Aegis Shield Bubble if active
        if self.shield_active:
            shield_radius = WIZARD_RADIUS + 18
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            
            # Pulsing alpha
            ticks = pygame.time.get_ticks()
            pulse = int(100 + 40 * math.sin(ticks * 0.01))
            
            # Translucent golden shield bubble
            pygame.draw.circle(shield_surf, (235, 180, 50, pulse), (shield_radius, shield_radius), shield_radius, width=3)
            pygame.draw.circle(shield_surf, (235, 180, 50, pulse // 3), (shield_radius, shield_radius), shield_radius - 2)
            
            # Draw hex shield segments or lines
            for i in range(6):
                angle = i * (math.pi / 3) + ticks * 0.001
                sx = shield_radius + math.cos(angle) * shield_radius
                sy = shield_radius + math.sin(angle) * shield_radius
                pygame.draw.line(shield_surf, (255, 220, 120, pulse), (shield_radius, shield_radius), (sx, sy), 1)
                
            surface.blit(shield_surf, (self.x - shield_radius, int(draw_y) - shield_radius))
            
            # Draw Shield HP text above the player
            if hasattr(self, 'shield_hp'):
                font = self.asset_manager.get_font(None, 16)
                hp_text = f"SHIELD: {max(0, int(self.shield_hp))} HP"
                hp_w = font.size(hp_text)[0]
                draw_text_with_outline(
                    surface, hp_text, font, 
                    (255, 220, 100), Colors.SHADOW, 
                    (self.x - hp_w // 2, int(draw_y) - shield_radius - 20)
                )
            
            # Add random shield sparkles
            if random.random() < 0.15:
                ang = random.uniform(0, 2 * math.pi)
                sp_x = self.x + math.cos(ang) * shield_radius
                sp_y = draw_y + math.sin(ang) * shield_radius
                animation_effects.add_particle_burst(
                    sp_x, sp_y, 
                    Colors.PARTICLE_SHIELD, 
                    count=1, 
                    speed_range=(0.2, 0.8), 
                    size_range=(2, 4)
                )

        # Spawning idle/casting sparks around player
        if self.is_casting and random.random() < 0.3:
            spell_color = SPELLS.get(self.last_cast_spell, {}).get("color", Colors.WIZARD_COLOR)
            animation_effects.add_particle_burst(
                self.x, int(draw_y), 
                [spell_color, Colors.TEXT_MAIN], 
                count=2, 
                speed_range=(0.5, 2.0), 
                size_range=(2, 4), 
                lifetime_range=(10, 20)
            )
            
    def get_hitbox(self):
        # Returns wizard's circle bounding region
        return pygame.Rect(self.x - WIZARD_RADIUS, self.y - WIZARD_RADIUS, WIZARD_RADIUS*2, WIZARD_RADIUS*2)

