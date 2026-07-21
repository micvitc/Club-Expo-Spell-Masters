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
        self.burn_timer = 0.0
        self.burn_damage_cooldown = 0.0
        self.slow_timer = 0.0
        
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

    def burn(self, duration):
        self.burn_timer = max(self.burn_timer, duration)
        if self.burn_damage_cooldown <= 0:
            self.burn_damage_cooldown = 0.1

    def update(self, dt, player_x=480, player_y=360):
        # Update freeze state (in seconds)
        if self.freeze_timer > 0:
            self.freeze_timer -= dt / 60.0
            if self.freeze_timer <= 0:
                self.is_frozen = False
                
        # Update burn state (in seconds)
        if self.burn_timer > 0:
            self.burn_timer -= dt / 60.0
            self.burn_damage_cooldown -= dt / 60.0
            if self.burn_damage_cooldown <= 0:
                self.take_damage(1) # Deals 1 burn damage
                self.burn_damage_cooldown = 0.25 # Tick every 0.25s
                
        # Update obstacle/slow timer (in seconds)
        if self.slow_timer > 0:
            self.slow_timer -= dt / 60.0
        
        # Update hurt flash
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
 
        # Move towards player center only if NOT frozen
        if not self.is_frozen:
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                current_speed = self.speed
                if self.slow_timer > 0:
                    current_speed *= 0.35 # 65% speed reduction from obstacles/earthquake
                self.x += (dx / dist) * current_speed * dt
                self.y += (dy / dist) * current_speed * dt
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
            alpha = 70 + int(30 * math.sin(pygame.time.get_ticks() * 0.01))
            overlay.fill((100, 180, 255, alpha))# Transparent blue
            temp_sprite.blit(overlay, (0, 0))
            # Ice crack lines
            pygame.draw.line(temp_sprite, (240, 250, 255), (6, 6), (self.width - 8, self.height - 8), 1)
            pygame.draw.line(temp_sprite, (220, 240, 255), (self.width - 10, 8), (10, self.height - 12), 1)
            pygame.draw.line(temp_sprite, (230, 245, 255), (self.width // 2, 0), (self.width // 2 - 5, self.height), 1)
            
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
                # Ice crystals around the enemy
            crystal_color = (200, 245, 255)

            crystals = [
                (hitbox.centerx, hitbox.y - 8),            # top
                (hitbox.x - 6, hitbox.centery),            # left
                (hitbox.right + 6, hitbox.centery),        # right
                (hitbox.x + 8, hitbox.bottom + 4),         # bottom left
                (hitbox.right - 8, hitbox.bottom + 4)      # bottom right
            ]

            for cx, cy in crystals:
                pygame.draw.polygon(surface, crystal_color, [
                    (cx, cy - 6),
                    (cx - 4, cy + 3),
                    (cx + 4, cy + 3)
                ])
                # Falling snow particles
            for i in range(8):
                offset = (pygame.time.get_ticks() / 12 + i * 18) % (self.height + 20)

                x = hitbox.x + 5 + (i * 11) % self.width
                y = hitbox.y - 10 + offset - int(bounce)

                pygame.draw.circle(surface, (235, 250, 255), (int(x), int(y)), 2)
                # Cold mist around frozen enemy
            mist_color = (180, 230, 255, 40)

            mist = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)

            pygame.draw.ellipse(
                mist,
                mist_color,
                (0, 4, self.width + 20, self.height // 2)
            )

            surface.blit(
                mist,
                (hitbox.x - 10, hitbox.y + self.height // 3 - int(bounce))
            )
        # If burning, draw fire embers floating up
        if self.burn_timer > 0:
            ticks = pygame.time.get_ticks()
            for i in range(3):
                phase = (ticks * 0.006 + i * (math.pi / 3)) % 1.0
                spark_x = hitbox.x + (self.width * 0.2) + (self.width * 0.6) * math.sin(ticks * 0.01 + i)
                spark_y = hitbox.y + self.height - (self.height + 15) * phase
                spark_r = max(1, int(4 * (1.0 - phase)))
                pygame.draw.circle(surface, (255, 80 + int(120 * phase), 30), (int(spark_x), int(spark_y)), spark_r)

        # Draw mini HP bar for damaged enemies
        # Draw mini HP bar for damaged enemies
        if self.hp < self.max_hp and self.hp > 0:
            bar_width = int(self.width * 1.2)   # 20% wider than the enemy
            bar_height = 7                       # Thicker
            bar_x = hitbox.centerx - bar_width // 2
            bar_y = hitbox.y - 16 - int(bounce)  # Slightly higher

            pygame.draw.rect(
                surface,
                Colors.HP_BAR_EMPTY,
                (bar_x, bar_y, bar_width, bar_height),
                border_radius=3
            )

            fill_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(
                surface,
                Colors.HP_BAR_FILL,
                (bar_x, bar_y, fill_width, bar_height),
                border_radius=3
            )
            
            # Background
            pygame.draw.rect(surface, Colors.HP_BAR_EMPTY, (bar_x, bar_y, bar_width, bar_height), border_radius=2)
            # Fill
            fill_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(surface, Colors.HP_BAR_FILL, (bar_x, bar_y, fill_width, bar_height), border_radius=2)
