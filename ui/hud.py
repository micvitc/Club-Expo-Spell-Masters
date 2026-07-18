import pygame
import math
import os
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT, GAMEPLAY_WIDTH, SIDEBAR_WIDTH
from utils.helpers import draw_health_bar, draw_text_with_outline

# A helper for drawing beautiful neon glow in Pygame
def draw_neon_glow(surface, rect_obj, color, radius=12, intensity=120):
    x, y, w, h = rect_obj
    glow_surf = pygame.Surface((w + radius*2, h + radius*2), pygame.SRCALPHA)
    for i in range(radius):
        alpha = int(intensity * (1.0 - (i / radius)**1.5))
        if alpha > 0:
            pygame.draw.rect(glow_surf, (*color[:3], alpha), (radius - i, radius - i, w + i*2, h + i*2), border_radius=8+i)
    surface.blit(glow_surf, (x - radius, y - radius))

class HUD:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        # Load fonts
        self.font_large = self.asset_manager.get_font(None, 28)
        self.font_medium = self.asset_manager.get_font(None, 18)
        self.font_small = self.asset_manager.get_font(None, 14)
        self.font_xsmall = self.asset_manager.get_font(None, 12)
        
        # Try loading emoji font
        try:
            self.font_emoji_small = pygame.font.SysFont("segoe ui emoji", 14)
            self.font_emoji_xsmall = pygame.font.SysFont("segoe ui emoji", 12)
        except Exception:
            self.font_emoji_small = self.font_small
            self.font_emoji_xsmall = self.font_xsmall

        try:
            raw_logo = pygame.image.load(os.path.join("assets", "logo", "logo.png")).convert_alpha()
            w, h = raw_logo.get_size()
            # Larger logo for bottom left of gameplay screen
            target_h = 100
            self.sidebar_logo = pygame.transform.smoothscale(raw_logo, (int(w * (target_h / h)), target_h))
            self.sidebar_logo.set_alpha(80) # Low opacity
        except FileNotFoundError:
            self.sidebar_logo = None
            
        # Preload gesture icons
        self.gesture_icons = {}
        gesture_names = ["fist", "peace", "lvibe", "threefinger", "palm", "spiderman"]
        for g in gesture_names:
            path = os.path.join("assets", "logo", f"{g}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                self.gesture_icons[g] = img
            except Exception:
                self.gesture_icons[g] = None
        
    def draw(self, surface, player, wave_manager, spell_manager, game=None):
        # 0. Draw Logo at bottom left of gameplay screen (low opacity background element)
        if hasattr(self, 'sidebar_logo') and self.sidebar_logo:
            logo_x = 20
            logo_y = SCREEN_HEIGHT - self.sidebar_logo.get_height() - 20
            surface.blit(self.sidebar_logo, (logo_x, logo_y))
            
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
        
        # (Bottom hotbar removed based on user request)

        # 5. Draw Right Sidebar (from 960 to 1280)
        self.draw_sidebar(surface, spell_manager, game)

    def draw_sidebar(self, surface, spell_manager, game=None):
        # 1. Background Frame
        sidebar_rect = pygame.Rect(GAMEPLAY_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, (14, 12, 22), sidebar_rect)
        pygame.draw.line(surface, Colors.GOLD, (GAMEPLAY_WIDTH, 0), (GAMEPLAY_WIDTH, SCREEN_HEIGHT), 2)
        
        # 2. Camera Viewport (Pushed slightly up to give the grid space)
        cam_w = 316
        cam_h = 237
        cam_x = GAMEPLAY_WIDTH + ((SIDEBAR_WIDTH - cam_w) // 2) 
        cam_y = 20 # Pushed from 60 to 20
        
        cam_rect = pygame.Rect(cam_x, cam_y, cam_w, cam_h)
        pygame.draw.rect(surface, Colors.SHADOW, cam_rect.move(2, 2), border_radius=6)
        if game and getattr(game, 'cv_frame', None) is not None:
            surface.blit(game.cv_frame, (cam_x, cam_y))
        else:
            pygame.draw.rect(surface, (22, 19, 34), cam_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 230, 150), cam_rect, width=2, border_radius=6)
        
        pygame.draw.rect(surface, (0, 230, 150, 40), (cam_x + 10, cam_y + 10, cam_w - 20, cam_h - 20), width=1)
        cx, cy = cam_x + cam_w // 2, cam_y + cam_h // 2
        pygame.draw.line(surface, (0, 230, 150, 90), (cx - 15, cy), (cx + 15, cy), 1)
        pygame.draw.line(surface, (0, 230, 150, 90), (cx, cy - 15), (cx, cy + 15), 1)
        
        ticks = pygame.time.get_ticks()
        rec_active = (ticks // 500) % 2 == 0
        dot_color = (255, 50, 50) if rec_active else (80, 20, 20)
        pygame.draw.circle(surface, dot_color, (cam_x + 25, cam_y + 25), 6)
        draw_text_with_outline(
            surface, "GESTURE FEED (LIVE)", 
            self.font_small, Colors.TEXT_MAIN, Colors.SHADOW, 
            (cam_x + 38, cam_y + 18)
        )
        
        import time
        if game and hasattr(game, 'last_gesture') and game.last_gesture != "None" and (time.time() - game.last_gesture_time < 1.5):
            msg = f"{game.last_gesture.upper()} ({game.last_gesture_accuracy}%)"
            msg_color = (0, 255, 100)
        else:
            msg = "[ WAITING FOR GESTURE ]"
            msg_color = (0, 230, 150)
            
        msg_w = self.font_small.size(msg)[0]
        draw_text_with_outline(
            surface, msg, 
            self.font_small, msg_color, Colors.SHADOW, 
            (cx - msg_w // 2, cy + 35)
        )

        # 3. Gesture Legend 2x3 Grid
        legend_y = cam_y + cam_h + 15
        draw_text_with_outline(
            surface, "SPELL GUIDE & COOLDOWNS", 
            self.font_medium, Colors.GOLD, Colors.SHADOW, 
            (cam_x + 10, legend_y)
        )
        
        grid_spells = [
            {"id": "fire", "symbol": "fist", "color": Colors.FIRE, "disp": "🔥 Fireball"},
            {"id": "ice", "symbol": "peace", "color": Colors.ICE, "disp": "❄️ Frost Chill"},
            {"id": "lightning", "symbol": "lvibe", "color": Colors.LIGHTNING, "disp": "⚡ Lightning"},
            {"id": "wind", "symbol": "threefinger", "color": Colors.WIND, "disp": "🌪️ Gale Blast"},
            {"id": "shield", "symbol": "palm", "color": Colors.SHIELD, "disp": "🛡️ Aegis Shield"},
            {"id": "earthquake", "symbol": "spiderman", "color": Colors.EARTHQUAKE, "disp": "🌍 Earthquake"}
        ]
        
        # Sized nicely to fit everything including the logo at the bottom
        box_w = 145
        box_h = 90
        padding_x = 10
        padding_y = 10
        
        start_x = cam_x + (cam_w - (box_w * 2 + padding_x)) // 2
        start_y = legend_y + 25
        
        for i, item in enumerate(grid_spells):
            col = i % 2
            row = i // 2
            
            bx = start_x + col * (box_w + padding_x)
            by = start_y + row * (box_h + padding_y)
            
            cd_ratio = spell_manager.get_cooldown_ratio(item["id"])
            
            # Base box background
            pygame.draw.rect(surface, Colors.BUTTON_NORMAL, (bx, by, box_w, box_h), border_radius=8)
            
            if cd_ratio == 0:
                # Add real neon glow around the entire box
                draw_neon_glow(surface, (bx, by, box_w, box_h), item["color"], radius=10, intensity=100)
                # Hard border
                pygame.draw.rect(surface, item["color"], (bx, by, box_w, box_h), width=2, border_radius=8)
            else:
                # Cooldown - draw base border
                pygame.draw.rect(surface, Colors.SHADOW, (bx, by, box_w, box_h), width=2, border_radius=8)
                
                # Glowing side border bar (loading effect)
                fill_ratio = 1.0 - cd_ratio
                bar_h = int((box_h - 4) * fill_ratio)
                if bar_h > 0:
                    bar_rect = (bx, by + (box_h - 2 - bar_h), 5, bar_h)
                    # Real neon glow just on the loading bar
                    draw_neon_glow(surface, bar_rect, item["color"], radius=6, intensity=150)
                    # Solid core line
                    pygame.draw.rect(surface, (255,255,255), bar_rect, border_radius=3)
            
            # Draw Custom Icon (Top 75%)
            img_h = int(box_h * 0.70)
            img = self.gesture_icons.get(item["symbol"])
            if img:
                iw, ih = img.get_size()
                scale = min((box_w - 20) / iw, img_h / ih)
                scaled_img = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
                img_x = bx + box_w // 2 - scaled_img.get_width() // 2
                img_y = by + 3 + (img_h - scaled_img.get_height()) // 2
                surface.blit(scaled_img, (img_x, img_y))
            else:
                # Placeholder text if missing
                draw_text_with_outline(
                    surface, "No Image", 
                    self.font_small, Colors.TEXT_MUTED, Colors.SHADOW, 
                    (bx + box_w // 2 - 25, by + img_h // 2)
                )
                
            # Text at bottom
            text_str = item["disp"]
            outline_surf = self.font_emoji_xsmall.render(text_str, True, Colors.SHADOW)
            text_surf = self.font_emoji_xsmall.render(text_str, True, Colors.TEXT_MAIN)
            
            text_x = bx + box_w // 2 - text_surf.get_width() // 2
            text_y = by + box_h - text_surf.get_height() - 5
            
            surface.blit(outline_surf, (text_x + 1, text_y + 1))
            surface.blit(text_surf, (text_x, text_y))


