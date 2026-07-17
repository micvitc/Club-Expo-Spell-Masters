"""Main menu screen for the CV Spell Master game.

CV-first title screen: pulsing title, a live camera panel so players can frame
their hand before starting, and a 'Spell Grimoire' that lists the REAL trained
poses (from ui.gesture_map) instead of the misleading positional hints in the
legacy menu. Buttons START / PRACTICE / QUIT are reused from MenuManager.

This screen renders its own fonts, so it does not depend on MenuManager's
undefined font_medium (which crashes the legacy demo overlay).
"""
import math
import pygame
from screens.base_screen import BaseScreen
from utils.constants import GameState, Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.helpers import draw_text_with_outline
from ui.gesture_map import spell_bindings, binding_for
from ui.camera_panel import CameraPanel


class MainMenuScreen(BaseScreen):
    name = GameState.MAIN_MENU

    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = self.asset_manager.get_font(None, 64)
        self.font_sub = self.asset_manager.get_font(None, 24)
        self.font_row = self.asset_manager.get_font(None, 16)
        self.camera = CameraPanel(self.asset_manager, x=SCREEN_WIDTH - 320, y=110)

    def on_enter(self, **kwargs):
        super().on_enter(**kwargs)
        self.game.reset_game()

    def handle_event(self, event):
        self.game.menu_manager.handle_event(self.name, event)

    def update(self, dt):
        self.game.menu_manager.update(self.name, self.mouse_pos())

    def draw(self, canvas):
        self._draw_backdrop(canvas)
        self._draw_title(canvas)
        self._draw_grimoire(canvas)
        self.camera.draw(canvas, self.game)
        for btn in self.game.menu_manager.menu_buttons:
            btn.draw(canvas)

    # -- Sections --------------------------------------------------------
    def _draw_backdrop(self, canvas):
        canvas.fill(Colors.BACKGROUND)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(canvas, (28, 24, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(canvas, (28, 24, 40), (0, y), (SCREEN_WIDTH, y))
        # Reuse the menu manager's drifting magic particles for atmosphere.
        for p in self.game.menu_manager.bg_particles:
            alpha = max(10, min(120, int(40 + 35 * math.sin(p["alpha_phase"]))))
            sz = int(p["size"])
            if sz > 0:
                surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                c = p["color"]
                pygame.draw.circle(surf, (c[0], c[1], c[2], alpha), (sz, sz), sz)
                canvas.blit(surf, (int(p["x"] - sz), int(p["y"] - sz)))

    def _draw_title(self, canvas):
        ticks = pygame.time.get_ticks()
        title = "SPELL MASTER"
        tw = self.font_title.size(title)[0]
        tx = SCREEN_WIDTH // 2 - tw // 2
        draw_text_with_outline(
            canvas, title, self.font_title,
            (255, int(185 + 40 * math.sin(ticks * 0.003)), 50), Colors.SHADOW,
            (tx, 40), outline_width=3,
        )
        sub = "Cast Real Hand-Gesture Magic"
        sw = self.font_sub.size(sub)[0]
        draw_text_with_outline(
            canvas, sub, self.font_sub, Colors.TEXT_MUTED, Colors.SHADOW,
            (SCREEN_WIDTH // 2 - sw // 2, 105),
        )

    def _draw_grimoire(self, canvas):
        panel = pygame.Rect(60, 160, 470, 470)
        pygame.draw.rect(canvas, Colors.SHADOW, panel.move(3, 3), border_radius=8)
        pygame.draw.rect(canvas, Colors.BUTTON_NORMAL, panel, border_radius=8)
        pygame.draw.rect(canvas, Colors.GOLD, panel, width=1, border_radius=8)

        draw_text_with_outline(
            canvas, "SPELL GRIMOIRE (HAND GESTURES)", self.font_sub, Colors.GOLD, Colors.SHADOW,
            (panel.x + 20, panel.y + 14),
        )

        for idx, b in enumerate(spell_bindings()):
            spell = self.game.spell_manager.spells.get(b["spell_id"])
            name = getattr(spell, "name", b["spell_id"].title())
            color = getattr(spell, "color", Colors.TEXT_MAIN)
            y = panel.y + 55 + idx * 44

            pygame.draw.circle(canvas, color, (panel.x + 26, y + 10), 6)
            # Emoji glyph + gesture name + spell name.
            draw_text_with_outline(
                canvas, f"{b['emoji']}  {name}", self.font_row,
                Colors.TEXT_MAIN, Colors.SHADOW, (panel.x + 42, y),
            )
            if b.get("needs_pose"):
                sub = f"{b['gesture']}  -  record pose '{b['record_as']}' to enable"
                sub_color = (230, 140, 90)
            else:
                sub = f"{b['gesture']}  (ready)"
                sub_color = color
            draw_text_with_outline(
                canvas, sub, self.font_row, sub_color, Colors.SHADOW,
                (panel.x + 42, y + 18),
            )

        start = binding_for("start")
        draw_text_with_outline(
            canvas, f"START / RESUME: {start['emoji']} {start['gesture']}", self.font_row,
            Colors.GOLD, Colors.SHADOW, (panel.x + 20, panel.bottom - 30),
        )
