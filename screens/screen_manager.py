"""Stack-based screen state machine controller.

Full screens (menu, gameplay) replace the stack via switch_to. Overlays (pause,
game over) are pushed on top so the frozen gameplay frame stays visible beneath
them. game.py may delegate to this manager, but the legacy inline state handling
on other branches is left untouched.
"""


class ScreenManager:
    def __init__(self, game):
        self.game = game
        self._registry = {}
        self._stack = []

    # -- Registration ----------------------------------------------------
    def register(self, screen):
        self._registry[screen.name] = screen
        return screen

    def get(self, name):
        return self._registry.get(name)

    # -- Stack -----------------------------------------------------------
    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def switch_to(self, name, **kwargs):
        """Replace the whole stack with a single fresh screen."""
        while self._stack:
            self._stack.pop().on_exit()
        screen = self._registry[name]
        self._stack.append(screen)
        screen.on_enter(**kwargs)
        self.game.state = name
        return screen

    def push(self, name, **kwargs):
        """Push an overlay screen, keeping the one beneath it alive."""
        screen = self._registry[name]
        self._stack.append(screen)
        screen.on_enter(**kwargs)
        self.game.state = name
        return screen

    def pop(self):
        if not self._stack:
            return None
        top = self._stack.pop()
        top.on_exit()
        if self._stack:
            self.game.state = self._stack[-1].name
        return top

    # -- Per-frame delegation -------------------------------------------
    def handle_event(self, event):
        if self.current:
            return self.current.handle_event(event)
        return None

    def update(self, dt):
        if self.current:
            return self.current.update(dt)
        return None

    def draw(self, canvas):
        # Bottom-to-top so overlays composite over the frame beneath them.
        for screen in self._stack:
            screen.draw(canvas)
