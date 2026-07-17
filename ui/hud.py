import pygame
import math
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT, GAMEPLAY_WIDTH, SIDEBAR_WIDTH
from utils.helpers import draw_health_bar, draw_text_with_outline

class HUD:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        # Load fonts
        self.font_large = self.asset_manager.get_font(None, 28)
        self.font_medium = self.asset_manager.get_font(None, 18)
        self.font_small = self.asset_manager.get_font(None, 14)
        self.font_xsmall = self.asset_manager.get_font(None, 12)

        # --- NEW LOGO CODE ---
        import os
        try:
            raw_logo = pygame.image.load(os.path.join("assets", "logo", "logo.png")).convert_alpha()
            # Scaled up from 40px to 80px tall for better visibility
            w, h = raw_logo.get_size()
            self.sidebar_logo = pygame.transform.smoothscale(raw_logo, (int(w * (80 / h)), 80))
        except FileNotFoundError:
            self.sidebar_logo = None
        
    def draw(self, surface, player, wave_manager, spell_manager, game=None):
        # 1. Draw Player HP Bar (Top Left of Gameplay)
        hp_x, hp_y = 30, 30
        hp_w, hp_h = 240, 24
        draw_health_bar(surface, hp_x, hp_y, hp_w, hp_h, player.hp, player.max_hp)
        
        # Draw HP text over bar
        hp_text = f"WIZARD HP: {player.hp}/{player.max_hp}"
        draw_text_with_outline(
            surface, hp_text, self.font_small, 
            Colors.TEXT_MAIN, Colors.SHADOW, 
            (hp_x + 10, hp_y + 5)
        )
        
        # 2. Draw Score (Top Right of Gameplay area, X <= 960)
        score_text = f"SCORE: {player.score:05d}"
        score_w = self.font_large.size(score_text)[0]
        draw_text_with_outline(
            surface, score_text, self.font_large, 
            Colors.GOLD, Colors.SHADOW, 
            (GAMEPLAY_WIDTH - score_w - 30, hp_y)
        )
        
        # 3. Draw Wave Info (Top Center of Gameplay)
        wave_str = f"WAVE {wave_manager.current_wave}"
        wave_w = self.font_large.size(wave_str)[0]
        wave_x = GAMEPLAY_WIDTH // 2 - wave_w // 2
        draw_text_with_outline(
            surface, wave_str, self.font_large, 
            Colors.TEXT_MAIN, Colors.SHADOW, 
            (wave_x, hp_y)
        )
        
        # Wave Status subtext
        if wave_manager.in_breather:
            status_text = f"Next wave in {int(wave_manager.breather_timer) + 1}s..."
            status_color = Colors.GOLD
        else:
            remaining = wave_manager.get_remaining_enemies_count()
            status_text = f"Enemies Left: {remaining}"
            status_color = Colors.TEXT_MUTED
            
        status_w = self.font_medium.size(status_text)[0]
        draw_text_with_outline(
            surface, status_text, self.font_medium, 
            status_color, Colors.SHADOW, 
            (GAMEPLAY_WIDTH // 2 - status_w // 2, hp_y + 30)
        )
        
        # 4. Draw Spell Guide & Cooldown Hotbar (Bottom Center of Gameplay)
        self.draw_spell_hotbar(surface, spell_manager)

        # 5. Draw Right Sidebar (from 960 to 1280)
        self.draw_sidebar(surface, spell_manager, game)

    def draw_spell_hotbar(self, surface, spell_manager):
        # Updated to 6 working spells and physical hand symbols
        spell_slots = [
            {"id": "fire", "key": "1", "symbol": "Gun", "color": Colors.FIRE, "disp_name": "Fireball"},
            {"id": "ice", "key": "2", "symbol": "Peace", "color": Colors.ICE, "disp_name": "Frost Chill"},
            {"id": "lightning", "key": "3", "symbol": "Spidey", "color": Colors.LIGHTNING, "disp_name": "Lightning"},
            {"id": "wind", "key": "4", "symbol": "Palm", "color": Colors.WIND, "disp_name": "Gale Blast"},
            {"id": "shield", "key": "5", "symbol": "Fist", "color": Colors.SHIELD, "disp_name": "Aegis Shield"},
            {"id": "earthquake", "key": "6", "symbol": "L-Vibe", "color": Colors.EARTHQUAKE, "disp_name": "Earthquake"}
        ]
        
        slot_w, slot_h = 105, 75
        spacing = 8
        # Updated math for 6 slots instead of 8 so it stays perfectly centered
        total_w = (slot_w * 6) + (spacing * 5) 
        start_x = (GAMEPLAY_WIDTH - total_w) // 2
        start_y = SCREEN_HEIGHT - slot_h - 20
        
        for i, slot in enumerate(spell_slots):
            x = start_x + i * (slot_w + spacing)
            y = start_y
            
            # Cooldown progress
            cd_ratio = spell_manager.get_cooldown_ratio(slot["id"])
            
            # Card background
            card_rect = pygame.Rect(x, y, slot_w, slot_h)
            
            # Subtle outer glow if spell is ready
            if cd_ratio == 0:
                glow_rect = card_rect.inflate(4, 4)
                pygame.draw.rect(surface, (slot["color"][0], slot["color"][1], slot["color"][2], 100), glow_rect, border_radius=6, width=1)
                
            pygame.draw.rect(surface, Colors.BUTTON_NORMAL, card_rect, border_radius=6)
            pygame.draw.rect(surface, Colors.SHADOW, card_rect, width=2, border_radius=6)
            
            # Left vertical stripe showing spell theme color
            pygame.draw.rect(surface, slot["color"], (x, y, 5, slot_h), border_radius=6)
            
            # Write key mapping & spell name (use size 12 font to prevent cutoffs)
            name_text = slot["disp_name"]
            draw_text_with_outline(
                surface, f"[{slot['key']}] {name_text}", 
                self.font_xsmall, Colors.TEXT_MAIN, Colors.SHADOW, 
                (x + 8, y + 10)
            )
            
            # Write gesture symbol guide
            draw_text_with_outline(
                surface, slot["symbol"], 
                self.font_xsmall, Colors.TEXT_MUTED, Colors.SHADOW, 
                (x + 8, y + 30)
            )
            
            # Status: READY or CD timer
            if cd_ratio > 0:
                # Render transparent grey overlay indicating CD progress
                overlay = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
                overlay.fill((25, 20, 35, 180))
                surface.blit(overlay, (x, y))
                
                # Show remaining time text
                spell = spell_manager.spells[slot["id"]]
                cd_left = f"{spell.cooldown_timer:.1f}s"
                cd_w = self.font_medium.size(cd_left)[0]
                
                # Draw countdown center-aligned
                draw_text_with_outline(
                    surface, cd_left, self.font_medium, 
                    slot["color"], Colors.SHADOW, 
                    (x + slot_w // 2 - cd_w // 2, y + slot_h // 2 - 8)
                )
            else:
                draw_text_with_outline(
                    surface, "READY", 
                    self.font_xsmall, slot["color"], Colors.SHADOW, 
                    (x + 8, y + 50)
                )

    def draw_sidebar(self, surface, spell_manager, game=None):
        # 1. Background Frame
        sidebar_rect = pygame.Rect(GAMEPLAY_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, (14, 12, 22), sidebar_rect)
        pygame.draw.line(surface, Colors.GOLD, (GAMEPLAY_WIDTH, 0), (GAMEPLAY_WIDTH, SCREEN_HEIGHT), 2)
        
        # --- NEW LOGO RENDER CODE ---
        # Draw branding logo at the bottom-left of the sidebar
        if hasattr(self, 'sidebar_logo') and self.sidebar_logo:
            logo_x = GAMEPLAY_WIDTH + 15 # 15px padding from the left edge of the sidebar
            logo_y = SCREEN_HEIGHT - self.sidebar_logo.get_height() - 15 # 15px padding from the bottom
            surface.blit(self.sidebar_logo, (logo_x, logo_y))
        
        # 2. Camera Viewport (Centered dynamically in the new wider sidebar)
        cam_w = 316
        cam_h = 237
        # Centers the camera perfectly by dividing the leftover sidebar space
        cam_x = GAMEPLAY_WIDTH + ((SIDEBAR_WIDTH - cam_w) // 2) 
        cam_y = 60 # Shifted up to make room for legend
        
        cam_rect = pygame.Rect(cam_x, cam_y, cam_w, cam_h)
        pygame.draw.rect(surface, Colors.SHADOW, cam_rect.move(2, 2), border_radius=6)
        if game and getattr(game, 'cv_frame', None) is not None:
            surface.blit(game.cv_frame, (cam_x, cam_y))
        else:
            pygame.draw.rect(surface, (22, 19, 34), cam_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 230, 150), cam_rect, width=2, border_radius=6)
        
        # Draw camera HUD grid lines
        pygame.draw.rect(surface, (0, 230, 150, 40), (cam_x + 10, cam_y + 10, cam_w - 20, cam_h - 20), width=1)
        # Crosshair in center
        cx, cy = cam_x + cam_w // 2, cam_y + cam_h // 2
        pygame.draw.line(surface, (0, 230, 150, 90), (cx - 15, cy), (cx + 15, cy), 1)
        pygame.draw.line(surface, (0, 230, 150, 90), (cx, cy - 15), (cx, cy + 15), 1)
        
        # Recording Blinking Dot
        ticks = pygame.time.get_ticks()
        rec_active = (ticks // 500) % 2 == 0
        dot_color = (255, 50, 50) if rec_active else (80, 20, 20)
        pygame.draw.circle(surface, dot_color, (cam_x + 25, cam_y + 25), 6)
        draw_text_with_outline(
            surface, "GESTURE FEED (LIVE)", 
            self.font_small, Colors.TEXT_MAIN, Colors.SHADOW, 
            (cam_x + 38, cam_y + 18)
        )
        
        # Wait/Status message
        import time
        if game and hasattr(game, 'last_gesture') and game.last_gesture != "None" and (time.time() - game.last_gesture_time < 1.5):
            msg = f"{game.last_gesture.upper()} ({game.last_gesture_accuracy}%)"
            msg_color = (0, 255, 100) # Bright green
        else:
            msg = "[ WAITING FOR GESTURE ]"
            msg_color = (0, 230, 150)
            
        msg_w = self.font_small.size(msg)[0]
        draw_text_with_outline(
            surface, msg, 
            self.font_small, msg_color, Colors.SHADOW, 
            (cx - msg_w // 2, cy + 35)
        )

        # 3. Gesture Legend Below Camera
        legend_y = cam_y + cam_h + 40
        draw_text_with_outline(
            surface, "LIVE GESTURE GUIDE", 
            self.font_medium, Colors.GOLD, Colors.SHADOW, 
            (cam_x + 20, legend_y)
        )
        
        gestures = [
            ("Start / Resume", "Thumb", Colors.GOLD),
            ("Fireball", "Gun", Colors.FIRE),
            ("Frost Chill", "Peace", Colors.ICE),
            ("Lightning", "Spiderman", Colors.LIGHTNING),
            ("Gale Blast", "Palm", Colors.WIND),
            ("Aegis Shield", "Fist", Colors.SHIELD),
            ("Earthquake", "L-Vibe", Colors.EARTHQUAKE)
        ]
        
        for i, (spell_name, gesture_name, color) in enumerate(gestures):
            y_pos = legend_y + 40 + (i * 35)
            
            # Draw color bullet
            pygame.draw.circle(surface, color, (cam_x + 28, y_pos + 6), 5)
            
            # Gesture Name
            draw_text_with_outline(
                surface, gesture_name, 
                self.font_small, color, Colors.SHADOW, 
                (cam_x + 45, y_pos)
            )
            
            # Arrow
            draw_text_with_outline(
                surface, "->", 
                self.font_small, Colors.TEXT_MUTED, Colors.SHADOW, 
                (cam_x + 130, y_pos)
            )
            
            # Spell Name
            draw_text_with_outline(
                surface, spell_name, 
                self.font_small, Colors.TEXT_MAIN, Colors.SHADOW, 
                (cam_x + 160, y_pos)
            )
