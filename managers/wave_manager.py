import pygame
import random
from utils.constants import Colors

class WaveManager:
    def __init__(self, enemy_manager):
        self.enemy_manager = enemy_manager
        
        # State
        self.current_wave = 1
        self.wave_active = False
        
        # Spawning Queue
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0  # seconds between spawns
        
        # Wave Breather (between waves)
        self.breather_timer = 0.0
        self.breather_duration = 5.0  # seconds breather
        self.in_breather = True
        
        # Statistics
        self.total_wave_enemies = 0
        
        # Start initial breather
        self.start_breather()

    def start_breather(self):
        self.in_breather = True
        self.wave_active = False
        self.breather_timer = self.breather_duration
        self.spawn_queue.clear()

    def start_next_wave(self):
        self.in_breather = False
        self.wave_active = True
        
        # Generate wave queue
        self.spawn_queue = self.generate_wave_enemies(self.current_wave)
        self.total_wave_enemies = len(self.spawn_queue)
        
        # Less frequent spawns each round (higher waves = longer interval, e.g. 4.0s, 4.5s...)
        self.spawn_interval = 3.5 + (self.current_wave * 0.5)
        self.spawn_timer = 0.5  # First spawn quickly after wave starts

    def generate_wave_enemies(self, wave_num):
        """
        Generates a list of enemy types for the wave based on progression.
        """
        queue = []
        if wave_num == 1:
            # 3 Goblins
            queue = ["goblin"] * 3
        elif wave_num == 2:
            # 4 Goblins, 2 Skeletons
            queue = ["goblin"] * 4 + ["skeleton"] * 2
            random.shuffle(queue)
        elif wave_num == 3:
            # 5 Goblins, 3 Skeletons, 1 Orc
            queue = ["goblin"] * 5 + ["skeleton"] * 3 + ["orc"] * 1
            random.shuffle(queue)
        else:
            # Dynamic gentle scaling for endless mode
            goblin_count = 3 + wave_num // 2
            skeleton_count = wave_num
            orc_count = max(0, wave_num - 2)
            
            queue = (
                ["goblin"] * goblin_count + 
                ["skeleton"] * skeleton_count + 
                ["orc"] * orc_count
            )
            random.shuffle(queue)
            
        return queue

    def get_remaining_enemies_count(self):
        """Returns number of enemies left in queue + active on screen."""
        return len(self.spawn_queue) + len(self.enemy_manager.enemies)

    def update(self, dt, player, animation_effects):
        # 1. Handle Breather State
        if self.in_breather:
            self.breather_timer -= dt
            if self.breather_timer <= 0:
                self.start_next_wave()
            return

        # 2. Handle Spawning State
        if len(self.spawn_queue) > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                # Pop next enemy from queue and spawn
                enemy_type = self.spawn_queue.pop(0)
                self.enemy_manager.spawn_enemy(enemy_type)
                
                # Reset spawn timer
                self.spawn_timer = self.spawn_interval

        # 3. Handle Checking for Wave Completion
        # If queue is empty and all spawned enemies are dead:
        if len(self.spawn_queue) == 0 and len(self.enemy_manager.enemies) == 0:
            self.current_wave += 1
            
            # Spawn wave completed alert
            player_hitbox = player.get_hitbox()
            animation_effects.add_floating_text(
                "WAVE CLEAR!", 
                350, 180, 
                Colors.GOLD, 
                self.enemy_manager.asset_manager.get_font(None, 48),
                duration=2.5,
                is_damage=False
            )
            self.start_breather()

    def reset(self):
        self.current_wave = 1
        self.total_wave_enemies = 0
        self.start_breather()
