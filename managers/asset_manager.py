import os
import pygame
from settings import SPRITES_DIR, BACKGROUNDS_DIR, FONTS_DIR, SOUNDS_DIR
from utils.constants import Colors

class DummySound:
    """A dummy sound class that does nothing when played, avoiding crashes if audio assets are missing."""
    def play(self):
        pass
    def stop(self):
        pass
    def set_volume(self, volume):
        pass

class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.fonts = {}
        
        # Initialize sound system if possible
        self.sound_enabled = True
        try:
            pygame.mixer.init()
        except pygame.error:
            self.sound_enabled = False
            print("Warning: Pygame mixer could not be initialized. Sound is disabled.")

    def get_image(self, category, filename, width=64, height=64, color=Colors.TEXT_MUTED):
        """
        Loads an image from the corresponding asset directory.
        If file doesn't exist, creates a colored placeholder surface with outline and detail.
        """
        key = f"{category}/{filename}"
        if key in self.images:
            return self.images[key]

        # Determine target folder
        if category == "sprites":
            folder = SPRITES_DIR
        elif category == "backgrounds":
            folder = BACKGROUNDS_DIR
        else:
            folder = SPRITES_DIR

        path = os.path.join(folder, filename)
        
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (width, height))
                self.images[key] = img
                return img
            except pygame.error as e:
                print(f"Error loading image {path}: {e}. Creating placeholder.")

        # Create a detailed placeholder surface
        placeholder = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if category == "backgrounds":
            # Dark grid background pattern
            placeholder.fill(Colors.BACKGROUND)
            for x in range(0, width, 40):
                pygame.draw.line(placeholder, (30, 26, 42), (x, 0), (x, height))
            for y in range(0, height, 40):
                pygame.draw.line(placeholder, (30, 26, 42), (0, y), (width, y))
        else:
            # Sprite placeholder: Rounded rectangle with border and inner core
            rect = pygame.Rect(0, 0, width, height)
            
            # Glow/Shadow
            pygame.draw.rect(placeholder, (color[0]//3, color[1]//3, color[2]//3, 100), rect, border_radius=8)
            
            # Main Body
            inner_rect = rect.inflate(-4, -4)
            pygame.draw.rect(placeholder, color, inner_rect, border_radius=6)
            
            # Border
            pygame.draw.rect(placeholder, Colors.TEXT_MAIN, inner_rect, width=2, border_radius=6)
            
            # Draw a decorative emblem/symbol in the center
            center_x, center_y = width // 2, height // 2
            pygame.draw.circle(placeholder, Colors.BACKGROUND, (center_x, center_y), min(width, height) // 4)
            pygame.draw.circle(placeholder, Colors.GOLD, (center_x, center_y), min(width, height) // 6)
            
        self.images[key] = placeholder
        return placeholder

    def get_font(self, filename, size):
        """
        Loads a font. Falls back to Pygame's system font if not found.
        """
        key = f"{filename}_{size}"
        if key in self.fonts:
            return self.fonts[key]

        path = os.path.join(FONTS_DIR, filename) if filename else ""
        
        if filename and os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                self.fonts[key] = font
                return font
            except pygame.error as e:
                print(f"Error loading font {path}: {e}. Falling back to default system font.")

        # Fallback to system font
        font = pygame.font.SysFont("Arial", size, bold=True)
        self.fonts[key] = font
        return font

    def get_sound(self, filename):
        """
        Loads a sound. Returns a DummySound if missing or if audio is disabled.
        """
        if not self.sound_enabled:
            return DummySound()

        if filename in self.sounds:
            return self.sounds[filename]

        path = os.path.join(SOUNDS_DIR, filename)
        
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                self.sounds[filename] = sound
                return sound
            except pygame.error as e:
                print(f"Error loading sound {path}: {e}. Returning dummy sound.")

        return DummySound()
