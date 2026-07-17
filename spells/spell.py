import pygame
import random
import math
from utils.constants import Colors, SPELLS, GAMEPLAY_WIDTH, SCREEN_HEIGHT
from entities.projectile import Projectile
from utils.helpers import Particle

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
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt / 60.0)

    def trigger_cooldown(self):
        self.cooldown_timer = self.cooldown

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        """
        To be implemented by subclasses. Returns True if successfully cast.
        """
        raise NotImplementedError("Each spell must implement its own cast logic.")


class FireSpell(Spell):
    def __init__(self):
        super().__init__("fire")

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
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
            x=player.x, 
            y=player.y, 
            target=target, 
            spell_type="fire", 
            damage=damage, 
            speed=9.0, 
            color=Colors.FIRE,
            player=player,
            animation_effects=animation_effects
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
            player.x, player.y, 
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

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
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
            x=player.x, 
            y=player.y, 
            target=target, 
            spell_type="ice", 
            damage=damage, 
            speed=11.0, 
            color=Colors.ICE,
            effect_duration=freeze_dur,
            player=player,
            animation_effects=animation_effects
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
            player.x, player.y, 
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

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        if not target:
            animation_effects.add_floating_text("No Target!", player.x, player.y - 40, Colors.TEXT_MUTED, player.asset_manager.get_font(None, 24), is_damage=False)
            return False

        # Super Effectiveness: Lightning vs Skeleton (Double DMG)
        damage = self.damage
        is_super = False
        if target.type_name == "skeleton":
            damage = self.damage * 2
            is_super = True

        # Instant hit on primary target
        target.take_damage(damage)
        
        from spells.effects import LightningStrikeEffect
        
        # Start of lightning is from top sky, end is target center
        target_hitbox = target.get_hitbox()
        strike_effect = LightningStrikeEffect(
            start_pos=(target_hitbox.centerx, 0),
            end_pos=(target_hitbox.centerx, target_hitbox.centery)
        )
        animation_effects.particles.append(strike_effect)
        
        # Chain Lightning Combo: target up to 2 other nearby enemies
        prev_hitbox = target_hitbox
        if enemies:
            # Find nearby enemies sorted by distance to the main target
            nearby = []
            for e in enemies:
                if e != target and hasattr(e, 'hp') and e.hp > 0:
                    dx = e.x - target.x
                    dy = e.y - target.y
                    dist = math.hypot(dx, dy)
                    if dist <= 250:
                        nearby.append((dist, e))
            nearby.sort(key=lambda item: item[0])
            
            # Strike up to 2 chain targets
            for i in range(min(2, len(nearby))):
                next_enemy = nearby[i][1]
                chain_damage = self.damage
                if next_enemy.type_name == "skeleton":
                    chain_damage *= 2
                next_enemy.take_damage(chain_damage)
                
                next_hitbox = next_enemy.get_hitbox()
                # Chain bolt effect connecting the enemies
                chain_effect = LightningStrikeEffect(
                    start_pos=(prev_hitbox.centerx, prev_hitbox.centery),
                    end_pos=(next_hitbox.centerx, next_hitbox.centery)
                )
                animation_effects.particles.append(chain_effect)
                
                animation_effects.add_particle_burst(
                    next_hitbox.centerx, next_hitbox.centery, 
                    Colors.PARTICLE_LIGHTNING, 
                    count=8, 
                    speed_range=(1.5, 4.0), 
                    size_range=(2, 5)
                )
                
                animation_effects.add_floating_text(
                    f"-{chain_damage} HP", 
                    next_hitbox.centerx, next_hitbox.y - 20, 
                    Colors.LIGHTNING, 
                    player.asset_manager.get_font(None, 24)
                )
                
                prev_hitbox = next_hitbox
        
        # Burst particles at main target
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

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        # Gale Blast pushes ALL active enemies back
        pushed_count = 0
        if enemies:
            for enemy in enemies:
                if hasattr(enemy, 'hp') and enemy.hp > 0:
                    push = self.pushback
                    if enemy.type_name == "goblin":
                        push *= 1.5 # Goblin push multiplier
                        
                    # Calculate vector away from player center
                    dx = enemy.x - player.x
                    dy = enemy.y - player.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        ux, uy = dx / dist, dy / dist
                        enemy.x = max(30.0, min(float(GAMEPLAY_WIDTH - 30), enemy.x + ux * push))
                        enemy.y = max(30.0, min(float(SCREEN_HEIGHT - 30), enemy.y + uy * push))
                        
                        enemy_hitbox = enemy.get_hitbox()
                        animation_effects.add_floating_text(
                            "PUSH!", 
                            enemy_hitbox.centerx, enemy_hitbox.y - 12, 
                            Colors.WIND, 
                            player.asset_manager.get_font(None, 16), 
                            duration=0.5,
                            is_damage=False
                        )
                        pushed_count += 1
                        
        # Visual gale wind vortex effect centered on player
        from spells.effects import GaleWindEffect
        gale_effect = GaleWindEffect(player.x, player.y, max_radius=180.0)
        animation_effects.particles.append(gale_effect)
            
        animation_effects.add_floating_text(
            "GALE BLAST!", 
            player.x - 30, player.y - 45, 
            Colors.WIND, 
            player.asset_manager.get_font(None, 24), 
            is_damage=False
        )
        
        # Soft green screen flash
        animation_effects.trigger_flash(0.08, (150, 240, 180))
        
        player.asset_manager.get_sound("wind.wav").play()
        self.trigger_cooldown()
        return True


class ShieldSpell(Spell):
    def __init__(self):
        super().__init__("shield")
        self.duration = SPELLS["shield"]["duration"]

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        player.activate_shield(self.duration)
        
        # Spawn shield activation burst particles
        animation_effects.add_particle_burst(
            player.x, player.y, 
            Colors.PARTICLE_SHIELD, 
            count=25, 
            speed_range=(1.5, 4.5), 
            size_range=(3, 7)
        )
        
        animation_effects.add_floating_text(
            "AEGIS SHIELD!", 
            player.x - 40, player.y - 45, 
            Colors.SHIELD, 
            player.asset_manager.get_font(None, 24),
            is_damage=False
        )
        
        player.asset_manager.get_sound("shield.wav").play()
        self.trigger_cooldown()
        return True


class EarthquakeSpell(Spell):
    def __init__(self):
        super().__init__("earthquake")

    def cast(self, player, target, projectiles, animation_effects, enemies=None):
        # Trigger massive shake and screen tint
        animation_effects.trigger_shake(duration=0.6, intensity=12.0)
        animation_effects.trigger_flash(0.12, (180, 110, 60))
        
        player.asset_manager.get_sound("earthquake.wav").play()
        
        if enemies:
            alive_enemies = [e for e in enemies if hasattr(e, 'hp') and e.hp > 0]
            for enemy in alive_enemies:
                # Earthquake hits all enemies
                enemy.take_damage(self.damage)
                # Apply 2-second obstacle speed slow
                enemy.slow_timer = 2.0
                
                # Spawn earth particle blast at enemy feet
                eh = enemy.get_hitbox()
                animation_effects.add_particle_burst(
                    eh.centerx, eh.bottom, 
                    Colors.PARTICLE_EARTHQUAKE, 
                    count=8, 
                    speed_range=(1.0, 3.5), 
                    size_range=(3, 6)
                )
                
                # Damage text above enemy
                animation_effects.add_floating_text(
                    f"-{self.damage} HP", 
                    eh.centerx, eh.y - 15, 
                    Colors.EARTHQUAKE, 
                    player.asset_manager.get_font(None, 24)
                )
                
        # Central earthquake visual shockwave
        animation_effects.add_particle_burst(
            player.x, player.y + 40, 
            Colors.PARTICLE_EARTHQUAKE, 
            count=24, 
            speed_range=(2.5, 6.0), 
            size_range=(4, 9)
        )
        
        animation_effects.add_floating_text(
            "EARTHQUAKE!", 
            player.x - 40, player.y - 45, 
            Colors.EARTHQUAKE, 
            player.asset_manager.get_font(None, 24),
            is_damage=False
        )
        
        self.trigger_cooldown()
        return True
