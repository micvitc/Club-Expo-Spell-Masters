# Spell Master 🧙‍♂️✨

Spell Master is a clean, modular 2D side-view fantasy game built in **Pygame**. It is designed with a decoupled architecture to allow easy integration with a Computer Vision (CV) gesture-recognition system. 

The game launches in **Fullscreen** by default and partitions the screen into a **Gameplay Viewport** (960x720) on the left and a **CV Control Console/Sidebar** (320x720) on the right.

---

## 📁 Project Structure

The project strictly follows the requested object-oriented, modular architecture:

```text
SpellMaster/
│
├── main.py                  # Game entry point
├── game.py                  # Core Game class & Main Game Loop (with Fullscreen toggles)
├── settings.py              # Directory paths & general window settings
│
├── entities/
│   ├── player.py            # Player Wizard class (hover anim, cast states)
│   ├── enemy.py             # Configurable Enemy class (Goblins, Skeletons, Orcs)
│   └── projectile.py        # Magic missile projectile (seeking logic)
│
├── spells/
│   ├── spell_manager.py     # Cooldown tracker & enemy target finder
│   ├── spell.py             # Base Spell class and individual spell classes (with effectiveness)
│   └── effects.py           # Custom visuals (Lightning strikes, explosions)
│
├── ui/
│   ├── hud.py               # HUD renderer (HP, Wave, Cooldowns, right-side Camera & Matrix)
│   ├── menus.py             # Main Menu, Pause Menu, Game Over screens
│   └── animations.py        # Screen shake, screen flash, global particle engine
│
├── managers/
│   ├── enemy_manager.py     # Updates enemies, collision checks & death triggers
│   ├── wave_manager.py      # Spawn wave manager, breather timers, difficulty scaling
│   └── asset_manager.py     # Safe file loader with colored placeholder fallbacks
│
└── utils/
    ├── constants.py         # Color schemes, stat values, spell properties
    └── helpers.py           # HP bar rendering, floating text, particles
```

---

## 🚀 How to Run the Game

1. Make sure you have Pygame installed in your Python environment:
   ```bash
   pip install pygame
   ```
2. Run the game from the root directory:
   ```bash
   python3 main.py
   ```

---

## 🕹️ Controls

* **Key `1`**: Cast **Fireball** (Deals 2 DMG to the nearest enemy)
* **Key `2`**: Cast **Frost Chill** (Deals 1 DMG and freezes the enemy in place for 4 seconds)
* **Key `3`**: Cast **Lightning Strike** (Instant hit, deals 3 DMG, shakes screen)
* **Key `4`**: Cast **Gale Blast** (Pushes the nearest enemy 200 pixels back)
* **Key `F` or `F11`**: Toggle **Fullscreen / Windowed** mode
* **Key `ESC`**: Pause / Resume the game

---

## ⚔️ Elemental Effectiveness Matrix

Casting specific spells against corresponding enemy types triggers **Super Effective** modifiers and displays indicators above targets:

* 🔥 **Fireball vs Goblins**: Deals **double damage** (4 DMG), immediately vaporizing Goblins.
* ❄️ **Frost Chill vs Orcs**: Deals **double damage** (2 DMG) and **doubles freeze duration** (8.0 seconds).
* ⚡ **Lightning Strike vs Skeletons**: Deals **double damage** (6 DMG), shattering skeletons.
* 🌀 **Gale Blast vs Goblins**: Deals **double pushback distance** (400 pixels).

---

## 📹 CV Console Sidebar (Right Side)

The right 320px of the screen acts as a dedicated CV Console containing:
1. **Gesture Feed Box**: A placeholder for the CV camera feed (displays active crosshairs, grid lines, a blinking red recording light `GESTURE FEED (LIVE)`, and a green horizontal scan line). The CV team can blit their camera feed directly into this region.
2. **Spell Effectiveness Matrix**: An on-screen guide cards detailing elemental interactions and damage/status multipliers.

---

## 🔮 Computer Vision Integration API

The game exposes a thread-safe API to trigger spell casting. The CV team only needs a reference to the running `game` object and can invoke:

```python
game.cast_spell("fire")
game.cast_spell("ice")
game.cast_spell("lightning")
game.cast_spell("wind")
```

### Thread-Safe Design
OpenCV and MediaPipe pipelines are usually run on a separate python thread. Since Pygame's render context is thread-unsafe, `game.cast_spell()` pushes requests to a thread-safe `queue.Queue`. The main rendering loop pulls and handles these spells safely during frame updates.
