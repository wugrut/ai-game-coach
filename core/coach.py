"""
Game coaching orchestrator for AI Game Coach.
Manages coaching modes, prompt construction, and coordinates capture → analysis → display.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List

from core.config import config
from core.capture import ScreenCapture
from core.analyzer import GeminiAnalyzer, AnalysisResult

logger = logging.getLogger(__name__)

# ── Prompt directory ─────────────────────────────────────────────────────────
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    logger.warning(f"Prompt file not found: {path}")
    return ""


class CoachMessage:
    """A single coaching message for the UI."""

    PRIORITY_CRITICAL = "critical"    # 🔴
    PRIORITY_IMPORTANT = "important"  # 🟡
    PRIORITY_TIP = "tip"             # 🟢
    PRIORITY_INFO = "info"           # 🔵

    def __init__(self, text: str, priority: str = "info", mode: str = "strategy"):
        self.text = text
        self.priority = priority
        self.mode = mode
        self.timestamp = time.time()

    @property
    def priority_emoji(self) -> str:
        return {
            "critical": "🔴",
            "important": "🟡",
            "tip": "🟢",
            "info": "🔵",
        }.get(self.priority, "🔵")


class GameCoach:
    """
    Game coaching orchestrator.

    Coordinates the screen capture → AI analysis → coaching advice pipeline.
    Supports three coaching modes:
      1. Real-time Callouts — Quick, actionable observations
      2. Strategy Advisor — Deeper strategic analysis
      3. Post-Play Review — Comprehensive post-game review
    """

    def __init__(self):
        self.capture = ScreenCapture()
        self.analyzer = GeminiAnalyzer()

        self._coaching_active = False
        self._coaching_thread: Optional[threading.Thread] = None
        self._messages: List[CoachMessage] = []
        self._messages_lock = threading.Lock()

        # Callbacks
        self._on_message: Optional[Callable[[CoachMessage], None]] = None
        self._on_status_change: Optional[Callable[[str], None]] = None
        self._on_frame_captured: Optional[Callable] = None

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def is_coaching(self) -> bool:
        return self._coaching_active

    @property
    def messages(self) -> List[CoachMessage]:
        with self._messages_lock:
            return list(self._messages)

    # ── Callback Registration ────────────────────────────────────────────

    def on_message(self, callback: Callable[[CoachMessage], None]):
        """Register a callback for new coaching messages."""
        self._on_message = callback

    def on_status_change(self, callback: Callable[[str], None]):
        """Register a callback for status updates."""
        self._on_status_change = callback

    def on_frame_captured(self, callback: Callable):
        """Register a callback for when a new frame is captured."""
        self._on_frame_captured = callback

    # ── Coaching Control ─────────────────────────────────────────────────

    def start_coaching(self):
        """Start the coaching pipeline."""
        if self._coaching_active:
            return

        # Initialize the analyzer
        if not self.analyzer.is_initialized:
            if not self.analyzer.initialize():
                self._emit_status("❌ Failed to connect to Gemini API")
                self._emit_message(CoachMessage(
                    "Could not connect to Gemini API. Please check your API key in Settings.",
                    priority=CoachMessage.PRIORITY_CRITICAL,
                ))
                return

        # Configure capture
        region = config.capture_region_tuple
        self.capture.region = region
        self.capture.target_fps = config.get("capture_fps", 2)

        # Start capture
        self.capture.start()

        # Start coaching loop
        self._coaching_active = True
        self._coaching_thread = threading.Thread(target=self._coaching_loop, daemon=True)
        self._coaching_thread.start()

        mode = config.get("coaching_mode", "strategy")
        game = config.get("game_name", "General")
        self._emit_status(f"🎮 Coaching active — {game} ({mode} mode)")
        self._emit_message(CoachMessage(
            f"Coaching started for **{game}**! I'm watching your screen and will provide {mode} advice.",
            priority=CoachMessage.PRIORITY_INFO,
            mode=mode,
        ))

    def stop_coaching(self):
        """Stop the coaching pipeline."""
        self._coaching_active = False
        self.capture.stop()
        if self._coaching_thread:
            self._coaching_thread.join(timeout=5.0)
            self._coaching_thread = None
        self._emit_status("⏸️ Coaching paused")

    def clear_messages(self):
        """Clear all coaching messages."""
        with self._messages_lock:
            self._messages.clear()
        self.analyzer.clear_history()

    # ── Coaching Loop ────────────────────────────────────────────────────

    def _coaching_loop(self):
        """Main coaching loop — captures frames and sends to AI."""
        analysis_interval = config.get("analysis_interval", 3.0)

        while self._coaching_active:
            loop_start = time.time()

            try:
                # Get the latest frame as JPEG
                jpeg_bytes = self.capture.get_latest_jpeg(resize_for_api=True)
                if jpeg_bytes is None:
                    time.sleep(0.5)
                    continue

                # Notify UI of frame capture
                if self._on_frame_captured:
                    try:
                        self._on_frame_captured()
                    except Exception:
                        pass

                # Build prompts
                system_prompt = self._build_system_prompt()
                user_prompt = self._build_user_prompt()

                # Send to Gemini for analysis
                self._emit_status("🧠 Analyzing...")
                result = self.analyzer.analyze_frame(
                    jpeg_bytes=jpeg_bytes,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )

                if result and result.text:
                    # Parse the response into coaching messages
                    messages = self._parse_response(result.text, result.mode)
                    for msg in messages:
                        self._emit_message(msg)

                    calls = self.analyzer.total_calls
                    fps = self.capture.actual_fps
                    self._emit_status(f"🎮 Coaching active — {fps:.0f} FPS | {calls} analyses")

            except Exception as e:
                logger.error(f"Coaching loop error: {e}")
                self._emit_status(f"⚠️ Error: {str(e)[:50]}")

            # Wait for the next analysis interval
            elapsed = time.time() - loop_start
            wait = max(0, analysis_interval - elapsed)
            if wait > 0 and self._coaching_active:
                time.sleep(wait)

    # ── Prompt Construction ──────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        """Build the system prompt based on current configuration."""
        base = _load_prompt("base_system.txt")
        mode = config.get("coaching_mode", "strategy")
        game_name = config.get("game_name", "General")
        game_genre = config.get("game_genre", "any")
        custom = config.get("custom_instructions", "")

        # Add mode-specific instructions
        if mode == "realtime":
            mode_prompt = _load_prompt("realtime_callouts.txt")
        elif mode == "post_analysis":
            mode_prompt = _load_prompt("post_analysis.txt")
        else:
            mode_prompt = ""

        parts = [base]
        parts.append(f"\n\n## Current Game\nGame: {game_name}\nGenre: {game_genre}")

        if mode_prompt:
            parts.append(f"\n\n## Mode-Specific Instructions\n{mode_prompt}")

        if custom:
            parts.append(f"\n\n## User's Custom Focus\n{custom}")

        return "\n".join(parts)

    def _build_user_prompt(self) -> str:
        """Build the user prompt for the current frame analysis."""
        mode = config.get("coaching_mode", "strategy")

        if mode == "realtime":
            return (
                "Analyze this game screenshot. Provide quick, actionable callouts about "
                "what you see — enemy positions, items, dangers, or opportunities. "
                "Keep it brief and urgent. Use priority markers: "
                "[CRITICAL] for immediate threats, [IMPORTANT] for key observations, [TIP] for suggestions."
            )
        elif mode == "post_analysis":
            return (
                "Review this game screenshot as part of a post-play analysis. "
                "Analyze the player's positioning, resource management, and decision-making. "
                "Provide constructive feedback with specific improvement suggestions. "
                "Use priority markers: [CRITICAL], [IMPORTANT], [TIP] for categorization."
            )
        else:  # strategy
            return (
                "Analyze this game screenshot and provide strategic coaching advice. "
                "Consider the current game state, player positioning, available resources, "
                "and suggest the best course of action. Explain your reasoning briefly. "
                "Use priority markers: [CRITICAL], [IMPORTANT], [TIP] for categorization."
            )

    # ── Response Parsing ─────────────────────────────────────────────────

    def _parse_response(self, text: str, mode: str) -> List[CoachMessage]:
        """Parse the AI response into categorized coaching messages."""
        messages = []

        # Split response into sections if it contains priority markers
        lines = text.strip().split("\n")
        current_text = []
        current_priority = CoachMessage.PRIORITY_INFO

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                if current_text:
                    current_text.append("")
                continue

            # Check for priority markers
            new_priority = None
            clean_line = line_stripped
            if "[CRITICAL]" in line_stripped.upper():
                new_priority = CoachMessage.PRIORITY_CRITICAL
                clean_line = line_stripped.replace("[CRITICAL]", "").replace("[critical]", "").strip()
            elif "[IMPORTANT]" in line_stripped.upper():
                new_priority = CoachMessage.PRIORITY_IMPORTANT
                clean_line = line_stripped.replace("[IMPORTANT]", "").replace("[important]", "").strip()
            elif "[TIP]" in line_stripped.upper():
                new_priority = CoachMessage.PRIORITY_TIP
                clean_line = line_stripped.replace("[TIP]", "").replace("[tip]", "").strip()

            if new_priority is not None:
                # Save previous message if any
                if current_text:
                    msg_text = "\n".join(current_text).strip()
                    if msg_text:
                        messages.append(CoachMessage(msg_text, current_priority, mode))
                current_text = [clean_line] if clean_line else []
                current_priority = new_priority
            else:
                current_text.append(line_stripped)

        # Don't forget the last message
        if current_text:
            msg_text = "\n".join(current_text).strip()
            if msg_text:
                messages.append(CoachMessage(msg_text, current_priority, mode))

        # If no markers were found, treat the whole response as one message
        if not messages and text.strip():
            messages.append(CoachMessage(text.strip(), CoachMessage.PRIORITY_INFO, mode))

        return messages

    # ── Event Emitters ───────────────────────────────────────────────────

    def _emit_message(self, message: CoachMessage):
        """Store and emit a coaching message."""
        with self._messages_lock:
            self._messages.append(message)
            # Keep a reasonable limit
            if len(self._messages) > 500:
                self._messages = self._messages[-300:]

        if self._on_message:
            try:
                self._on_message(message)
            except Exception as e:
                logger.error(f"Message callback error: {e}")

    def _emit_status(self, status: str):
        """Emit a status update."""
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
