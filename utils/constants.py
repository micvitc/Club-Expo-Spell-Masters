import pygame

# Game States
class GameState:
    MAIN_MENU = "MAIN_MENU"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    DEMO_MODE = "DEMO_MODE"

# Color Palette (Premium Dark Fantasy Theme)
class Colors:
    BACKGROUND = (18, 16, 26)       # Deep dark violet/gray
    WIZARD_COLOR = (120, 80, 220)   # Vibrant purple
    TEXT_MAIN = (240, 240, 245)     # Soft off-white
    TEXT_MUTED = (140, 135, 160)    # Muted lavender-gray
    GOLD = (235, 180, 50)           # Gold/accent color
    
    # Spell Colors
    FIRE = (240, 80, 40)            # Fiery orange-red
    ICE = (80, 180, 240)            # Frozen cyan
    LIGHTNING = (250, 220, 50)      # Electric yellow
    WIND = (80, 200, 140)           # Airy mint-green
    SHIELD = (235, 180, 50)         # Bright golden yellow
    EARTHQUAKE = (180, 110, 60)     # Terra-cotta brown/orange
    SHADOW_SPELL = (160, 50, 240)   # Dark shadow purple
    SOLARBEAM = (255, 235, 170)     # Solar yellow-white
    
    # UI/Status Colors
    HP_BAR_EMPTY = (50, 30, 40)     # Dark reddish-brown
    HP_BAR_FILL = (220, 50, 80)     # Vibrant red-pink
    BUTTON_HOVER = (60, 50, 85)     # Indigo hover state
    BUTTON_NORMAL = (35, 30, 50)    # Indigo normal state
    SHADOW = (10, 8, 15)            # Near black
    
    # Particle Colors
    PARTICLE_FIRE = [(255, 100, 30), (255, 160, 50), (200, 50, 10)]
    PARTICLE_ICE = [(100, 200, 255), (180, 230, 255), (50, 120, 200)]
    PARTICLE_LIGHTNING = [(255, 255, 200), (250, 220, 50), (255, 180, 30)]
    PARTICLE_WIND = [(150, 220, 180), (120, 200, 160), (190, 240, 210)]
    PARTICLE_SHIELD = [(255, 220, 100), (235, 180, 50), (255, 245, 180)]
    PARTICLE_EARTHQUAKE = [(140, 80, 40), (180, 110, 60), (100, 60, 30)]
    PARTICLE_SHADOW = [(140, 40, 220), (90, 20, 150), (200, 100, 255)]
    PARTICLE_SOLARBEAM = [(255, 255, 200), (255, 230, 120), (255, 255, 255)]

# Screen dimensions and UI layouts
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GAMEPLAY_WIDTH = 920
SIDEBAR_WIDTH = 360
FPS = 60

# Wizard positioning and stats
GAMEPLAY_CENTER_X = GAMEPLAY_WIDTH // 2
GAMEPLAY_CENTER_Y = SCREEN_HEIGHT // 2
WIZARD_X = GAMEPLAY_CENTER_X
WIZARD_Y = GAMEPLAY_CENTER_Y
WIZARD_RADIUS = 30
WIZARD_MAX_HP = 100

# Enemy Configurations
ENEMY_TYPES = {
    "goblin": {
        "name": "Goblin",
        "hp": 1,
        "speed": 2.2,
        "damage": 5,          # Reduced from 10
        "color": (90, 180, 80),
        "size": (30, 35),
        "score_val": 10
    },
    "skeleton": {
        "name": "Skeleton",
        "hp": 2,
        "speed": 1.4,
        "damage": 8,          # Reduced from 15
        "color": (210, 210, 200),
        "size": (32, 45),
        "score_val": 20
    },
    "orc": {
        "name": "Orc",
        "hp": 4,
        "speed": 0.8,
        "damage": 12,         # Reduced from 25
        "color": (150, 75, 40),
        "size": (45, 55),
        "score_val": 40
    }
}

# Spell Configurations
SPELLS = {
    "fire": {
        "name": "Fireball",
        "damage": 2,
        "cooldown": 0.8, # 0.8s: Fast enough to be your main attack, slow enough to require aiming
        "description": "Ignite & burn closest (0.2s)",
        "color": Colors.FIRE,
        "symbol": "Top-Right Hand",
        "key": "1"
    },
    "ice": {
        "name": "Frost Chill",
        "damage": 1,
        "cooldown": 1.5, # 1.5s: Prevents you from instantly freezing the entire screen at once
        "freeze_duration": 3.0, # 3.0s freeze
        "freeze_slow_factor": 0.0,
        "description": "Freeze closest enemy (3s)",
        "color": Colors.ICE,
        "symbol": "Top-Left Hand",
        "key": "2"
    },
    "lightning": {
        "name": "Lightning",
        "damage": 3,
        "cooldown": 2.5, # 2.5s: A heavy combo strike needs a bit of a breather
        "description": "Chain lightning combo strike",
        "color": Colors.LIGHTNING,
        "symbol": "High-Center Hand",
        "key": "3"
    },
    "wind": {
        "name": "Gale Blast",
        "damage": 0,
        "cooldown": 3.0, # 3.0s: Stops players from just pinning enemies against the wall forever
        "pushback": 180,
        "description": "Blast all screen enemies back",
        "color": Colors.WIND,
        "symbol": "Low-Center Hand",
        "key": "4"
    },
    "shield": {
        "name": "Aegis Shield",
        "damage": 0,
        "cooldown": 12.0, # 12.0s: With a 10s duration, this gives a 2-second vulnerability window!
        "duration": 10.0,
        "description": "Absorb damage barrier (30 HP)",
        "color": Colors.SHIELD,
        "symbol": "Both Hands Up",
        "key": "5"
    },
    "earthquake": {
        "name": "Earthquake",
        "damage": 10,
        "cooldown": 8.0, # 8.0s: 10 damage is basically a screen-wipe, so this becomes an "Ultimate" ability
        "description": "DMG & slow all screen (2s)",
        "color": Colors.EARTHQUAKE,
        "symbol": "Low-Left Hand",
        "key": "6"
    }
}
