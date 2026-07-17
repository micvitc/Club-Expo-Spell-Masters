"""Gameplay + Practice screen layouts.

Composites the 960px arena (background, enemies, wizard, projectiles,
particles) with screen shake, then draws the steady overlays: floating combat
text, the HUD (health / wave / spell hotbar / live camera feed), and full-screen
flashes. Number keys and SPACE are routed through game.keyboard_tester so the
game is fully playable without the camera.

DemoScreen subclasses this for the PRACTICE arena and adds the BACK TO MENU
overlay button.
"""
import pygame
from screens.base_screen import BaseScreen
from utils.constants import GameState, Colors, SCREEN_HEIGHT, GAMEPLAY_WIDTH


class GameplayScreen(BaseScreen):
    name = GameState.PLAYING

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.pause_game()
        elif event.key in (pygame.K_f, pygame.K_F11):
            self.game.toggle_fullscreen()
        else:
            self.game.keyboard_tester.handle_keydown(event.key)

    def draw(self, canvas):
        shake = self.game.animation_effects.shake_offset

        arena = pygame.Surface((GAMEPLAY_WIDTH, SCREEN_HEIGHT))
        arena.blit(self.game.background, (0, 0))
        self.game.enemy_manager.draw(arena)
        self.game.player.draw(arena, self.game.animation_effects)
        for proj in self.game.projectiles:
            proj.draw(arena, self.game.animation_effects)
        self.game.animation_effects.draw_particles(arena)

        canvas.fill(Colors.BACKGROUND)
        canvas.blit(arena, (shake[0], shake[1]))

        # Steady (non-shaking) overlays.
        self.game.animation_effects.draw_floating_texts(canvas)
        self.game.hud.draw(
            canvas, self.game.player, self.game.wave_manager,
            self.game.spell_manager, self.game,
        )
        self.game.animation_effects.draw_flash(canvas)


class DemoScreen(GameplayScreen):
    """Practice arena: same layout plus the BACK TO MENU button."""

    name = GameState.DEMO_MODE

    def handle_event(self, event):
        self.game.menu_manager.handle_event(self.name, event)
        if event.type == pygame.KEYDOWN and event.key not in (pygame.K_ESCAPE,):
            self.game.keyboard_tester.handle_keydown(event.key)

    def update(self, dt):
        self.game.menu_manager.update(self.name, self.mouse_pos())

    def draw(self, canvas):
        super().draw(canvas)
        for btn in self.game.menu_manager.demo_buttons:
            btn.draw(canvas)
