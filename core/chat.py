"""
Chat companion engine for AI Game Coach.
Manages an interactive conversation with the AI about the game being played.
Shares screen capture context with the coaching system.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List, Dict

from core.config import config

logger = logging.getLogger(__name__)

# ── Prompt directory ─────────────────────────────────────────────────────────
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class ChatMessage:
    """A single chat message."""

    ROLE_USER = "user"
    ROLE_AI = "ai"
    ROLE_SYSTEM = "system"

    def __init__(self, text: str, role: str = ROLE_USER, include_screenshot: bool = False):
        self.text = text
        self.role = role
        self.timestamp = time.time()
        self.include_screenshot = include_screenshot


class ChatEngine:
    """
    Interactive chat companion engine.

    Allows the player to ask questions about the game in real-time.
    Maintains its own conversation history, separate from coaching.
    Can optionally include the current screenshot for context-aware responses.
    """

    def __init__(self):
        self._history: List[Dict] = []
        self._messages: List[ChatMessage] = []
        self._messages_lock = threading.Lock()
        self._analyzer = None  # Set externally to share with coach

        # Callbacks
        self._on_response: Optional[Callable[[ChatMessage], None]] = None
        self._on_typing: Optional[Callable[[bool], None]] = None

        # Screenshot provider callback — returns JPEG bytes or None
        self._get_screenshot: Optional[Callable[[], Optional[bytes]]] = None

    # ── Configuration ────────────────────────────────────────────────────

    def set_analyzer(self, analyzer):
        """Share the GeminiAnalyzer instance from the coach."""
        self._analyzer = analyzer

    def set_screenshot_provider(self, provider: Callable[[], Optional[bytes]]):
        """Set a callback that provides the current screenshot as JPEG bytes."""
        self._get_screenshot = provider

    def on_response(self, callback: Callable[[ChatMessage], None]):
        """Register a callback for AI responses."""
        self._on_response = callback

    def on_typing(self, callback: Callable[[bool], None]):
        """Register a callback for typing indicator."""
        self._on_typing = callback

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def messages(self) -> List[ChatMessage]:
        with self._messages_lock:
            return list(self._messages)

    @property
    def message_count(self) -> int:
        with self._messages_lock:
            return len(self._messages)

    # ── Public API ───────────────────────────────────────────────────────

    def send_message(self, text: str, include_screenshot: bool = True):
        """
        Send a message to the AI chat companion.

        Args:
            text: The user's message.
            include_screenshot: Whether to include the current screenshot for context.
        """
        if not text.strip():
            return

        if not self._analyzer:
            error_msg = ChatMessage(
                "Chat is not available — no AI analyzer connected.",
                role=ChatMessage.ROLE_SYSTEM,
            )
            self._add_message(error_msg)
            return

        # Add user message
        user_msg = ChatMessage(text.strip(), ChatMessage.ROLE_USER, include_screenshot)
        self._add_message(user_msg)

        # Process in background thread
        thread = threading.Thread(
            target=self._process_message,
            args=(text.strip(), include_screenshot),
            daemon=True,
        )
        thread.start()

    def clear_history(self):
        """Clear all chat messages and history."""
        with self._messages_lock:
            self._messages.clear()
        self._history.clear()

    # ── Internal Processing ──────────────────────────────────────────────

    def _process_message(self, text: str, include_screenshot: bool):
        """Process a user message and get an AI response (runs in background)."""
        # Signal typing
        if self._on_typing:
            try:
                self._on_typing(True)
            except Exception:
                pass

        try:
            # Get screenshot if requested
            jpeg_bytes = None
            if include_screenshot and self._get_screenshot:
                try:
                    jpeg_bytes = self._get_screenshot()
                except Exception:
                    pass

            # Load chat system prompt
            system_prompt = self._load_chat_prompt()

            # Send to Gemini
            response_text = self._analyzer.send_chat_message(
                message=text,
                system_prompt=system_prompt,
                jpeg_bytes=jpeg_bytes,
                chat_history=self._history,
            )

            if response_text:
                # Add to history
                self._history.append({
                    "user": text,
                    "model": response_text,
                    "timestamp": time.time(),
                })

                # Trim history
                if len(self._history) > 20:
                    self._history = self._history[-20:]

                # Create AI response message
                ai_msg = ChatMessage(response_text, ChatMessage.ROLE_AI)
                self._add_message(ai_msg)
            else:
                error_msg = ChatMessage(
                    "Sorry, I couldn't process that. Please try again.",
                    role=ChatMessage.ROLE_SYSTEM,
                )
                self._add_message(error_msg)

        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            error_msg = ChatMessage(
                f"Error: {str(e)[:100]}",
                role=ChatMessage.ROLE_SYSTEM,
            )
            self._add_message(error_msg)

        finally:
            # Signal done typing
            if self._on_typing:
                try:
                    self._on_typing(False)
                except Exception:
                    pass

    def _add_message(self, message: ChatMessage):
        """Add a message and notify via callback."""
        with self._messages_lock:
            self._messages.append(message)
            if len(self._messages) > 200:
                self._messages = self._messages[-150:]

        if self._on_response:
            try:
                self._on_response(message)
            except Exception as e:
                logger.error(f"Chat response callback error: {e}")

    def _load_chat_prompt(self) -> str:
        """Load the chat companion system prompt."""
        path = PROMPTS_DIR / "chat_system.txt"
        if path.exists():
            prompt = path.read_text(encoding="utf-8").strip()
        else:
            prompt = self._default_chat_prompt()

        # Inject game context
        game_name = config.get("game_name", "General")
        game_genre = config.get("game_genre", "any")
        prompt += f"\n\n## Current Context\nGame: {game_name}\nGenre: {game_genre}"

        return prompt

    @staticmethod
    def _default_chat_prompt() -> str:
        """Fallback chat prompt if the file doesn't exist."""
        return (
            "You are an AI gaming companion and expert game advisor. "
            "The player is currently in a gaming session and can ask you questions. "
            "You may receive a screenshot of the current game state for context. "
            "Be conversational, helpful, and knowledgeable about games."
        )
