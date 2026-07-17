"""Keyboard testing / fallback system for the CV Spell Master game.

Centralizes every physical-key -> spell/control mapping so the game can be fully
exercised without the MediaPipe gesture pipeline. Casts are pushed onto the same
thread-safe game.spell_queue the CV thread uses, so keyboard and gesture input
take identical code paths. Gated by DEV_KEYS_ENABLED in settings.py.

Bindings are derived from ui.gesture_map.GESTURE_BINDINGS, so the keyboard and
the on-screen grimoire can never drift apart:
    1..8  -> fire, ice, lightning, wind, shield, earthquake, shadow, solarbeam
    SPACE / RETURN / S -> 'start' (start / resume / restart)
"""
import pygame
from settings import DEV_KEYS_ENABLED
from ui.gesture_map import GESTURE_BINDINGS


class KeyboardTester:
    START_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_s)

    def __init__(self, game):
        self.game = game
        self.enabled = DEV_KEYS_ENABLED
        # Build {pygame.K_1: "fire", ...} from the canonical gesture bindings.
        self.key_to_spell = {}
        for b in GESTURE_BINDINGS:
            key_char = str(b.get("key", "")).strip()
            if key_char.isdigit():
                pygame_key = getattr(pygame, f"K_{key_char}", None)
                if pygame_key is not None:
                    self.key_to_spell[pygame_key] = b["spell_id"]

    def handle_keydown(self, key):
        """Queue a spell/control for a KEYDOWN key. Returns the id queued, or None."""
        if not self.enabled:
            return None
        if key in self.START_KEYS:
            self.game.cast_spell("start")
            return "start"
        spell_id = self.key_to_spell.get(key)
        if spell_id is not None:
            self.game.cast_spell(spell_id)
            return spell_id
        return None

    def describe_bindings(self):
        """Ordered [(key, spell_id), ...] for on-screen help panels."""
        return [(b["key"], b["spell_id"]) for b in GESTURE_BINDINGS]
