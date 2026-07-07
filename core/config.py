"""
Configuration management for AI Game Coach.
Handles loading/saving settings, API key management, and defaults.
"""

import json
import os
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "game_name": "General",
    "game_genre": "any",
    "coaching_mode": "strategy",      # "realtime", "strategy", "post_analysis"
    "gemini_model": "gemini-2.5-flash",
    "capture_fps": 2,
    "capture_region": None,           # (left, top, right, bottom) or None for full screen
    "analysis_interval": 3.0,         # Seconds between AI analysis calls
    "max_context_messages": 10,       # Sliding window of conversation history
    "custom_instructions": "",        # User's custom coaching focus
    "auto_scroll": True,
    "sound_alerts": False,
}

CONFIG_FILE = _PROJECT_ROOT / "config.json"


class AppConfig:
    """Thread-safe application configuration manager."""

    def __init__(self):
        self._lock = threading.Lock()
        self._config: dict = {}
        self.load()

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def api_key(self) -> str:
        """Get Gemini API key from environment."""
        return os.getenv("GEMINI_API_KEY", "")

    @api_key.setter
    def api_key(self, value: str):
        """Save API key to .env file."""
        env_path = _PROJECT_ROOT / ".env"
        lines = []
        found = False
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        lines.append(f"GEMINI_API_KEY={value}\n")
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f"GEMINI_API_KEY={value}\n")
        with open(env_path, "w") as f:
            f.writelines(lines)
        os.environ["GEMINI_API_KEY"] = value

    # ── Getters / Setters ────────────────────────────────────────────────

    def get(self, key: str, default=None):
        with self._lock:
            return self._config.get(key, DEFAULT_CONFIG.get(key, default))

    def set(self, key: str, value):
        with self._lock:
            self._config[key] = value
        self.save()

    def update(self, updates: dict):
        with self._lock:
            self._config.update(updates)
        self.save()

    def to_dict(self) -> dict:
        with self._lock:
            merged = {**DEFAULT_CONFIG, **self._config}
        return merged

    # ── Persistence ──────────────────────────────────────────────────────

    def load(self):
        """Load configuration from disk."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                with self._lock:
                    self._config = data
            except (json.JSONDecodeError, IOError):
                with self._lock:
                    self._config = {}
        else:
            with self._lock:
                self._config = {}

    def save(self):
        """Persist configuration to disk."""
        with self._lock:
            data = dict(self._config)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Fail silently — config save is best-effort

    # ── Validation ───────────────────────────────────────────────────────

    @property
    def is_api_key_set(self) -> bool:
        key = self.api_key
        return bool(key) and key != "your_api_key_here"

    @property
    def capture_region_tuple(self):
        """Return capture region as a tuple or None."""
        region = self.get("capture_region")
        if region and isinstance(region, (list, tuple)) and len(region) == 4:
            return tuple(region)
        return None


# ── Singleton ────────────────────────────────────────────────────────────────
config = AppConfig()
