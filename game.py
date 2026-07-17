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
from screens.screen_manager import ScreenManager
from screens.main_menu_screen import MainMenuScreen
from screens.gameplay_screen import GameplayScreen, DemoScreen
from screens.pause_screen import PauseScreen
from screens.game_over_screen import GameOverScreen
from utils.keyboard_tester import KeyboardTester

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

        # Register the gesture-first extra spells (Self Heal, Black Hole,
        # Telekinesis) onto the existing manager without editing spell.py.
        from spells.extra_spells import register_extra_spells
        register_extra_spells(self.spell_manager)
        
        # Game State
        self.state = GameState.MAIN_MENU
        
        # Game Entities
        self.player = Player(self.asset_manager)
        self.projectiles = []
        
        # UI
        self.hud = HUD(self.asset_manager)
        self.menu_manager = MenuManager(self.asset_manager, self)

        # Keyboard testing / fallback input (queues casts like the CV thread)
        self.keyboard_tester = KeyboardTester(self)

        # Screen state machine (drives the new CV-aware UI/UX layouts)
        self.screen_manager = ScreenManager(self)
        self.screen_manager.register(MainMenuScreen(self.screen_manager))
        self.screen_manager.register(GameplayScreen(self.screen_manager))
        self.screen_manager.register(DemoScreen(self.screen_manager))
        self.screen_manager.register(PauseScreen(self.screen_manager))
        self.screen_manager.register(GameOverScreen(self.screen_manager))
        
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

        # Start on the main menu screen (also sets self.state).
        self.screen_manager.switch_to(GameState.MAIN_MENU)

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
        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils

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
                        
                        # Trigger spell cast using the shared gesture map so the
                        # webcam poses, on-screen grimoire, and keyboard testing
                        # never drift apart (adds the previously-unused
                        # "no ring" -> shadow binding).
                        from ui.gesture_map import POSE_TO_SPELL
                        mapped_spell = POSE_TO_SPELL.get(recognized_gesture.lower().strip())
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
        self.screen_manager.switch_to(GameState.PLAYING)

    def start_demo(self):
        self.screen_manager.switch_to(GameState.DEMO_MODE)

    def resume_game(self):
        # Pause is an overlay pushed on top of gameplay; pop back to it.
        if self.screen_manager.current and self.screen_manager.current.name == GameState.PAUSED:
            self.screen_manager.pop()
        else:
            self.screen_manager.switch_to(GameState.PLAYING)

    def pause_game(self):
        self.screen_manager.push(GameState.PAUSED)

    def restart_game(self):
        self.reset_game()
        self.screen_manager.switch_to(GameState.PLAYING)

    def go_to_menu(self):
        self.reset_game()
        self.screen_manager.switch_to(GameState.MAIN_MENU)

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
        # Advance per-frame screen logic (hover states, button scaling, etc.).
        self.screen_manager.update(0.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            # Delegate all input to the active screen's state machine node.
            self.screen_manager.handle_event(event)

            # Universal fullscreen toggle available in every state.
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_f, pygame.K_F11):
                self.toggle_fullscreen()

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
                    from ui.gesture_map import NO_TARGET_SPELLS
                    if spell_name in NO_TARGET_SPELLS and spell_name in self.spell_manager.spells:
                        # Self/AoE spells cast directly, bypassing the
                        # target-required guard in SpellManager.cast.
                        spell = self.spell_manager.spells[spell_name]
                        if spell.is_ready():
                            spell.cast(
                                self.player, None,
                                self.projectiles, self.animation_effects,
                                self.enemy_manager.enemies,
                            )
                        else:
                            self.animation_effects.add_floating_text(
                                "Cooldown!", self.player.x - 20, self.player.y - 45,
                                Colors.TEXT_MUTED, self.asset_manager.get_font(None, 20),
                                duration=0.6, is_damage=False,
                            )
                    else:
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

        # Let the active screen advance its own per-frame logic.
        self.screen_manager.update(dt)

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
        # The active screen (and any overlays) render the full frame onto the
        # virtual 1280x720 canvas via the screen state machine.
        self.canvas.fill(Colors.BACKGROUND)
        self.screen_manager.draw(self.canvas)

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
