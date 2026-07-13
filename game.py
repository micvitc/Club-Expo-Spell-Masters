import pygame
import queue
import threading
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
        
        # Create virtual canvas (always 1280x720)
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Default to Fullscreen with windowed fallback
        self.is_fullscreen = True
        try:
            # Query native desktop resolution to run native fullscreen
            info = pygame.display.Info()
            self.desktop_width = info.current_w
            self.desktop_height = info.current_h
            
            # Start in native fullscreen
            self.screen = pygame.display.set_mode(
                (self.desktop_width, self.desktop_height), 
                pygame.FULLSCREEN | pygame.DOUBLEBUF
            )
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
        
        # CV server tracking info
        self.cv_frame = None
        self.last_gesture = "None"
        self.last_gesture_accuracy = 0
        self.last_gesture_time = 0.0
        
        # Start background CV pipeline thread
        self.cv_thread_active = True
        self.cv_thread = threading.Thread(target=self._run_cv_pipeline, daemon=True)
        self.cv_thread.start()
        
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

    def _run_cv_pipeline(self):
        import cv2
        import mediapipe as mp
        import json
        import math
        import time
        import pygame
        import mediapipe.solutions.hands as mp_hands
        import mediapipe.solutions.drawing_utils as mp_draw

        # Load gestures database
        try:
            with open("gestures.json", "r") as f:
                gestures_db = json.load(f)
        except Exception:
            gestures_db = {}

        if not gestures_db:
            print("[CV Pipeline] Warning: gestures.json not found or empty.")
            
        hands_detector = mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=1, 
            min_detection_confidence=0.7
        )

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[CV Pipeline] Error: Could not open camera.")
            return

        MAX_TOLERANCE = 0.15 
        MATCH_THRESHOLD = 60

        while self.cv_thread_active:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            
            # Process with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands_detector.process(rgb_frame)

            recognized_gesture = "None"
            best_accuracy = 0

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    live_landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand_landmarks.landmark]
                    live_wrist = live_landmarks[0]
                    norm_live = [
                        {'x': lm['x'] - live_wrist['x'], 'y': lm['y'] - live_wrist['y'], 'z': lm['z'] - live_wrist['z']}
                        for lm in live_landmarks
                    ]

                    for name, s_landmarks in gestures_db.items():
                        total_distance = 0
                        for i in range(21):
                            dx = norm_live[i]['x'] - s_landmarks[i]['x']
                            dy = norm_live[i]['y'] - s_landmarks[i]['y']
                            dz = norm_live[i]['z'] - s_landmarks[i]['z']
                            total_distance += math.sqrt(dx**2 + dy**2 + dz**2)
                        
                        average_error = total_distance / 21
                        raw_percentage = (1 - (average_error / MAX_TOLERANCE)) * 100
                        accuracy = max(0, int(raw_percentage))
                        
                        if accuracy > best_accuracy:
                            best_accuracy = accuracy
                            recognized_gesture = name

                    if best_accuracy >= MATCH_THRESHOLD:
                        self.last_gesture = recognized_gesture
                        self.last_gesture_accuracy = best_accuracy
                        self.last_gesture_time = time.time()
                        
                        # Trigger spell cast
                        spell_map = {
                            "thumb": "start",
                            "gun": "fire",
                            "peace": "ice",
                            "spiderman": "lightning",
                            "palm": "wind",
                            "fist": "shield",
                            "lvibe": "earthquake"
                        }
                        mapped_spell = spell_map.get(recognized_gesture.lower().strip())
                        if mapped_spell:
                            self.cast_spell(mapped_spell)

            # Convert BGR frame to RGB for Pygame
            rgb_frame_for_pygame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = rgb_frame_for_pygame.shape
            
            try:
                raw_surface = pygame.image.frombuffer(rgb_frame_for_pygame.tobytes(), (w, h), "RGB")
                # Scale to fit 300x225
                scaled_surface = pygame.transform.scale(raw_surface, (300, 225))
                self.cv_frame = scaled_surface
            except Exception as e:
                pass

            time.sleep(0.03)

        cap.release()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            try:
                info = pygame.display.Info()
                self.screen = pygame.display.set_mode(
                    (info.current_w, info.current_h), 
                    pygame.FULLSCREEN | pygame.DOUBLEBUF
                )
            except pygame.error:
                self.is_fullscreen = False
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def get_canvas_mouse_pos(self):
        """Maps raw screen mouse coordinates back to the 1280x720 virtual canvas space."""
        mx, my = pygame.mouse.get_pos()
        screen_w, screen_h = self.screen.get_size()
        
        canvas_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
        screen_aspect = screen_w / screen_h
        
        if screen_aspect > canvas_aspect:
            # Pillarboxing
            scale_factor = screen_h / SCREEN_HEIGHT
            offset_x = (screen_w - SCREEN_WIDTH * scale_factor) / 2
            offset_y = 0
        else:
            # Letterboxing
            scale_factor = screen_w / SCREEN_WIDTH
            offset_x = 0
            offset_y = (screen_h - SCREEN_HEIGHT * scale_factor) / 2
            
        canvas_x = (mx - offset_x) / scale_factor
        canvas_y = (my - offset_y) / scale_factor
        
        # Clamp to canvas boundaries
        canvas_x = max(0, min(SCREEN_WIDTH - 1, canvas_x))
        canvas_y = max(0, min(SCREEN_HEIGHT - 1, canvas_y))
        
        return int(canvas_x), int(canvas_y)

    def start_game(self):
        self.reset_game()
        self.state = GameState.PLAYING

    def start_demo(self):
        self.state = GameState.DEMO_MODE

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
        mouse_pos = self.get_canvas_mouse_pos()
        self.menu_manager.update(self.state, mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle menu clicks (include DEMO_MODE for EXIT PRACTICE button clicks)
            if self.state in [GameState.MAIN_MENU, GameState.PAUSED, GameState.GAME_OVER, GameState.DEMO_MODE]:
                self.menu_manager.handle_event(self.state, event)
                
            # Play mode inputs
            if self.state == GameState.PLAYING:
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
                    elif event.key == pygame.K_5:
                        self.cast_spell("shield")
                    elif event.key == pygame.K_6:
                        self.cast_spell("earthquake")
                    elif event.key == pygame.K_7:
                        self.cast_spell("shadow")
                    elif event.key == pygame.K_8:
                        self.cast_spell("solarbeam")
            
            # Universal keypresses for starting or toggling fullscreen
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f or event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_SPACE or event.key == pygame.K_s or event.key == pygame.K_RETURN:
                    # Simulate start gesture
                    self.cast_spell("start")

    def process_spell_queue(self):
        """Processes queued CV spell casts on the main game thread."""
        while not self.spell_queue.empty():
            try:
                spell_name = self.spell_queue.get_nowait()
                spell_name = spell_name.lower().strip()
                
                if spell_name == "start":
                    # Start gesture: starts or resumes the game depending on state
                    if self.state == GameState.MAIN_MENU:
                        self.start_game()
                        # Add a quick visual feedback floating text
                        self.animation_effects.add_floating_text(
                            "GAME START!", 
                            SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 
                            Colors.GOLD, 
                            self.asset_manager.get_font(None, 36),
                            duration=1.5,
                            is_damage=False
                        )
                    elif self.state == GameState.PAUSED:
                        self.resume_game()
                    elif self.state == GameState.GAME_OVER:
                        self.restart_game()
                elif self.state == GameState.PLAYING or self.state == GameState.DEMO_MODE:
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
        
        # Process queue in all states (so start gesture works in menus)
        self.process_spell_queue()
        
        if self.state == GameState.PLAYING or self.state == GameState.DEMO_MODE:
            # Update entities & spell cooldowns
            self.player.update(dt)
            self.spell_manager.update(dt)  # Updates spell cooldown timers
            self.enemy_manager.update(dt, self.player, self.animation_effects)
            
            if self.state == GameState.PLAYING:
                self.wave_manager.update(dt, self.player, self.animation_effects)
            
            # Update projectiles
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
                    
            # Check for GameOver (Wizard HP <= 0)
            if self.player.hp <= 0:
                self.state = GameState.GAME_OVER

    def draw(self):
        # Calculate screen shake offset
        shake_offset = self.animation_effects.shake_offset
        
        # All gameplay elements are drawn onto a game surface matching GAMEPLAY_WIDTH (960px)
        game_surf = pygame.Surface((GAMEPLAY_WIDTH, SCREEN_HEIGHT))
        
        # 1. Draw background
        game_surf.blit(self.background, (0, 0))
        
        if self.state in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER, GameState.DEMO_MODE]:
            # 2. Draw enemies & player
            self.enemy_manager.draw(game_surf)
            self.player.draw(game_surf, self.animation_effects)
            
            # 3. Draw projectiles
            for proj in self.projectiles:
                proj.draw(game_surf, self.animation_effects)
                
            # 4. Draw game particle effects
            self.animation_effects.draw_particles(game_surf)
            
        # Draw game surface to virtual canvas with shake offset (stays clipped inside gameplay area)
        self.canvas.fill(Colors.BACKGROUND)
        self.canvas.blit(game_surf, (shake_offset[0], shake_offset[1]))
        
        # Floating texts and overlays are drawn on top of screenshake on the virtual canvas
        if self.state in [GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER, GameState.DEMO_MODE]:
            self.animation_effects.draw_floating_texts(self.canvas)
            self.hud.draw(self.canvas, self.player, self.wave_manager, self.spell_manager, self)
            
        # Draw full screen flashes on the virtual canvas
        self.animation_effects.draw_flash(self.canvas)
        
        # 5. Draw menus overlays on the virtual canvas
        if self.state == GameState.MAIN_MENU:
            self.menu_manager.draw_main_menu(self.canvas)
        elif self.state == GameState.DEMO_MODE:
            self.menu_manager.draw_demo_overlay(self.canvas)
        elif self.state == GameState.PAUSED:
            self.menu_manager.draw_pause_menu(self.canvas)
        elif self.state == GameState.GAME_OVER:
            self.menu_manager.draw_game_over(self.canvas, self.player.score, self.wave_manager.current_wave)
            
        # Scale the virtual 1280x720 canvas to fit the actual display window
        screen_w, screen_h = self.screen.get_size()
        canvas_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
        screen_aspect = screen_w / screen_h
        
        if screen_aspect > canvas_aspect:
            # Display window is wider than canvas -> Pillarbox (bars on left/right)
            new_h = screen_h
            new_w = int(new_h * canvas_aspect)
            offset_x = (screen_w - new_w) // 2
            offset_y = 0
        else:
            # Display window is taller than canvas -> Letterbox (bars on top/bottom)
            new_w = screen_w
            new_h = int(new_w / canvas_aspect)
            offset_x = 0
            offset_y = (screen_h - new_h) // 2
            
        # Scale and render the canvas centered on the screen
        scaled_canvas = pygame.transform.smoothscale(self.canvas, (new_w, new_h))
        self.screen.fill((0, 0, 0)) # Fill screen with pure black bars
        self.screen.blit(scaled_canvas, (offset_x, offset_y))
        
        pygame.display.flip()

    def run(self):
        # Game loop timing
        dt = 1.0  # Normalized dt at 60 FPS (1.0 = ~16.6ms)
        
        try:
            while self.running:
                # Limit frame rate
                self.clock.tick(TARGET_FPS)
                
                # Compute actual delta time normalized to 60fps
                actual_dt = self.clock.get_time() / 16.667
                actual_dt = min(actual_dt, 3.0)
                
                self.handle_events()
                self.update(actual_dt)
                self.draw()
        finally:
            self.cv_thread_active = False
            pygame.quit()
