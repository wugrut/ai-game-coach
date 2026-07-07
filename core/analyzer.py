"""
Gemini AI vision analysis engine for AI Game Coach.
Sends captured frames to Google Gemini for multimodal game state analysis.
"""

import base64
import logging
import threading
import time
from typing import Optional, List, Dict

from google import genai
from google.genai import types

from core.config import config

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Represents a single AI analysis result."""

    def __init__(self, text: str, timestamp: float, mode: str):
        self.text = text
        self.timestamp = timestamp
        self.mode = mode

    def __repr__(self):
        return f"AnalysisResult(mode={self.mode}, len={len(self.text)})"


class GeminiAnalyzer:
    """
    Google Gemini multimodal vision analyzer.

    Sends game screenshots to Gemini and receives coaching analysis.
    Maintains conversation history for context-aware responses.
    """

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._lock = threading.Lock()
        self._history: List[Dict] = []
        self._last_call_time = 0.0
        self._total_calls = 0
        self._is_initialized = False

    # ── Initialization ───────────────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize the Gemini client with the configured API key."""
        api_key = config.api_key
        if not api_key or api_key == "your_api_key_here":
            logger.error("Gemini API key not configured")
            return False

        try:
            self._client = genai.Client(api_key=api_key)
            self._is_initialized = True
            logger.info("Gemini client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self._is_initialized = False
            return False

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized and self._client is not None

    @property
    def total_calls(self) -> int:
        return self._total_calls

    # ── Analysis ─────────────────────────────────────────────────────────

    def analyze_frame(
        self,
        jpeg_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
    ) -> Optional[AnalysisResult]:
        """
        Analyze a single game frame using Gemini vision.

        Args:
            jpeg_bytes: The captured frame as JPEG bytes.
            system_prompt: The system instruction for the AI coach.
            user_prompt: The user-facing prompt for this analysis request.

        Returns:
            AnalysisResult or None if the call fails.
        """
        if not self.is_initialized:
            if not self.initialize():
                return None

        # Rate limiting
        min_interval = config.get("analysis_interval", 3.0)
        elapsed = time.time() - self._last_call_time
        if elapsed < min_interval:
            wait = min_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait:.1f}s")
            time.sleep(wait)

        try:
            # Build the content parts
            image_part = types.Part.from_bytes(
                data=jpeg_bytes,
                mime_type="image/jpeg",
            )

            # Build conversation with history context
            contents = self._build_contents(image_part, user_prompt)

            # Call Gemini
            response = self._client.models.generate_content(
                model=config.get("gemini_model", "gemini-2.5-flash"),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )

            self._last_call_time = time.time()
            self._total_calls += 1

            # Extract text response
            text = response.text if response.text else ""
            if not text:
                logger.warning("Empty response from Gemini")
                return None

            # Store in history
            result = AnalysisResult(
                text=text,
                timestamp=time.time(),
                mode=config.get("coaching_mode", "strategy"),
            )
            self._add_to_history(user_prompt, text)

            return result

        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            self._last_call_time = time.time()  # Still count for rate limiting
            return None

    def test_connection(self) -> tuple[bool, str]:
        """Test the Gemini API connection with a simple prompt."""
        if not self.is_initialized:
            if not self.initialize():
                return False, "Failed to initialize — check your API key"

        try:
            response = self._client.models.generate_content(
                model=config.get("gemini_model", "gemini-2.5-flash"),
                contents="Say 'AI Game Coach connected!' in exactly those words.",
            )
            text = response.text.strip() if response.text else ""
            return True, text
        except Exception as e:
            return False, f"Connection failed: {e}"

    # ── History Management ───────────────────────────────────────────────

    def _build_contents(self, image_part: types.Part, user_prompt: str) -> list:
        """Build the contents list including conversation history."""
        contents = []

        # Add recent history for context (sliding window)
        max_history = config.get("max_context_messages", 10)
        with self._lock:
            recent = self._history[-max_history:]

        for entry in recent:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"[Previous observation] {entry['user']}")],
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=entry["model"])],
                )
            )

        # Add current frame + prompt
        contents.append(
            types.Content(
                role="user",
                parts=[image_part, types.Part.from_text(text=user_prompt)],
            )
        )

        return contents

    def _add_to_history(self, user_prompt: str, model_response: str):
        """Add an exchange to the conversation history."""
        with self._lock:
            self._history.append({
                "user": user_prompt,
                "model": model_response,
                "timestamp": time.time(),
            })
            # Trim to max size
            max_size = config.get("max_context_messages", 10) * 2
            if len(self._history) > max_size:
                self._history = self._history[-max_size:]

    def clear_history(self):
        """Clear conversation history (e.g., when switching games or modes)."""
        with self._lock:
            self._history.clear()
        logger.info("Conversation history cleared")
