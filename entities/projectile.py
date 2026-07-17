import pygame
import math
import random
from utils.constants import Colors

class Projectile:
    def __init__(self, x, y, target, spell_type, damage, speed, color, effect_duration=0, player=None, animation_effects=None):
        self.x = float(x)
        self.y = float(y)
        self.target = target
        self.spell_type = spell_type
        self.damage = damage
        self.speed = speed
        self.color = color
        self.effect_duration = effect_duration
        self.player = player
        self.animation_effects = animation_effects
        self.radius = 8 if spell_type == "fire" else 6
        self.alive = True
        
        # Glow trail angle
        self.trail_timer = 0.0

    def update(self, dt):
        if not self.target or not hasattr(self.target, 'hp') or self.target.hp <= 0:
            # If target died, target nearest coordinate or self-destruct
            self.alive = False
            return

        # Calculate vector to target center
        target_hitbox = self.target.get_hitbox()
        tx, ty = target_hitbox.centerx, target_hitbox.centery
        
        # Adjust for height wiggles
        ty -= 4
        
        dx = tx - self.x
        dy = ty - self.y
        distance = math.hypot(dx, dy)
        
        if distance < self.speed * dt:
            # Impact!
            self.on_impact()
        else:
            # Move towards target
            self.x += (dx / distance) * self.speed * dt
            self.y += (dy / distance) * self.speed * dt
            
        self.trail_timer += dt

    def on_impact(self):
        self.alive = False
        if self.target and hasattr(self.target, 'hp') and self.target.hp > 0:
            self.target.take_damage(self.damage)
            
            # Apply spell-specific status effects
            if self.spell_type == "fire":
                self.target.burn(1.0) # Burn for 1s
                
            elif self.spell_type == "ice":
                self.target.freeze(self.effect_duration) # Freeze duration
                
            elif self.spell_type == "shadow" and self.player:
                # Lifesteal: heal the player
                heal_amount = 10
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                
                # Trigger floating heal text and green particles rising from player
                if self.animation_effects:
                    self.animation_effects.add_floating_text(
                        f"+{heal_amount} HP", 
                        self.player.x - 20, self.player.y - 45, 
                        (50, 220, 100), 
                        self.player.asset_manager.get_font(None, 24),
                        is_damage=False
                    )
                    self.animation_effects.add_particle_burst(
                        self.player.x, self.player.y, 
                        [(50, 220, 100), (100, 255, 150), (255, 255, 255)], 
                        count=12, 
                        speed_range=(0.6, 2.2), 
                        size_range=(2, 5),
                        lifetime_range=(15, 35)
                    )
                self.player.asset_manager.get_sound("heal.wav").play()
                
    def draw(self, surface, animation_effects):
        # Draw soft glow behind the projectile
        glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        glow_color = (self.color[0], self.color[1], self.color[2], 80)
        pygame.draw.circle(glow_surf, glow_color, (self.radius * 2, self.radius * 2), self.radius * 2)
        surface.blit(glow_surf, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))
        
        # Draw central projectile core
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, Colors.TEXT_MAIN, (int(self.x), int(self.y)), self.radius // 2)
        
        # Spawn small trailing particles
        if random.random() < 0.4:
            animation_effects.add_particle_burst(
                self.x, self.y, 
                [self.color, Colors.TEXT_MAIN], 
                count=1, 
                speed_range=(0.2, 1.0), 
                size_range=(2, 4), 
                lifetime_range=(5, 12)
            )
