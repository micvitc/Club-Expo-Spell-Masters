import pygame
import random
import math
from utils.constants import Colors, SPELLS, GAMEPLAY_WIDTH
from entities.projectile import Projectile

class Spell:
    def __init__(self, spell_id):
        self.id = spell_id
        config = SPELLS.get(spell_id)
        self.name = config["name"]
        self.damage = config["damage"]
        self.cooldown = config["cooldown"]
        self.description = config["description"]
        self.color = config["color"]
        
        self.cooldown_timer = 0.0

    def is_ready(self):
        return self.cooldown_timer <= 0.0

    def update(self, dt):
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def trigger_cooldown(self):
        self.cooldown_timer = self.cooldown

    def cast(self, player, target, projectiles, animation_effects):
        """
        To be implemented by subclasses. Returns True if successfully cast.
        """
        raise NotImplementedError("Each spell must implement its own cast logic.")


class FireSpell(Spell):
    def __init__(self):
        super().__init__("fire")

    def cast(self, player, target, projectiles, animation_effects):
        if not target:
            animation_effects.add_floating_text("No Target!", player.x, player.y - 40, Colors.TEXT_MUTED, player.asset_manager.get_font(None, 24), is_damage=False)
            return False

        # Super Effectiveness: Fire vs Goblin (Double DMG)
        damage = self.damage
        is_super = False
        if target.type_name == "goblin":
            damage = self.damage * 2
            is_super = True

        # Spawn Fireball Projectile
        proj = Projectile(
            x=player.x + 20, 
            y=player.y - 10, 
            target=target, 
            spell_type="fire", 
            damage=damage, 
            speed=9.0, 
            color=Colors.FIRE
        )
        projectiles.append(proj)
        
        # Super effective floating popup
        if is_super:
            target_hitbox = target.get_hitbox()
            animation_effects.add_floating_text(
                "🔥 SUPER EFFECTIVE!", 
                target_hitbox.centerx - 40, target_hitbox.y - 25, 
                Colors.GOLD, 
                player.asset_manager.get_font(None, 20),
                duration=1.2,
                is_damage=False
            )
        
        # Fire cast flash/particles
        animation_effects.add_particle_burst(
            player.x + 20, player.y - 10, 
            Colors.PARTICLE_FIRE, 
            count=10, 
            speed_range=(1.0, 3.0), 
            size_range=(3, 6)
        )
        
        # Trigger short screen flash (soft orange glow)
        animation_effects.trigger_flash(0.1, (255, 120, 60))
        
        # Play cast sound
        player.asset_manager.get_sound("fire.wav").play()
        self.trigger_cooldown()
        return True


class IceSpell(Spell):
    def __init__(self):
        super().__init__("ice")
        self.freeze_duration = SPELLS["ice"]["freeze_duration"]

    def cast(self, player, target, projectiles, animation_effects):
        if not target:
            animation_effects.add_floating_text("No Target!", player.x, player.y - 40, Colors.TEXT_MUTED, player.asset_manager.get_font(None, 24), is_damage=False)
            return False

        # Super Effectiveness: Ice vs Orc (Double DMG + Double Freeze duration)
        damage = self.damage
        freeze_dur = self.freeze_duration
        is_super = False
        if target.type_name == "orc":
            damage = self.damage * 2
            freeze_dur = self.freeze_duration * 2.0
            is_super = True

        # Spawn Ice Projectile
        proj = Projectile(
            x=player.x + 20, 
            y=player.y - 10, 
            target=target, 
            spell_type="ice", 
            damage=damage, 
            speed=11.0, 
            color=Colors.ICE,
            effect_duration=freeze_dur
        )
        projectiles.append(proj)
        
        # Super effective popup
        if is_super:
            target_hitbox = target.get_hitbox()
            animation_effects.add_floating_text(
                "❄️ CRITICAL FREEZE!", 
                target_hitbox.centerx - 40, target_hitbox.y - 25, 
                Colors.GOLD, 
                player.asset_manager.get_font(None, 20),
                duration=1.2,
                is_damage=False
            )
        
        # Ice particles from wizard
        animation_effects.add_particle_burst(
            player.x + 20, player.y - 10, 
            Colors.PARTICLE_ICE, 
            count=8, 
            speed_range=(0.8, 2.5), 
            size_range=(2, 5)
        )
        
        player.asset_manager.get_sound("ice.wav").play()
        self.trigger_cooldown()
        return True


class LightningSpell(Spell):
    def __init__(self):
        super().__init__("lightning")

    def cast(self, player, target, projectiles, animation_effects):
        if not target:
            animation_effects.add_floating_text("No Target!", player.x, player.y - 40, Colors.TEXT_MUTED, player.asset_manager.get_font(None, 24), is_damage=False)
            return False

        # Super Effectiveness: Lightning vs Skeleton (Double DMG)
        damage = self.damage
        is_super = False
        if target.type_name == "skeleton":
            damage = self.damage * 2
            is_super = True

        # Instant hit
        target.take_damage(damage)
        
        from spells.effects import LightningStrikeEffect
        
        # Start of lightning is from top sky, end is target center
        target_hitbox = target.get_hitbox()
        strike_effect = LightningStrikeEffect(
            start_pos=(target_hitbox.centerx - 80, 0),
            end_pos=(target_hitbox.centerx, target_hitbox.centery)
        )
        animation_effects.particles.append(strike_effect) # Rendered as a particle!
        
        # Burst particles at target
        animation_effects.add_particle_burst(
            target_hitbox.centerx, target_hitbox.centery, 
            Colors.PARTICLE_LIGHTNING, 
            count=15, 
            speed_range=(2.0, 6.0), 
            size_range=(3, 7)
        )
        
        # Heavy screen shake & bright white flash
        animation_effects.trigger_shake(0.3, 10.0)
        animation_effects.trigger_flash(0.15, (255, 255, 255))
        
        # Floating damage text
        animation_effects.add_floating_text(
            f"-{damage} HP", 
            target_hitbox.centerx, target_hitbox.y - 20, 
            Colors.LIGHTNING, 
            player.asset_manager.get_font(None, 28)
        )
        
        # Super effective popup
        if is_super:
            animation_effects.add_floating_text(
                "⚡ SUPER EFFECTIVE!", 
                target_hitbox.centerx - 40, target_hitbox.y - 45, 
                Colors.GOLD, 
                player.asset_manager.get_font(None, 20),
                duration=1.2,
                is_damage=False
            )
        
        player.asset_manager.get_sound("lightning.wav").play()
        self.trigger_cooldown()
        return True


class WindSpell(Spell):
    def __init__(self):
        super().__init__("wind")
        self.pushback = SPELLS["wind"]["pushback"]

    def cast(self, player, target, projectiles, animation_effects):
        if not target:
            animation_effects.add_floating_text("No Target!", player.x, player.y - 40, Colors.TEXT_MUTED, player.asset_manager.get_font(None, 24), is_damage=False)
            return False

        # Super Effectiveness: Wind vs Goblin (Double pushback distance)
        push = self.pushback
        is_super = False
        if target.type_name == "goblin":
            push = self.pushback * 2.0
            is_super = True

        # Push target backward (x increases, capped at spawning boundary near GAMEPLAY_WIDTH - 60)
        original_x = target.x
        target.x = min(float(GAMEPLAY_WIDTH - 60), target.x + push)
        
        # Wind gust effect particles flowing from wizard to target
        target_hitbox = target.get_hitbox()
        
        # Spawn gale blast particles along the horizontal line
        y_center = player.y - 10
        dist = target_hitbox.centerx - player.x
        
        # Create beautiful wind tunnels/particles moving fast
        for i in range(12):
            px = player.x + (i * (dist / 12.0)) + random.uniform(-15, 15)
            py = y_center + random.uniform(-20, 20)
            p = animation_effects.add_particle_burst(
                px, py, Colors.PARTICLE_WIND, 
                count=2, 
                speed_range=(3.0, 7.0), 
                size_range=(2, 5), 
                lifetime_range=(10, 20)
            )
            
        animation_effects.add_floating_text(
            "PUSHED BACK!", 
            target_hitbox.centerx, target_hitbox.y - 20, 
            Colors.WIND, 
            player.asset_manager.get_font(None, 22), 
            is_damage=False
        )
        
        # Super effective popup
        if is_super:
            animation_effects.add_floating_text(
                "🌀 BLOWN AWAY!", 
                target_hitbox.centerx - 40, target_hitbox.y - 45, 
                Colors.GOLD, 
                player.asset_manager.get_font(None, 20),
                duration=1.2,
                is_damage=False
            )
        
        # Soft green screen flash
        animation_effects.trigger_flash(0.08, (150, 240, 180))
        
        player.asset_manager.get_sound("wind.wav").play()
        self.trigger_cooldown()
        return True
