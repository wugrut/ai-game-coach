"""
AI Game Coach — Main Entry Point

An AI-powered educational tool that captures Discord video streams
and provides real-time gameplay coaching using Google Gemini vision.

Usage:
    python main.py                  Launch the app
    python main.py --test-capture   Test screen capture
    python main.py --test-api       Test Gemini API connection
"""

import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ai-game-coach")


def test_capture():
    """Test screen capture by saving a single screenshot."""
    from core.capture import ScreenCapture
    from pathlib import Path

    print("Testing screen capture...")
    capture = ScreenCapture()

    # Get screen dimensions
    w, h = capture.get_screen_dimensions()
    print(f"  Screen size: {w}x{h}")

    # Take a screenshot
    frame = capture.grab_single()
    if frame:
        save_path = Path(__file__).parent / "test_capture.png"
        frame.save(str(save_path))
        print(f"  [OK] Screenshot saved to: {save_path}")
        print(f"  Frame size: {frame.size}")
    else:
        print("  [FAIL] Failed to capture screenshot")
        sys.exit(1)


def test_api():
    """Test Gemini API connection."""
    from core.analyzer import GeminiAnalyzer
    from core.config import config

    print("Testing Gemini API connection...")
    print(f"  API Key configured: {'Yes' if config.is_api_key_set else 'No'}")

    if not config.is_api_key_set:
        print("  [FAIL] No API key found. Set GEMINI_API_KEY in .env file")
        print("  Tip: Copy .env.example to .env and add your key")
        sys.exit(1)

    analyzer = GeminiAnalyzer()
    success, message = analyzer.test_connection()

    if success:
        print(f"  [OK] {message}")
    else:
        print(f"  [FAIL] {message}")
        sys.exit(1)


def main():
    """Launch the AI Game Coach application."""
    parser = argparse.ArgumentParser(
        description="AI Game Coach — Educational gameplay coaching powered by Gemini AI",
    )
    parser.add_argument(
        "--test-capture", action="store_true",
        help="Test screen capture (saves a screenshot)",
    )
    parser.add_argument(
        "--test-api", action="store_true",
        help="Test Gemini API connection",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test_capture:
        test_capture()
        return

    if args.test_api:
        test_api()
        return

    # Launch the GUI
    logger.info("Starting AI Game Coach...")
    from ui.app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
