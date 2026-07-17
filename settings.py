import os
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

# Window configuration
WINDOW_WIDTH = SCREEN_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
WINDOW_TITLE = "Spell Master - CV Magic Duel"
TARGET_FPS = FPS

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

# Ensure asset directories exist
for folder in [ASSETS_DIR, SPRITES_DIR, BACKGROUNDS_DIR, FONTS_DIR, SOUNDS_DIR]:
    os.makedirs(folder, exist_ok=True)

# Debug flags
SHOW_HITBOXES = False
DEV_KEYS_ENABLED = True
