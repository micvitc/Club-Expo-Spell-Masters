import pygame
from spells.spell import FireSpell, IceSpell, LightningSpell, WindSpell
from utils.constants import Colors

class SpellManager:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        # Load all spell modules
        self.spells = {
            "fire": FireSpell(),
            "ice": IceSpell(),
            "lightning": LightningSpell(),
            "wind": WindSpell()
        }

    def update(self, dt):
        """Updates spell cooldowns."""
        for spell in self.spells.values():
            spell.update(dt)

    def cast(self, spell_name, player, enemies, projectiles, animation_effects):
        """
        Attempts to cast a spell. Targets the enemy closest to the player (leftmost).
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

        # Find target: nearest living enemy (leftmost, closest to player.x)
        # Enemies walk from right to left, so the smallest x value that is greater than player's coordinate is closest
        target = None
        closest_dist = float('inf')
        
        # Filter alive enemies
        alive_enemies = [e for e in enemies if hasattr(e, 'hp') and e.hp > 0]
        
        for enemy in alive_enemies:
            # We want the enemy closest to the player on the x-axis
            dist = enemy.x - player.x
            # The enemy must be in front of the player (dist > 0)
            if 0 < dist < closest_dist:
                closest_dist = dist
                target = enemy
                
        # Attempt to cast the spell
        success = spell.cast(player, target, projectiles, animation_effects)
        
        if success:
            # Trigger player casting animation state
            player.start_cast(spell_name)
            
        return success
        
    def get_cooldown_ratio(self, spell_name):
        """Returns the ratio (0.0 to 1.0) of cooldown remaining. 0.0 means ready."""
        spell = self.spells.get(spell_name.lower())
        if spell and spell.cooldown > 0:
            return spell.cooldown_timer / spell.cooldown
        return 0.0
