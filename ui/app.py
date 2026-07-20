"""
Main application window for AI Game Coach.
Brings together all UI components with sidebar navigation.
v2: Adds chat companion, voice controls, overlay toggle, and audio status.
"""

import customtkinter as ctk
from typing import Optional

from core.config import config
from core.coach import GameCoach, CoachMessage
from core.chat import ChatEngine, ChatMessage
from ui.theme import (
    Colors, Fonts, apply_theme,
    create_card_frame, create_label, create_accent_button, create_outline_button,
)
from ui.coach_panel import CoachPanel
from ui.capture_preview import CapturePreview
from ui.settings_panel import SettingsPanel
from ui.chat_panel import ChatPanel
from ui.region_selector import RegionSelector


class App(ctk.CTk):
    """Main AI Game Coach application window."""

    APP_TITLE = "AI Game Coach"
    DEFAULT_WIDTH = 1100
    DEFAULT_HEIGHT = 750

    def __init__(self):
        super().__init__()

        # Apply theme
        apply_theme()

        # Window config
        self.title(self.APP_TITLE)
        self.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.minsize(900, 600)
        self.configure(fg_color=Colors.BG_DARKEST)

        # Initialize the coaching engine
        self.coach = GameCoach()
        self.coach.on_message(self._on_coach_message)
        self.coach.on_status_change(self._on_status_change)
        self.coach.on_frame_captured(self._on_frame_captured)
        self.coach.on_overlay_message(self._on_overlay_message)

        # Initialize the chat engine
        self.chat_engine = ChatEngine()
        self.chat_engine.set_analyzer(self.coach.analyzer)
        self.chat_engine.set_screenshot_provider(self._get_current_screenshot)
        self.chat_engine.on_response(self._on_chat_response)
        self.chat_engine.on_typing(self._on_chat_typing)

        # Overlay (lazy-loaded)
        self._overlay = None

        # Current view
        self._current_view = "dashboard"

        # Build the UI
        self._build_layout()

        # Start periodic preview updates
        self._update_preview_loop()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Keyboard shortcuts
        self.bind("<Control-m>", lambda e: self._toggle_voice_mute())
        self.bind("<Control-o>", lambda e: self._toggle_overlay())

    # ── Layout ───────────────────────────────────────────────────────────

    def _build_layout(self):
        """Build the main application layout."""

        # ── Sidebar ──────────────────────────────────────────────────────
        self._sidebar = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, width=220, corner_radius=0)
        self._sidebar.pack(side=ctk.LEFT, fill=ctk.Y)
        self._sidebar.pack_propagate(False)

        # Logo / Title
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill=ctk.X, padx=16, pady=(20, 8))

        title_label = ctk.CTkLabel(
            logo_frame, text="🎮 AI Game Coach",
            font=(Fonts.FAMILY, 18, "bold"),
            text_color=Colors.ACCENT_BLUE,
        )
        title_label.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            logo_frame, text="Full AI Gaming Companion",
            font=Fonts.small(), text_color=Colors.TEXT_DISABLED,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Divider
        ctk.CTkFrame(self._sidebar, fg_color=Colors.BORDER_SUBTLE, height=1).pack(
            fill=ctk.X, padx=16, pady=12,
        )

        # Navigation buttons
        self._nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("chat", "💬  Chat"),
            ("settings", "⚙️  Settings"),
        ]

        for view_id, label in nav_items:
            btn = ctk.CTkButton(
                self._sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_PRIMARY,
                font=Fonts.body(),
                height=40,
                corner_radius=8,
                command=lambda vid=view_id: self._switch_view(vid),
            )
            btn.pack(fill=ctk.X, padx=12, pady=2)
            self._nav_buttons[view_id] = btn

        # Spacer
        ctk.CTkFrame(self._sidebar, fg_color="transparent").pack(fill=ctk.BOTH, expand=True)

        # ── Feature toggles ──────────────────────────────────────────────
        toggles_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        toggles_frame.pack(fill=ctk.X, padx=12, pady=(0, 4))

        # Voice toggle
        self._voice_btn = create_outline_button(
            toggles_frame, "🔇 Voice Off",
            command=self._toggle_voice_mute,
        )
        self._voice_btn.pack(fill=ctk.X, pady=2)

        # Overlay toggle
        self._overlay_btn = create_outline_button(
            toggles_frame, "🖥️ Overlay Off",
            command=self._toggle_overlay,
        )
        self._overlay_btn.pack(fill=ctk.X, pady=2)

        # ── Coach controls ───────────────────────────────────────────────
        controls_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        controls_frame.pack(fill=ctk.X, padx=12, pady=(0, 8))

        # Region select button
        self._region_btn = create_outline_button(
            controls_frame, "📐 Select Region",
            command=self._select_region,
        )
        self._region_btn.pack(fill=ctk.X, pady=4)

        # Start/Stop coaching button
        self._coach_btn = create_accent_button(
            controls_frame, "▶ Start Coaching",
            command=self._toggle_coaching,
            color=Colors.ACCENT_GREEN,
        )
        self._coach_btn.pack(fill=ctk.X, pady=4)

        # Status bar
        self._status_frame = ctk.CTkFrame(
            self._sidebar, fg_color=Colors.BG_MEDIUM,
            corner_radius=8, height=50,
        )
        self._status_frame.pack(fill=ctk.X, padx=12, pady=(4, 16))
        self._status_frame.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            self._status_frame,
            text="⏸️ Ready",
            font=Fonts.small(),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=180,
        )
        self._status_label.pack(padx=8, pady=8, anchor="w")

        # ── Main Content Area ────────────────────────────────────────────
        self._content = ctk.CTkFrame(self, fg_color=Colors.BG_DARKEST, corner_radius=0)
        self._content.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        # Create views
        self._views = {}
        self._build_dashboard_view()
        self._build_chat_view()
        self._build_settings_view()

        # Show default view
        self._switch_view("dashboard")

    # ── Dashboard View ───────────────────────────────────────────────────

    def _build_dashboard_view(self):
        """Build the main dashboard view with coach panel and capture preview."""
        view = ctk.CTkFrame(self._content, fg_color="transparent")
        self._views["dashboard"] = view

        # Split: left = coach panel, right = preview + info

        # Right sidebar (preview + stats)
        right_panel = ctk.CTkFrame(view, fg_color="transparent", width=350)
        right_panel.pack(side=ctk.RIGHT, fill=ctk.Y, padx=(0, 4), pady=4)
        right_panel.pack_propagate(False)

        # Capture preview
        self._capture_preview = CapturePreview(right_panel)
        self._capture_preview.pack(fill=ctk.X)

        # Game info card
        info_card = create_card_frame(right_panel)
        info_card.pack(fill=ctk.X, padx=4, pady=4)

        create_label(info_card, "📋 Session Info", style="body_bold").pack(
            anchor="w", padx=12, pady=(12, 8),
        )

        self._game_info_label = create_label(
            info_card, "Game: General",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._game_info_label.pack(anchor="w", padx=12, pady=2)

        self._mode_info_label = create_label(
            info_card, "Mode: Strategy Advisor",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._mode_info_label.pack(anchor="w", padx=12, pady=2)

        self._model_info_label = create_label(
            info_card, "Model: gemini-2.5-flash",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._model_info_label.pack(anchor="w", padx=12, pady=2)

        self._audio_info_label = create_label(
            info_card, "Audio: Enabled",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._audio_info_label.pack(anchor="w", padx=12, pady=2)

        self._calls_info_label = create_label(
            info_card, "API Calls: 0",
            style="small", text_color=Colors.TEXT_SECONDARY,
        )
        self._calls_info_label.pack(anchor="w", padx=12, pady=(2, 12))

        # Tips card
        tips_card = create_card_frame(right_panel)
        tips_card.pack(fill=ctk.X, padx=4, pady=4)

        create_label(tips_card, "💡 Quick Tips", style="body_bold").pack(
            anchor="w", padx=12, pady=(12, 8),
        )

        tips = [
            "• Select the game window area for best results",
            "• 🎤 Audio captures game sounds automatically",
            "• 💬 Chat tab: ask AI questions mid-game",
            "• 🖥️ Overlay: tips shown over your game",
            "• 🔊 Voice: AI reads advice aloud",
            "• Ctrl+M to mute voice, Ctrl+O for overlay",
        ]
        for tip in tips:
            create_label(
                tips_card, tip,
                style="small", text_color=Colors.TEXT_DISABLED,
            ).pack(anchor="w", padx=12, pady=1)

        ctk.CTkFrame(tips_card, fg_color="transparent", height=12).pack()

        # Left panel (coach messages) — fills remaining space
        self._coach_panel = CoachPanel(view)
        self._coach_panel.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=4, pady=4)

        # Wire up the clear callback
        self._coach_panel.on_clear_callback = lambda: self.coach.clear_messages()

    # ── Chat View ────────────────────────────────────────────────────────

    def _build_chat_view(self):
        """Build the chat companion view."""
        view = ctk.CTkFrame(self._content, fg_color="transparent")
        self._views["chat"] = view

        # Chat panel
        self._chat_panel = ChatPanel(view)
        self._chat_panel.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

        # Wire up send callback
        self._chat_panel.set_send_callback(self._on_chat_send)

    # ── Settings View ────────────────────────────────────────────────────

    def _build_settings_view(self):
        """Build the settings view."""
        view = ctk.CTkFrame(self._content, fg_color="transparent")
        self._views["settings"] = view

        # Header
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill=ctk.X, padx=16, pady=(16, 8))

        create_label(header, "⚙️ Settings", style="title").pack(anchor="w")
        create_label(
            header, "Configure your AI coaching experience",
            style="small", text_color=Colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 0))

        # Settings panel
        self._settings_panel = SettingsPanel(
            view, on_settings_changed=self._on_settings_changed,
        )
        self._settings_panel.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

    # ── View Switching ───────────────────────────────────────────────────

    def _switch_view(self, view_id: str):
        """Switch the active content view."""
        # Hide all views
        for vid, view in self._views.items():
            view.pack_forget()

        # Show selected view
        if view_id in self._views:
            self._views[view_id].pack(fill=ctk.BOTH, expand=True)

        # Update nav button styling
        for vid, btn in self._nav_buttons.items():
            if vid == view_id:
                btn.configure(fg_color=Colors.BG_LIGHT, text_color=Colors.ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=Colors.TEXT_PRIMARY)

        self._current_view = view_id

        # Refresh session info when switching to dashboard
        if view_id == "dashboard":
            self._refresh_session_info()

    # ── Coaching Control ─────────────────────────────────────────────────

    def _toggle_coaching(self):
        """Start or stop the coaching pipeline."""
        if self.coach.is_coaching:
            self.coach.stop_coaching()
            self._coach_btn.configure(text="▶ Start Coaching", fg_color=Colors.ACCENT_GREEN)
            # Update overlay
            if self._overlay:
                self._overlay.update_status(False)
        else:
            if not config.is_api_key_set:
                self._on_status_change("❌ Set your API key in Settings first!")
                self._switch_view("settings")
                return
            self.coach.start_coaching()
            self._coach_btn.configure(text="⏹ Stop Coaching", fg_color=Colors.ACCENT_RED)
            # Update overlay
            if self._overlay and self._overlay._visible:
                self._overlay.update_status(True)

    def _select_region(self):
        """Open the region selector overlay."""
        # Minimize the app first
        self.iconify()
        self.update()

        # Short delay to let the window minimize
        import time
        time.sleep(0.3)

        selector = RegionSelector(on_selected=self._on_region_selected)
        result = selector.show()

        # Restore the app
        self.deiconify()

        if result:
            self._on_region_selected(result)

    def _on_region_selected(self, region):
        """Handle a new capture region being selected."""
        config.set("capture_region", list(region))
        self._capture_preview.update_region_info(region)
        self._on_status_change(f"📐 Region set: {region[2]-region[0]}×{region[3]-region[1]}")

        # Take a test screenshot
        self.coach.capture.region = region
        frame = self.coach.capture.grab_single()
        if frame:
            self._capture_preview.update_preview(frame)

    # ── Voice Control ────────────────────────────────────────────────────

    def _toggle_voice_mute(self):
        """Toggle voice mute/unmute."""
        voice = self.coach.voice
        if voice and voice.is_available:
            if voice.is_running:
                voice.is_muted = not voice.is_muted
                if voice.is_muted:
                    self._voice_btn.configure(text="🔇 Voice Muted")
                else:
                    self._voice_btn.configure(text="🔊 Voice On")
            else:
                # Start the voice engine
                voice.start()
                config.set("voice_enabled", True)
                self._voice_btn.configure(text="🔊 Voice On")
        else:
            self._on_status_change("⚠️ Voice engine not available (install pyttsx3)")

    # ── Overlay Control ──────────────────────────────────────────────────

    def _toggle_overlay(self):
        """Toggle the overlay HUD."""
        if self._overlay is None:
            try:
                from ui.overlay import OverlayHUD
                self._overlay = OverlayHUD(self)
            except Exception as e:
                self._on_status_change(f"⚠️ Overlay failed: {str(e)[:40]}")
                return

        self._overlay.toggle()
        if self._overlay._visible:
            self._overlay_btn.configure(text="🖥️ Overlay On")
            config.set("overlay_enabled", True)
            if self.coach.is_coaching:
                self._overlay.update_status(True, self.coach.capture.actual_fps)
        else:
            self._overlay_btn.configure(text="🖥️ Overlay Off")
            config.set("overlay_enabled", False)

    # ── Callbacks ────────────────────────────────────────────────────────

    def _on_coach_message(self, message: CoachMessage):
        """Handle a new coaching message from the AI."""
        # Must update UI from the main thread
        self.after(0, lambda: self._coach_panel.add_message(
            text=message.text,
            priority=message.priority,
            mode=message.mode,
        ))

    def _on_status_change(self, status: str):
        """Handle a status update."""
        self.after(0, lambda: self._status_label.configure(text=status))

    def _on_frame_captured(self):
        """Handle a new frame being captured (triggers preview update)."""
        pass  # Preview is updated via the periodic loop

    def _on_overlay_message(self, text: str, priority: str):
        """Forward a coaching message to the overlay."""
        if self._overlay and self._overlay._visible:
            self.after(0, lambda: self._overlay.show_message(text, priority))

    def _on_settings_changed(self):
        """Handle settings being saved."""
        self._refresh_session_info()
        self._on_status_change("✅ Settings saved!")

    # ── Chat Callbacks ───────────────────────────────────────────────────

    def _on_chat_send(self, text: str, include_screenshot: bool):
        """Handle a chat message being sent from the UI."""
        self.chat_engine.send_message(text, include_screenshot)

    def _on_chat_response(self, message: ChatMessage):
        """Handle a chat response from the AI."""
        def _update():
            if message.role == ChatMessage.ROLE_AI:
                self._chat_panel.add_ai_message(message.text)
            elif message.role == ChatMessage.ROLE_SYSTEM:
                self._chat_panel.add_system_message(message.text)
        self.after(0, _update)

    def _on_chat_typing(self, is_typing: bool):
        """Handle the chat typing indicator."""
        def _update():
            if is_typing:
                self._chat_panel.show_typing()
            else:
                self._chat_panel.hide_typing()
        self.after(0, _update)

    def _get_current_screenshot(self) -> bytes:
        """Get the current screenshot as JPEG bytes for the chat companion."""
        return self.coach.capture.get_latest_jpeg(resize_for_api=True)

    # ── Preview Update Loop ──────────────────────────────────────────────

    def _update_preview_loop(self):
        """Periodically update the capture preview and session info."""
        if self.coach.capture.is_running:
            frame = self.coach.capture.latest_frame
            if frame:
                self._capture_preview.update_preview(frame)
            self._capture_preview.update_status(True, self.coach.capture.actual_fps)
        else:
            self._capture_preview.update_status(False)

        # Update API call count
        if hasattr(self, '_calls_info_label'):
            calls = self.coach.analyzer.total_calls
            self._calls_info_label.configure(text=f"API Calls: {calls}")

        # Update overlay status
        if self._overlay and self._overlay._visible and self.coach.is_coaching:
            self._overlay.update_status(True, self.coach.capture.actual_fps)

        # Schedule next update (500ms)
        self.after(500, self._update_preview_loop)

    def _refresh_session_info(self):
        """Refresh the session info panel."""
        if hasattr(self, '_game_info_label'):
            game = config.get("game_name", "General")
            self._game_info_label.configure(text=f"Game: {game}")

        if hasattr(self, '_mode_info_label'):
            mode_map = {
                "realtime": "⚡ Real-time Callouts",
                "strategy": "🎯 Strategy Advisor",
                "post_analysis": "📊 Post-Play Review",
            }
            mode = config.get("coaching_mode", "strategy")
            self._mode_info_label.configure(text=f"Mode: {mode_map.get(mode, mode)}")

        if hasattr(self, '_model_info_label'):
            model = config.get("gemini_model", "gemini-2.5-flash")
            self._model_info_label.configure(text=f"Model: {model}")

        if hasattr(self, '_audio_info_label'):
            audio_on = config.get("audio_enabled", True)
            self._audio_info_label.configure(
                text=f"Audio: {'Enabled' if audio_on else 'Disabled'}"
            )

    # ── Cleanup ──────────────────────────────────────────────────────────

    def _on_close(self):
        """Handle window close — stop coaching and clean up."""
        if self.coach.is_coaching:
            self.coach.stop_coaching()
        if self._overlay:
            try:
                self._overlay.destroy()
            except Exception:
                pass
        self.destroy()
