import pygame
import math
import random
from utils.constants import ENEMY_TYPES, Colors, SCREEN_WIDTH

class Enemy:
    def __init__(self, x, y, enemy_type, asset_manager):
        self.asset_manager = asset_manager
        self.type_name = enemy_type
        
        # Load configs from constants
        config = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES["goblin"])
        self.name = config["name"]
        self.max_hp = config["hp"]
        self.hp = self.max_hp
        self.speed = config["speed"]
        self.damage = config["damage"]
        self.color = config["color"]
        self.width, self.height = config["size"]
        self.score_value = config["score_val"]
        
        # Physics / Positioning
        self.x = float(x)
        self.y = float(y)
        
        # Status Effects
        self.freeze_timer = 0.0
        self.is_frozen = False
        
        # Visual feedback timers
        self.hurt_timer = 0.0
        self.hurt_duration = 0.15
        
        # Animation
        self.walk_cycle = random.uniform(0, 100) # random phase so enemies don't walk in lockstep
        
        # Get Sprite (creates placeholder using category, filename, size, and config color)
        self.sprite = self.asset_manager.get_image(
            "sprites", f"{self.type_name}.png", 
            width=self.width, height=self.height, 
            color=self.color
        )

    def take_damage(self, amount):
        self.hp -= amount
        self.hurt_timer = self.hurt_duration

    def freeze(self, duration):
        self.freeze_timer = max(self.freeze_timer, duration)
        self.is_frozen = True

    def update(self, dt):
        # Update freeze state
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.is_frozen = False
        
        # Update hurt flash
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        # Move left towards player only if NOT frozen
        if not self.is_frozen:
            self.x -= self.speed * dt
            # Bouncing walking cycle based on speed
            self.walk_cycle += 0.15 * self.speed * dt
        else:
            self.walk_cycle += 0.02 * dt

    def get_hitbox(self):
        # Center-aligned hitbox
        return pygame.Rect(
            int(self.x - self.width / 2), 
            int(self.y - self.height / 2), 
            self.width, 
            self.height
        )

    def draw(self, surface):
        hitbox = self.get_hitbox()
        
        # Determine bounce height and rotation for walk wiggle
        bounce = abs(math.sin(self.walk_cycle)) * 4
        angle = math.sin(self.walk_cycle) * 5
        
        # Scale/rotate sprite according to walk wiggle
        temp_sprite = self.sprite
        
        # If frozen, apply ice-blue overlay
        if self.is_frozen:
            temp_sprite = self.sprite.copy()
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((100, 180, 255, 100)) # Transparent blue
            temp_sprite.blit(overlay, (0, 0))
            
            # Draw tiny ice shards around them
            # (Done on the fly or drawn directly)
            
        # If recently hurt, override with a white/red flash
        elif self.hurt_timer > 0:
            temp_sprite = self.sprite.copy()
            temp_sprite.fill((255, 100, 100, 150), special_flags=pygame.BLEND_RGBA_MULT)
            
        # Rotate sprite for wiggle
        if angle != 0:
            rotated_sprite = pygame.transform.rotate(temp_sprite, angle)
            new_rect = rotated_sprite.get_rect()
            new_rect.center = (hitbox.centerx, hitbox.centery - int(bounce))
            surface.blit(rotated_sprite, new_rect)
        else:
            surface.blit(temp_sprite, (hitbox.x, hitbox.y - int(bounce)))
            
        # Draw floating freeze text indicator if frozen
        if self.is_frozen:
            # Subtle frozen aura glow
            glow_surf = pygame.Surface((self.width + 12, self.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (80, 180, 240, 60), (0, 0, self.width + 12, self.height + 12), border_radius=6)
            surface.blit(glow_surf, (hitbox.x - 6, hitbox.y - 6 - int(bounce)))

        # Draw mini HP bar for damaged enemies
        if self.hp < self.max_hp and self.hp > 0:
            bar_width = self.width
            bar_height = 5
            bar_x = hitbox.centerx - bar_width // 2
            bar_y = hitbox.y - 12 - int(bounce)
            
            # Background
            pygame.draw.rect(surface, Colors.HP_BAR_EMPTY, (bar_x, bar_y, bar_width, bar_height), border_radius=2)
            # Fill
            fill_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(surface, Colors.HP_BAR_FILL, (bar_x, bar_y, fill_width, bar_height), border_radius=2)
