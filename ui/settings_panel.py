"""
Settings panel for AI Game Coach.
Configuration UI for API key, game settings, coaching mode, capture, audio,
voice, overlay, and plugin options.
v2: Adds audio, voice, overlay, and plugin settings sections.
"""

import customtkinter as ctk
from typing import Optional, Callable

from core.config import config
from ui.theme import Colors, Fonts, create_card_frame, create_label, create_accent_button


class SettingsPanel(ctk.CTkFrame):
    """
    Settings and configuration panel.
    Provides UI controls for all app settings.
    """

    def __init__(self, parent, on_settings_changed: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_settings_changed = on_settings_changed

        # Scrollable container
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_LIGHT,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self._scroll.pack(fill=ctk.BOTH, expand=True, padx=4, pady=4)

        self._build_api_section()
        self._build_game_section()
        self._build_coaching_section()
        self._build_capture_section()
        self._build_audio_section()
        self._build_voice_section()
        self._build_overlay_section()
        self._build_advanced_section()

        # Load current values
        self._load_settings()

    # ── API Key Section ──────────────────────────────────────────────────

    def _build_api_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🔑 API Configuration", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        # API Key input
        key_frame = ctk.CTkFrame(card, fg_color="transparent")
        key_frame.pack(fill=ctk.X, padx=16, pady=(0, 4))

        create_label(key_frame, "Gemini API Key", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        input_row = ctk.CTkFrame(key_frame, fg_color="transparent")
        input_row.pack(fill=ctk.X, pady=(4, 0))

        self._api_key_entry = ctk.CTkEntry(
            input_row, show="•",
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.mono(),
            placeholder_text="Enter your Gemini API key...",
            height=36, corner_radius=8,
        )
        self._api_key_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 8))

        self._show_key_btn = ctk.CTkButton(
            input_row, text="👁", width=36, height=36,
            fg_color=Colors.BG_LIGHT, hover_color=Colors.BG_HOVER,
            font=Fonts.body(), corner_radius=8,
            command=self._toggle_key_visibility,
        )
        self._show_key_btn.pack(side=ctk.RIGHT)

        # API status
        self._api_status = create_label(
            card, "Status: Not configured",
            style="small", text_color=Colors.TEXT_DISABLED,
        )
        self._api_status.pack(anchor="w", padx=16, pady=(4, 4))

        # Test button
        self._test_btn = create_accent_button(
            card, "Test Connection", command=self._test_api,
        )
        self._test_btn.pack(anchor="w", padx=16, pady=(4, 16))

    # ── Game Section ─────────────────────────────────────────────────────

    def _build_game_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🎮 Game Settings", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        # Game name
        name_frame = ctk.CTkFrame(card, fg_color="transparent")
        name_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        create_label(name_frame, "Game Name", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        self._game_name_entry = ctk.CTkEntry(
            name_frame,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            placeholder_text="e.g., Valorant, League of Legends, Minecraft...",
            height=36, corner_radius=8,
        )
        self._game_name_entry.pack(fill=ctk.X, pady=(4, 0))

        # Game genre
        genre_frame = ctk.CTkFrame(card, fg_color="transparent")
        genre_frame.pack(fill=ctk.X, padx=16, pady=(0, 16))

        create_label(genre_frame, "Game Genre", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        self._genre_var = ctk.StringVar(value="any")
        self._genre_menu = ctk.CTkOptionMenu(
            genre_frame,
            values=["any", "fps", "moba", "rts", "rpg", "card", "battle_royale", "puzzle", "sports", "sandbox"],
            variable=self._genre_var,
            fg_color=Colors.BG_INPUT, button_color=Colors.BG_LIGHT,
            button_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            dropdown_fg_color=Colors.BG_MEDIUM,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            dropdown_hover_color=Colors.BG_HOVER,
            height=36, corner_radius=8,
        )
        self._genre_menu.pack(fill=ctk.X, pady=(4, 0))

    # ── Coaching Section ─────────────────────────────────────────────────

    def _build_coaching_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🧠 Coaching Mode", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        # Mode selector
        self._mode_var = ctk.StringVar(value="strategy")
        modes = [
            ("⚡ Real-time Callouts", "realtime",
             "Quick, actionable observations during gameplay"),
            ("🎯 Strategy Advisor", "strategy",
             "Deeper strategic analysis with reasoning"),
            ("📊 Post-Play Review", "post_analysis",
             "Comprehensive review after a session"),
        ]

        for label, value, desc in modes:
            mode_frame = ctk.CTkFrame(card, fg_color="transparent")
            mode_frame.pack(fill=ctk.X, padx=16, pady=2)

            rb = ctk.CTkRadioButton(
                mode_frame, text=label, variable=self._mode_var, value=value,
                fg_color=Colors.ACCENT_BLUE, hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
                border_color=Colors.BORDER_SUBTLE,
            )
            rb.pack(anchor="w")

            desc_label = create_label(
                mode_frame, desc,
                style="small", text_color=Colors.TEXT_DISABLED,
            )
            desc_label.pack(anchor="w", padx=(28, 0))

        # Custom instructions
        instr_frame = ctk.CTkFrame(card, fg_color="transparent")
        instr_frame.pack(fill=ctk.X, padx=16, pady=(12, 16))

        create_label(instr_frame, "Custom Focus / Instructions", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        self._custom_instr = ctk.CTkTextbox(
            instr_frame, height=80,
            fg_color=Colors.BG_INPUT, border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            corner_radius=8, border_width=1,
        )
        self._custom_instr.pack(fill=ctk.X, pady=(4, 0))

    # ── Capture Section ──────────────────────────────────────────────────

    def _build_capture_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "📸 Capture Settings", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        # Capture FPS slider
        fps_frame = ctk.CTkFrame(card, fg_color="transparent")
        fps_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        fps_header = ctk.CTkFrame(fps_frame, fg_color="transparent")
        fps_header.pack(fill=ctk.X)

        create_label(fps_header, "Capture FPS", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._fps_value_label = create_label(fps_header, "2", style="small",
                                              text_color=Colors.ACCENT_BLUE)
        self._fps_value_label.pack(side=ctk.RIGHT)

        self._fps_slider = ctk.CTkSlider(
            fps_frame, from_=1, to=10, number_of_steps=9,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_fps_change,
        )
        self._fps_slider.pack(fill=ctk.X, pady=(4, 0))

        # Analysis interval slider
        interval_frame = ctk.CTkFrame(card, fg_color="transparent")
        interval_frame.pack(fill=ctk.X, padx=16, pady=(0, 16))

        interval_header = ctk.CTkFrame(interval_frame, fg_color="transparent")
        interval_header.pack(fill=ctk.X)

        create_label(interval_header, "AI Analysis Interval (sec)", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._interval_value_label = create_label(interval_header, "3.0s", style="small",
                                                   text_color=Colors.ACCENT_BLUE)
        self._interval_value_label.pack(side=ctk.RIGHT)

        self._interval_slider = ctk.CTkSlider(
            interval_frame, from_=1, to=15, number_of_steps=14,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_interval_change,
        )
        self._interval_slider.pack(fill=ctk.X, pady=(4, 0))

    # ── Audio Section (v2) ───────────────────────────────────────────────

    def _build_audio_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🎤 Audio Capture", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        create_label(
            card, "Captures system audio (what you hear) via WASAPI loopback",
            style="small", text_color=Colors.TEXT_DISABLED,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # Enable toggle
        toggle_frame = ctk.CTkFrame(card, fg_color="transparent")
        toggle_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        self._audio_enabled_var = ctk.BooleanVar(value=True)
        self._audio_toggle = ctk.CTkSwitch(
            toggle_frame, text="Enable Audio Capture",
            variable=self._audio_enabled_var,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_GREEN,
            button_color=Colors.ACCENT_BLUE,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
        )
        self._audio_toggle.pack(anchor="w")

        # Buffer duration slider
        buf_frame = ctk.CTkFrame(card, fg_color="transparent")
        buf_frame.pack(fill=ctk.X, padx=16, pady=(0, 16))

        buf_header = ctk.CTkFrame(buf_frame, fg_color="transparent")
        buf_header.pack(fill=ctk.X)

        create_label(buf_header, "Audio Buffer (seconds)", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._audio_buf_label = create_label(buf_header, "5.0s", style="small",
                                              text_color=Colors.ACCENT_BLUE)
        self._audio_buf_label.pack(side=ctk.RIGHT)

        self._audio_buf_slider = ctk.CTkSlider(
            buf_frame, from_=1, to=15, number_of_steps=14,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_audio_buf_change,
        )
        self._audio_buf_slider.pack(fill=ctk.X, pady=(4, 0))

    # ── Voice Section (v2) ───────────────────────────────────────────────

    def _build_voice_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🔊 Voice Commentary", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        create_label(
            card, "AI reads coaching advice aloud using text-to-speech",
            style="small", text_color=Colors.TEXT_DISABLED,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # Enable toggle
        toggle_frame = ctk.CTkFrame(card, fg_color="transparent")
        toggle_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        self._voice_enabled_var = ctk.BooleanVar(value=False)
        self._voice_toggle = ctk.CTkSwitch(
            toggle_frame, text="Enable Voice Commentary",
            variable=self._voice_enabled_var,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_GREEN,
            button_color=Colors.ACCENT_BLUE,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
        )
        self._voice_toggle.pack(anchor="w")

        # Speed slider
        speed_frame = ctk.CTkFrame(card, fg_color="transparent")
        speed_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        speed_header = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_header.pack(fill=ctk.X)

        create_label(speed_header, "Speech Speed", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._voice_speed_label = create_label(speed_header, "1.2x", style="small",
                                                text_color=Colors.ACCENT_BLUE)
        self._voice_speed_label.pack(side=ctk.RIGHT)

        self._voice_speed_slider = ctk.CTkSlider(
            speed_frame, from_=0.5, to=3.0, number_of_steps=25,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_voice_speed_change,
        )
        self._voice_speed_slider.pack(fill=ctk.X, pady=(4, 0))

        # Volume slider
        vol_frame = ctk.CTkFrame(card, fg_color="transparent")
        vol_frame.pack(fill=ctk.X, padx=16, pady=(0, 16))

        vol_header = ctk.CTkFrame(vol_frame, fg_color="transparent")
        vol_header.pack(fill=ctk.X)

        create_label(vol_header, "Voice Volume", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._voice_vol_label = create_label(vol_header, "80%", style="small",
                                              text_color=Colors.ACCENT_BLUE)
        self._voice_vol_label.pack(side=ctk.RIGHT)

        self._voice_vol_slider = ctk.CTkSlider(
            vol_frame, from_=0, to=1.0, number_of_steps=20,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_voice_vol_change,
        )
        self._voice_vol_slider.pack(fill=ctk.X, pady=(4, 0))

    # ── Overlay Section (v2) ─────────────────────────────────────────────

    def _build_overlay_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "🖥️ Overlay HUD", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        create_label(
            card, "Shows coaching tips directly over your game (click-through)",
            style="small", text_color=Colors.TEXT_DISABLED,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # Position
        pos_frame = ctk.CTkFrame(card, fg_color="transparent")
        pos_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        create_label(pos_frame, "Overlay Position", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        self._overlay_pos_var = ctk.StringVar(value="bottom")
        self._overlay_pos_menu = ctk.CTkOptionMenu(
            pos_frame,
            values=["top", "bottom", "top_right", "bottom_right"],
            variable=self._overlay_pos_var,
            fg_color=Colors.BG_INPUT, button_color=Colors.BG_LIGHT,
            button_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            dropdown_fg_color=Colors.BG_MEDIUM,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            dropdown_hover_color=Colors.BG_HOVER,
            height=36, corner_radius=8,
        )
        self._overlay_pos_menu.pack(fill=ctk.X, pady=(4, 0))

        # Opacity slider
        opacity_frame = ctk.CTkFrame(card, fg_color="transparent")
        opacity_frame.pack(fill=ctk.X, padx=16, pady=(0, 16))

        opacity_header = ctk.CTkFrame(opacity_frame, fg_color="transparent")
        opacity_header.pack(fill=ctk.X)

        create_label(opacity_header, "Overlay Opacity", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._overlay_opacity_label = create_label(opacity_header, "85%", style="small",
                                                    text_color=Colors.ACCENT_BLUE)
        self._overlay_opacity_label.pack(side=ctk.RIGHT)

        self._overlay_opacity_slider = ctk.CTkSlider(
            opacity_frame, from_=0.3, to=1.0, number_of_steps=14,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_overlay_opacity_change,
        )
        self._overlay_opacity_slider.pack(fill=ctk.X, pady=(4, 0))

    # ── Advanced Section ─────────────────────────────────────────────────

    def _build_advanced_section(self):
        card = create_card_frame(self._scroll)
        card.pack(fill=ctk.X, pady=(0, 8))

        create_label(card, "⚙️ Advanced", style="heading").pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        # Model selection
        model_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        create_label(model_frame, "Gemini Model", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        self._model_var = ctk.StringVar(value="gemini-2.5-flash")
        self._model_menu = ctk.CTkOptionMenu(
            model_frame,
            values=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
            variable=self._model_var,
            fg_color=Colors.BG_INPUT, button_color=Colors.BG_LIGHT,
            button_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            dropdown_fg_color=Colors.BG_MEDIUM,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            dropdown_hover_color=Colors.BG_HOVER,
            height=36, corner_radius=8,
        )
        self._model_menu.pack(fill=ctk.X, pady=(4, 0))

        # Context window size
        ctx_frame = ctk.CTkFrame(card, fg_color="transparent")
        ctx_frame.pack(fill=ctk.X, padx=16, pady=(0, 8))

        ctx_header = ctk.CTkFrame(ctx_frame, fg_color="transparent")
        ctx_header.pack(fill=ctk.X)

        create_label(ctx_header, "Context History (messages)", style="small",
                     text_color=Colors.TEXT_SECONDARY).pack(side=ctk.LEFT)

        self._ctx_value_label = create_label(ctx_header, "10", style="small",
                                              text_color=Colors.ACCENT_BLUE)
        self._ctx_value_label.pack(side=ctk.RIGHT)

        self._ctx_slider = ctk.CTkSlider(
            ctx_frame, from_=2, to=20, number_of_steps=18,
            fg_color=Colors.BG_INPUT, progress_color=Colors.ACCENT_BLUE,
            button_color=Colors.ACCENT_BLUE, button_hover_color=Colors.ACCENT_GREEN,
            command=self._on_ctx_change,
        )
        self._ctx_slider.pack(fill=ctk.X, pady=(4, 0))

        # Save button
        save_frame = ctk.CTkFrame(card, fg_color="transparent")
        save_frame.pack(fill=ctk.X, padx=16, pady=(8, 16))

        create_accent_button(
            save_frame, "💾 Save Settings",
            command=self._save_settings,
            color=Colors.ACCENT_GREEN,
        ).pack(fill=ctk.X)

    # ── Settings Load / Save ─────────────────────────────────────────────

    def _load_settings(self):
        """Load current settings into the UI controls."""
        # API key
        api_key = config.api_key
        if api_key and api_key != "your_api_key_here":
            self._api_key_entry.insert(0, api_key)
            self._api_status.configure(
                text="Status: Key configured ✓",
                text_color=Colors.STATUS_ONLINE,
            )

        # Game settings
        game_name = config.get("game_name", "General")
        self._game_name_entry.insert(0, game_name)

        genre = config.get("game_genre", "any")
        self._genre_var.set(genre)

        # Coaching mode
        mode = config.get("coaching_mode", "strategy")
        self._mode_var.set(mode)

        # Custom instructions
        custom = config.get("custom_instructions", "")
        if custom:
            self._custom_instr.insert("1.0", custom)

        # Capture settings
        fps = config.get("capture_fps", 2)
        self._fps_slider.set(fps)
        self._fps_value_label.configure(text=str(int(fps)))

        interval = config.get("analysis_interval", 3.0)
        self._interval_slider.set(interval)
        self._interval_value_label.configure(text=f"{interval:.0f}s")

        # Audio settings (v2)
        self._audio_enabled_var.set(config.get("audio_enabled", True))
        audio_buf = config.get("audio_buffer_duration", 5.0)
        self._audio_buf_slider.set(audio_buf)
        self._audio_buf_label.configure(text=f"{audio_buf:.0f}s")

        # Voice settings (v2)
        self._voice_enabled_var.set(config.get("voice_enabled", False))
        voice_speed = config.get("voice_speed", 1.2)
        self._voice_speed_slider.set(voice_speed)
        self._voice_speed_label.configure(text=f"{voice_speed:.1f}x")
        voice_vol = config.get("voice_volume", 0.8)
        self._voice_vol_slider.set(voice_vol)
        self._voice_vol_label.configure(text=f"{int(voice_vol * 100)}%")

        # Overlay settings (v2)
        self._overlay_pos_var.set(config.get("overlay_position", "bottom"))
        opacity = config.get("overlay_opacity", 0.85)
        self._overlay_opacity_slider.set(opacity)
        self._overlay_opacity_label.configure(text=f"{int(opacity * 100)}%")

        # Advanced
        model = config.get("gemini_model", "gemini-2.5-flash")
        self._model_var.set(model)

        ctx = config.get("max_context_messages", 10)
        self._ctx_slider.set(ctx)
        self._ctx_value_label.configure(text=str(int(ctx)))

    def _save_settings(self):
        """Save all settings from the UI to the config."""
        # API key
        api_key = self._api_key_entry.get().strip()
        if api_key:
            config.api_key = api_key

        # All settings
        config.update({
            "game_name": self._game_name_entry.get().strip() or "General",
            "game_genre": self._genre_var.get(),
            "coaching_mode": self._mode_var.get(),
            "custom_instructions": self._custom_instr.get("1.0", "end-1c").strip(),
            "capture_fps": int(self._fps_slider.get()),
            "analysis_interval": float(self._interval_slider.get()),
            # v2: Audio
            "audio_enabled": self._audio_enabled_var.get(),
            "audio_buffer_duration": float(self._audio_buf_slider.get()),
            # v2: Voice
            "voice_enabled": self._voice_enabled_var.get(),
            "voice_speed": float(self._voice_speed_slider.get()),
            "voice_volume": float(self._voice_vol_slider.get()),
            # v2: Overlay
            "overlay_position": self._overlay_pos_var.get(),
            "overlay_opacity": float(self._overlay_opacity_slider.get()),
            # Advanced
            "gemini_model": self._model_var.get(),
            "max_context_messages": int(self._ctx_slider.get()),
        })

        # Update API status
        if config.is_api_key_set:
            self._api_status.configure(
                text="Status: Key configured ✓ — Settings saved!",
                text_color=Colors.STATUS_ONLINE,
            )
        else:
            self._api_status.configure(
                text="Status: Key not set ✗",
                text_color=Colors.STATUS_OFFLINE,
            )

        if self._on_settings_changed:
            self._on_settings_changed()

    # ── Event Handlers ───────────────────────────────────────────────────

    def _toggle_key_visibility(self):
        current = self._api_key_entry.cget("show")
        if current == "•":
            self._api_key_entry.configure(show="")
            self._show_key_btn.configure(text="🔒")
        else:
            self._api_key_entry.configure(show="•")
            self._show_key_btn.configure(text="👁")

    def _test_api(self):
        """Test the Gemini API connection."""
        self._api_status.configure(
            text="Status: Testing connection...",
            text_color=Colors.STATUS_WORKING,
        )
        self._test_btn.configure(state="disabled")

        # Save the key first
        api_key = self._api_key_entry.get().strip()
        if api_key:
            config.api_key = api_key

        # Run test in background
        import threading
        def _test():
            from core.analyzer import GeminiAnalyzer
            analyzer = GeminiAnalyzer()
            success, message = analyzer.test_connection()
            self.after(0, lambda: self._show_test_result(success, message))

        threading.Thread(target=_test, daemon=True).start()

    def _show_test_result(self, success: bool, message: str):
        self._test_btn.configure(state="normal")
        if success:
            self._api_status.configure(
                text=f"Status: Connected ✓ — {message}",
                text_color=Colors.STATUS_ONLINE,
            )
        else:
            self._api_status.configure(
                text=f"Status: Failed ✗ — {message[:60]}",
                text_color=Colors.STATUS_OFFLINE,
            )

    def _on_fps_change(self, value):
        self._fps_value_label.configure(text=str(int(value)))

    def _on_interval_change(self, value):
        self._interval_value_label.configure(text=f"{value:.0f}s")

    def _on_ctx_change(self, value):
        self._ctx_value_label.configure(text=str(int(value)))

    def _on_audio_buf_change(self, value):
        self._audio_buf_label.configure(text=f"{value:.0f}s")

    def _on_voice_speed_change(self, value):
        self._voice_speed_label.configure(text=f"{value:.1f}x")

    def _on_voice_vol_change(self, value):
        self._voice_vol_label.configure(text=f"{int(value * 100)}%")

    def _on_overlay_opacity_change(self, value):
        self._overlay_opacity_label.configure(text=f"{int(value * 100)}%")
