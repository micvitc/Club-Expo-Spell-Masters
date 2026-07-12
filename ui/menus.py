import pygame
import sys
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT
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
        self.font_hud = self.asset_manager.get_font(None, 18)

        # Initialize Button lists for different states
        self.menu_buttons = []
        self.pause_buttons = []
        self.gameover_buttons = []
        
        self.setup_buttons()

    def setup_buttons(self):
        # 1. Main Menu Buttons
        self.menu_buttons = [
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, 200, 45, 
                "START MAGIC", self.font_button, lambda: self.game.start_game()
            ),
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100, 200, 45, 
                "QUIT GAME", self.font_button, lambda: sys.exit()
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
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, 200, 45, 
                "TRY AGAIN", self.font_button, lambda: self.game.restart_game()
            ),
            Button(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 115, 200, 45, 
                "MAIN MENU", self.font_button, lambda: self.game.go_to_menu()
            )
        ]

    def update(self, state, mouse_pos):
        if state == "MAIN_MENU":
            for btn in self.menu_buttons:
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

        # Title
        title_text = "SPELL MASTER"
        title_w = self.font_title.size(title_text)[0]
        draw_text_with_outline(
            surface, title_text, self.font_title, 
            Colors.GOLD, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - title_w // 2, SCREEN_HEIGHT // 4 - 20),
            outline_width=3
        )
        
        # Subtitle
        sub_text = "CV Gesture Magic Arena"
        sub_w = self.font_subtitle.size(sub_text)[0]
        draw_text_with_outline(
            surface, sub_text, self.font_subtitle, 
            Colors.TEXT_MUTED, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - sub_w // 2, SCREEN_HEIGHT // 4 + 45)
        )
        
        # Draw Spells Guide Panel on main menu
        self.draw_guide_panel(surface)

        # Draw Buttons
        for btn in self.menu_buttons:
            btn.draw(surface)

    def draw_guide_panel(self, surface):
        # Draw a beautiful dark glass-like box listing gestures
        panel_w, panel_h = 320, 220
        panel_rect = pygame.Rect(30, SCREEN_HEIGHT // 2 - 70, panel_w, panel_h)
        
        # Shadow
        pygame.draw.rect(surface, Colors.SHADOW, panel_rect.move(3, 3), border_radius=8)
        # Background
        pygame.draw.rect(surface, Colors.BUTTON_NORMAL, panel_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.GOLD, panel_rect, width=1, border_radius=8)
        
        # Header
        draw_text_with_outline(
            surface, "MAGIC SPELL GUIDE", 
            self.font_subtitle, Colors.GOLD, Colors.SHADOW, 
            (panel_rect.x + 20, panel_rect.y + 15)
        )
        
        # Spell lines
        spells_info = [
            ("Fireball", "○ (Circle)", Colors.FIRE),
            ("Frost Chill", "— (Horizontal)", Colors.ICE),
            ("Lightning", "Z (Z-Shape)", Colors.LIGHTNING),
            ("Gale Blast", "Spiral (S)", Colors.WIND)
        ]
        
        for idx, (name, symbol, color) in enumerate(spells_info):
            y_offset = panel_rect.y + 55 + idx * 36
            # Bullet point indicator
            pygame.draw.circle(surface, color, (panel_rect.x + 30, y_offset + 10), 6)
            
            draw_text_with_outline(
                surface, f"{name}:", 
                self.font_hud, Colors.TEXT_MAIN, Colors.SHADOW, 
                (panel_rect.x + 46, y_offset)
            )
            draw_text_with_outline(
                surface, symbol, 
                self.font_hud, color, Colors.SHADOW, 
                (panel_rect.x + 160, y_offset)
            )

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
        title_w = self.font_title.size(title_str)[0]
        draw_text_with_outline(
            surface, title_str, self.font_subtitle, 
            Colors.GOLD, Colors.SHADOW, 
            (SCREEN_WIDTH // 2 - title_w // 4, panel_rect.y + 25)
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
        
        # Final Stats panel
        stats_w, stats_h = 240, 90
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

        # Draw Buttons
        for btn in self.gameover_buttons:
            btn.draw(surface)
