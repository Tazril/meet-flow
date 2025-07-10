"""Audio/Video output module for browser automation."""

import time
from typing import Optional, Callable, Any
import numpy as np
from pathlib import Path

try:
    from ..audio.capture import AudioCapture
    from ..audio.vad import VoiceActivityDetector
    from ..utils.logger import setup_logger
except ImportError:
    # Handle direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from audio.capture import AudioCapture
    from audio.vad import VoiceActivityDetector
    from utils.logger import setup_logger

logger = setup_logger("browser.av_output")

class AudioVideoOutput:
    """Handles audio and video output capture for browser automation."""
    
    def __init__(self):
        """Initialize AV output system."""
        self.audio_capture = AudioCapture()
        self.vad = VoiceActivityDetector()
        self.capturing = False
        self.audio_callback: Optional[Callable] = None
        logger.info("🎤 AudioVideo Output system initialized")
    
    def start_audio_capture(self, callback: Optional[Callable] = None) -> bool:
        """Start capturing audio from the meeting.
        
        Args:
            callback: Optional callback function for real-time audio processing
            
        Returns:
            True if successfully started
        """
        try:
            if self.capturing:
                logger.warning("Audio capture already running")
                return True
            
            logger.info("🎵 Starting audio capture from meeting...")
            self.audio_callback = callback
            success = self.audio_capture.start_recording()
            
            if success:
                self.capturing = True
                logger.info("✅ Audio capture started")
            else:
                logger.error("❌ Failed to start audio capture")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error starting audio capture: {e}")
            return False
    
    def stop_audio_capture(self) -> bool:
        """Stop capturing audio from the meeting.
        
        Returns:
            True if successfully stopped
        """
        try:
            if not self.capturing:
                logger.warning("Audio capture not running")
                return True
            
            self.audio_capture.stop_recording()
            self.capturing = False
            self.audio_callback = None
            logger.info("🛑 Audio capture stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping audio capture: {e}")
            return False
    
    def capture_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Capture a single audio chunk.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Audio data as numpy array or None
        """
        try:
            if not self.capturing:
                logger.warning("Audio capture not running")
                return None
            
            chunk = self.audio_capture.get_audio_chunk(timeout)
            
            # Call callback if provided
            if chunk is not None and self.audio_callback:
                try:
                    self.audio_callback(chunk)
                except Exception as e:
                    logger.error(f"Error in audio callback: {e}")
            
            return chunk
            
        except Exception as e:
            logger.error(f"❌ Error capturing audio chunk: {e}")
            return None
    
    def capture_audio_buffer(self, duration: float) -> Optional[np.ndarray]:
        """Capture audio for a specific duration.
        
        Args:
            duration: Duration in seconds to capture
            
        Returns:
            Audio data as numpy array or None
        """
        try:
            if not self.capturing:
                logger.warning("Audio capture not running")
                return None
            
            logger.info(f"🎵 Capturing audio buffer for {duration}s...")
            audio_buffer = self.audio_capture.get_audio_buffer(duration)
            
            if audio_buffer is not None:
                logger.info(f"✅ Captured {len(audio_buffer)} samples")
            else:
                logger.warning("⚠️  No audio captured")
            
            return audio_buffer
            
        except Exception as e:
            logger.error(f"❌ Error capturing audio buffer: {e}")
            return None
    
    def capture_speech_segment(self, max_duration: float = 10.0, 
                              silence_timeout: float = 3.0) -> Optional[np.ndarray]:
        """Capture a speech segment using voice activity detection.
        
        Args:
            max_duration: Maximum duration to capture in seconds
            silence_timeout: Seconds of silence before stopping capture
            
        Returns:
            Audio data containing speech or None
        """
        try:
            if not self.capturing:
                logger.warning("Audio capture not running")
                return None
            
            logger.info("🗣️  Waiting for speech...")
            
            audio_chunks = []
            speech_detected = False
            silence_duration = 0.0
            start_time = time.time()
            
            while (time.time() - start_time) < max_duration:
                # Get audio chunk
                chunk = self.capture_audio_chunk(timeout=0.1)
                if chunk is None:
                    continue
                
                audio_chunks.append(chunk)
                
                # Check for speech in this chunk
                is_speaking, speech_started, speech_ended = self.vad.update_speech_state(chunk)
                
                if speech_started:
                    logger.debug("🗣️  Speech started")
                    speech_detected = True
                    silence_duration = 0.0
                
                if speech_ended:
                    logger.debug("🤫 Speech ended")
                    silence_duration = 0.0
                
                # Track silence duration
                if speech_detected and not is_speaking:
                    silence_duration += len(chunk) / self.audio_capture.sample_rate
                    
                    if silence_duration >= silence_timeout:
                        logger.info(f"✅ Speech segment captured ({silence_duration:.1f}s silence)")
                        break
            
            if not audio_chunks:
                logger.warning("No audio captured")
                return None
            
            # Concatenate all chunks
            full_audio = np.concatenate(audio_chunks)
            
            # Extract only speech portions if speech was detected
            if speech_detected:
                speech_audio = self.vad.extract_speech_audio(full_audio)
                if speech_audio is not None:
                    logger.info(f"🗣️  Extracted speech: {len(speech_audio)/self.audio_capture.sample_rate:.2f}s")
                    return speech_audio
            
            # Return full audio if no speech extraction possible
            logger.info(f"📼 Captured audio segment: {len(full_audio)/self.audio_capture.sample_rate:.2f}s")
            return full_audio
            
        except Exception as e:
            logger.error(f"❌ Error capturing speech segment: {e}")
            return None
    
    def save_captured_audio(self, audio_data: np.ndarray, 
                           filename: Optional[str] = None) -> Optional[str]:
        """Save captured audio to file.
        
        Args:
            audio_data: Audio data to save
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            if audio_data is None or audio_data.size == 0:
                logger.error("No audio data to save")
                return None
            
            filepath = self.audio_capture.save_audio_to_wav(audio_data, filename)
            logger.info(f"💾 Audio saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error saving audio: {e}")
            return None
    
    def get_vad_stats(self) -> dict:
        """Get voice activity detection statistics.
        
        Returns:
            Dictionary with VAD stats
        """
        try:
            return self.vad.get_stats()
        except Exception as e:
            logger.error(f"Error getting VAD stats: {e}")
            return {}
    
    def reset_vad(self) -> None:
        """Reset voice activity detection state."""
        try:
            self.vad.reset_state()
            logger.info("🔄 VAD state reset")
        except Exception as e:
            logger.error(f"Error resetting VAD: {e}")
    
    def is_speech_detected(self, audio_data: np.ndarray) -> bool:
        """Check if speech is detected in audio data.
        
        Args:
            audio_data: Audio data to analyze
            
        Returns:
            True if speech detected
        """
        try:
            speech_detected, _ = self.vad.detect_speech(audio_data)
            return speech_detected
        except Exception as e:
            logger.error(f"Error detecting speech: {e}")
            return False
    
    def get_capture_status(self) -> dict:
        """Get status of audio capture system.
        
        Returns:
            Dictionary with capture status
        """
        try:
            capture_info = self.audio_capture.get_device_info()
            vad_stats = self.get_vad_stats()
            
            return {
                "system": "AudioVideo Output", 
                "capturing": self.capturing,
                "audio_capture": capture_info,
                "vad_stats": vad_stats,
                "callback_enabled": self.audio_callback is not None
            }
        except Exception as e:
            logger.error(f"Error getting capture status: {e}")
            return {"error": str(e)}
    
    def clear_audio_buffer(self) -> None:
        """Clear the audio capture buffer."""
        try:
            self.audio_capture.clear_buffer()
            logger.info("🗑️  Audio buffer cleared")
        except Exception as e:
            logger.error(f"Error clearing audio buffer: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_audio_capture()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_audio_capture() 