"""
Generic (game-agnostic) plugin for AI Game Coach.
This is the default plugin — it works with any game.
"""

from core.plugin_manager import GamePlugin


class GenericGamePlugin(GamePlugin):
    """Default game-agnostic coaching plugin."""

    name = "Generic"
    genre = "any"
    description = "Game-agnostic coaching that works with any game."
    version = "1.0"

    def get_system_prompt_additions(self) -> str:
        return (
            "You are coaching a game that has not been specifically identified. "
            "Use general gaming knowledge and adapt your advice based on what you "
            "observe in the screenshot and audio."
        )

    def get_analysis_hints(self) -> str:
        return (
            "- Look for any HUD elements (health bars, minimaps, inventory)\n"
            "- Identify the game genre from visual cues\n"
            "- Note the player's current objective if visible\n"
            "- Check for any text or UI notifications on screen"
        )
