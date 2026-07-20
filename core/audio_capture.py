"""
Audio capture engine for AI Game Coach.
Captures system audio via WASAPI loopback (Windows) for multimodal AI analysis.
Records into a circular buffer and provides WAV bytes for the Gemini API.
"""

import io
import logging
import struct
import threading
import time
import wave
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Try to import sounddevice ────────────────────────────────────────────────
_HAS_SOUNDDEVICE = False
try:
    import sounddevice as sd
    _HAS_SOUNDDEVICE = True
    logger.info("sounddevice available — audio capture supported")
except ImportError:
    logger.warning("sounddevice not installed — audio capture disabled")


class AudioCapture:
    """
    System audio capture engine using WASAPI loopback.

    Captures the system's audio output (what you hear through speakers/headphones)
    into a circular buffer. Provides the buffered audio as WAV bytes for API
    consumption.

    On Windows, uses WASAPI loopback mode for zero-latency system audio capture.
    Does NOT require a microphone — it captures the audio output directly.
    """

    DEFAULT_SAMPLE_RATE = 16000   # 16kHz — good balance for speech/game audio
    DEFAULT_CHANNELS = 1          # Mono — sufficient for AI analysis
    DEFAULT_BUFFER_DURATION = 5.0  # Seconds of audio to keep in the buffer

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
        buffer_duration: float = DEFAULT_BUFFER_DURATION,
    ):
        """
        Args:
            sample_rate: Audio sample rate in Hz.
            channels: Number of audio channels (1=mono, 2=stereo).
            buffer_duration: Duration of the circular audio buffer in seconds.
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._buffer_duration = buffer_duration

        # Circular buffer for audio samples
        buffer_size = int(sample_rate * buffer_duration * channels)
        self._buffer = np.zeros(buffer_size, dtype=np.float32)
        self._buffer_pos = 0
        self._buffer_lock = threading.Lock()
        self._has_data = False

        # Stream state
        self._stream: Optional[object] = None
        self._running = False
        self._device_name: Optional[str] = ""
        self._loopback_device_id: Optional[int] = None

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """Whether audio capture is available on this system."""
        return _HAS_SOUNDDEVICE

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def device_name(self) -> str:
        return self._device_name or "Unknown"

    @property
    def buffer_duration(self) -> float:
        return self._buffer_duration

    @buffer_duration.setter
    def buffer_duration(self, value: float):
        """Update buffer duration. Only takes effect on next start()."""
        self._buffer_duration = max(1.0, min(value, 30.0))

    # ── Device Discovery ─────────────────────────────────────────────────

    def find_loopback_device(self) -> Optional[int]:
        """
        Find a WASAPI loopback device for capturing system audio output.

        Returns the device ID or None if no suitable device is found.
        """
        if not _HAS_SOUNDDEVICE:
            return None

        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()

            # Find the WASAPI host API
            wasapi_index = None
            for i, api in enumerate(hostapis):
                if "WASAPI" in api.get("name", ""):
                    wasapi_index = i
                    break

            if wasapi_index is None:
                logger.warning("WASAPI host API not found — cannot do loopback capture")
                return None

            # Find loopback devices (output devices under WASAPI)
            # In WASAPI, you can open an output device as an input for loopback
            default_output = sd.default.device[1]

            # Try the default output device first
            if default_output is not None and default_output >= 0:
                dev = devices[default_output]
                if dev.get("hostapi") == wasapi_index:
                    self._device_name = dev.get("name", "Default Output")
                    logger.info(f"Using default WASAPI output for loopback: {self._device_name}")
                    return default_output

            # Fallback: find any WASAPI output device
            for i, dev in enumerate(devices):
                if (dev.get("hostapi") == wasapi_index
                        and dev.get("max_output_channels", 0) > 0):
                    self._device_name = dev.get("name", f"Device {i}")
                    logger.info(f"Found WASAPI output for loopback: {self._device_name}")
                    return i

            logger.warning("No WASAPI output device found for loopback")
            return None

        except Exception as e:
            logger.error(f"Error finding loopback device: {e}")
            return None

    def list_audio_devices(self) -> list:
        """List all available audio devices."""
        if not _HAS_SOUNDDEVICE:
            return []

        try:
            devices = sd.query_devices()
            result = []
            for i, dev in enumerate(devices):
                result.append({
                    "id": i,
                    "name": dev.get("name", f"Device {i}"),
                    "max_input_channels": dev.get("max_input_channels", 0),
                    "max_output_channels": dev.get("max_output_channels", 0),
                    "default_samplerate": dev.get("default_samplerate", 0),
                })
            return result
        except Exception as e:
            logger.error(f"Error listing audio devices: {e}")
            return []

    # ── Public API ───────────────────────────────────────────────────────

    def start(self):
        """Start audio capture from the system loopback device."""
        if self._running:
            return

        if not _HAS_SOUNDDEVICE:
            logger.warning("Cannot start audio capture — sounddevice not available")
            return

        # Find loopback device
        self._loopback_device_id = self.find_loopback_device()
        if self._loopback_device_id is None:
            logger.warning("No loopback device found — audio capture disabled")
            return

        # Reinitialize the buffer
        buffer_size = int(self._sample_rate * self._buffer_duration * self._channels)
        with self._buffer_lock:
            self._buffer = np.zeros(buffer_size, dtype=np.float32)
            self._buffer_pos = 0
            self._has_data = False

        try:
            # Open WASAPI loopback stream
            # Setting wasapi_loopback=True tells sounddevice to capture audio output
            extra_settings = sd.WasapiSettings(loopback=True)

            self._stream = sd.InputStream(
                device=self._loopback_device_id,
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=1024,
                extra_settings=extra_settings,
            )
            self._stream.start()
            self._running = True
            logger.info(
                f"Audio capture started: {self._sample_rate}Hz, "
                f"{self._channels}ch, {self._buffer_duration}s buffer, "
                f"device='{self._device_name}'"
            )

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self._running = False
            self._stream = None

    def stop(self):
        """Stop audio capture."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self._stream = None
        logger.info("Audio capture stopped")

    def get_latest_audio_bytes(self, duration: Optional[float] = None) -> Optional[bytes]:
        """
        Get the latest captured audio as WAV bytes.

        Args:
            duration: How many seconds of audio to return (default: full buffer).

        Returns:
            WAV file bytes ready for API consumption, or None if no audio is available.
        """
        if not self._has_data:
            return None

        with self._buffer_lock:
            if duration is not None:
                # Only take the last N seconds
                samples_needed = int(self._sample_rate * duration * self._channels)
                samples_needed = min(samples_needed, len(self._buffer))
            else:
                samples_needed = len(self._buffer)

            # Extract from circular buffer in correct order
            end = self._buffer_pos
            if end >= samples_needed:
                audio_data = self._buffer[end - samples_needed:end].copy()
            else:
                # Wrap around
                part1 = self._buffer[-(samples_needed - end):]
                part2 = self._buffer[:end]
                audio_data = np.concatenate([part1, part2])

        return self._to_wav_bytes(audio_data)

    def get_audio_level(self) -> float:
        """
        Get the current audio level (RMS) as a float between 0.0 and 1.0.
        Useful for UI visualization.
        """
        if not self._has_data:
            return 0.0

        with self._buffer_lock:
            # Use the last 0.1 seconds for a responsive level meter
            samples = int(self._sample_rate * 0.1 * self._channels)
            end = self._buffer_pos
            if end >= samples:
                chunk = self._buffer[end - samples:end]
            else:
                chunk = self._buffer[:end] if end > 0 else self._buffer[:samples]

        rms = np.sqrt(np.mean(chunk ** 2))
        # Normalize to 0-1 range (audio is already float32 in -1..1)
        return min(1.0, rms * 3.0)  # Slight amplification for visibility

    # ── Audio Callback ───────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Sounddevice callback — called from the audio thread.
        Writes incoming audio samples to the circular buffer.
        """
        if status:
            logger.debug(f"Audio callback status: {status}")

        # Flatten to 1D if mono, otherwise interleave
        if self._channels == 1:
            samples = indata[:, 0]
        else:
            samples = indata.flatten()

        with self._buffer_lock:
            n = len(samples)
            buf_len = len(self._buffer)

            if n >= buf_len:
                # More data than buffer — take the last buffer_len samples
                self._buffer[:] = samples[-buf_len:]
                self._buffer_pos = 0
            else:
                # Write into circular buffer
                end = self._buffer_pos + n
                if end <= buf_len:
                    self._buffer[self._buffer_pos:end] = samples
                else:
                    # Wrap around
                    first_part = buf_len - self._buffer_pos
                    self._buffer[self._buffer_pos:] = samples[:first_part]
                    self._buffer[:n - first_part] = samples[first_part:]
                self._buffer_pos = end % buf_len

            self._has_data = True

    # ── WAV Encoding ─────────────────────────────────────────────────────

    def _to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """
        Convert float32 audio samples to WAV file bytes.

        Args:
            audio_data: NumPy array of float32 audio samples (-1.0 to 1.0).

        Returns:
            WAV file bytes (16-bit PCM).
        """
        # Convert float32 to int16
        audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return buf.getvalue()
