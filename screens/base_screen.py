"""Abstract base class for all game screens.

Each concrete screen is one node of the game engine state machine. The
ScreenManager drives the lifecycle hooks below every frame. Screens draw ONLY
onto the virtual 1280x720 canvas, never the real display, so the outer
pillarbox/letterbox scaler in game.draw keeps working unchanged.
"""


class BaseScreen:
    #: Mirrors a utils.constants.GameState value.
    name = "BASE"

    def __init__(self, manager):
        self.manager = manager
        self.game = manager.game
        self.asset_manager = manager.game.asset_manager
        self.active = False

    # -- Lifecycle -------------------------------------------------------
    def on_enter(self, **kwargs):
        self.active = True

    def on_exit(self):
        self.active = False

    def handle_event(self, event):
        return None

    def update(self, dt):
        return None

    def draw(self, canvas):
        return None

    # -- Helpers ---------------------------------------------------------
    def mouse_pos(self):
        """Mouse position mapped into virtual canvas space."""
        return self.game.get_canvas_mouse_pos()
