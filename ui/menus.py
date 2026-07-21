import pygame
import sys
import random
import math
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT, GAMEPLAY_WIDTH
from utils.helpers import draw_text_with_outline

class Button:
    def __init__(self, x, y, width, height, text, font, action, normal_color=Colors.BUTTON_NORMAL, hover_color=Colors.BUTTON_HOVER, text_color=Colors.TEXT_MAIN):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        
        self.is_hovered = False
        self.scale = 1.0

    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Smoothly expand button size on hover
        if self.is_hovered:
            self.scale = min(1.05, self.scale + 0.01)
        else:
            self.scale = max(1.0, self.scale - 0.01)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return self.action()
        return None

    def draw(self, surface):
        # Apply scaling based on hover state
        scaled_w = int(self.rect.width * self.scale)
        scaled_h = int(self.rect.height * self.scale)
        draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        draw_rect.center = self.rect.center
        
        # Determine background color
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # Draw Shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(surface, Colors.SHADOW, shadow_rect, border_radius=6)
        
        # Draw Main Button
        pygame.draw.rect(surface, color, draw_rect, border_radius=6)
        
        # Draw Border
        border_color = Colors.GOLD if self.is_hovered else Colors.TEXT_MUTED
        pygame.draw.rect(surface, border_color, draw_rect, width=2, border_radius=6)
        
        # Draw Text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class MenuManager:
    def __init__(self, asset_manager, game):
        self.asset_manager = asset_manager
        self.game = game
        
        # Fonts
        self.font_title = self.asset_manager.get_font(None, 64)
        self.font_subtitle = self.asset_manager.get_font(None, 24)
        self.font_button = self.asset_manager.get_font(None, 24)
        self.font_medium = self.asset_manager.get_font(None, 20)
        self.font_hud = self.asset_manager.get_font(None, 18)

        # Initialize Button lists for different states
        self.menu_buttons = []
        self.pause_buttons = []
        self.gameover_buttons = []
        
        self.setup_buttons()
        
        # Magical drifting background particles for title screen
        self.bg_particles = []
        for _ in range(60):
            self.bg_particles.append({
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(-0.9, -0.2), # Slow float upwards
                "color": random.choice([Colors.WIZARD_COLOR, Colors.GOLD, Colors.FIRE, Colors.ICE]),
                "size": random.uniform(2, 6),
                "alpha_phase": random.uniform(0, 100)
            })

        # --- NEW LOGO CODE ---
        import os
        try:
            raw_logo = pygame.image.load(os.path.join("assets", "logo", "logo.png")).convert_alpha()
            # Scale dynamically to keep aspect ratio (120px tall for a nice Hero size)
            w, h = raw_logo.get_size()
            self.menu_logo = pygame.transform.smoothscale(raw_logo, (int(w * (120 / h)), 120))
        except FileNotFoundError:
            self.menu_logo = None

    def setup_buttons(self):
        # 1. Main Menu Buttons (Positioned to the right to avoid overlapping)
        self.menu_buttons = [
            Button(
                920, 310, 240, 50, 
                "START MAGIC", self.font_button, lambda: self.game.start_game()
            ),
            Button(
                920, 390, 240, 50, 
                "DEMO TUTORIAL", self.font_button, lambda: self.game.start_demo()
            ),
            Button(
                920, 470, 240, 50, 
                "QUIT GAME", self.font_button, lambda: sys.exit()
            )
        ]
        
        # 4. Demo Tutorial Buttons (Shifted up to avoid spell bar)
        self.demo_buttons = [
            Button(
                SCREEN_WIDTH // 2, 560, 220, 45, 
                "BACK TO MENU", self.font_button, lambda: self.game.go_to_menu()
            )
        ]
        
        # 2. Pause Buttons
        self.pause_buttons = [
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, 200, 45, 
                "RESUME GAME", self.font_button, lambda: self.game.resume_game()
            ),
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 25, 200, 45, 
                "RESTART", self.font_button, lambda: self.game.restart_game()
            ),
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90, 200, 45, 
                "MAIN MENU", self.font_button, lambda: self.game.go_to_menu()
            )
        ]
        
        # 3. Game Over Buttons
        self.gameover_buttons = [
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 95, 200, 45, 
                "TRY AGAIN", self.font_button, lambda: self.game.restart_game()
            ),
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 160, 200, 45, 
                "MAIN MENU", self.font_button, lambda: self.game.go_to_menu()
            )
        ]

    def update(self, state, mouse_pos):
        # Update background floating sparks
        for p in self.bg_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha_phase"] += 0.05
            
            # Wrap around edges
            if p["y"] < -10:
                p["y"] = SCREEN_HEIGHT + 10
                p["x"] = random.uniform(0, SCREEN_WIDTH)
            if p["x"] < -10:
                p["x"] = SCREEN_WIDTH + 10
            elif p["x"] > SCREEN_WIDTH + 10:
                p["x"] = -10
                
        if state == "MAIN_MENU":
            for btn in self.menu_buttons:
                btn.update(mouse_pos)
        elif state == "DEMO_MODE":
            for btn in self.demo_buttons:
                btn.update(mouse_pos)
        elif state == "PAUSED":
            for btn in self.pause_buttons:
                btn.update(mouse_pos)
        elif state == "GAME_OVER":
            for btn in self.gameover_buttons:
                btn.update(mouse_pos)

    def handle_event(self, state, event):
        if state == "MAIN_MENU":
            for btn in self.menu_buttons:
                btn.handle_event(event)
        elif state == "DEMO_MODE":
            for btn in self.demo_buttons:
                btn.handle_event(event)
        elif state == "PAUSED":
            for btn in self.pause_buttons:
                btn.handle_event(event)
        elif state == "GAME_OVER":
            for btn in self.gameover_buttons:
                btn.handle_event(event)

    def draw_main_menu(self, surface):
        # Clean Background Grid
        surface.fill(Colors.BACKGROUND)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, (28, 24, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(surface, (28, 24, 40), (0, y), (SCREEN_WIDTH, y))

        # Render magical drifts
        for p in self.bg_particles:
            alpha = int(40 + 35 * math.sin(p["alpha_phase"]))
            alpha = max(10, min(120, alpha))
            sz = int(p["size"])
            if sz > 0:
                surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                c = p["color"]
                pygame.draw.circle(surf, (c[0], c[1], c[2], alpha), (sz, sz), sz)
                surface.blit(surf, (int(p["x"] - sz), int(p["y"] - sz)))

        # Pulsing Title
        ticks = pygame.time.get_ticks()
        pulse_g = int(185 + 40 * math.sin(ticks * 0.003))
        title_color = (255, pulse_g, 50) # Shift between orange/gold
        
        title_text = "SPELL MASTER"
        title_w, title_h = self.font_title.size(title_text)
        title_x = SCREEN_WIDTH // 2 - title_w // 2
        
        # --- NEW LOGO RENDER CODE ---
        title_y = SCREEN_HEIGHT // 4 - 30 # Title stays in its normal center position
        
        if hasattr(self, 'menu_logo') and self.menu_logo:
            # Positioned in the Top-Right with 20px of padding
            logo_x = SCREEN_WIDTH - self.menu_logo.get_width() - 20
            surface.blit(self.menu_logo, (logo_x, 20))
            
        # Soft glowing title backdrop ellipse
        glow_surf = pygame.Surface((title_w + 120, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (120, 80, 220, 30), (60, 20, title_w, 60))
        surface.blit(glow_surf, (title_x - 60, title_y - 20))
        
        draw_text_with_outline(
            surface, title_text, self.font_title, 
            title_color, Colors.SHADOW, 
            (title_x, title_y),
            outline_width=3
        )
        
        # Subtitle - Positioned dynamically below the Title
        sub_text = "CV Position-Based Magic Duel"
        sub_w, sub_h = self.font_subtitle.size(sub_text)
        sub_y = title_y + title_h + 10
        draw_text_with_outline(
            surface, sub_text, self.font_subtitle, 
            Colors.TEXT_MUTED, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - sub_w // 2, sub_y)
        )
        
        # Draw Spells Guide Panel - Positioned dynamically below the Subtitle
        grimoire_y = sub_y + sub_h + 40
        self.draw_guide_panel(surface, start_y=grimoire_y)

        # Draw Buttons
        for btn in self.menu_buttons:
            btn.draw(surface)
            
    def draw_guide_panel(self, surface, start_y):
        # Draw a beautiful dark glass-like box listing gestures (Single Column Layout)
        panel_w, panel_h = 450, 360
        panel_x = 80
        panel_rect = pygame.Rect(panel_x, start_y, panel_w, panel_h)
        
        # Shadow
        pygame.draw.rect(surface, Colors.SHADOW, panel_rect.move(3, 3), border_radius=8)
        # Background
        pygame.draw.rect(surface, Colors.BUTTON_NORMAL, panel_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.GOLD, panel_rect, width=1, border_radius=8)
        
        # Header
        draw_text_with_outline(
            surface, "MAGIC GRIMOIRE (POSITIONS)", 
            self.font_subtitle, Colors.GOLD, Colors.SHADOW, 
            (panel_rect.x + 20, panel_rect.y + 15)
        )
        
        # 6 Spell lines using Hand Positions stacked vertically
        spells_info = [
            ("Fireball", "Top-Right Hand", Colors.FIRE),
            ("Frost Chill", "Top-Left Hand", Colors.ICE),
            ("Lightning", "High-Center Hand", Colors.LIGHTNING),
            ("Gale Blast", "Low-Center Hand", Colors.WIND),
            ("Aegis Shield", "Both Hands Up", Colors.SHIELD),
            ("Earthquake", "Low-Left Hand", Colors.EARTHQUAKE)
        ]
        
        for idx, (name, symbol, color) in enumerate(spells_info):
            col_x = panel_rect.x + 20
            y_offset = panel_rect.y + 50 + idx * 25
            
            # Bullet point indicator
            pygame.draw.circle(surface, color, (col_x + 8, y_offset + 10), 5)
            
            # Draw name and position dynamically back-to-back
            name_str = f"{name}: "
            name_w = self.font_hud.size(name_str)[0]
            
            draw_text_with_outline(
                surface, name_str, 
                self.font_hud, Colors.TEXT_MAIN, Colors.SHADOW, 
                (col_x + 22, y_offset)
            )
            draw_text_with_outline(
                surface, symbol, 
                self.font_hud, color, Colors.SHADOW, 
                (col_x + 22 + name_w, y_offset)
            )
            
        # Start Gesture instruction (positioned cleanly inside the box)
        draw_text_with_outline(
            surface, "* START GESTURE: Wave Hand / High Five (SPACE key)", 
            self.font_hud, Colors.GOLD, Colors.SHADOW, 
            (panel_rect.x + 20, panel_rect.y + 320)
        )

    def draw_demo_overlay(self, surface):
        # Draw pulsating alert text below the top HUD (No solid background)
        ticks = pygame.time.get_ticks()
        # Create a pulsing alpha effect between ~100 and 255
        alpha = int(175 + 80 * math.sin(ticks * 0.004))
        
        bot_text = "DEMO MODE: AUTOMATED BOT PLAYING"
        bot_w = self.font_subtitle.size(bot_text)[0]
        
        # Render text with alpha transparency
        text_surf = self.font_subtitle.render(bot_text, True, Colors.GOLD)
        text_surf.set_alpha(alpha)
        
        # Position it at Y=85, safely below the Wave & Score text
        text_x = (GAMEPLAY_WIDTH // 2) - (bot_w // 2)
        surface.blit(text_surf, (text_x, 85))

        # Draw Back Button
        for btn in self.demo_buttons:
            btn.draw(surface)

    def draw_pause_menu(self, surface):
        # Semi-transparent dark overlay over the game scene
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 15, 180))
        surface.blit(overlay, (0, 0))
        
        # Panel
        panel_w, panel_h = 320, 320
        panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) // 2, (SCREEN_HEIGHT - panel_h) // 2 - 20, panel_w, panel_h)
        pygame.draw.rect(surface, Colors.BUTTON_NORMAL, panel_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.GOLD, panel_rect, width=2, border_radius=8)
        
        # Pause Title
        title_str = "GAME PAUSED"
        title_w = self.font_subtitle.size(title_str)[0]
        draw_text_with_outline(
            surface, title_str, self.font_subtitle, 
            Colors.GOLD, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - title_w // 2, panel_rect.y + 25)
        )
        
        # Draw Buttons
        for btn in self.pause_buttons:
            btn.draw(surface)

    def draw_game_over(self, surface, final_score, final_wave):
        # Dark red transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((25, 10, 15, 210))
        surface.blit(overlay, (0, 0))
        
        # Defeat Title
        title_str = "DEFEAT"
        title_w = self.font_title.size(title_str)[0]
        draw_text_with_outline(
            surface, title_str, self.font_title, 
            Colors.HP_BAR_FILL, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - title_w // 2, SCREEN_HEIGHT // 4 - 30),
            outline_width=3
        )
        
        # Subtitle
        sub_str = "Your magic has run out..."
        sub_w = self.font_subtitle.size(sub_str)[0]
        draw_text_with_outline(
            surface, sub_str, self.font_subtitle, 
            Colors.TEXT_MUTED, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - sub_w // 2, SCREEN_HEIGHT // 4 + 40)
        )
        
        # Final Stats panel (widened to 320 to prevent text overflow)
        stats_w, stats_h = 320, 100
        stats_rect = pygame.Rect((SCREEN_WIDTH - stats_w) // 2, SCREEN_HEIGHT // 2 - 50, stats_w, stats_h)
        pygame.draw.rect(surface, Colors.BUTTON_NORMAL, stats_rect, border_radius=6)
        pygame.draw.rect(surface, Colors.HP_BAR_FILL, stats_rect, width=1, border_radius=6)
        
        score_str = f"Final Score: {final_score}"
        score_w = self.font_subtitle.size(score_str)[0]
        draw_text_with_outline(
            surface, score_str, self.font_subtitle, 
            Colors.GOLD, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - score_w // 2, stats_rect.y + 15)
        )
        
        wave_str = f"Waves Cleared: {final_wave - 1}"
        wave_w = self.font_subtitle.size(wave_str)[0]
        draw_text_with_outline(
            surface, wave_str, self.font_subtitle, 
            Colors.TEXT_MAIN, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - wave_w // 2, stats_rect.y + 48)
        )

        # Dynamically switch button action and text if game over occurred during demo run
        if getattr(self.game, 'was_demo', False):
            self.gameover_buttons[0].text = "RESTART DEMO"
            self.gameover_buttons[0].action = lambda: self.game.start_demo()
        else:
            self.gameover_buttons[0].text = "TRY AGAIN"
            self.gameover_buttons[0].action = lambda: self.game.restart_game()

        # Draw Buttons
        for btn in self.gameover_buttons:
            btn.draw(surface)