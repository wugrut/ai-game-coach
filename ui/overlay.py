"""
Transparent overlay HUD for AI Game Coach.
Displays coaching tips and status directly on top of the game screen.
Uses win32 APIs for click-through transparency on Windows.
"""

import logging
import threading
import time
from typing import Optional

import customtkinter as ctk

from core.config import config
from ui.theme import Colors, Fonts

logger = logging.getLogger(__name__)

# ── Try to import win32 APIs ────────────────────────────────────────────────
_HAS_WIN32 = False
try:
    import win32gui
    import win32con
    import win32api
    _HAS_WIN32 = True
except ImportError:
    logger.warning("pywin32 not available — overlay click-through disabled")


class OverlayHUD(ctk.CTkToplevel):
    """
    Transparent, always-on-top overlay window.

    Displays the latest coaching tip in a semi-transparent bar that
    floats over the game. On Windows, the overlay is click-through,
    meaning game input passes through it.
    """

    # How long a message stays visible (seconds)
    MESSAGE_DISPLAY_DURATION = 8.0
    # Fade-out duration (seconds)
    FADE_DURATION = 1.0

    def __init__(self, master=None):
        super().__init__(master)

        # Window configuration
        self.title("")
        self.overrideredirect(True)      # Remove title bar
        self.attributes("-topmost", True)  # Always on top

        # Transparency
        opacity = config.get("overlay_opacity", 0.85)
        self.attributes("-alpha", opacity)

        # Set transparent color for click-through
        self._transparent_color = "#010101"
        self.configure(fg_color=self._transparent_color)
        self.attributes("-transparentcolor", self._transparent_color)

        # Sizing and positioning
        self._overlay_width = config.get("overlay_width", 400)
        self._position = config.get("overlay_position", "bottom")
        self._update_geometry()

        # State
        self._visible = False
        self._current_message = ""
        self._message_time = 0.0
        self._fade_timer_id = None

        # Build UI
        self._build_overlay()

        # Make click-through on Windows
        if _HAS_WIN32:
            self.after(100, self._make_click_through)

        # Start the auto-hide timer
        self._check_fade_loop()

        # Start hidden
        self.withdraw()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_overlay(self):
        """Build the overlay UI elements."""
        # Main container with semi-transparent background
        self._container = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_DARKEST + "dd",
            corner_radius=16,
            border_width=1,
            border_color=Colors.ACCENT_BLUE + "44",
        )
        self._container.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

        # Header row: icon + status
        header = ctk.CTkFrame(self._container, fg_color="transparent")
        header.pack(fill=ctk.X, padx=12, pady=(10, 4))

        self._status_dot = ctk.CTkLabel(
            header,
            text="●",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.STATUS_ONLINE,
            width=16,
        )
        self._status_dot.pack(side=ctk.LEFT)

        self._status_label = ctk.CTkLabel(
            header,
            text="AI Coach Active",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.TEXT_DISABLED,
        )
        self._status_label.pack(side=ctk.LEFT, padx=(4, 0))

        # Priority indicator
        self._priority_label = ctk.CTkLabel(
            header,
            text="",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.TEXT_DISABLED,
        )
        self._priority_label.pack(side=ctk.RIGHT)

        # Message area
        self._message_label = ctk.CTkLabel(
            self._container,
            text="Waiting for coaching advice...",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=self._overlay_width - 40,
        )
        self._message_label.pack(fill=ctk.X, padx=12, pady=(4, 10))

    # ── Public API ───────────────────────────────────────────────────────

    def show_message(self, text: str, priority: str = "info"):
        """
        Display a coaching message on the overlay.

        Args:
            text: The coaching message text.
            priority: Priority level (critical, important, tip, info).
        """
        if not self._visible:
            return

        # Priority styling
        priority_config = {
            "critical": {"color": Colors.ACCENT_RED, "emoji": "🔴", "border": Colors.ACCENT_RED},
            "important": {"color": Colors.ACCENT_YELLOW, "emoji": "🟡", "border": Colors.ACCENT_YELLOW},
            "tip": {"color": Colors.ACCENT_GREEN, "emoji": "🟢", "border": Colors.ACCENT_GREEN},
            "info": {"color": Colors.ACCENT_BLUE, "emoji": "🔵", "border": Colors.ACCENT_BLUE},
        }
        style = priority_config.get(priority, priority_config["info"])

        # Update UI (must be on main thread)
        try:
            self._message_label.configure(text=text)
            self._priority_label.configure(
                text=f"{style['emoji']} {priority.upper()}",
                text_color=style["color"],
            )
            self._container.configure(border_color=style["border"] + "66")
            self._message_time = time.time()
            self._current_message = text

            # Ensure visible
            self.attributes("-alpha", config.get("overlay_opacity", 0.85))
        except Exception as e:
            logger.error(f"Overlay update error: {e}")

    def show_overlay(self):
        """Show the overlay window."""
        self._visible = True
        self._update_geometry()
        self.deiconify()
        self.lift()
        logger.info("Overlay shown")

    def hide_overlay(self):
        """Hide the overlay window."""
        self._visible = False
        self.withdraw()
        logger.info("Overlay hidden")

    def toggle(self):
        """Toggle overlay visibility."""
        if self._visible:
            self.hide_overlay()
        else:
            self.show_overlay()

    def update_status(self, is_active: bool, fps: float = 0.0):
        """Update the coaching status indicator."""
        try:
            if is_active:
                self._status_dot.configure(text_color=Colors.STATUS_ONLINE)
                self._status_label.configure(text=f"AI Coach • {fps:.0f} FPS")
            else:
                self._status_dot.configure(text_color=Colors.STATUS_OFFLINE)
                self._status_label.configure(text="AI Coach Paused")
        except Exception:
            pass

    def update_position(self, position: Optional[str] = None):
        """Update the overlay position on screen."""
        if position:
            self._position = position
        self._update_geometry()

    # ── Window Management ────────────────────────────────────────────────

    def _update_geometry(self):
        """Position the overlay on the screen."""
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        except Exception:
            screen_w, screen_h = 1920, 1080

        overlay_h = 100  # Fixed height
        overlay_w = self._overlay_width

        if self._position == "top":
            x = (screen_w - overlay_w) // 2
            y = 10
        elif self._position == "top_right":
            x = screen_w - overlay_w - 20
            y = 10
        elif self._position == "bottom_right":
            x = screen_w - overlay_w - 20
            y = screen_h - overlay_h - 50
        else:  # bottom (default)
            x = (screen_w - overlay_w) // 2
            y = screen_h - overlay_h - 50

        self.geometry(f"{overlay_w}x{overlay_h}+{x}+{y}")

    def _make_click_through(self):
        """Make the window click-through using Win32 APIs."""
        if not _HAS_WIN32:
            return

        try:
            hwnd = self.winfo_id()
            # Get current extended style
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            # Add layered + transparent flags
            style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            logger.info("Overlay set to click-through mode")
        except Exception as e:
            logger.warning(f"Failed to set click-through: {e}")

    # ── Auto-fade ────────────────────────────────────────────────────────

    def _check_fade_loop(self):
        """Periodically check if the message should fade out."""
        if self._visible and self._current_message:
            elapsed = time.time() - self._message_time
            remaining = self.MESSAGE_DISPLAY_DURATION - elapsed

            if remaining <= 0:
                # Fully faded — show idle text
                try:
                    self._message_label.configure(
                        text="Listening...",
                    )
                    self._priority_label.configure(text="")
                    self._container.configure(border_color=Colors.ACCENT_BLUE + "22")
                    self._current_message = ""
                except Exception:
                    pass

            elif remaining <= self.FADE_DURATION:
                # Fading out — reduce alpha
                fade_progress = 1.0 - (remaining / self.FADE_DURATION)
                base_opacity = config.get("overlay_opacity", 0.85)
                current_alpha = base_opacity * (1.0 - fade_progress * 0.5)
                try:
                    self.attributes("-alpha", max(0.3, current_alpha))
                except Exception:
                    pass

        # Schedule next check
        self.after(200, self._check_fade_loop)
