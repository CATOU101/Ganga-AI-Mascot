"""
Chacha Chaudhary - Digital Avatar Microphone Audio Capture
Stage 12A: Microphone Capture & WAV Storage

Records microphone audio into uncompressed 16-bit mono 16kHz PCM WAV format.
Storage destination: Output/Audio/Input/

Features:
- Non-blocking start_recording() / stop_recording()
- Deterministic synchronous record_once(duration_seconds)
- Device discovery and validation
- Strict error handling for missing/inaccessible audio hardware
"""

import os
import sys
import wave
import time
import datetime
import threading
from typing import List, Dict, Optional

# Ensure sounddevice & numpy are available
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_CAPTURE_AVAILABLE = True
    CAPTURE_INIT_ERROR = None
except Exception as err:
    AUDIO_CAPTURE_AVAILABLE = False
    CAPTURE_INIT_ERROR = str(err)


class MicrophoneError(Exception):
    """Base exception for microphone capture errors."""
    pass


class MicrophoneNotFoundError(MicrophoneError):
    """Raised when no audio input hardware is detected on the system."""
    pass


class MicrophoneAccessError(MicrophoneError):
    """Raised when audio capture device access or permission fails."""
    pass


class AudioRecordingError(MicrophoneError):
    """Raised when recording fails during capture."""
    pass


class EmptyAudioError(MicrophoneError):
    """Raised when recorded audio is empty or zero-duration."""
    pass


class ChachaMicrophone:
    """
    Manages live microphone audio recording for the Chacha Chaudhary avatar.
    Stores clean 16-bit mono PCM WAV files under Output/Audio/Input/.
    """

    def __init__(self, output_dir: Optional[str] = None, sample_rate: int = 16000, channels: int = 1):
        """
        Initializes the microphone capture interface.
        
        Args:
            output_dir: Destination folder (default: Output/Audio/Input).
            sample_rate: Recording sampling rate in Hz (default: 16000).
            channels: Channel count (default: 1 for mono).
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(base_dir, "Audio", "Input")
        os.makedirs(self.output_dir, exist_ok=True)

        self.sample_rate = sample_rate
        self.channels = channels
        self.last_recorded_path = None

        # Background recording state
        self._is_recording = False
        self._stream = None
        self._recorded_frames: List[np.ndarray] = []
        self._lock = threading.Lock()
        self._active_output_file = None

    def list_microphones(self) -> List[Dict]:
        """
        Lists available microphone input devices on the system.
        
        Returns:
            List of device dictionaries with index, name, and channels.
        """
        if not AUDIO_CAPTURE_AVAILABLE:
            raise MicrophoneNotFoundError(f"Audio capture dependencies unavailable: {CAPTURE_INIT_ERROR}")

        devices = []
        try:
            device_list = sd.query_devices()
            for idx, dev in enumerate(device_list):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append({
                        "index": idx,
                        "name": dev.get("name"),
                        "channels": dev.get("max_input_channels"),
                        "default_samplerate": dev.get("default_samplerate")
                    })
        except Exception as e:
            raise MicrophoneAccessError(f"Error querying audio input devices: {str(e)}")

        return devices

    def _generate_filename(self, prefix: str = "mic_recording") -> str:
        """Generates a timestamped filename inside the output directory."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"{prefix}_{ts}.wav")

    def record_once(self, duration_seconds: float, output_path: Optional[str] = None) -> str:
        """
        Synchronously records audio for a fixed duration from the default microphone.
        
        Args:
            duration_seconds: Recording duration in seconds.
            output_path: Optional destination WAV filepath.
            
        Returns:
            Absolute filepath to the saved WAV recording.
        """
        if not AUDIO_CAPTURE_AVAILABLE:
            raise MicrophoneNotFoundError(f"Audio recording subsystem unavailable: {CAPTURE_INIT_ERROR}")

        if duration_seconds <= 0:
            raise AudioRecordingError(f"Invalid recording duration: {duration_seconds}s. Must be > 0.")

        devices = self.list_microphones()
        if not devices:
            raise MicrophoneNotFoundError("No active microphone or input audio device detected.")

        target_file = output_path or self._generate_filename("recording")
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        num_samples = int(duration_seconds * self.sample_rate)

        try:
            # Synchronous capture via sounddevice
            audio_data = sd.rec(
                frames=num_samples,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16"
            )
            sd.wait()
        except Exception as err:
            raise AudioRecordingError(f"Microphone recording failed: {str(err)}")

        if audio_data is None or len(audio_data) == 0:
            raise EmptyAudioError("Recorded audio buffer is empty.")

        # Save to 16-bit mono PCM WAV
        try:
            with wave.open(target_file, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
        except Exception as err:
            raise AudioRecordingError(f"Failed to write audio file '{target_file}': {str(err)}")

        if not os.path.exists(target_file) or os.path.getsize(target_file) < 44:
            raise EmptyAudioError(f"Created WAV file '{target_file}' is empty or corrupt.")

        self.last_recorded_path = os.path.abspath(target_file)
        return self.last_recorded_path

    def start_recording(self, output_path: Optional[str] = None):
        """
        Begins asynchronous / background microphone recording.
        Call stop_recording() to complete capture and retrieve the saved WAV file.
        """
        if not AUDIO_CAPTURE_AVAILABLE:
            raise MicrophoneNotFoundError(f"Audio recording subsystem unavailable: {CAPTURE_INIT_ERROR}")

        devices = self.list_microphones()
        if not devices:
            raise MicrophoneNotFoundError("No active microphone detected.")

        with self._lock:
            if self._is_recording:
                raise AudioRecordingError("Recording is already in progress.")

            self._active_output_file = output_path or self._generate_filename("async_mic")
            os.makedirs(os.path.dirname(self._active_output_file), exist_ok=True)
            self._recorded_frames = []
            self._is_recording = True

            def _audio_callback(indata, frames, time_info, status):
                if status:
                    pass
                with self._lock:
                    if self._is_recording:
                        self._recorded_frames.append(indata.copy())

            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="int16",
                    callback=_audio_callback
                )
                self._stream.start()
            except Exception as e:
                self._is_recording = False
                raise MicrophoneAccessError(f"Could not open microphone input stream: {str(e)}")

    def stop_recording(self) -> str:
        """
        Stops background recording and writes the captured audio to a WAV file.
        
        Returns:
            Absolute filepath to the saved WAV recording.
        """
        with self._lock:
            if not self._is_recording:
                raise AudioRecordingError("No active recording in progress to stop.")

            self._is_recording = False
            target_path = self._active_output_file

            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

            if not self._recorded_frames:
                raise EmptyAudioError("No audio frames were captured during recording session.")

            captured_data = np.concatenate(self._recorded_frames, axis=0)

        # Write to WAV
        try:
            with wave.open(target_path, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(captured_data.tobytes())
        except Exception as err:
            raise AudioRecordingError(f"Failed to write audio file '{target_path}': {str(err)}")

        if not os.path.exists(target_path) or os.path.getsize(target_path) < 44:
            raise EmptyAudioError(f"Recorded WAV file '{target_path}' is empty or corrupt.")

        self.last_recorded_path = os.path.abspath(target_path)
        return self.last_recorded_path

    def get_audio_path(self) -> Optional[str]:
        """Returns the path to the most recently recorded audio file."""
        return self.last_recorded_path


# Module-level convenience functions
def record_once(duration_seconds: float = 3.0, output_path: Optional[str] = None) -> str:
    """Convenience helper to record a single audio segment."""
    mic = ChachaMicrophone()
    return mic.record_once(duration_seconds=duration_seconds, output_path=output_path)
