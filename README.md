# 🎮 AI Game Coach

**An AI-powered educational tool that watches Discord video streams and provides real-time gameplay coaching using Google Gemini's multimodal vision.**

> ⚠️ **Educational Use Only** — This tool is designed as a learning aid. It only *observes* and *advises*. It does not interact with games directly.

---

## ✨ Features

- **🖥️ Screen Capture** — High-performance capture using DXcam (Windows) with MSS fallback
- **🧠 AI Vision Analysis** — Google Gemini multimodal vision analyzes your game in real-time
- **⚡ Real-time Callouts** — Quick, actionable observations during gameplay
- **🎯 Strategy Advisor** — Deeper strategic analysis with explanations
- **📊 Post-Play Review** — Comprehensive coaching after a session
- **🎮 Game-Agnostic** — Works with any game you specify
- **🌙 Dark Theme** — Sleek, modern UI with glassmorphism accents

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or newer
- A Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/))

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

1. **Open Discord** and start watching a stream
2. **Launch AI Game Coach** with `python main.py`
3. **Set your API key** in the Settings tab (first time only)
4. **Select a capture region** — click "📐 Select Region" and drag over the Discord stream window
5. **Choose your coaching mode** — Real-time, Strategy, or Post-Play
6. **Hit "Start Coaching"** — the AI will begin analyzing your screen and providing advice!

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
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                 # API key (create from .env.example)
├── config.json          # User settings (auto-created)
├── core/
│   ├── config.py        # Configuration management
│   ├── capture.py       # Screen capture engine
│   ├── analyzer.py      # Gemini AI vision engine
│   └── coach.py         # Coaching orchestrator
├── ui/
│   ├── app.py           # Main application window
│   ├── theme.py         # Dark theme & styling
│   ├── coach_panel.py   # AI coaching message display
│   ├── capture_preview.py   # Live capture preview
│   ├── settings_panel.py    # Settings UI
│   └── region_selector.py   # Screen region picker
└── prompts/
    ├── base_system.txt       # Base coaching system prompt
    ├── realtime_callouts.txt # Real-time mode prompt
    └── post_analysis.txt     # Post-play review prompt
```

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

---

## 📝 License

This project is for **educational purposes only**.
