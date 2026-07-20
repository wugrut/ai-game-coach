# 🎮 AI Game Coach v2 — Full AI Gaming Companion

**An AI-powered gaming companion that watches your screen, listens to game audio, and provides real-time coaching, voice commentary, and interactive chat — powered by Google Gemini's multimodal AI.**

> ⚠️ **Educational Use Only** — This tool is designed as a learning aid. It only *observes* and *advises*. It does not interact with games directly.

---

## ✨ Features

### Core
- **🖥️ Screen Capture** — High-performance capture using DXcam (Windows) with MSS fallback
- **🎤 Audio Capture** — System audio capture via WASAPI loopback (hears what you hear)
- **🧠 Multimodal AI** — Google Gemini analyzes both video AND audio together
- **🎮 Game-Agnostic** — Works with any game, with plugin support for game-specific coaching

### Coaching Modes
- **⚡ Real-time Callouts** — Quick, actionable observations during gameplay
- **🎯 Strategy Advisor** — Deeper strategic analysis with explanations
- **📊 Post-Play Review** — Comprehensive coaching after a session

### v2 Additions
- **🔊 Voice Commentary** — AI reads coaching advice aloud via text-to-speech
- **💬 Chat Companion** — Interactive AI sidebar to ask questions mid-game
- **🖥️ Overlay HUD** — Transparent, click-through overlay shows tips over your game
- **🔌 Plugin System** — Game-specific plugins for specialized coaching
- **⌨️ Keyboard Shortcuts** — `Ctrl+M` mute voice, `Ctrl+O` toggle overlay

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or newer
- A Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/))
- Windows 10/11 (for WASAPI audio and DXcam)

### 2. Install Dependencies
```bash
cd ai-game-coach
pip install -r requirements.txt
```

### 3. Configure API Key
```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_actual_key_here
```

Or set it through the app's Settings panel.

### 4. Launch
```bash
python main.py
```

---

## 🎯 How to Use

1. **Launch AI Game Coach** with `python main.py`
2. **Set your API key** in the Settings tab (first time only)
3. **Select a capture region** — click "📐 Select Region" and drag over your game window
4. **Choose your coaching mode** — Real-time, Strategy, or Post-Play
5. **Hit "Start Coaching"** — the AI will begin analyzing your screen and audio!

### New in v2
- **💬 Chat Tab** — Switch to the Chat tab and ask the AI questions while playing
- **🔊 Voice** — Click the voice button in the sidebar to hear coaching advice aloud
- **🖥️ Overlay** — Toggle the overlay to see tips float over your game
- **Settings** — Configure audio, voice speed/volume, and overlay position

---

## 🧪 Testing

```bash
# Test screen capture
python main.py --test-capture

# Test Gemini API connection
python main.py --test-api

# Enable debug logging
python main.py --debug
```

---

## 📁 Project Structure

```
ai-game-coach/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── .env                     # API key (create from .env.example)
├── config.json              # User settings (auto-created)
├── core/
│   ├── config.py            # Configuration management
│   ├── capture.py           # Screen capture engine (DXcam/MSS)
│   ├── audio_capture.py     # 🆕 System audio capture (WASAPI)
│   ├── analyzer.py          # Gemini AI multimodal engine
│   ├── coach.py             # Coaching orchestrator
│   ├── chat.py              # 🆕 Chat companion engine
│   ├── voice.py             # 🆕 Voice commentary (pyttsx3)
│   └── plugin_manager.py    # 🆕 Game plugin system
├── ui/
│   ├── app.py               # Main application window
│   ├── theme.py             # Dark theme & styling
│   ├── coach_panel.py       # AI coaching message display
│   ├── chat_panel.py        # 🆕 Interactive chat UI
│   ├── capture_preview.py   # Live capture preview
│   ├── settings_panel.py    # Settings UI (expanded for v2)
│   ├── overlay.py           # 🆕 Transparent HUD overlay
│   └── region_selector.py   # Screen region picker
├── prompts/
│   ├── base_system.txt      # Base coaching system prompt
│   ├── realtime_callouts.txt # Real-time mode prompt
│   ├── post_analysis.txt    # Post-play review prompt
│   └── chat_system.txt      # 🆕 Chat companion prompt
└── plugins/
    ├── __init__.py
    ├── generic.py            # Default game-agnostic plugin
    └── README.md             # Guide for creating plugins
```

---

## 🔌 Creating Game Plugins

Create game-specific plugins for enhanced coaching:

```python
# plugins/valorant.py
from core.plugin_manager import GamePlugin

class ValorantPlugin(GamePlugin):
    name = "Valorant"
    genre = "fps"
    description = "Specialized Valorant coaching"

    def get_system_prompt_additions(self):
        return "You are coaching Valorant. Focus on economy, agent abilities..."

    def get_knowledge(self):
        return "Maps: Ascent, Bind, Haven... Agents: Jett, Reyna, Sage..."
```

See [plugins/README.md](plugins/README.md) for full documentation.

---

## 🔧 Configuration

All settings are configurable through the UI or `config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| `game_name` | General | Name of the game being played |
| `game_genre` | any | Game genre (fps, moba, rts, etc.) |
| `coaching_mode` | strategy | realtime, strategy, or post_analysis |
| `gemini_model` | gemini-2.5-flash | Gemini model to use |
| `capture_fps` | 2 | Frames captured per second |
| `analysis_interval` | 3.0 | Seconds between AI analysis calls |
| `audio_enabled` | true | Enable system audio capture |
| `audio_buffer_duration` | 5.0 | Audio buffer length in seconds |
| `voice_enabled` | false | Enable voice commentary |
| `voice_speed` | 1.2 | Speech speed multiplier |
| `voice_volume` | 0.8 | Voice volume (0.0–1.0) |
| `overlay_enabled` | false | Enable overlay HUD |
| `overlay_position` | bottom | top, bottom, top_right, bottom_right |
| `overlay_opacity` | 0.85 | Overlay background opacity |
| `active_plugin` | generic | Active game plugin |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+M` | Toggle voice mute/unmute |
| `Ctrl+O` | Toggle overlay on/off |

---

## 📝 License

This project is for **educational purposes only**.
