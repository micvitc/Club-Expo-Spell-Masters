import pygame

# Game States
class GameState:
    MAIN_MENU = "MAIN_MENU"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"

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

# Screen dimensions and UI layouts
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GAMEPLAY_WIDTH = 960
SIDEBAR_WIDTH = 320
FPS = 60

# Wizard positioning and stats
WIZARD_X = 120
WIZARD_Y = SCREEN_HEIGHT // 2 + 50
WIZARD_RADIUS = 30
WIZARD_MAX_HP = 100

# Enemy Configurations
ENEMY_TYPES = {
    "goblin": {
        "name": "Goblin",
        "hp": 1,
        "speed": 2.2,
        "damage": 10,
        "color": (90, 180, 80),     # Forest green
        "size": (30, 35),
        "score_val": 10
    },
    "skeleton": {
        "name": "Skeleton",
        "hp": 2,
        "speed": 1.4,
        "damage": 15,
        "color": (210, 210, 200),   # Bony white
        "size": (32, 45),
        "score_val": 20
    },
    "orc": {
        "name": "Orc",
        "hp": 4,
        "speed": 0.8,
        "damage": 25,
        "color": (150, 75, 40),     # Muddy brown-red
        "size": (45, 55),
        "score_val": 40
    }
}

# Spell Configurations
SPELLS = {
    "fire": {
        "name": "Fireball",
        "damage": 2,
        "cooldown": 0.8, # in seconds
        "description": "Ignite & damage the nearest enemy",
        "color": Colors.FIRE
    },
    "ice": {
        "name": "Frost Chill",
        "damage": 1,
        "cooldown": 1.5,
        "freeze_duration": 4.0, # in seconds
        "freeze_slow_factor": 0.0, # Complete stop for freeze_duration
        "description": "Freeze and halt the closest enemy",
        "color": Colors.ICE
    },
    "lightning": {
        "name": "Lightning strike",
        "damage": 3,
        "cooldown": 2.0,
        "description": "Powerful, instant strike on the closest enemy",
        "color": Colors.LIGHTNING
    },
    "wind": {
        "name": "Gale Blast",
        "damage": 0,
        "cooldown": 1.2,
        "pushback": 200, # pixels pushback
        "description": "Blow back the closest enemy",
        "color": Colors.WIND
    }
}
