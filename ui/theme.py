"""
Custom dark theme and styling for AI Game Coach.
Deep navy/charcoal backgrounds with vibrant accent colors.
"""

import customtkinter as ctk

# ── Color Palette ────────────────────────────────────────────────────────────

class Colors:
    """Application color palette — dark theme with vibrant accents."""

    # Backgrounds
    BG_DARKEST = "#0a0a14"       # Deepest background (main window)
    BG_DARK = "#0f0f1a"          # Primary background
    BG_MEDIUM = "#1a1a2e"        # Card / panel background
    BG_LIGHT = "#242442"         # Elevated surfaces
    BG_HOVER = "#2d2d52"         # Hover state backgrounds
    BG_INPUT = "#16162b"         # Input field backgrounds

    # Accents
    ACCENT_BLUE = "#00d4ff"      # Primary accent (electric blue)
    ACCENT_GREEN = "#00ff88"     # Success / tip accent
    ACCENT_YELLOW = "#ffb800"    # Warning / important accent
    ACCENT_RED = "#ff4466"       # Critical / error accent
    ACCENT_PURPLE = "#b366ff"    # Secondary accent

    # Text
    TEXT_PRIMARY = "#e8e8f0"     # Primary text
    TEXT_SECONDARY = "#8888aa"   # Secondary / muted text
    TEXT_DISABLED = "#555570"    # Disabled text
    TEXT_ACCENT = "#00d4ff"      # Accent-colored text

    # Borders
    BORDER_SUBTLE = "#2a2a45"    # Subtle borders
    BORDER_ACCENT = "#00d4ff33"  # Accent borders (with alpha)

    # Priority message colors
    PRIORITY_CRITICAL = "#ff4466"
    PRIORITY_IMPORTANT = "#ffb800"
    PRIORITY_TIP = "#00ff88"
    PRIORITY_INFO = "#00d4ff"

    # Status
    STATUS_ONLINE = "#00ff88"
    STATUS_OFFLINE = "#ff4466"
    STATUS_WORKING = "#ffb800"


# ── Fonts ────────────────────────────────────────────────────────────────────

class Fonts:
    """Font configuration for the application."""

    FAMILY = "Segoe UI"
    FAMILY_MONO = "Cascadia Code"

    # Sizes
    SIZE_TITLE = 20
    SIZE_HEADING = 16
    SIZE_BODY = 13
    SIZE_SMALL = 11
    SIZE_TINY = 10

    @staticmethod
    def title():
        return (Fonts.FAMILY, Fonts.SIZE_TITLE, "bold")

    @staticmethod
    def heading():
        return (Fonts.FAMILY, Fonts.SIZE_HEADING, "bold")

    @staticmethod
    def body():
        return (Fonts.FAMILY, Fonts.SIZE_BODY)

    @staticmethod
    def body_bold():
        return (Fonts.FAMILY, Fonts.SIZE_BODY, "bold")

    @staticmethod
    def small():
        return (Fonts.FAMILY, Fonts.SIZE_SMALL)

    @staticmethod
    def mono():
        return (Fonts.FAMILY_MONO, Fonts.SIZE_SMALL)


# ── Theme Setup ──────────────────────────────────────────────────────────────

def apply_theme():
    """Configure CustomTkinter with our dark theme."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


# ── Styled Widget Helpers ────────────────────────────────────────────────────

def create_card_frame(parent, **kwargs) -> ctk.CTkFrame:
    """Create a styled card-like frame with rounded corners."""
    defaults = {
        "fg_color": Colors.BG_MEDIUM,
        "corner_radius": 12,
        "border_width": 1,
        "border_color": Colors.BORDER_SUBTLE,
    }
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def create_accent_button(parent, text: str, command=None, color=None, **kwargs) -> ctk.CTkButton:
    """Create a styled accent button."""
    fg = color or Colors.ACCENT_BLUE
    defaults = {
        "text": text,
        "command": command,
        "fg_color": fg,
        "hover_color": _lighten(fg, 0.2),
        "text_color": Colors.BG_DARKEST,
        "font": Fonts.body_bold(),
        "corner_radius": 8,
        "height": 36,
    }
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def create_outline_button(parent, text: str, command=None, **kwargs) -> ctk.CTkButton:
    """Create a styled outline button."""
    defaults = {
        "text": text,
        "command": command,
        "fg_color": "transparent",
        "hover_color": Colors.BG_HOVER,
        "text_color": Colors.TEXT_PRIMARY,
        "border_width": 1,
        "border_color": Colors.BORDER_SUBTLE,
        "font": Fonts.body(),
        "corner_radius": 8,
        "height": 36,
    }
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def create_label(parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
    """Create a styled label."""
    font_map = {
        "title": Fonts.title(),
        "heading": Fonts.heading(),
        "body": Fonts.body(),
        "body_bold": Fonts.body_bold(),
        "small": Fonts.small(),
        "mono": Fonts.mono(),
    }
    defaults = {
        "text": text,
        "font": font_map.get(style, Fonts.body()),
        "text_color": Colors.TEXT_PRIMARY,
    }
    defaults.update(kwargs)
    return ctk.CTkLabel(parent, **defaults)


# ── Utility ──────────────────────────────────────────────────────────────────

def _lighten(hex_color: str, factor: float = 0.2) -> str:
    """Lighten a hex color by a factor."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) < 6:
        return f"#{hex_color}"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"
