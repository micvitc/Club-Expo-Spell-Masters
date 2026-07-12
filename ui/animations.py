import pygame
import random
import math
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.helpers import Particle, FloatingText

class AnimationEffects:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        
        # Screen Shake properties
        self.shake_time = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = [0, 0]
        
        # Screen Flash properties
        self.flash_time = 0.0
        self.flash_duration = 0.0
        self.flash_color = (255, 255, 255)
        
    def trigger_shake(self, duration, intensity):
        """Triggers a screen shake effect."""
        self.shake_time = duration
        self.shake_intensity = intensity

    def trigger_flash(self, duration, color=Colors.TEXT_MAIN):
        """Triggers a full-screen tint flash (e.g., lightning strike or taking damage)."""
        self.flash_time = duration
        self.flash_duration = duration
        self.flash_color = color

    def add_particle_burst(self, x, y, color_palette, count=15, speed_range=(1.0, 5.0), size_range=(4, 8), lifetime_range=(15, 30), gravity=0.0):
        """Creates a circular blast of particles from a point."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice(color_palette)
            size = random.uniform(*size_range)
            lifetime = random.uniform(*lifetime_range)
            
            p = Particle(x, y, vx, vy, color, size, lifetime, shrink=True, gravity=gravity)
            self.particles.append(p)
            
    def add_floating_text(self, text, x, y, color, font, duration=1.0, is_damage=True):
        """Adds rising text for damage, spell actions, or alerts."""
        ft = FloatingText(text, x, y, color, font, duration, is_damage)
        self.floating_texts.append(ft)

    def update(self, dt):
        # Update Screen Shake
        if self.shake_time > 0:
            self.shake_time -= dt
            # Random shake offset scaling with remaining shake time
            current_intensity = self.shake_intensity * (self.shake_time / 0.5)
            self.shake_offset[0] = int(random.uniform(-current_intensity, current_intensity))
            self.shake_offset[1] = int(random.uniform(-current_intensity, current_intensity))
        else:
            self.shake_offset = [0, 0]
            
        # Update Screen Flash
        if self.flash_time > 0:
            self.flash_time -= dt

        # Update Particles
        for p in self.particles[:]:
            p.update(dt)
            if p.lifetime <= 0:
                self.particles.remove(p)

        # Update Floating Text
        for ft in self.floating_texts[:]:
            ft.update(dt)
            if ft.time_alive >= ft.duration:
                self.floating_texts.remove(ft)

    def draw_particles(self, surface):
        for p in self.particles:
            p.draw(surface)

    def draw_floating_texts(self, surface):
        for ft in self.floating_texts:
            ft.draw(surface)

    def draw_flash(self, surface):
        """Draws full-screen flash overlays."""
        if self.flash_time > 0:
            # Calculate alpha fading out
            alpha = int(120 * (self.flash_time / self.flash_duration))
            if alpha > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                # Ensure color includes alpha
                color = self.flash_color
                flash_surf.fill((color[0], color[1], color[2], alpha))
                surface.blit(flash_surf, (0, 0))

    def clear(self):
        """Clears all ongoing animations/particles."""
        self.particles.clear()
        self.floating_texts.clear()
        self.shake_time = 0.0
        self.shake_offset = [0, 0]
        self.flash_time = 0.0
