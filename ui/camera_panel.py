"""Reusable live gesture-feed widget for a CV-controlled game.

Renders the webcam surface produced by game._run_cv_pipeline (game.cv_frame,
already scaled to 300x225) inside a framed viewport with a HUD overlay:
crosshair, blinking REC dot, and a live readout of the last recognized pose and
its accuracy. When no frame or no recent gesture is available it shows clear
"connecting" / "waiting for gesture" states, which is essential feedback for a
gesture game.

Draws onto the 1280x720 virtual canvas so it composites with everything else.
"""
import time
import pygame
from utils.constants import Colors
from utils.helpers import draw_text_with_outline

FEED_W = 300
FEED_H = 225
HUD_GREEN = (0, 230, 150)
LIVE_GREEN = (0, 255, 100)
REC_RED = (255, 50, 50)


class CameraPanel:
    def __init__(self, asset_manager, x, y, width=FEED_W, height=FEED_H):
        self.asset_manager = asset_manager
        self.rect = pygame.Rect(x, y, width, height)
        self.font_title = asset_manager.get_font(None, 16)
        self.font_body = asset_manager.get_font(None, 14)

    def draw(self, surface, game):
        r = self.rect

        # Drop shadow + feed / placeholder.
        pygame.draw.rect(surface, Colors.SHADOW, r.move(2, 2), border_radius=6)
        frame = getattr(game, "cv_frame", None)
        if frame is not None:
            surface.blit(frame, (r.x, r.y))
        else:
            pygame.draw.rect(surface, (22, 19, 34), r, border_radius=6)
            msg = "CONNECTING CAMERA..."
            w = self.font_body.size(msg)[0]
            draw_text_with_outline(
                surface, msg, self.font_body, Colors.TEXT_MUTED, Colors.SHADOW,
                (r.centerx - w // 2, r.centery - 6),
            )

        # Neon border + inner tracking frame.
        pygame.draw.rect(surface, HUD_GREEN, r, width=2, border_radius=6)
        pygame.draw.rect(surface, HUD_GREEN, r.inflate(-20, -20), width=1)

        # Center crosshair.
        cx, cy = r.centerx, r.centery
        pygame.draw.line(surface, HUD_GREEN, (cx - 15, cy), (cx + 15, cy), 1)
        pygame.draw.line(surface, HUD_GREEN, (cx, cy - 15), (cx, cy + 15), 1)

        # Blinking REC dot + title.
        rec_on = (pygame.time.get_ticks() // 500) % 2 == 0
        pygame.draw.circle(surface, REC_RED if rec_on else (80, 20, 20), (r.x + 18, r.y + 18), 6)
        draw_text_with_outline(
            surface, "GESTURE FEED (LIVE)", self.font_title, Colors.TEXT_MAIN, Colors.SHADOW,
            (r.x + 30, r.y + 11),
        )

        # Live pose + accuracy readout.
        recent = (
            hasattr(game, "last_gesture")
            and game.last_gesture not in (None, "None")
            and (time.time() - getattr(game, "last_gesture_time", 0.0) < 1.5)
        )
        if recent:
            msg = f"{str(game.last_gesture).upper()}  ({game.last_gesture_accuracy}%)"
            color = LIVE_GREEN
        else:
            msg = "[ WAITING FOR GESTURE ]"
            color = HUD_GREEN
        w = self.font_body.size(msg)[0]
        draw_text_with_outline(
            surface, msg, self.font_body, color, Colors.SHADOW,
            (cx - w // 2, r.bottom - 26),
        )
