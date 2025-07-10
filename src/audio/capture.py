"""Audio capture module for recording from BlackHole input."""

import threading
import time
import numpy as np
import sounddevice as sd
from typing import Callable, Optional, List
from queue import Queue, Empty
import tempfile
import os

try:
    from ..utils.config import Config
    from ..utils.logger import setup_logger, log_audio_info
except ImportError:
    # Handle direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import Config
    from utils.logger import setup_logger, log_audio_info

logger = setup_logger("audio.capture")

class AudioCapture:
    """Handles audio capture from BlackHole input device."""
    
    def __init__(self, 
                 sample_rate: int = None,
                 buffer_size: int = None,
                 device: Optional[str] = None):
        """Initialize audio capture.
        
        Args:
            sample_rate: Audio sample rate (default from config)
            buffer_size: Buffer size for audio chunks (default from config)  
            device: Input device name (auto-detect BlackHole if None)
        """
        self.sample_rate = sample_rate or Config.SAMPLE_RATE
        self.buffer_size = buffer_size or Config.BUFFER_SIZE
        self.device = device
        
        self.audio_queue = Queue()
        self.recording = False
        self.stream = None
        self._recording_thread = None
        
        # Auto-detect BlackHole device
        if not self.device:
            self.device = self._find_blackhole_device()
            
        logger.info(f"🎤 Audio capture initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Sample Rate: {self.sample_rate}Hz")
        logger.info(f"   Buffer Size: {self.buffer_size}")
    
    def _find_blackhole_device(self) -> Optional[str]:
        """Find BlackHole input device automatically."""
        try:
            devices = sd.query_devices()
            for device in devices:
                if isinstance(device, dict) and 'BlackHole' in device.get('name', ''):
                    if device.get('max_input_channels', 0) > 0:
                        logger.info(f"🔍 Found BlackHole device: {device['name']}")
                        log_audio_info(logger, device)
                        return device['name']
        except Exception as e:
            logger.error(f"Error finding BlackHole device: {e}")
        
        logger.warning("⚠️  BlackHole device not found, using default input")
        return None
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if self.recording:
            # Convert to mono if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata[:, 0]
            
            # Add to queue
            self.audio_queue.put(audio_data.copy())
    
    def start_recording(self) -> bool:
        """Start audio recording.
        
        Returns:
            bool: True if recording started successfully
        """
        if self.recording:
            logger.warning("Recording already in progress")
            return True
        
        try:
            # Find device index
            device_index = None
            if self.device:
                devices = sd.query_devices()
                for i, device in enumerate(devices):
                    if isinstance(device, dict) and device.get('name') == self.device:
                        device_index = i
                        break
            
            # Start audio stream
            self.stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback,
                dtype=np.float32
            )
            
            self.stream.start()
            self.recording = True
            
            logger.info("🎵 Audio recording started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> None:
        """Stop audio recording."""
        if not self.recording:
            return
        
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        logger.info("🛑 Audio recording stopped")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get the next audio chunk from the queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Audio data as numpy array or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_audio_buffer(self, duration: float) -> Optional[np.ndarray]:
        """Get audio buffer for specified duration.
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Concatenated audio data or None if insufficient data
        """
        if not self.recording:
            logger.warning("Not recording - cannot get audio buffer")
            return None
        
        chunks = []
        start_time = time.time()
        expected_samples = int(duration * self.sample_rate)
        collected_samples = 0
        
        while collected_samples < expected_samples and (time.time() - start_time) < duration * 2:
            chunk = self.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                chunks.append(chunk)
                collected_samples += len(chunk)
        
        if not chunks:
            return None
        
        # Concatenate chunks
        audio_buffer = np.concatenate(chunks)
        
        # Trim to exact duration if we have too much
        if len(audio_buffer) > expected_samples:
            audio_buffer = audio_buffer[:expected_samples]
        
        logger.debug(f"Collected audio buffer: {len(audio_buffer)} samples ({len(audio_buffer)/self.sample_rate:.2f}s)")
        return audio_buffer
    
    def save_audio_to_wav(self, audio_data: np.ndarray, filename: Optional[str] = None) -> str:
        """Save audio data to WAV file.
        
        Args:
            audio_data: Audio data as numpy array
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"/tmp/gmeet_audio_{timestamp}.wav"
        
        # Ensure audio is in correct format
        if audio_data.dtype != np.int16:
            # Convert from float32 to int16
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Use scipy to write WAV file
        from scipy.io.wavfile import write
        write(filename, self.sample_rate, audio_data)
        
        logger.debug(f"Audio saved to: {filename}")
        return filename
    
    def get_device_info(self) -> dict:
        """Get information about the current audio device."""
        try:
            if self.stream:
                return {
                    'device': self.device,
                    'sample_rate': self.sample_rate,
                    'buffer_size': self.buffer_size,
                    'recording': self.recording,
                    'queue_size': self.audio_queue.qsize()
                }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
        
        return {}
    
    def clear_buffer(self) -> None:
        """Clear the audio buffer queue."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break
        logger.debug("Audio buffer cleared")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_recording()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_recording() 