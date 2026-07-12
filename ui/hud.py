import pygame
import math
from utils.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT, GAMEPLAY_WIDTH, SIDEBAR_WIDTH
from utils.helpers import draw_health_bar, draw_text_with_outline

class HUD:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        
        # Load fonts
        self.font_large = self.asset_manager.get_font(None, 28)
        self.font_medium = self.asset_manager.get_font(None, 18)
        self.font_small = self.asset_manager.get_font(None, 14)
        self.font_xsmall = self.asset_manager.get_font(None, 12)
        
    def draw(self, surface, player, wave_manager, spell_manager):
        # 1. Draw Player HP Bar (Top Left of Gameplay)
        hp_x, hp_y = 30, 30
        hp_w, hp_h = 240, 24
        draw_health_bar(surface, hp_x, hp_y, hp_w, hp_h, player.hp, player.max_hp)
        
        # Draw HP text over bar
        hp_text = f"WIZARD HP: {player.hp}/{player.max_hp}"
        draw_text_with_outline(
            surface, hp_text, self.font_small, 
            Colors.TEXT_MAIN, Colors.SHADOW, 
            (hp_x + 10, hp_y + 5)
        )
        
        # 2. Draw Score (Top Right of Gameplay area, X <= 960)
        score_text = f"SCORE: {player.score:05d}"
        score_w = self.font_large.size(score_text)[0]
        draw_text_with_outline(
            surface, score_text, self.font_large, 
            Colors.GOLD, Colors.SHADOW, 
            (GAMEPLAY_WIDTH - score_w - 30, hp_y)
        )
        
        # 3. Draw Wave Info (Top Center of Gameplay)
        wave_str = f"WAVE {wave_manager.current_wave}"
        wave_w = self.font_large.size(wave_str)[0]
        wave_x = GAMEPLAY_WIDTH // 2 - wave_w // 2
        draw_text_with_outline(
            surface, wave_str, self.font_large, 
            Colors.TEXT_MAIN, Colors.SHADOW, 
            (wave_x, hp_y)
        )
        
        # Wave Status subtext
        if wave_manager.in_breather:
            status_text = f"Next wave in {int(wave_manager.breather_timer) + 1}s..."
            status_color = Colors.GOLD
        else:
            remaining = wave_manager.get_remaining_enemies_count()
            status_text = f"Enemies Left: {remaining}"
            status_color = Colors.TEXT_MUTED
            
        status_w = self.font_medium.size(status_text)[0]
        draw_text_with_outline(
            surface, status_text, self.font_medium, 
            status_color, Colors.SHADOW, 
            (GAMEPLAY_WIDTH // 2 - status_w // 2, hp_y + 30)
        )
        
        # 4. Draw Spell Guide & Cooldown Hotbar (Bottom Center of Gameplay)
        self.draw_spell_hotbar(surface, spell_manager)

        # 5. Draw Right Sidebar (from 960 to 1280)
        self.draw_sidebar(surface, spell_manager)

    def draw_spell_hotbar(self, surface, spell_manager):
        # Spells metadata for HUD hotbar layout
        spell_slots = [
            {"id": "fire", "key": "1", "symbol": "Circle (O)", "color": Colors.FIRE},
            {"id": "ice", "key": "2", "symbol": "Line (-)", "color": Colors.ICE},
            {"id": "lightning", "key": "3", "symbol": "Z-Shape (Z)", "color": Colors.LIGHTNING},
            {"id": "wind", "key": "4", "symbol": "Spiral (S)", "color": Colors.WIND}
        ]
        
        slot_w, slot_h = 135, 75
        spacing = 15
        total_w = (slot_w * 4) + (spacing * 3)
        start_x = (GAMEPLAY_WIDTH - total_w) // 2
        start_y = SCREEN_HEIGHT - slot_h - 20
        
        for i, slot in enumerate(spell_slots):
            x = start_x + i * (slot_w + spacing)
            y = start_y
            
            # Cooldown progress
            cd_ratio = spell_manager.get_cooldown_ratio(slot["id"])
            
            # Card background
            card_rect = pygame.Rect(x, y, slot_w, slot_h)
            
            # Subtle outer glow if spell is ready
            if cd_ratio == 0:
                glow_rect = card_rect.inflate(4, 4)
                pygame.draw.rect(surface, (slot["color"][0], slot["color"][1], slot["color"][2], 100), glow_rect, border_radius=6, width=1)
                
            pygame.draw.rect(surface, Colors.BUTTON_NORMAL, card_rect, border_radius=6)
            pygame.draw.rect(surface, Colors.SHADOW, card_rect, width=2, border_radius=6)
            
            # Left vertical stripe showing spell theme color
            pygame.draw.rect(surface, slot["color"], (x, y, 6, slot_h), border_radius=6)
            
            # Write key mapping & spell name
            name_text = slot["id"].upper()
            draw_text_with_outline(
                surface, f"[{slot['key']}] {name_text}", 
                self.font_medium, Colors.TEXT_MAIN, Colors.SHADOW, 
                (x + 12, y + 8)
            )
            
            # Write gesture symbol guide
            draw_text_with_outline(
                surface, f"Gesture: {slot['symbol']}", 
                self.font_small, Colors.TEXT_MUTED, Colors.SHADOW, 
                (x + 12, y + 32)
            )
            
            # Status: READY or CD timer
            if cd_ratio > 0:
                # Render transparent grey overlay indicating CD progress
                overlay = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
                overlay.fill((25, 20, 35, 180))
                surface.blit(overlay, (x, y))
                
                # Show remaining time text
                spell = spell_manager.spells[slot["id"]]
                cd_left = f"{spell.cooldown_timer:.1f}s"
                cd_w = self.font_large.size(cd_left)[0]
                
                # Draw countdown center-aligned
                draw_text_with_outline(
                    surface, cd_left, self.font_large, 
                    slot["color"], Colors.SHADOW, 
                    (x + slot_w // 2 - cd_w // 2, y + slot_h // 2 - 10)
                )
            else:
                draw_text_with_outline(
                    surface, "READY", 
                    self.font_small, slot["color"], Colors.SHADOW, 
                    (x + 12, y + 52)
                )

    def draw_sidebar(self, surface, spell_manager):
        # 1. Background Frame
        sidebar_rect = pygame.Rect(GAMEPLAY_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, (14, 12, 22), sidebar_rect)
        pygame.draw.line(surface, Colors.GOLD, (GAMEPLAY_WIDTH, 0), (GAMEPLAY_WIDTH, SCREEN_HEIGHT), 2)
        
        # 2. Camera Viewport Placeholder
        cam_x = GAMEPLAY_WIDTH + 20
        cam_y = 30
        cam_w = 280
        cam_h = 210
        
        cam_rect = pygame.Rect(cam_x, cam_y, cam_w, cam_h)
        pygame.draw.rect(surface, Colors.SHADOW, cam_rect.move(2, 2), border_radius=6)
        pygame.draw.rect(surface, (22, 19, 34), cam_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 230, 150), cam_rect, width=2, border_radius=6)
        
        # Draw camera HUD grid lines
        pygame.draw.rect(surface, (0, 230, 150, 40), (cam_x + 10, cam_y + 10, cam_w - 20, cam_h - 20), width=1)
        # Crosshair in center
        cx, cy = cam_x + cam_w // 2, cam_y + cam_h // 2
        pygame.draw.line(surface, (0, 230, 150, 90), (cx - 15, cy), (cx + 15, cy), 1)
        pygame.draw.line(surface, (0, 230, 150, 90), (cx, cy - 15), (cx, cy + 15), 1)
        
        # Dynamic scan line moving up and down
        ticks = pygame.time.get_ticks()
        scan_y = cam_y + 10 + int((math.sin(ticks * 0.0035) + 1.0) / 2.0 * (cam_h - 20))
        pygame.draw.line(surface, (0, 230, 150), (cam_x + 4, scan_y), (cam_x + cam_w - 4, scan_y), 1)
        
        # Recording Blinking Dot
        rec_active = (ticks // 500) % 2 == 0
        dot_color = (255, 50, 50) if rec_active else (80, 20, 20)
        pygame.draw.circle(surface, dot_color, (cam_x + 25, cam_y + 25), 6)
        draw_text_with_outline(
            surface, "GESTURE FEED (LIVE)", 
            self.font_small, Colors.TEXT_MAIN, Colors.SHADOW, 
            (cam_x + 38, cam_y + 18)
        )
        
        # Wait message
        wait_msg = "[ WAITING FOR HAND GESTURE ]"
        msg_w = self.font_small.size(wait_msg)[0]
        draw_text_with_outline(
            surface, wait_msg, 
            self.font_small, (0, 230, 150), Colors.SHADOW, 
            (cx - msg_w // 2, cy + 45)
        )
        
        # 3. Super Effectiveness Panel
        title_y = 265
        draw_text_with_outline(
            surface, "SPELL EFFECTIVENESS MATRIX", 
            self.font_large, Colors.GOLD, Colors.SHADOW, 
            (cam_x, title_y)
        )
        
        # Spell cards
        cards_info = [
            {"name": "FIREBALL", "color": Colors.FIRE, "target": "Goblin", "effect": "Deals Double Damage (2x DMG)", "target_color": (90, 180, 80)},
            {"name": "FROST CHILL", "color": Colors.ICE, "target": "Orc", "effect": "Double DMG & Freeze Time (8s)", "target_color": (150, 75, 40)},
            {"name": "LIGHTNING STRIKE", "color": Colors.LIGHTNING, "target": "Skeleton", "effect": "Deals Double Damage (2x DMG)", "target_color": (210, 210, 200)},
            {"name": "GALE BLAST", "color": Colors.WIND, "target": "Goblin", "effect": "Double Pushback Distance (400px)", "target_color": (90, 180, 80)}
        ]
        
        start_card_y = 300
        card_h = 85
        card_spacing = 15
        
        for idx, card in enumerate(cards_info):
            y = start_card_y + idx * (card_h + card_spacing)
            
            # Card background
            card_rect = pygame.Rect(cam_x, y, cam_w, card_h)
            pygame.draw.rect(surface, Colors.SHADOW, card_rect.move(2, 2), border_radius=6)
            pygame.draw.rect(surface, Colors.BUTTON_NORMAL, card_rect, border_radius=6)
            pygame.draw.rect(surface, Colors.BUTTON_HOVER, card_rect, width=1, border_radius=6)
            
            # Left stripe in spell color
            pygame.draw.rect(surface, card["color"], (cam_x, y, 6, card_h), border_radius=6)
            
            # Title
            draw_text_with_outline(
                surface, card["name"], 
                self.font_medium, card["color"], Colors.SHADOW, 
                (cam_x + 15, y + 10)
            )
            
            # Weakness arrow
            draw_text_with_outline(
                surface, f"VS   {card['target']}", 
                self.font_small, Colors.TEXT_MAIN, Colors.SHADOW, 
                (cam_x + 15, y + 33)
            )
            
            # Description text
            draw_text_with_outline(
                surface, card["effect"], 
                self.font_small, Colors.GOLD, Colors.SHADOW, 
                (cam_x + 15, y + 55)
            )
