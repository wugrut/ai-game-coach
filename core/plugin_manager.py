"""
Game plugin manager for AI Game Coach.
Provides a plugin architecture for game-specific coaching customization.
"""

import importlib
import logging
from pathlib import Path
from typing import Optional, Dict, List

from core.config import config

logger = logging.getLogger(__name__)

# ── Plugin directory ─────────────────────────────────────────────────────────
PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


class GamePlugin:
    """
    Base class for game-specific plugins.

    Subclass this to create a custom plugin for a specific game.
    Each plugin can provide:
    - Custom system prompts tailored to the game
    - Custom user prompts for analysis
    - Game-specific knowledge (items, maps, champions, etc.)
    - Optional frame parsing (future: CV-based state extraction)
    """

    # Override these in subclasses
    name: str = "Generic"
    genre: str = "any"
    description: str = "Generic game-agnostic coaching"
    version: str = "1.0"

    def get_system_prompt_additions(self) -> str:
        """
        Return additional system prompt text specific to this game.
        This is appended to the base system prompt.
        """
        return ""

    def get_user_prompt_override(self, mode: str) -> Optional[str]:
        """
        Optionally override the user prompt for a given coaching mode.
        Return None to use the default prompt.

        Args:
            mode: The coaching mode (realtime, strategy, post_analysis)
        """
        return None

    def get_knowledge(self) -> str:
        """
        Return game-specific knowledge as text.
        This is included in the system prompt for domain expertise.
        """
        return ""

    def get_analysis_hints(self) -> str:
        """
        Return hints about what to look for in this specific game.
        E.g., "Look for the minimap in the bottom-left corner" or
        "Health bar is the red bar at the top of the screen."
        """
        return ""


class GenericPlugin(GamePlugin):
    """
    Default game-agnostic plugin.
    Wraps the original behavior — no game-specific customization.
    """
    name = "Generic"
    genre = "any"
    description = "Game-agnostic coaching — works with any game by analyzing visuals and audio generically."
    version = "1.0"


class PluginManager:
    """
    Discovers, loads, and manages game plugins.

    Plugins are Python modules in the plugins/ directory that define
    a class inheriting from GamePlugin.
    """

    def __init__(self):
        self._plugins: Dict[str, GamePlugin] = {}
        self._active_plugin: Optional[GamePlugin] = None

        # Always register the generic plugin
        self._plugins["generic"] = GenericPlugin()

        # Discover additional plugins
        self._discover_plugins()

        # Set the active plugin from config
        active_name = config.get("active_plugin", "generic")
        self.set_active(active_name)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def active_plugin(self) -> GamePlugin:
        """Get the currently active plugin."""
        return self._active_plugin or self._plugins["generic"]

    @property
    def available_plugins(self) -> List[Dict]:
        """List all available plugins with their metadata."""
        return [
            {
                "name": p.name,
                "id": plugin_id,
                "genre": p.genre,
                "description": p.description,
                "version": p.version,
            }
            for plugin_id, p in self._plugins.items()
        ]

    @property
    def plugin_names(self) -> List[str]:
        """Get a list of plugin IDs."""
        return list(self._plugins.keys())

    # ── Public API ───────────────────────────────────────────────────────

    def set_active(self, plugin_id: str) -> bool:
        """
        Set the active plugin by ID.

        Args:
            plugin_id: The plugin identifier (e.g., "generic", "valorant").

        Returns:
            True if the plugin was found and activated.
        """
        if plugin_id in self._plugins:
            self._active_plugin = self._plugins[plugin_id]
            config.set("active_plugin", plugin_id)
            logger.info(f"Active plugin: {self._active_plugin.name}")
            return True
        else:
            logger.warning(f"Plugin not found: {plugin_id}")
            self._active_plugin = self._plugins["generic"]
            return False

    def get_plugin(self, plugin_id: str) -> Optional[GamePlugin]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def register_plugin(self, plugin_id: str, plugin: GamePlugin):
        """Manually register a plugin."""
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered plugin: {plugin.name} ({plugin_id})")

    # ── Plugin Discovery ─────────────────────────────────────────────────

    def _discover_plugins(self):
        """Discover and load plugins from the plugins directory."""
        if not PLUGINS_DIR.exists():
            logger.info(f"No plugins directory found at {PLUGINS_DIR}")
            return

        for py_file in PLUGINS_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            plugin_id = py_file.stem
            if plugin_id == "generic":
                continue  # Already registered

            try:
                self._load_plugin_file(plugin_id, py_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_id}: {e}")

    def _load_plugin_file(self, plugin_id: str, path: Path):
        """Load a plugin from a Python file."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            f"plugins.{plugin_id}", str(path),
        )
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find GamePlugin subclasses in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, GamePlugin)
                    and attr is not GamePlugin):
                plugin = attr()
                self._plugins[plugin_id] = plugin
                logger.info(f"Loaded plugin: {plugin.name} ({plugin_id})")
                return

        logger.warning(f"No GamePlugin subclass found in {path.name}")
