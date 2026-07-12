import pygame
import random
from entities.enemy import Enemy
from utils.constants import GAMEPLAY_WIDTH, SCREEN_HEIGHT, Colors
from spells.effects import FireExplosionEffect

class EnemyManager:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.enemies = []

    def spawn_enemy(self, enemy_type):
        """Spawns a new enemy off-screen on the right with a randomized lane height."""
        # Standard lane height (around wizard's center height)
        # Randomize Y slightly to give vertical depth
        lane_y = random.uniform(SCREEN_HEIGHT // 2, SCREEN_HEIGHT // 2 + 120)
        
        # Spawn off-screen to the right
        spawn_x = GAMEPLAY_WIDTH + 50
        
        new_enemy = Enemy(spawn_x, lane_y, enemy_type, self.asset_manager)
        self.enemies.append(new_enemy)

    def update(self, dt, player, animation_effects):
        # Sort enemies by x-coordinate to draw back-to-front (depth sorting)
        self.enemies.sort(key=lambda e: e.y)

        # Update all active enemies
        for enemy in self.enemies[:]:
            enemy.update(dt)
            
            # Check for death
            if enemy.hp <= 0:
                self.handle_enemy_death(enemy, player, animation_effects)
                continue
                
            # Check collision with wizard
            # Wizard hitbox is centered at WIZARD_X. If enemy gets close enough:
            # We check if enemy's front border (left side) crosses player's right border
            player_hitbox = player.get_hitbox()
            enemy_hitbox = enemy.get_hitbox()
            
            if enemy_hitbox.left <= player_hitbox.right:
                self.handle_player_collision(enemy, player, animation_effects)

    def handle_enemy_death(self, enemy, player, animation_effects):
        # Award score
        player.add_score(enemy.score_value)
        
        # Spawn floating score text
        hitbox = enemy.get_hitbox()
        animation_effects.add_floating_text(
            f"+{enemy.score_value}", 
            hitbox.centerx, hitbox.y, 
            Colors.GOLD, 
            self.asset_manager.get_font(None, 24),
            duration=0.8,
            is_damage=False
        )
        
        # Visual death particle burst (matching enemy color)
        animation_effects.add_particle_burst(
            hitbox.centerx, hitbox.centery, 
            [enemy.color, Colors.TEXT_MAIN], 
            count=18, 
            speed_range=(1.5, 4.5), 
            size_range=(3, 7)
        )
        
        # Add custom explosion effect particle
        explosion = FireExplosionEffect(hitbox.centerx, hitbox.centery, max_radius=35)
        animation_effects.particles.append(explosion)
        
        # Play death sound
        self.asset_manager.get_sound("death.wav").play()
        
        # Remove from list
        if enemy in self.enemies:
            self.enemies.remove(enemy)

    def handle_player_collision(self, enemy, player, animation_effects):
        # Damage wizard
        player.take_damage(enemy.damage)
        
        # Trigger damage feedback
        animation_effects.trigger_shake(0.25, 8.0)
        animation_effects.trigger_flash(0.2, (220, 50, 80)) # Red flash
        
        # Floating damage text above wizard
        player_hitbox = player.get_hitbox()
        animation_effects.add_floating_text(
            f"-{enemy.damage} HP", 
            player_hitbox.centerx - 20, player_hitbox.y - 30, 
            Colors.HP_BAR_FILL, 
            self.asset_manager.get_font(None, 28)
        )
        
        # Particle explosion at impact point
        hitbox = enemy.get_hitbox()
        animation_effects.add_particle_burst(
            player_hitbox.right, hitbox.centery, 
            [Colors.HP_BAR_FILL, Colors.TEXT_MAIN], 
            count=12, 
            speed_range=(2.0, 5.0), 
            size_range=(4, 8)
        )
        
        # Play damage sound
        self.asset_manager.get_sound("hurt.wav").play()
        
        # Remove enemy
        if enemy in self.enemies:
            self.enemies.remove(enemy)

    def draw(self, surface):
        for enemy in self.enemies:
            enemy.draw(surface)
            
    def clear(self):
        self.enemies.clear()
