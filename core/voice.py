"""
Voice commentary engine for AI Game Coach.
Speaks coaching messages aloud using pyttsx3 (offline) with optional
Google Cloud TTS support. Runs in a background thread with priority queuing.
"""

import logging
import queue
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try to import pyttsx3 ───────────────────────────────────────────────────
_HAS_PYTTSX3 = False
try:
    import pyttsx3
    _HAS_PYTTSX3 = True
    logger.info("pyttsx3 available — voice commentary supported")
except ImportError:
    logger.warning("pyttsx3 not installed — voice commentary disabled")


class VoiceEngine:
    """
    Text-to-speech engine for coaching voice commentary.

    Uses pyttsx3 for offline speech synthesis. Runs in a background thread
    and processes messages from a priority queue.

    Priority messages (CRITICAL) are inserted at the front of the queue
    and interrupt any non-priority speech in progress.
    """

    def __init__(self):
        self._engine: Optional[object] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._muted = False

        # Queue: (priority, timestamp, text)
        # priority=0 is highest (CRITICAL), priority=1 is normal
        self._queue: queue.PriorityQueue = queue.PriorityQueue()

        # Track current state
        self._is_speaking = False
        self._current_text = ""

        # Settings
        self._speed = 1.2   # Multiplier (1.0 = normal)
        self._volume = 0.8  # 0.0 to 1.0

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """Whether voice synthesis is available."""
        return _HAS_PYTTSX3

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    @property
    def is_muted(self) -> bool:
        return self._muted

    @is_muted.setter
    def is_muted(self, value: bool):
        self._muted = value

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float):
        self._speed = max(0.5, min(value, 3.0))

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(value, 1.0))

    # ── Public API ───────────────────────────────────────────────────────

    def start(self):
        """Start the voice engine background thread."""
        if self._running:
            return

        if not _HAS_PYTTSX3:
            logger.warning("Cannot start voice engine — pyttsx3 not available")
            return

        self._running = True
        self._thread = threading.Thread(target=self._voice_loop, daemon=True)
        self._thread.start()
        logger.info("Voice engine started")

    def stop(self):
        """Stop the voice engine and clear the queue."""
        self._running = False
        # Put a sentinel to unblock the queue
        self._queue.put((999, 0, None))
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        # Clear remaining items
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Voice engine stopped")

    def speak(self, text: str, priority: bool = False):
        """
        Queue a message to be spoken.

        Args:
            text: The text to speak.
            priority: If True, this is a high-priority message (CRITICAL)
                     that will be spoken before normal messages.
        """
        if not self._running or self._muted:
            return

        # Clean the text for speech — remove markdown and emojis
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return

        # Priority: 0 = critical (high), 1 = normal
        prio = 0 if priority else 1
        self._queue.put((prio, time.time(), clean_text))

    def clear_queue(self):
        """Clear all pending messages from the queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def speak_immediately(self, text: str):
        """
        Speak a message immediately, clearing the queue first.
        Used for critical announcements.
        """
        self.clear_queue()
        self.speak(text, priority=True)

    # ── Voice Loop ───────────────────────────────────────────────────────

    def _voice_loop(self):
        """Background thread that processes the speech queue."""
        # Initialize pyttsx3 in this thread (it must be created in the
        # same thread that calls runAndWait)
        try:
            engine = pyttsx3.init()
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self._running = False
            return

        while self._running:
            try:
                # Wait for next message (with timeout so we can check _running)
                try:
                    prio, timestamp, text = self._queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Sentinel value
                if text is None:
                    continue

                # Skip if muted
                if self._muted:
                    continue

                # Skip messages that are too old (> 30 seconds)
                if time.time() - timestamp > 30.0:
                    logger.debug(f"Skipping stale voice message: {text[:30]}...")
                    continue

                # Configure engine settings
                try:
                    # Speed: pyttsx3 uses words per minute (default ~200)
                    base_rate = 200
                    engine.setProperty("rate", int(base_rate * self._speed))
                    engine.setProperty("volume", self._volume)
                except Exception:
                    pass

                # Speak!
                self._is_speaking = True
                self._current_text = text
                logger.debug(f"Speaking: {text[:50]}...")

                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"Speech error: {e}")
                    # Try to reinitialize the engine
                    try:
                        engine = pyttsx3.init()
                    except Exception:
                        pass

                self._is_speaking = False
                self._current_text = ""

            except Exception as e:
                logger.error(f"Voice loop error: {e}")
                self._is_speaking = False

        # Cleanup
        try:
            engine.stop()
        except Exception:
            pass

    # ── Text Cleaning ────────────────────────────────────────────────────

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """
        Clean text for natural speech output.
        Removes markdown formatting, emojis, and other non-speech elements.
        """
        import re

        # Remove markdown bold/italic
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)

        # Remove markdown links [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove common emojis and special characters
        text = re.sub(r'[🔴🟡🟢🔵🎮🧠⚡📊🎯💡🖥️📐⏸️⏹▶❌✅⚠️]', '', text)

        # Remove priority markers (already parsed)
        text = re.sub(r'\[(CRITICAL|IMPORTANT|TIP|INFO)\]', '', text, flags=re.IGNORECASE)

        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove leading/trailing punctuation artifacts
        text = text.strip('- •')

        return text.strip()
