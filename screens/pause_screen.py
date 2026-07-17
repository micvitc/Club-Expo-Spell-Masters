"""Pause overlay screen.

Pushed on top of the gameplay screen so the frozen arena stays visible beneath a
dimmed panel with RESUME / RESTART / MAIN MENU. ESC (or the START gesture) also
resumes the game.
"""
import pygame
from screens.base_screen import BaseScreen
from utils.constants import GameState, Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.helpers import draw_text_with_outline


class PauseScreen(BaseScreen):
    name = GameState.PAUSED

    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = self.asset_manager.get_font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.resume_game()
            return
        self.game.menu_manager.handle_event(self.name, event)

    def update(self, dt):
        self.game.menu_manager.update(self.name, self.mouse_pos())

    def draw(self, canvas):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 15, 180))
        canvas.blit(overlay, (0, 0))

        panel_w, panel_h = 320, 320
        panel = pygame.Rect(
            (SCREEN_WIDTH - panel_w) // 2, (SCREEN_HEIGHT - panel_h) // 2 - 20,
            panel_w, panel_h,
        )
        pygame.draw.rect(canvas, Colors.BUTTON_NORMAL, panel, border_radius=8)
        pygame.draw.rect(canvas, Colors.GOLD, panel, width=2, border_radius=8)

        title = "GAME PAUSED"
        tw = self.font_title.size(title)[0]
        draw_text_with_outline(
            canvas, title, self.font_title, Colors.GOLD, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - tw // 2, panel.y + 25),
        )
        for btn in self.game.menu_manager.pause_buttons:
            btn.draw(canvas)
