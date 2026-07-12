import pygame
import math
from spells.spell import FireSpell, IceSpell, LightningSpell, WindSpell, ShieldSpell, EarthquakeSpell, ShadowSpell, SolarBeamSpell
from utils.constants import Colors

class SpellManager:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        # Load all 8 spell modules
        self.spells = {
            "fire": FireSpell(),
            "ice": IceSpell(),
            "lightning": LightningSpell(),
            "wind": WindSpell(),
            "shield": ShieldSpell(),
            "earthquake": EarthquakeSpell(),
            "shadow": ShadowSpell(),
            "solarbeam": SolarBeamSpell()
        }

    def update(self, dt):
        """Updates spell cooldowns."""
        for spell in self.spells.values():
            spell.update(dt)

    def cast(self, spell_name, player, enemies, projectiles, animation_effects):
        """
        Attempts to cast a spell. Targets the enemy closest to the player (in 2D space).
        Returns True if casting was successful, False otherwise.
        """
        spell_name = spell_name.lower().strip()
        
        if spell_name not in self.spells:
            print(f"Warning: Unknown spell '{spell_name}' requested.")
            return False
            
        spell = self.spells[spell_name]
        
        # Check cooldown
        if not spell.is_ready():
            # Trigger floating cooldown notification above player
            animation_effects.add_floating_text(
                "Cooldown!", 
                player.x - 20, player.y - 45, 
                Colors.TEXT_MUTED, 
                self.asset_manager.get_font(None, 20),
                duration=0.6,
                is_damage=False
            )
            return False

        # Find target: nearest living enemy (closest 2D Euclidean distance to player)
        target = None
        closest_dist = float('inf')
        
        # Filter alive enemies
        alive_enemies = [e for e in enemies if hasattr(e, 'hp') and e.hp > 0]
        
        for enemy in alive_enemies:
            # We want the enemy closest in 2D Euclidean distance
            dist = math.hypot(enemy.x - player.x, enemy.y - player.y)
            if dist < closest_dist:
                closest_dist = dist
                target = enemy
                
        # Spells like shield and earthquake do not require a target to be present
        needs_target = spell_name not in ["shield", "earthquake"]
        if needs_target and not target:
            animation_effects.add_floating_text(
                "No Target!", 
                player.x, player.y - 40, 
                Colors.TEXT_MUTED, 
                self.asset_manager.get_font(None, 24), 
                is_damage=False
            )
            return False

        # Attempt to cast the spell
        success = spell.cast(player, target, projectiles, animation_effects, enemies)
        
        if success:
            # Trigger player casting animation state, aiming towards target if present
            target_pos = (target.x, target.y) if target else None
            player.start_cast(spell_name, target_pos)
            
        return success
        
    def get_cooldown_ratio(self, spell_name):
        """Returns the ratio (0.0 to 1.0) of cooldown remaining. 0.0 means ready."""
        spell = self.spells.get(spell_name.lower())
        if spell and spell.cooldown > 0:
            return spell.cooldown_timer / spell.cooldown
        return 0.0

