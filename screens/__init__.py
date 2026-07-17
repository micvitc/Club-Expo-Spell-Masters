"""Screen package: a clean, stack-based state machine plus one layout module per
game state for the CV Spell Master game.

These modules are additive. They wrap the existing managers (AssetManager,
MenuManager, HUD, AnimationEffects) and never modify the legacy inline state
handling in game.py, so main and shaurya branches are unaffected.
"""

from screens.screen_manager import ScreenManager
from screens.base_screen import BaseScreen

__all__ = ["ScreenManager", "BaseScreen"]
