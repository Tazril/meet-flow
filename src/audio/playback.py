"""Audio playback module for injecting TTS audio into BlackHole output."""

import sounddevice as sd
import numpy as np
import threading
import time
from typing import Optional, Union
from pathlib import Path
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

logger = setup_logger("audio.playback")

class AudioPlayback:
    """Handles audio playback to BlackHole output device for Google Meet microphone injection."""
    
    def __init__(self, 
                 sample_rate: int = None,
                 device: Optional[str] = None):
        """Initialize audio playback.
        
        Args:
            sample_rate: Audio sample rate (default from config)
            device: Output device name (auto-detect BlackHole if None)
        """
        self.sample_rate = sample_rate or Config.SAMPLE_RATE
        self.device = device
        self.playing = False
        
        # Auto-detect BlackHole device
        if not self.device:
            self.device = self._find_blackhole_output_device()
            
        logger.info(f"🔊 Audio playback initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Sample Rate: {self.sample_rate}Hz")
    
    def _find_blackhole_output_device(self) -> Optional[str]:
        """Find BlackHole output device automatically."""
        try:
            devices = sd.query_devices()
            for device in devices:
                if isinstance(device, dict) and 'BlackHole' in device.get('name', ''):
                    if device.get('max_output_channels', 0) > 0:
                        logger.info(f"🔍 Found BlackHole output device: {device['name']}")
                        log_audio_info(logger, device)
                        return device['name']
        except Exception as e:
            logger.error(f"Error finding BlackHole output device: {e}")
        
        logger.warning("⚠️  BlackHole output device not found, using default output")
        return None
    
    def play_audio_data(self, audio_data: np.ndarray, blocking: bool = True) -> bool:
        """Play audio data directly.
        
        Args:
            audio_data: Audio data as numpy array
            blocking: If True, wait for playback to complete
            
        Returns:
            True if playback started successfully
        """
        try:
            # Find device index
            device_index = None
            if self.device:
                devices = sd.query_devices()
                for i, device in enumerate(devices):
                    if isinstance(device, dict) and device.get('name') == self.device:
                        device_index = i
                        break
            
            # Ensure audio is in correct format
            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32767.0
                else:
                    audio_data = audio_data.astype(np.float32)
            
            # Ensure audio is mono -> stereo for output
            if len(audio_data.shape) == 1:
                # Convert mono to stereo
                audio_data = np.column_stack((audio_data, audio_data))
            
            self.playing = True
            
            # Play audio
            sd.play(audio_data, 
                   samplerate=self.sample_rate, 
                   device=device_index,
                   blocking=blocking)
            
            logger.info(f"🎵 Playing audio: {len(audio_data)} samples ({len(audio_data)/self.sample_rate:.2f}s)")
            
            if blocking:
                self.playing = False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            self.playing = False
            return False
    
    def play_audio_file(self, file_path: Union[str, Path], blocking: bool = True) -> bool:
        """Play audio from file.
        
        Args:
            file_path: Path to audio file
            blocking: If True, wait for playback to complete
            
        Returns:
            True if playback started successfully
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Audio file not found: {file_path}")
                return False
            
            # Load audio file based on extension
            if file_path.suffix.lower() in ['.wav']:
                audio_data, file_sample_rate = self._load_wav_file(file_path)
            elif file_path.suffix.lower() in ['.mp3']:
                audio_data, file_sample_rate = self._load_mp3_file(file_path)
            else:
                logger.error(f"Unsupported audio format: {file_path.suffix}")
                return False
            
            # Resample if necessary
            if file_sample_rate != self.sample_rate:
                audio_data = self._resample_audio(audio_data, file_sample_rate, self.sample_rate)
            
            return self.play_audio_data(audio_data, blocking=blocking)
            
        except Exception as e:
            logger.error(f"Failed to play audio file {file_path}: {e}")
            return False
    
    def _load_wav_file(self, file_path: Path) -> tuple:
        """Load WAV file using scipy."""
        from scipy.io.wavfile import read
        sample_rate, audio_data = read(file_path)
        
        # Convert to float32
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32767.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483647.0
        
        return audio_data, sample_rate
    
    def _load_mp3_file(self, file_path: Path) -> tuple:
        """Load MP3 file using pydub."""
        try:
            from pydub import AudioSegment
            
            # Load MP3
            audio = AudioSegment.from_mp3(str(file_path))
            
            # Convert to numpy array
            audio_data = np.array(audio.get_array_of_samples(), dtype=np.float32)
            
            # Normalize
            if audio.sample_width == 2:  # 16-bit
                audio_data = audio_data / 32767.0
            elif audio.sample_width == 4:  # 32-bit
                audio_data = audio_data / 2147483647.0
            
            # Handle stereo
            if audio.channels == 2:
                audio_data = audio_data.reshape((-1, 2))
            
            return audio_data, audio.frame_rate
            
        except ImportError:
            logger.error("pydub not available for MP3 playback")
            return None, None
    
    def _resample_audio(self, audio_data: np.ndarray, 
                       original_rate: int, 
                       target_rate: int) -> np.ndarray:
        """Resample audio data to target sample rate."""
        try:
            from scipy import signal
            
            # Calculate resampling ratio
            ratio = target_rate / original_rate
            
            # Resample
            if len(audio_data.shape) == 1:
                # Mono
                resampled = signal.resample(audio_data, 
                                          int(len(audio_data) * ratio))
            else:
                # Stereo - resample each channel
                resampled = np.column_stack([
                    signal.resample(audio_data[:, 0], int(len(audio_data) * ratio)),
                    signal.resample(audio_data[:, 1], int(len(audio_data) * ratio))
                ])
            
            logger.debug(f"Resampled audio from {original_rate}Hz to {target_rate}Hz")
            return resampled.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to resample audio: {e}")
            return audio_data
    
    def play_tts_response(self, text: str, voice: str = "alloy") -> bool:
        """Play text-to-speech response (placeholder for TTS integration).
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for TTS
            
        Returns:
            True if TTS and playback successful
        """
        # This will be implemented when we add the TTS module
        logger.info(f"🗣️  TTS Playback requested: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        logger.warning("TTS integration not yet implemented - this is a placeholder")
        return False
    
    def stop_playback(self) -> None:
        """Stop current audio playback."""
        try:
            sd.stop()
            self.playing = False
            logger.info("🛑 Audio playback stopped")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    def wait_for_playback_complete(self, timeout: float = 30.0) -> bool:
        """Wait for current playback to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if playback completed, False if timeout
        """
        start_time = time.time()
        while self.playing and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        return not self.playing
    
    def get_device_info(self) -> dict:
        """Get information about the current audio output device."""
        try:
            return {
                'device': self.device,
                'sample_rate': self.sample_rate,
                'playing': self.playing
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}
    
    def test_playback(self, frequency: float = 440.0, duration: float = 1.0) -> bool:
        """Test audio playback with a sine wave tone.
        
        Args:
            frequency: Tone frequency in Hz
            duration: Duration in seconds
            
        Returns:
            True if test successful
        """
        try:
            # Generate sine wave
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            tone = np.sin(2 * np.pi * frequency * t) * 0.3  # 30% volume
            
            logger.info(f"🎵 Testing playback with {frequency}Hz tone for {duration}s")
            return self.play_audio_data(tone, blocking=True)
            
        except Exception as e:
            logger.error(f"Playback test failed: {e}")
            return False 