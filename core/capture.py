"""
Screen capture engine for AI Game Coach.
Uses DXcam (Windows, high-performance) with MSS as a cross-platform fallback.
Captures frames as NumPy arrays and converts to JPEG for the Gemini API.
"""

import io
import threading
import time
import logging
from typing import Optional, Tuple, Callable

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ── Try to import DXcam first (Windows-only, high performance) ──────────────
_HAS_DXCAM = False
try:
    import dxcam
    # DXcam internally requires cv2 — verify it's available
    import cv2 as _cv2_check  # noqa: F401
    _HAS_DXCAM = True
    logger.info("DXcam available — using high-performance DirectX capture")
except ImportError:
    logger.info("DXcam not available — falling back to MSS")

import mss


class ScreenCapture:
    """
    High-performance screen capture engine.

    Captures frames from a configurable screen region at a target FPS.
    Frames are returned as PIL Images or JPEG bytes for API consumption.
    """

    # Target resolution for Gemini API (recommended 768×768)
    GEMINI_TARGET_SIZE = (768, 768)

    def __init__(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        target_fps: int = 2,
        on_frame: Optional[Callable] = None,
    ):
        """
        Args:
            region: Capture region as (left, top, right, bottom). None = full primary screen.
            target_fps: Target frames per second for capture loop.
            on_frame: Callback invoked with each captured PIL.Image frame.
        """
        self._region = region
        self._target_fps = max(1, min(target_fps, 30))
        self._on_frame = on_frame

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._latest_frame: Optional[Image.Image] = None
        self._frame_count = 0
        self._fps_actual = 0.0

        # DXcam camera instance (lazily initialized)
        self._dxcam_camera = None

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def region(self) -> Optional[Tuple[int, int, int, int]]:
        return self._region

    @region.setter
    def region(self, value: Optional[Tuple[int, int, int, int]]):
        with self._lock:
            self._region = value
        # If running with DXcam, restart the capture with the new region
        if self._running and _HAS_DXCAM and self._dxcam_camera:
            self._restart_dxcam()

    @property
    def target_fps(self) -> int:
        return self._target_fps

    @target_fps.setter
    def target_fps(self, value: int):
        self._target_fps = max(1, min(value, 30))

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def actual_fps(self) -> float:
        return self._fps_actual

    @property
    def latest_frame(self) -> Optional[Image.Image]:
        """Get the most recently captured frame as a PIL Image."""
        with self._lock:
            return self._latest_frame

    # ── Public API ───────────────────────────────────────────────────────

    def grab_single(self) -> Optional[Image.Image]:
        """Capture a single frame immediately (blocking)."""
        try:
            if _HAS_DXCAM:
                return self._grab_dxcam()
            else:
                return self._grab_mss()
        except Exception as e:
            logger.error(f"Single frame capture failed: {e}")
            return None

    def start(self):
        """Start continuous capture in a background thread."""
        if self._running:
            return
        self._running = True
        self._frame_count = 0
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Screen capture started at {self._target_fps} FPS")

    def stop(self):
        """Stop the capture loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        if self._dxcam_camera:
            try:
                self._dxcam_camera.stop()
            except Exception:
                pass
            self._dxcam_camera = None
        logger.info("Screen capture stopped")

    @staticmethod
    def frame_to_jpeg_bytes(frame: Image.Image, quality: int = 80) -> bytes:
        """Convert a PIL Image to JPEG bytes for API consumption."""
        buf = io.BytesIO()
        # Ensure RGB mode (no alpha channel)
        if frame.mode != "RGB":
            frame = frame.convert("RGB")
        frame.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()

    def get_latest_jpeg(self, resize_for_api: bool = True) -> Optional[bytes]:
        """Get the latest frame as JPEG bytes, optionally resized for Gemini."""
        frame = self.latest_frame
        if frame is None:
            return None
        if resize_for_api:
            frame = self._resize_for_gemini(frame)
        return self.frame_to_jpeg_bytes(frame)

    # ── Capture Loop ─────────────────────────────────────────────────────

    def _capture_loop(self):
        """Main capture loop running in a background thread."""
        interval = 1.0 / self._target_fps
        fps_start = time.time()
        fps_frames = 0

        while self._running:
            loop_start = time.time()

            try:
                if _HAS_DXCAM:
                    frame = self._grab_dxcam()
                else:
                    frame = self._grab_mss()

                if frame is not None:
                    with self._lock:
                        self._latest_frame = frame
                        self._frame_count += 1
                    fps_frames += 1

                    # Invoke callback
                    if self._on_frame:
                        try:
                            self._on_frame(frame)
                        except Exception as e:
                            logger.error(f"Frame callback error: {e}")

            except Exception as e:
                logger.error(f"Capture error: {e}")

            # Calculate actual FPS every second
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                self._fps_actual = fps_frames / elapsed
                fps_frames = 0
                fps_start = time.time()

            # Sleep to maintain target FPS
            work_time = time.time() - loop_start
            sleep_time = max(0, interval - work_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ── DXcam Backend ────────────────────────────────────────────────────

    def _grab_dxcam(self) -> Optional[Image.Image]:
        """Capture a single frame using DXcam."""
        if self._dxcam_camera is None:
            self._dxcam_camera = dxcam.create(output_color="BGR")

        region = self._region
        frame_np = self._dxcam_camera.grab(region=region)
        if frame_np is None:
            return None

        # DXcam returns BGR numpy array — convert to RGB PIL Image
        frame_rgb = frame_np[:, :, ::-1]  # BGR → RGB
        return Image.fromarray(frame_rgb)

    def _restart_dxcam(self):
        """Restart DXcam capture with updated region."""
        if self._dxcam_camera:
            try:
                self._dxcam_camera.stop()
            except Exception:
                pass
            self._dxcam_camera = None

    # ── MSS Backend (Fallback) ───────────────────────────────────────────

    def _grab_mss(self) -> Optional[Image.Image]:
        """Capture a single frame using MSS (cross-platform fallback)."""
        with mss.mss() as sct:
            if self._region:
                left, top, right, bottom = self._region
                monitor = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top,
                }
            else:
                monitor = sct.monitors[1]  # Primary monitor

            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # ── Utilities ────────────────────────────────────────────────────────

    def _resize_for_gemini(self, frame: Image.Image) -> Image.Image:
        """Resize frame to the recommended Gemini input resolution while preserving aspect ratio."""
        target_w, target_h = self.GEMINI_TARGET_SIZE
        orig_w, orig_h = frame.size

        # Calculate scale to fit within target while preserving aspect ratio
        scale = min(target_w / orig_w, target_h / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        return frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def get_screen_dimensions(self) -> Tuple[int, int]:
        """Get the primary screen dimensions."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            return monitor["width"], monitor["height"]
