"""New spells added on the Susnata branch for the gesture-first control scheme.

These are self-contained and DO NOT modify spells/spell.py or utils/constants.py
(so main and shaurya are untouched). Each class carries its own config instead
of reading from SPELLS, and follows the exact cast(...) signature used by
SpellManager:

    cast(self, player, target, projectiles, animation_effects, enemies=None) -> bool

Spells added:
    * SelfHealSpell  (🩰 finger heart)  - restores wizard HP, no target needed
    * BlackHoleSpell (👌 OK sign)       - pulls all enemies inward + heavy damage
    * TelekinesisSpell (🤌 pinch)       - flings the nearest enemy across the arena

Register them by calling register_extra_spells(spell_manager) once after the
SpellManager is built (done in game.py on Susnata).
"""
import math
import random
import pygame
from utils.constants import Colors, GAMEPLAY_WIDTH, SCREEN_HEIGHT

# Distinct accent colors for the new spells (local, not added to constants.py).
HEAL_COLOR = (60, 230, 120)
BLACKHOLE_COLOR = (90, 40, 160)
TELEKINESIS_COLOR = (150, 120, 255)

HEAL_PARTICLES = [(60, 230, 120), (120, 255, 170), (255, 255, 255)]
BLACKHOLE_PARTICLES = [(120, 60, 200), (60, 20, 110), (200, 140, 255)]
TELEKINESIS_PARTICLES = [(170, 150, 255), (120, 90, 220), (230, 220, 255)]


class _BaseExtraSpell:
    """Minimal spell base mirroring spells.spell.Spell's public surface.

    Implements the cooldown contract SpellManager and the HUD rely on
    (is_ready, update, trigger_cooldown, cooldown, cooldown_timer, name, color).
    """

    id = "extra"
    name = "Extra"
    cooldown = 5.0
    color = Colors.WIZARD_COLOR

    def __init__(self):
        self.cooldown_timer = 0.0

    def is_ready(self):
        return self.cooldown_timer <= 0.0

    def update(self, dt):
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt / 60.0)

    def trigger_cooldown(self):
        self.cooldown_timer = self.cooldown

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        raise NotImplementedError


class SelfHealSpell(_BaseExtraSpell):
    """🩰 Finger heart -> restore the wizard's HP. Needs no enemy target."""

    id = "heal"
    name = "Self Heal"
    cooldown = 12.0
    color = HEAL_COLOR
    heal_amount = 25

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        before = player.hp
        player.hp = min(player.max_hp, player.hp + self.heal_amount)
        healed = player.hp - before

        animation_effects.add_particle_burst(
            player.x, player.y, HEAL_PARTICLES,
            count=22, speed_range=(0.6, 2.4), size_range=(2, 6),
            lifetime_range=(18, 38),
        )
        animation_effects.trigger_flash(0.1, (120, 255, 170))
        animation_effects.add_floating_text(
            f"+{healed} HP" if healed else "FULL HP",
            player.x - 30, player.y - 48, HEAL_COLOR,
            player.asset_manager.get_font(None, 26), duration=1.2, is_damage=False,
        )
        player.asset_manager.get_sound("heal.wav").play()
        self.trigger_cooldown()
        return True


class BlackHoleSpell(_BaseExtraSpell):
    """👌 OK sign -> collapse a void that pulls every enemy inward and damages them."""

    id = "blackhole"
    name = "Black Hole"
    cooldown = 11.0
    color = BLACKHOLE_COLOR
    damage = 3
    pull_strength = 140.0

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        # Collapse the void at the arena center for a strong visual anchor.
        cx, cy = GAMEPLAY_WIDTH // 2, SCREEN_HEIGHT // 2

        if enemies:
            for enemy in [e for e in enemies if hasattr(e, "hp") and e.hp > 0]:
                dx = cx - enemy.x
                dy = cy - enemy.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    ux, uy = dx / dist, dy / dist
                    enemy.x = max(30.0, min(float(GAMEPLAY_WIDTH - 30), enemy.x + ux * self.pull_strength))
                    enemy.y = max(30.0, min(float(SCREEN_HEIGHT - 30), enemy.y + uy * self.pull_strength))
                enemy.take_damage(self.damage)
                eh = enemy.get_hitbox()
                animation_effects.add_floating_text(
                    f"-{self.damage} HP", eh.centerx, eh.y - 15,
                    BLACKHOLE_COLOR, player.asset_manager.get_font(None, 22),
                )

        # Swirling collapse particles + shake.
        for _ in range(28):
            ang = random.uniform(0, 2 * math.pi)
            rad = random.uniform(60, 160)
            sx = cx + math.cos(ang) * rad
            sy = cy + math.sin(ang) * rad
            animation_effects.add_particle_burst(
                sx, sy, BLACKHOLE_PARTICLES,
                count=1, speed_range=(1.5, 3.5), size_range=(2, 5),
            )
        animation_effects.trigger_shake(0.4, 8.0)
        animation_effects.trigger_flash(0.12, (60, 20, 110))
        animation_effects.add_floating_text(
            "BLACK HOLE!", cx - 45, cy - 60, BLACKHOLE_COLOR,
            player.asset_manager.get_font(None, 26), duration=1.2, is_damage=False,
        )
        player.asset_manager.get_sound("shadow_cast.wav").play()
        self.trigger_cooldown()
        return True


class TelekinesisSpell(_BaseExtraSpell):
    """🤌 Pinch -> grab the nearest enemy and fling it to the far edge of the arena."""

    id = "telekinesis"
    name = "Telekinesis"
    cooldown = 6.0
    color = TELEKINESIS_COLOR
    damage = 2
    fling_distance = 260.0

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        if not target:
            animation_effects.add_floating_text(
                "No Target!", player.x, player.y - 40, Colors.TEXT_MUTED,
                player.asset_manager.get_font(None, 24), is_damage=False,
            )
            return False

        # Fling the target directly away from the wizard.
        dx = target.x - player.x
        dy = target.y - player.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            ux, uy = dx / dist, dy / dist
        else:
            ux, uy = 1.0, 0.0
        target.x = max(30.0, min(float(GAMEPLAY_WIDTH - 30), target.x + ux * self.fling_distance))
        target.y = max(30.0, min(float(SCREEN_HEIGHT - 30), target.y + uy * self.fling_distance))
        target.take_damage(self.damage)
        if hasattr(target, "slow_timer"):
            target.slow_timer = 1.0

        eh = target.get_hitbox()
        animation_effects.add_particle_burst(
            eh.centerx, eh.centery, TELEKINESIS_PARTICLES,
            count=16, speed_range=(1.5, 4.5), size_range=(2, 5),
        )
        animation_effects.add_floating_text(
            "FLUNG!", eh.centerx, eh.y - 18, TELEKINESIS_COLOR,
            player.asset_manager.get_font(None, 22), duration=0.7, is_damage=False,
        )
        animation_effects.add_floating_text(
            f"-{self.damage} HP", eh.centerx, eh.y - 40, TELEKINESIS_COLOR,
            player.asset_manager.get_font(None, 22),
        )
        player.asset_manager.get_sound("wind.wav").play()
        self.trigger_cooldown()
        return True


def register_extra_spells(spell_manager):
    """Add the new spells to an existing SpellManager instance.

    Safe to call once after the SpellManager is constructed. Uses each spell's
    own id as the key so SpellManager.cast("heal"/"blackhole"/"telekinesis")
    works, alongside the original 8 spells.
    """
    for spell in (SelfHealSpell(), BlackHoleSpell(), TelekinesisSpell()):
        spell_manager.spells[spell.id] = spell
    return spell_manager
