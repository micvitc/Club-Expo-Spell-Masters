import pygame
import random
import math
from utils.constants import Colors
from utils.helpers import Particle

class LightningStrikeEffect(Particle):
    """
    Custom particle representing a jagged lightning bolt strike.
    Generates random vertices along a path and draws connecting electric segments.
    """
    def __init__(self, start_pos, end_pos, lifetime=15.0):
        # We pass dummy velocities; position is fixed but we draw path
        super().__init__(start_pos[0], start_pos[1], 0.0, 0.0, Colors.LIGHTNING, 3.0, lifetime, shrink=False)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.segments = self.generate_lightning_path(start_pos, end_pos)
        self.glow_color = (255, 255, 230)
        
    def generate_lightning_path(self, start, end, displacement=15):
        """Generates jagged lightning segments using mid-point displacement."""
        points = [start]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        
        # Determine number of intermediate segments based on distance
        num_segments = int(dist // 25)
        
        for i in range(1, num_segments):
            t = i / num_segments
            # Interpolated base position
            base_x = start[0] + dx * t
            base_y = start[1] + dy * t
            
            # Perpendicular vector for offset
            perp_x = -dy / dist
            perp_y = dx / dist
            
            # Displace point perpendicular to direction
            offset = random.uniform(-displacement, displacement)
            px = base_x + perp_x * offset
            py = base_y + perp_y * offset
            
            points.append((px, py))
            
        points.append(end)
        return points

    def update(self, dt=1.0):
        self.lifetime -= dt
        # Slightly wobble lightning line thickness/glow for sparkle effect
        self.size = max(1.0, random.uniform(1.5, 4.0))

    def draw(self, surface):
        if self.lifetime <= 0 or len(self.segments) < 2:
            return
            
        # Calculate fade alpha
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Color with alpha
        main_c = Colors.LIGHTNING
        color_with_alpha = (main_c[0], main_c[1], main_c[2], alpha)
        glow_with_alpha = (self.glow_color[0], self.glow_color[1], self.glow_color[2], alpha // 2)
        
        # Render onto a temporary transparent surface to support transparency lines in Pygame
        # (Pygame draw lines doesn't natively do alpha blend lines unless drawn on an alpha surface)
        width = surface.get_width()
        height = surface.get_height()
        
        # To optimize, create small bounding box surface or draw directly. 
        # For simplicity & speed, we draw directly. If alpha is needed, draw multiple thin lines or 
        # blit a temporary surface. Let's use a temporary surface matching bounding box.
        xs = [p[0] for p in self.segments]
        ys = [p[1] for p in self.segments]
        min_x, max_x = int(min(xs)) - 20, int(max(xs)) + 20
        min_y, max_y = int(min(ys)) - 20, int(max(ys)) + 20
        
        # Clamp dimensions
        min_x = max(0, min_x)
        max_x = min(width, max_x)
        min_y = max(0, min_y)
        max_y = min(height, max_y)
        
        surf_w = max_x - min_x
        surf_h = max_y - min_y
        
        if surf_w > 0 and surf_h > 0:
            temp_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            
            # Map points to surface coordinates
            mapped_pts = [(p[0] - min_x, p[1] - min_y) for p in self.segments]
            
            # Draw outer glow
            for i in range(len(mapped_pts) - 1):
                p1, p2 = mapped_pts[i], mapped_pts[i+1]
                # Thick glow line
                pygame.draw.line(temp_surf, glow_with_alpha, p1, p2, int(self.size * 3))
                # Medium glow line
                pygame.draw.line(temp_surf, color_with_alpha, p1, p2, int(self.size * 1.5))
                # Core bright white line
                pygame.draw.line(temp_surf, (255, 255, 255, alpha), p1, p2, max(1, int(self.size * 0.5)))
                
            surface.blit(temp_surf, (min_x, min_y))


class FireExplosionEffect(Particle):
    """
    Visual explosion showing expanding rings/particles.
    """
    def __init__(self, x, y, max_radius=30, lifetime=20.0):
        super().__init__(x, y, 0.0, 0.0, Colors.FIRE, 2.0, lifetime, shrink=False)
        self.max_radius = max_radius
        self.current_radius = 2.0

    def update(self, dt=1.0):
        self.lifetime -= dt
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.current_radius = self.max_radius * progress

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        
        alpha = int(180 * (self.lifetime / self.max_lifetime))
        temp_surf = pygame.Surface((self.max_radius * 2 + 10, self.max_radius * 2 + 10), pygame.SRCALPHA)
        
        c = Colors.FIRE
        color = (c[0], c[1], c[2], alpha)
        
        # Draw expanding ring
        pygame.draw.circle(temp_surf, color, (self.max_radius + 5, self.max_radius + 5), int(self.current_radius), width=3)
        pygame.draw.circle(temp_surf, (255, 200, 100, alpha // 2), (self.max_radius + 5, self.max_radius + 5), int(self.current_radius - 2))
        
        surface.blit(temp_surf, (int(self.x - self.max_radius - 5), int(self.y - self.max_radius - 5)))
