"""
Chat companion UI panel for AI Game Coach.
Interactive chat sidebar with message bubbles, text input, and screenshot toggle.
"""

import time
import customtkinter as ctk
from typing import Optional, Callable

from ui.theme import Colors, Fonts, create_card_frame, create_label, blend_colors


class ChatPanel(ctk.CTkFrame):
    """
    Interactive chat companion panel.
    Shows chat bubbles with user messages (right-aligned) and AI responses
    (left-aligned), plus a text input bar at the bottom.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._include_screenshot = True

        # Callback for sending messages
        self._on_send: Optional[Callable[[str, bool], None]] = None

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=ctk.X, padx=4, pady=(4, 0))

        create_label(header, "💬 Chat Companion", style="heading").pack(
            side=ctk.LEFT, padx=8,
        )

        # Clear button
        self._clear_btn = ctk.CTkButton(
            header, text="Clear", width=60, height=28,
            fg_color="transparent", hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_SECONDARY, font=Fonts.small(),
            corner_radius=6, border_width=1, border_color=Colors.BORDER_SUBTLE,
            command=self._on_clear,
        )
        self._clear_btn.pack(side=ctk.RIGHT, padx=8)

        # Message count
        self._count_label = create_label(
            header, "",
            style="small", text_color=Colors.TEXT_DISABLED,
        )
        self._count_label.pack(side=ctk.RIGHT, padx=4)

        # ── Scrollable chat area ─────────────────────────────────────────
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
        self._add_system_message(
            "👋 Hey there! I'm your AI gaming companion.\n\n"
            "Ask me anything about your game — strategies, builds, "
            "what to do next, or what's happening on screen.\n\n"
            "I can see your screen when the 📸 toggle is on!"
        )

        # ── Input area ───────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color=Colors.BG_MEDIUM, corner_radius=12)
        input_frame.pack(fill=ctk.X, padx=4, pady=(0, 4))

        # Screenshot toggle
        self._screenshot_toggle = ctk.CTkButton(
            input_frame, text="📸", width=36, height=36,
            fg_color=blend_colors(Colors.ACCENT_BLUE, Colors.BG_MEDIUM, 0.2),
            hover_color=Colors.BG_HOVER,
            text_color=Colors.ACCENT_BLUE,
            font=(Fonts.FAMILY, 16),
            corner_radius=8,
            command=self._toggle_screenshot,
        )
        self._screenshot_toggle.pack(side=ctk.LEFT, padx=(8, 4), pady=8)

        # Text input
        self._input_entry = ctk.CTkEntry(
            input_frame,
            fg_color=Colors.BG_INPUT,
            border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_PRIMARY,
            font=Fonts.body(),
            placeholder_text="Ask me anything about the game...",
            height=36,
            corner_radius=8,
        )
        self._input_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=4, pady=8)
        self._input_entry.bind("<Return>", lambda e: self._send_message())

        # Send button
        self._send_btn = ctk.CTkButton(
            input_frame, text="➤", width=36, height=36,
            fg_color=Colors.ACCENT_BLUE,
            hover_color=Colors.ACCENT_GREEN,
            text_color=Colors.BG_DARKEST,
            font=(Fonts.FAMILY, 16, "bold"),
            corner_radius=8,
            command=self._send_message,
        )
        self._send_btn.pack(side=ctk.RIGHT, padx=(4, 8), pady=8)

        # Typing indicator (hidden by default)
        self._typing_frame = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
        self._typing_label = None

        # Track message count
        self._msg_count = 0

    # ── Public API ───────────────────────────────────────────────────────

    def set_send_callback(self, callback: Callable[[str, bool], None]):
        """Set the callback for sending messages: callback(text, include_screenshot)."""
        self._on_send = callback

    def add_user_message(self, text: str):
        """Add a user message bubble (right-aligned)."""
        self._create_bubble(text, is_user=True)
        self._msg_count += 1
        self._update_count()

    def add_ai_message(self, text: str):
        """Add an AI response bubble (left-aligned)."""
        self._hide_typing()
        self._create_bubble(text, is_user=False)
        self._msg_count += 1
        self._update_count()

    def add_system_message(self, text: str):
        """Add a system/error message."""
        self._hide_typing()
        self._add_system_message(text)

    def show_typing(self):
        """Show the typing indicator."""
        self._typing_frame.pack_forget()

        self._typing_frame = ctk.CTkFrame(
            self._scroll_frame, fg_color="transparent",
        )
        self._typing_frame.pack(fill=ctk.X, padx=4, pady=2, anchor="w")

        typing_bubble = ctk.CTkFrame(
            self._typing_frame,
            fg_color=Colors.BG_MEDIUM,
            corner_radius=12,
        )
        typing_bubble.pack(anchor="w", padx=(8, 60))

        self._typing_label = ctk.CTkLabel(
            typing_bubble,
            text="● ● ●",
            font=Fonts.body(),
            text_color=Colors.TEXT_DISABLED,
        )
        self._typing_label.pack(padx=16, pady=8)

        self._scroll_to_bottom()

    def hide_typing(self):
        """Hide the typing indicator."""
        self._hide_typing()

    def clear_messages(self):
        """Clear all messages."""
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._msg_count = 0
        self._update_count()
        self._add_system_message(
            "💬 Chat cleared. Ask me anything!"
        )

    # ── Private Methods ──────────────────────────────────────────────────

    def _create_bubble(self, text: str, is_user: bool):
        """Create a chat message bubble."""
        container = ctk.CTkFrame(
            self._scroll_frame, fg_color="transparent",
        )
        container.pack(fill=ctk.X, padx=4, pady=2)

        if is_user:
            # User bubble — right-aligned, accent color
            bubble = ctk.CTkFrame(
                container,
                fg_color=blend_colors(Colors.ACCENT_BLUE, Colors.BG_DARK, 0.13),
                corner_radius=12,
                border_width=1,
                border_color=blend_colors(Colors.ACCENT_BLUE, Colors.BG_DARK, 0.26),
            )
            bubble.pack(anchor="e", padx=(60, 8))

            # Timestamp
            time_label = ctk.CTkLabel(
                bubble,
                text=time.strftime("%H:%M"),
                font=(Fonts.FAMILY, 9),
                text_color=Colors.TEXT_DISABLED,
                anchor="e",
            )
            time_label.pack(fill=ctk.X, padx=12, pady=(8, 0))

            msg_label = ctk.CTkLabel(
                bubble,
                text=text,
                font=Fonts.body(),
                text_color=Colors.TEXT_PRIMARY,
                anchor="e",
                justify="right",
                wraplength=350,
            )
            msg_label.pack(padx=12, pady=(2, 10))

        else:
            # AI bubble — left-aligned, subtle background
            bubble = ctk.CTkFrame(
                container,
                fg_color=Colors.BG_MEDIUM,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER_SUBTLE,
            )
            bubble.pack(anchor="w", padx=(8, 60))

            # Header with AI label + timestamp
            header_frame = ctk.CTkFrame(bubble, fg_color="transparent")
            header_frame.pack(fill=ctk.X, padx=12, pady=(8, 0))

            ctk.CTkLabel(
                header_frame,
                text="🤖 AI",
                font=(Fonts.FAMILY, 10, "bold"),
                text_color=Colors.ACCENT_PURPLE,
                anchor="w",
            ).pack(side=ctk.LEFT)

            ctk.CTkLabel(
                header_frame,
                text=time.strftime("%H:%M"),
                font=(Fonts.FAMILY, 9),
                text_color=Colors.TEXT_DISABLED,
                anchor="e",
            ).pack(side=ctk.RIGHT)

            msg_label = ctk.CTkLabel(
                bubble,
                text=text,
                font=Fonts.body(),
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                justify="left",
                wraplength=350,
            )
            msg_label.pack(padx=12, pady=(4, 10))

        self._scroll_to_bottom()

    def _add_system_message(self, text: str):
        """Add a system/info message (centered, muted)."""
        container = ctk.CTkFrame(
            self._scroll_frame, fg_color="transparent",
        )
        container.pack(fill=ctk.X, padx=4, pady=4)

        bubble = ctk.CTkFrame(
            container,
            fg_color=blend_colors(Colors.BG_LIGHT, Colors.BG_DARK, 0.53),
            corner_radius=10,
        )
        bubble.pack(padx=20)

        msg_label = ctk.CTkLabel(
            bubble,
            text=text,
            font=Fonts.small(),
            text_color=Colors.TEXT_SECONDARY,
            justify="center",
            wraplength=350,
        )
        msg_label.pack(padx=16, pady=10)

    def _send_message(self):
        """Handle the send button click."""
        text = self._input_entry.get().strip()
        if not text:
            return

        # Clear input
        self._input_entry.delete(0, ctk.END)

        # Add to UI
        self.add_user_message(text)

        # Show typing
        self.show_typing()

        # Invoke callback
        if self._on_send:
            self._on_send(text, self._include_screenshot)

    def _toggle_screenshot(self):
        """Toggle whether screenshots are included with messages."""
        self._include_screenshot = not self._include_screenshot
        if self._include_screenshot:
            self._screenshot_toggle.configure(
                fg_color=blend_colors(Colors.ACCENT_BLUE, Colors.BG_MEDIUM, 0.2),
                text_color=Colors.ACCENT_BLUE,
            )
        else:
            self._screenshot_toggle.configure(
                fg_color="transparent",
                text_color=Colors.TEXT_DISABLED,
            )

    def _hide_typing(self):
        """Hide the typing indicator."""
        try:
            self._typing_frame.pack_forget()
            self._typing_frame.destroy()
        except Exception:
            pass
        self._typing_frame = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")

    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        try:
            self._scroll_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _update_count(self):
        """Update the message count label."""
        if self._msg_count > 0:
            self._count_label.configure(text=f"{self._msg_count} messages")
        else:
            self._count_label.configure(text="")

    def _on_clear(self):
        """Handle the clear button."""
        self.clear_messages()
