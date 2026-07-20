# Creating Game Plugins

You can create game-specific plugins to enhance coaching for specific games.

## How to Create a Plugin

1. Create a new `.py` file in this `plugins/` directory
2. Define a class that inherits from `GamePlugin`
3. Override the methods you need
4. Restart the app — your plugin will be auto-discovered

## Example Plugin

```python
"""
Example: Valorant coaching plugin.
"""
from core.plugin_manager import GamePlugin


class ValorantPlugin(GamePlugin):
    name = "Valorant"
    genre = "fps"
    description = "Specialized coaching for Valorant — agents, maps, economy, and tactics."
    version = "1.0"

    def get_system_prompt_additions(self) -> str:
        return (
            "You are coaching Valorant. Key concepts:\n"
            "- Economy: pistol rounds, eco, force buy, full buy\n"
            "- Agents: Controllers, Duelists, Initiators, Sentinels\n"
            "- Callouts: use map-specific location names\n"
            "- Ultimate tracking: note ult points and suggest timing"
        )

    def get_knowledge(self) -> str:
        return (
            "Valorant Maps: Ascent, Bind, Haven, Split, Icebox, Breeze, "
            "Fracture, Pearl, Lotus, Sunset, Abyss\n"
            "Agents: Jett, Reyna, Phoenix, Raze, Neon, Yoru, Iso (Duelists), "
            "Brimstone, Omen, Astra, Viper, Harbor, Clove (Controllers), "
            "Sova, Breach, Skye, KAY/O, Fade, Gekko (Initiators), "
            "Sage, Cypher, Killjoy, Chamber, Deadlock, Vyse (Sentinels)"
        )

    def get_analysis_hints(self) -> str:
        return (
            "- Minimap is in the top-left corner\n"
            "- Economy/credits shown at top of buy phase\n"
            "- Agent abilities shown at bottom-center\n"
            "- Kill feed is in the top-right corner\n"
            "- Round score shown at top-center"
        )
```

## Plugin Methods

| Method | Purpose |
|--------|---------|
| `get_system_prompt_additions()` | Extra system prompt text specific to your game |
| `get_user_prompt_override(mode)` | Optionally override the analysis prompt per coaching mode |
| `get_knowledge()` | Game-specific knowledge (items, maps, characters) |
| `get_analysis_hints()` | Hints about where to find game info on screen |

## Plugin Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Display name (e.g., "Valorant") |
| `genre` | str | Game genre (fps, moba, rts, rpg, etc.) |
| `description` | str | Brief description |
| `version` | str | Plugin version |
