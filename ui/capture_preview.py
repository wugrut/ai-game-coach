"""
Live capture preview widget for AI Game Coach.
Shows a thumbnail of the captured screen region with FPS counter.
"""

import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Optional

from ui.theme import Colors, Fonts, create_card_frame, create_label


class CapturePreview(ctk.CTkFrame):
    """
    Live preview widget showing what the screen capture engine is seeing.
    Displays a resized thumbnail and capture status information.
    """

    PREVIEW_WIDTH = 320
    PREVIEW_HEIGHT = 180

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Preview card
        self._card = create_card_frame(self)
        self._card.pack(fill=ctk.X, padx=4, pady=4)

        # Header
        header = ctk.CTkFrame(self._card, fg_color="transparent")
        header.pack(fill=ctk.X, padx=12, pady=(12, 8))

        create_label(header, "📸 Capture Preview", style="body_bold").pack(side=ctk.LEFT)

        self._status_dot = ctk.CTkLabel(
            header, text="●", font=Fonts.body(),
            text_color=Colors.STATUS_OFFLINE, width=20,
        )
        self._status_dot.pack(side=ctk.RIGHT)

        self._fps_label = create_label(header, "0 FPS", style="small",
                                        text_color=Colors.TEXT_SECONDARY)
        self._fps_label.pack(side=ctk.RIGHT, padx=(0, 8))

        # Preview image area
        self._preview_frame = ctk.CTkFrame(
            self._card,
            fg_color=Colors.BG_DARKEST,
            corner_radius=8,
            width=self.PREVIEW_WIDTH,
            height=self.PREVIEW_HEIGHT,
        )
        self._preview_frame.pack(padx=12, pady=(0, 12))
        self._preview_frame.pack_propagate(False)

        self._preview_label = ctk.CTkLabel(
            self._preview_frame,
            text="No capture active\nSelect a region to start",
            text_color=Colors.TEXT_DISABLED,
            font=Fonts.small(),
        )
        self._preview_label.pack(expand=True)

        # Keep reference to prevent garbage collection
        self._photo_image: Optional[ImageTk.PhotoImage] = None

        # Region info
        self._region_label = create_label(
            self._card, "Region: Not set",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._region_label.pack(padx=12, pady=(0, 12))

    def update_preview(self, frame: Image.Image):
        """Update the preview with a new captured frame."""
        try:
            # Resize to preview dimensions
            frame_resized = frame.copy()
            frame_resized.thumbnail(
                (self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT),
                Image.Resampling.LANCZOS,
            )

            self._photo_image = ImageTk.PhotoImage(frame_resized)
            self._preview_label.configure(
                image=self._photo_image,
                text="",
            )
        except Exception:
            pass

    def update_status(self, is_running: bool, fps: float = 0.0):
        """Update the capture status indicator."""
        if is_running:
            self._status_dot.configure(text_color=Colors.STATUS_ONLINE)
            self._fps_label.configure(text=f"{fps:.0f} FPS")
        else:
            self._status_dot.configure(text_color=Colors.STATUS_OFFLINE)
            self._fps_label.configure(text="Stopped")

    def update_region_info(self, region):
        """Update the displayed region information."""
        if region and len(region) == 4:
            l, t, r, b = region
            w, h = r - l, b - t
            self._region_label.configure(
                text=f"Region: ({l}, {t}) → ({r}, {b})  |  {w}×{h}",
                text_color=Colors.TEXT_SECONDARY,
            )
        else:
            self._region_label.configure(
                text="Region: Full screen",
                text_color=Colors.TEXT_SECONDARY,
            )

    def show_placeholder(self, message: str = "No capture active"):
        """Show a placeholder message instead of a frame."""
        self._photo_image = None
        self._preview_label.configure(
            image="",
            text=message,
            text_color=Colors.TEXT_DISABLED,
        )
