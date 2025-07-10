"""Audio/Video input module for browser automation."""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Union
import numpy as np

try:
    from ..audio.playback import AudioPlayback
    from ..utils.logger import setup_logger
except ImportError:
    # Handle direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from audio.playback import AudioPlayback
    from utils.logger import setup_logger

logger = setup_logger("browser.av_input")

class AudioVideoInput:
    """Handles audio and video input injection for browser automation."""
    
    def __init__(self):
        """Initialize AV input system."""
        self.audio_playback = AudioPlayback()
        logger.info("🎬 AudioVideo Input system initialized")
    
    def inject_audio_file(self, file_path: Union[str, Path], blocking: bool = True) -> bool:
        """Inject audio from file into the meeting via BlackHole.
        
        Args:
            file_path: Path to audio file (WAV, MP3)
            blocking: Whether to wait for playback to complete
            
        Returns:
            True if successfully injected
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Audio file not found: {file_path}")
                return False
            
            logger.info(f"🎵 Injecting audio file: {file_path.name}")
            success = self.audio_playback.play_audio_file(file_path, blocking=blocking)
            
            if success:
                logger.info("✅ Audio injection completed")
            else:
                logger.error("❌ Audio injection failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error injecting audio file: {e}")
            return False
    
    def inject_audio_data(self, audio_data: np.ndarray, blocking: bool = True) -> bool:
        """Inject raw audio data into the meeting via BlackHole.
        
        Args:
            audio_data: Audio data as numpy array
            blocking: Whether to wait for playback to complete
            
        Returns:
            True if successfully injected
        """
        try:
            logger.info(f"🎵 Injecting audio data: {len(audio_data)} samples")
            success = self.audio_playback.play_audio_data(audio_data, blocking=blocking)
            
            if success:
                logger.info("✅ Audio data injection completed")
            else:
                logger.error("❌ Audio data injection failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error injecting audio data: {e}")
            return False
    
    def inject_tts_text(self, text: str, voice: str = "alloy", blocking: bool = True) -> bool:
        """Convert text to speech and inject into meeting.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for TTS
            blocking: Whether to wait for playback to complete
            
        Returns:
            True if successfully injected
        """
        try:
            logger.info(f"🗣️  Converting text to speech: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # This will be enhanced when we add TTS integration
            # For now, use the playback system's TTS placeholder
            success = self.audio_playback.play_tts_response(text, voice)
            
            if success:
                logger.info("✅ TTS injection completed")
            else:
                logger.warning("⚠️  TTS not yet implemented - placeholder used")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error injecting TTS: {e}")
            return False
    
    def inject_audio_with_ffmpeg(self, file_path: Union[str, Path]) -> bool:
        """Inject audio using ffmpeg (alternative method).
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if successfully injected
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Audio file not found: {file_path}")
                return False
            
            logger.info(f"🎵 Injecting audio with ffmpeg: {file_path.name}")
            
            # Use ffplay to play audio (will route through default output)
            cmd = [
                "ffplay",
                "-nodisp",           # No video display
                "-autoexit",         # Exit when done
                "-loglevel", "quiet", # Suppress ffmpeg logs
                str(file_path)
            ]
            
            try:
                result = subprocess.run(cmd, check=True, capture_output=True)
                logger.info("✅ FFmpeg audio injection completed")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed: {e}")
                return False
            except FileNotFoundError:
                logger.error("FFmpeg not found - install with 'brew install ffmpeg'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error with ffmpeg injection: {e}")
            return False
    
    def inject_test_tone(self, frequency: float = 440.0, duration: float = 2.0) -> bool:
        """Inject a test tone into the meeting.
        
        Args:
            frequency: Tone frequency in Hz
            duration: Duration in seconds
            
        Returns:
            True if successfully injected
        """
        try:
            logger.info(f"🎵 Injecting test tone: {frequency}Hz for {duration}s")
            success = self.audio_playback.test_playback(frequency, duration)
            
            if success:
                logger.info("✅ Test tone injection completed")
            else:
                logger.error("❌ Test tone injection failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error injecting test tone: {e}")
            return False
    
    def stop_audio_injection(self) -> bool:
        """Stop any current audio injection.
        
        Returns:
            True if successfully stopped
        """
        try:
            self.audio_playback.stop_playback()
            logger.info("🛑 Audio injection stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping audio injection: {e}")
            return False
    
    def wait_for_injection_complete(self, timeout: float = 30.0) -> bool:
        """Wait for current audio injection to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if completed, False if timeout
        """
        try:
            return self.audio_playback.wait_for_playback_complete(timeout)
        except Exception as e:
            logger.error(f"❌ Error waiting for injection: {e}")
            return False
    
    def get_injection_status(self) -> dict:
        """Get status of audio injection system.
        
        Returns:
            Dictionary with injection status
        """
        try:
            playback_info = self.audio_playback.get_device_info()
            return {
                "system": "AudioVideo Input",
                "audio_playback": playback_info,
                "available_methods": ["audio_file", "audio_data", "tts_text", "ffmpeg", "test_tone"]
            }
        except Exception as e:
            logger.error(f"Error getting injection status: {e}")
            return {"error": str(e)} 