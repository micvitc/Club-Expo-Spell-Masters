import pygame
import queue
from utils.constants import GameState, Colors, SCREEN_WIDTH, SCREEN_HEIGHT, GAMEPLAY_WIDTH
from settings import TARGET_FPS
from managers.asset_manager import AssetManager
from managers.enemy_manager import EnemyManager
from managers.wave_manager import WaveManager
from spells.spell_manager import SpellManager
from ui.animations import AnimationEffects
from ui.hud import HUD
from ui.menus import MenuManager
from entities.player import Player

class Game:
    def __init__(self):
        pygame.init()
        
        # Default to Fullscreen with windowed fallback
        self.is_fullscreen = True
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        except pygame.error:
            self.is_fullscreen = False
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            print("Warning: Fullscreen mode not supported. Falling back to windowed mode.")
            
        pygame.display.set_caption("Spell Master - Gesture Magic Duel")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # System Managers
        self.asset_manager = AssetManager()
        self.animation_effects = AnimationEffects()
        self.enemy_manager = EnemyManager(self.asset_manager)
        self.wave_manager = WaveManager(self.enemy_manager)
        self.spell_manager = SpellManager(self.asset_manager)
        
        # Game State
        self.state = GameState.MAIN_MENU
        
        # Game Entities
        self.player = Player(self.asset_manager)
        self.projectiles = []
        
        # UI
        self.hud = HUD(self.asset_manager)
        self.menu_manager = MenuManager(self.asset_manager, self)
        
        # Thread-safe queue for external spell casts (CV Team integration)
        self.spell_queue = queue.Queue()
        
        # Load background scaled to gameplay viewport
        self.background = self.asset_manager.get_image(
            "backgrounds", "arena_bg.png", 
            width=GAMEPLAY_WIDTH, height=SCREEN_HEIGHT
        )

    def cast_spell(self, spell_name):
        """
        Public API for CV Team Integration.
        Adds a spell request to a thread-safe queue.
        Can be safely called from secondary OpenCV/MediaPipe threads.
        """
        self.spell_queue.put(spell_name)
        return True

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            try:
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            except pygame.error:
                self.is_fullscreen = False
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def start_game(self):
        self.reset_game()
        self.state = GameState.PLAYING

    def resume_game(self):
        self.state = GameState.PLAYING

    def pause_game(self):
        self.state = GameState.PAUSED

    def restart_game(self):
        self.reset_game()
        self.state = GameState.PLAYING

    def go_to_menu(self):
        self.state = GameState.MAIN_MENU
        self.reset_game()

    def reset_game(self):
        self.player = Player(self.asset_manager)
        self.projectiles.clear()
        self.enemy_manager.clear()
        self.wave_manager.reset()
        self.animation_effects.clear()
        # Empty spell queue
        while not self.spell_queue.empty():
            try:
                self.spell_queue.get_nowait()
            except queue.Empty:
                break

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        self.menu_manager.update(self.state, mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle menu clicks
            if self.state in [GameState.MAIN_MENU, GameState.PAUSED, GameState.GAME_OVER]:
                self.menu_manager.handle_event(self.state, event)
                
            # Play mode inputs
            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_game()
                    elif event.key == pygame.K_f or event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                        
                    # Dev / Testing Keyboard controls mapping
                    elif event.key == pygame.K_1:
                        self.cast_spell("fire")
                    elif event.key == pygame.K_2:
                        self.cast_spell("ice")
                    elif event.key == pygame.K_3:
                        self.cast_spell("lightning")
                    elif event.key == pygame.K_4:
                        self.cast_spell("wind")
            
            # Universal keypresses
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f or event.key == pygame.K_F11:
                    self.toggle_fullscreen()

    def process_spell_queue(self):
        """Processes queued CV spell casts on the main game thread."""
        while not self.spell_queue.empty():
            try:
                spell_name = self.spell_queue.get_nowait()
                if self.state == GameState.PLAYING:
                    self.spell_manager.cast(
                        spell_name, 
                        self.player, 
                        self.enemy_manager.enemies, 
                        self.projectiles, 
                        self.animation_effects
                    )
            except queue.Empty:
                break

    def update(self, dt):
        self.animation_effects.update(dt)
        
        if self.state == GameState.PLAYING:
            # 1. Process CV Spells
            self.process_spell_queue()
            
            # 2. Update entities & spell cooldowns
            self.player.update(dt)
            self.spell_manager.update(dt)  # Updates spell cooldown timers
            self.enemy_manager.update(dt, self.player, self.animation_effects)
            self.wave_manager.update(dt, self.player, self.animation_effects)
            
            # 3. Update projectiles
            for proj in self.projectiles[:]:
                proj.update(dt)
                if not proj.alive:
                    # Remove and spawn impact burst at target position
                    if proj.target and hasattr(proj.target, 'hp'):
                        hitbox = proj.target.get_hitbox()
                        self.animation_effects.add_particle_burst(
                            proj.x, proj.y, 
                            [proj.color, Colors.TEXT_MAIN], 
                            count=12, 
                            speed_range=(1.0, 3.5), 
                            size_range=(2, 6)
                        )
                    self.projectiles.remove(proj)
                    
            # 4. Check for GameOver (Wizard HP <= 0)
            if self.player.hp <= 0:
                self.state = GameState.GAME_OVER

    def draw(self):
        # Calculate screen shake offset
        shake_offset = self.animation_effects.shake_offset
        
        # All gameplay elements are drawn onto a game surface matching GAMEPLAY_WIDTH (960px)
        game_surf = pygame.Surface((GAMEPLAY_WIDTH, SCREEN_HEIGHT))
        
        # 1. Draw background
        game_surf.blit(self.background, (0, 0))
        
        if self.state in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER]:
            # 2. Draw enemies & player
            self.enemy_manager.draw(game_surf)
            self.player.draw(game_surf, self.animation_effects)
            
            # 3. Draw projectiles
            for proj in self.projectiles:
                proj.draw(game_surf, self.animation_effects)
                
            # 4. Draw game particle effects
            self.animation_effects.draw_particles(game_surf)
            
        # Draw game surface to screen with shake offset (stays clipped inside gameplay area)
        self.screen.fill(Colors.BACKGROUND)
        self.screen.blit(game_surf, (shake_offset[0], shake_offset[1]))
        
        # Floating texts and overlays are drawn on top of screenshake to keep them readable
        if self.state in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER]:
            self.animation_effects.draw_floating_texts(self.screen)
            self.hud.draw(self.screen, self.player, self.wave_manager, self.spell_manager)
            
        # Draw full screen flashes
        self.animation_effects.draw_flash(self.screen)
        
        # 5. Draw menus overlays
        if self.state == GameState.MAIN_MENU:
            self.menu_manager.draw_main_menu(self.screen)
        elif self.state == GameState.PAUSED:
            self.menu_manager.draw_pause_menu(self.screen)
        elif self.state == GameState.GAME_OVER:
            self.menu_manager.draw_game_over(self.screen, self.player.score, self.wave_manager.current_wave)
            
        pygame.display.flip()

    def run(self):
        # Game loop timing
        dt = 1.0  # Normalized dt at 60 FPS (1.0 = ~16.6ms)
        
        while self.running:
            # Limit frame rate
            self.clock.tick(TARGET_FPS)
            
            # Compute actual delta time normalized to 60fps
            actual_dt = self.clock.get_time() / 16.667
            actual_dt = min(actual_dt, 3.0)
            
            self.handle_events()
            self.update(actual_dt)
            self.draw()
            
        pygame.quit()
