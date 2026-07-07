"""
AI coaching advice display panel for AI Game Coach.
Shows a scrollable feed of coaching messages with priority coloring and timestamps.
"""

import time
import customtkinter as ctk
from typing import List

from ui.theme import Colors, Fonts, create_card_frame, create_label


class CoachPanel(ctk.CTkFrame):
    """
    Main coaching display panel.
    Shows a scrollable feed of AI coaching messages with:
    - Color-coded priority levels
    - Timestamps
    - Auto-scroll with pause-on-hover
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._auto_scroll = True
        self._is_hovered = False

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=ctk.X, padx=4, pady=(4, 0))

        create_label(header, "🧠 AI Coach", style="heading").pack(side=ctk.LEFT, padx=8)

        # Clear button
        self._clear_btn = ctk.CTkButton(
            header, text="Clear", width=60, height=28,
            fg_color="transparent", hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_SECONDARY, font=Fonts.small(),
            corner_radius=6, border_width=1, border_color=Colors.BORDER_SUBTLE,
            command=self._on_clear,
        )
        self._clear_btn.pack(side=ctk.RIGHT, padx=8)

        # Export button
        self._export_btn = ctk.CTkButton(
            header, text="Export", width=60, height=28,
            fg_color="transparent", hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_SECONDARY, font=Fonts.small(),
            corner_radius=6, border_width=1, border_color=Colors.BORDER_SUBTLE,
            command=self._on_export,
        )
        self._export_btn.pack(side=ctk.RIGHT)

        # Message count
        self._count_label = create_label(
            header, "0 messages",
            style="small", text_color=Colors.TEXT_DISABLED,
        )
        self._count_label.pack(side=ctk.RIGHT, padx=12)

        # Scrollable message area
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Colors.BG_DARK,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            scrollbar_button_color=Colors.BG_LIGHT,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self._scroll_frame.pack(fill=ctk.BOTH, expand=True, padx=4, pady=8)

        # Welcome message
        self._add_welcome_message()

        # Track messages for export
        self._messages_data: List[dict] = []

        # Hover detection for auto-scroll pause
        self._scroll_frame.bind("<Enter>", lambda e: self._set_hover(True))
        self._scroll_frame.bind("<Leave>", lambda e: self._set_hover(False))

    def add_message(self, text: str, priority: str = "info", mode: str = "strategy"):
        """Add a new coaching message to the feed."""
        # Priority styling
        priority_config = {
            "critical": {"color": Colors.PRIORITY_CRITICAL, "emoji": "🔴", "border": Colors.ACCENT_RED},
            "important": {"color": Colors.PRIORITY_IMPORTANT, "emoji": "🟡", "border": Colors.ACCENT_YELLOW},
            "tip": {"color": Colors.PRIORITY_TIP, "emoji": "🟢", "border": Colors.ACCENT_GREEN},
            "info": {"color": Colors.PRIORITY_INFO, "emoji": "🔵", "border": Colors.ACCENT_BLUE},
        }
        style = priority_config.get(priority, priority_config["info"])

        # Message card
        msg_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=Colors.BG_MEDIUM,
            corner_radius=10,
            border_width=1,
            border_color=style["border"] + "44",  # Semi-transparent border
        )
        msg_card.pack(fill=ctk.X, padx=4, pady=3)

        # Priority indicator bar (left accent)
        accent_bar = ctk.CTkFrame(
            msg_card, fg_color=style["color"],
            width=3, corner_radius=2,
        )
        accent_bar.pack(side=ctk.LEFT, fill=ctk.Y, padx=(8, 0), pady=8)

        # Content area
        content = ctk.CTkFrame(msg_card, fg_color="transparent")
        content.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=10, pady=8)

        # Timestamp
        timestamp = time.strftime("%H:%M:%S")
        time_label = ctk.CTkLabel(
            content, text=f"{style['emoji']} {timestamp}",
            font=Fonts.small(), text_color=Colors.TEXT_DISABLED,
            anchor="w",
        )
        time_label.pack(fill=ctk.X)

        # Message text
        msg_label = ctk.CTkLabel(
            content, text=text,
            font=Fonts.body(), text_color=Colors.TEXT_PRIMARY,
            anchor="w", justify="left",
            wraplength=400,
        )
        msg_label.pack(fill=ctk.X, pady=(2, 0))

        # Store for export
        self._messages_data.append({
            "time": timestamp,
            "priority": priority,
            "mode": mode,
            "text": text,
        })

        # Update count
        self._count_label.configure(text=f"{len(self._messages_data)} messages")

        # Auto-scroll to bottom
        if self._auto_scroll and not self._is_hovered:
            self._scroll_frame._parent_canvas.yview_moveto(1.0)

    def clear_messages(self):
        """Clear all messages from the feed."""
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._messages_data.clear()
        self._count_label.configure(text="0 messages")
        self._add_welcome_message()

    # ── Private Helpers ──────────────────────────────────────────────────

    def _add_welcome_message(self):
        """Add the initial welcome message."""
        welcome_card = ctk.CTkFrame(
            self._scroll_frame,
            fg_color=Colors.BG_MEDIUM,
            corner_radius=10,
            border_width=1,
            border_color=Colors.ACCENT_BLUE + "33",
        )
        welcome_card.pack(fill=ctk.X, padx=4, pady=3)

        welcome_text = ctk.CTkLabel(
            welcome_card,
            text=(
                "🎮 Welcome to AI Game Coach!\n\n"
                "1. Set your Gemini API key in Settings\n"
                "2. Select a screen region to capture\n"
                "3. Hit Start Coaching to begin!\n\n"
                "The AI will watch your screen and provide\n"
                "real-time coaching advice."
            ),
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
            justify="left",
        )
        welcome_text.pack(padx=16, pady=16)

    def _set_hover(self, hovered: bool):
        self._is_hovered = hovered

    def _on_clear(self):
        self.clear_messages()

    def _on_export(self):
        """Export coaching log to a text file."""
        if not self._messages_data:
            return

        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Coaching Log",
                initialfile=f"coaching_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            )
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("AI Game Coach — Session Log\n")
                    f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    for msg in self._messages_data:
                        priority_map = {
                            "critical": "🔴 CRITICAL",
                            "important": "🟡 IMPORTANT",
                            "tip": "🟢 TIP",
                            "info": "🔵 INFO",
                        }
                        p = priority_map.get(msg["priority"], "INFO")
                        f.write(f"[{msg['time']}] [{p}] ({msg['mode']})\n")
                        f.write(f"{msg['text']}\n\n")
        except Exception:
            pass

    @property
    def on_clear_callback(self):
        return None

    @on_clear_callback.setter
    def on_clear_callback(self, callback):
        """Set an external callback for when messages are cleared."""
        self._external_clear = callback
        original = self._on_clear
        def wrapped():
            original()
            if callback:
                callback()
        self._on_clear = wrapped
        self._clear_btn.configure(command=wrapped)
