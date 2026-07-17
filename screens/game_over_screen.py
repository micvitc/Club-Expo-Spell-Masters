"""Game over (Defeat) screen.

Dark-red overlay with the final score and waves cleared, plus TRY AGAIN /
MAIN MENU buttons reused from MenuManager. Renders its own fonts so it does not
depend on the legacy MenuManager font set.
"""
import pygame
from screens.base_screen import BaseScreen
from utils.constants import GameState, Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.helpers import draw_text_with_outline


class GameOverScreen(BaseScreen):
    name = GameState.GAME_OVER

    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = self.asset_manager.get_font(None, 64)
        self.font_sub = self.asset_manager.get_font(None, 24)

    def handle_event(self, event):
        self.game.menu_manager.handle_event(self.name, event)

    def update(self, dt):
        self.game.menu_manager.update(self.name, self.mouse_pos())

    def draw(self, canvas):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((25, 10, 15, 210))
        canvas.blit(overlay, (0, 0))

        title = "DEFEAT"
        tw = self.font_title.size(title)[0]
        draw_text_with_outline(
            canvas, title, self.font_title, Colors.HP_BAR_FILL, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - tw // 2, SCREEN_HEIGHT // 4 - 30), outline_width=3,
        )
        sub = "Your magic has run out..."
        sw = self.font_sub.size(sub)[0]
        draw_text_with_outline(
            canvas, sub, self.font_sub, Colors.TEXT_MUTED, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - sw // 2, SCREEN_HEIGHT // 4 + 40),
        )

        stats_w, stats_h = 320, 100
        stats = pygame.Rect(
            (SCREEN_WIDTH - stats_w) // 2, SCREEN_HEIGHT // 2 - 50, stats_w, stats_h,
        )
        pygame.draw.rect(canvas, Colors.BUTTON_NORMAL, stats, border_radius=6)
        pygame.draw.rect(canvas, Colors.HP_BAR_FILL, stats, width=1, border_radius=6)

        score_str = f"Final Score: {self.game.player.score}"
        score_w = self.font_sub.size(score_str)[0]
        draw_text_with_outline(
            canvas, score_str, self.font_sub, Colors.GOLD, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - score_w // 2, stats.y + 15),
        )
        wave_str = f"Waves Cleared: {max(0, self.game.wave_manager.current_wave - 1)}"
        wave_w = self.font_sub.size(wave_str)[0]
        draw_text_with_outline(
            canvas, wave_str, self.font_sub, Colors.TEXT_MAIN, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - wave_w // 2, stats.y + 48),
        )
        for btn in self.game.menu_manager.gameover_buttons:
            btn.draw(canvas)
