import pygame
import random
import math
from utils.constants import Colors
from utils.helpers import Particle

class LightningStrikeEffect(Particle):
    """
    Custom particle representing a jagged lightning bolt strike.
    Generates random vertices along a main path and secondary branching bolts.
    """
    def __init__(self, start_pos, end_pos, lifetime=15.0):
        super().__init__(start_pos[0], start_pos[1], 0.0, 0.0, Colors.LIGHTNING, 3.0, lifetime, shrink=False)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.segments = self.generate_lightning_path(start_pos, end_pos)
        self.glow_color = (255, 255, 230)
        
        # Generate 2-3 secondary branching forks for improved visual power
        self.branches = []
        num_branches = random.randint(2, 3)
        for _ in range(num_branches):
            if len(self.segments) > 4:
                # Pick a random node on the main bolt to branch from
                idx = random.randint(2, len(self.segments) - 3)
                branch_start = self.segments[idx]
                
                # Offset end outward and downwards
                offset_x = random.uniform(-70, 70)
                offset_y = random.uniform(40, 110)
                branch_end = (branch_start[0] + offset_x, branch_start[1] + offset_y)
                
                branch_path = self.generate_lightning_path(branch_start, branch_end, displacement=8)
                self.branches.append(branch_path)
        
    def generate_lightning_path(self, start, end, displacement=15):
        """Generates jagged lightning segments using mid-point displacement."""
        points = [start]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        
        num_segments = int(dist // 25)
        
        for i in range(1, num_segments):
            t = i / num_segments
            base_x = start[0] + dx * t
            base_y = start[1] + dy * t
            
            perp_x = -dy / dist
            perp_y = dx / dist
            
            offset = random.uniform(-displacement, displacement)
            px = base_x + perp_x * offset
            py = base_y + perp_y * offset
            
            points.append((px, py))
            
        points.append(end)
        return points

    def update(self, dt=1.0):
        self.lifetime -= dt
        self.size = max(1.0, random.uniform(1.5, 4.0))

    def draw(self, surface):
        if self.lifetime <= 0 or len(self.segments) < 2:
            return
            
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        main_c = Colors.LIGHTNING
        color_with_alpha = (main_c[0], main_c[1], main_c[2], alpha)
        glow_with_alpha = (self.glow_color[0], self.glow_color[1], self.glow_color[2], alpha // 2)
        
        # Calculate bounding box for local alpha surface drawing
        all_x = [p[0] for p in self.segments]
        all_y = [p[1] for p in self.segments]
        
        # Include branches in bounding box
        for branch in self.branches:
            for p in branch:
                all_x.append(p[0])
                all_y.append(p[1])
                
        min_x, max_x = int(min(all_x)) - 20, int(max(all_x)) + 20
        min_y, max_y = int(min(all_y)) - 20, int(max(all_y)) + 20
        
        min_x = max(0, min_x)
        max_x = min(surface.get_width(), max_x)
        min_y = max(0, min_y)
        max_y = min(surface.get_height(), max_y)
        
        surf_w = max_x - min_x
        surf_h = max_y - min_y
        
        if surf_w > 0 and surf_h > 0:
            temp_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            
            # 1. Draw secondary branching forks first (slightly thinner)
            for branch in self.branches:
                mapped_branch = [(p[0] - min_x, p[1] - min_y) for p in branch]
                for i in range(len(mapped_branch) - 1):
                    p1, p2 = mapped_branch[i], mapped_branch[i+1]
                    pygame.draw.line(temp_surf, glow_with_alpha, p1, p2, int(self.size * 2))
                    pygame.draw.line(temp_surf, color_with_alpha, p1, p2, int(self.size * 1.0))
                    pygame.draw.line(temp_surf, (255, 255, 255, alpha), p1, p2, 1)
            
            # 2. Draw main lightning bolt (thickest, in front)
            mapped_pts = [(p[0] - min_x, p[1] - min_y) for p in self.segments]
            for i in range(len(mapped_pts) - 1):
                p1, p2 = mapped_pts[i], mapped_pts[i+1]
                pygame.draw.line(temp_surf, glow_with_alpha, p1, p2, int(self.size * 3))
                pygame.draw.line(temp_surf, color_with_alpha, p1, p2, int(self.size * 1.5))
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


class SolarBeamEffect(Particle):
    """
    Visual effect representing a massive piercing solar laser.
    Draws a thick core, outer aura, and propagating energy rings.
    """
    def __init__(self, start_pos, end_pos, lifetime=20.0):
        super().__init__(start_pos[0], start_pos[1], 0.0, 0.0, Colors.SOLARBEAM, 12.0, lifetime, shrink=False)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.max_width = 55.0

    def update(self, dt=1.0):
        self.lifetime -= dt
        self.size = self.max_width * (self.lifetime / self.max_lifetime)

    def draw(self, surface):
        if self.lifetime <= 0 or self.size < 1.0:
            return

        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Calculate bounding box for alpha surface
        x1, y1 = self.start_pos
        x2, y2 = self.end_pos
        
        min_x = int(min(x1, x2)) - 80
        max_x = int(max(x1, x2)) + 80
        min_y = int(min(y1, y2)) - 80
        max_y = int(max(y1, y2)) + 80
        
        min_x = max(0, min_x)
        max_x = min(surface.get_width(), max_x)
        min_y = max(0, min_y)
        max_y = min(surface.get_height(), max_y)
        
        surf_w = max_x - min_x
        surf_h = max_y - min_y
        
        if surf_w > 0 and surf_h > 0:
            temp_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            
            p1 = (x1 - min_x, y1 - min_y)
            p2 = (x2 - min_x, y2 - min_y)
            
            # 1. Draw outer gold aura (thickest)
            pygame.draw.line(temp_surf, (235, 180, 50, alpha // 3), p1, p2, int(self.size * 2))
            
            # 2. Draw middle solar beam core
            pygame.draw.line(temp_surf, (255, 210, 80, alpha // 2), p1, p2, int(self.size * 1.2))
            
            # 3. Draw propagating energy rings along the beam
            dx = x2 - x1
            dy = y2 - y1
            dist = math.hypot(dx, dy)
            
            ticks = pygame.time.get_ticks()
            num_rings = 4
            for i in range(num_rings):
                # Ripple time phase
                t = ((ticks * 0.006) + (i / num_rings)) % 1.0
                rx = p1[0] + dx * t
                ry = p1[1] + dy * t
                
                # Expand size slightly near the end
                ring_r = int(self.size * (1.2 + 0.8 * t))
                
                # Draw concentric rings
                pygame.draw.circle(temp_surf, (255, 235, 170, alpha // 2), (int(rx), int(ry)), ring_r, width=2)
                pygame.draw.circle(temp_surf, (255, 255, 255, alpha), (int(rx), int(ry)), ring_r // 2, width=1)
                
            # 4. Draw bright white core (on top of rings)
            pygame.draw.line(temp_surf, (255, 255, 255, alpha), p1, p2, max(1, int(self.size * 0.4)))
            
            surface.blit(temp_surf, (min_x, min_y))


class GaleWindEffect(Particle):
    """
    Visual effect representing a massive sweeping wind vortex.
    Draws rotating spokes and concentric expanding rings.
    """
    def __init__(self, x, y, max_radius=180.0, lifetime=25.0):
        super().__init__(x, y, 0.0, 0.0, Colors.WIND, 1.0, lifetime, shrink=False)
        self.max_radius = max_radius
        self.current_radius = 10.0

    def update(self, dt=1.0):
        self.lifetime -= dt
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.current_radius = 10.0 + (self.max_radius - 10.0) * progress

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = int(180 * (self.lifetime / self.max_lifetime))
        
        # Draw concentric expanding wind rings
        num_rings = 3
        for i in range(num_rings):
            r = self.current_radius - i * 35
            if r > 0:
                # Ring base
                pygame.draw.circle(
                    surface, 
                    (Colors.WIND[0], Colors.WIND[1], Colors.WIND[2], alpha // (i + 1)), 
                    (int(self.x), int(self.y)), 
                    int(r), 
                    width=max(1, int(4 * (1.0 - r / self.max_radius)))
                )
                
                # Rotating hurricane spokes
                ticks = pygame.time.get_ticks()
                for j in range(8):
                    angle = j * (math.pi / 4) + ticks * 0.005 + (i * 0.5)
                    sx = self.x + math.cos(angle) * r
                    sy = self.y + math.sin(angle) * r
                    ex = self.x + math.cos(angle + 0.2) * (r + 10)
                    ey = self.y + math.sin(angle + 0.2) * (r + 10)
                    pygame.draw.line(
                        surface, 
                        (Colors.WIND[0], Colors.WIND[1], Colors.WIND[2], alpha // (i + 2)), 
                        (int(sx), int(sy)), 
                        (int(ex), int(ey)), 
                        2
                    )

