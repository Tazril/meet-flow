"""Voice Activity Detection (VAD) module using WebRTC VAD."""

import webrtcvad
import numpy as np
from typing import List, Tuple, Optional
import struct

try:
    from ..utils.config import Config
    from ..utils.logger import setup_logger
except ImportError:
    # Handle direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import Config
    from utils.logger import setup_logger

logger = setup_logger("audio.vad")

class VoiceActivityDetector:
    """Detects voice activity in audio streams using WebRTC VAD."""
    
    def __init__(self, 
                 sample_rate: int = None,
                 aggressiveness: int = None,
                 frame_duration_ms: int = 30):
        """Initialize VAD.
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            frame_duration_ms: Frame duration in milliseconds (10, 20, or 30)
        """
        self.sample_rate = sample_rate or Config.SAMPLE_RATE
        self.aggressiveness = aggressiveness or Config.VAD_AGGRESSIVENESS
        self.frame_duration_ms = frame_duration_ms
        
        # Validate sample rate for WebRTC VAD
        valid_rates = [8000, 16000, 32000, 48000]
        if self.sample_rate not in valid_rates:
            logger.warning(f"Sample rate {self.sample_rate} not supported by WebRTC VAD, using 16000")
            self.sample_rate = 16000
        
        # Calculate frame size
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.aggressiveness)
        
        # Speech detection state
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        
        # Thresholds for speech detection
        self.speech_threshold = 5  # Frames needed to start speech
        self.silence_threshold = 10  # Frames needed to end speech
        
        logger.info(f"🗣️  VAD initialized")
        logger.info(f"   Sample Rate: {self.sample_rate}Hz")
        logger.info(f"   Aggressiveness: {self.aggressiveness}")
        logger.info(f"   Frame Duration: {self.frame_duration_ms}ms")
        logger.info(f"   Frame Size: {self.frame_size} samples")
    
    def _convert_to_pcm16(self, audio_data: np.ndarray) -> bytes:
        """Convert float32 audio to PCM16 bytes for WebRTC VAD.
        
        Args:
            audio_data: Audio data as float32 numpy array
            
        Returns:
            PCM16 audio data as bytes
        """
        # Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
        if audio_data.dtype == np.float32:
            audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)
        
        # Convert to bytes
        return audio_int16.tobytes()
    
    def _split_into_frames(self, audio_data: np.ndarray) -> List[np.ndarray]:
        """Split audio data into VAD-compatible frames.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            List of audio frames
        """
        frames = []
        for i in range(0, len(audio_data), self.frame_size):
            frame = audio_data[i:i + self.frame_size]
            
            # Pad frame if necessary
            if len(frame) < self.frame_size:
                frame = np.pad(frame, (0, self.frame_size - len(frame)), 'constant')
            
            frames.append(frame)
        
        return frames
    
    def is_speech_frame(self, audio_frame: np.ndarray) -> bool:
        """Check if a single audio frame contains speech.
        
        Args:
            audio_frame: Audio frame as numpy array
            
        Returns:
            True if frame contains speech
        """
        try:
            # Ensure frame is correct size
            if len(audio_frame) != self.frame_size:
                return False
            
            # Convert to PCM16 bytes
            pcm_data = self._convert_to_pcm16(audio_frame)
            
            # Use WebRTC VAD
            return self.vad.is_speech(pcm_data, self.sample_rate)
            
        except Exception as e:
            logger.error(f"Error in VAD processing: {e}")
            return False
    
    def detect_speech(self, audio_data: np.ndarray) -> Tuple[bool, List[bool]]:
        """Detect speech in audio data.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Tuple of (overall_speech_detected, frame_by_frame_results)
        """
        frames = self._split_into_frames(audio_data)
        frame_results = []
        speech_count = 0
        
        for frame in frames:
            is_speech = self.is_speech_frame(frame)
            frame_results.append(is_speech)
            if is_speech:
                speech_count += 1
        
        # Overall speech detection (majority voting)
        overall_speech = speech_count > len(frames) * 0.3  # 30% threshold
        
        return overall_speech, frame_results
    
    def update_speech_state(self, audio_data: np.ndarray) -> Tuple[bool, bool, bool]:
        """Update speech state with new audio data.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Tuple of (is_speaking_now, speech_started, speech_ended)
        """
        speech_detected, frame_results = self.detect_speech(audio_data)
        
        speech_started = False
        speech_ended = False
        
        if speech_detected:
            self.speech_frames += 1
            self.silence_frames = 0
            
            # Check if speech just started
            if not self.is_speaking and self.speech_frames >= self.speech_threshold:
                self.is_speaking = True
                speech_started = True
                logger.debug("🗣️  Speech started")
        else:
            self.silence_frames += 1
            self.speech_frames = 0
            
            # Check if speech just ended
            if self.is_speaking and self.silence_frames >= self.silence_threshold:
                self.is_speaking = False
                speech_ended = True
                logger.debug("🤫 Speech ended")
        
        return self.is_speaking, speech_started, speech_ended
    
    def get_speech_segments(self, audio_data: np.ndarray, 
                           min_segment_duration: float = 0.5) -> List[Tuple[int, int]]:
        """Get speech segments from audio data.
        
        Args:
            audio_data: Audio data as numpy array
            min_segment_duration: Minimum segment duration in seconds
            
        Returns:
            List of (start_sample, end_sample) tuples for speech segments
        """
        frames = self._split_into_frames(audio_data)
        frame_results = [self.is_speech_frame(frame) for frame in frames]
        
        segments = []
        start_frame = None
        
        for i, is_speech in enumerate(frame_results):
            if is_speech and start_frame is None:
                start_frame = i
            elif not is_speech and start_frame is not None:
                # End of speech segment
                start_sample = start_frame * self.frame_size
                end_sample = i * self.frame_size
                duration = (end_sample - start_sample) / self.sample_rate
                
                if duration >= min_segment_duration:
                    segments.append((start_sample, end_sample))
                
                start_frame = None
        
        # Handle case where audio ends during speech
        if start_frame is not None:
            start_sample = start_frame * self.frame_size
            end_sample = len(audio_data)
            duration = (end_sample - start_sample) / self.sample_rate
            
            if duration >= min_segment_duration:
                segments.append((start_sample, end_sample))
        
        return segments
    
    def extract_speech_audio(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Extract only speech portions from audio data.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Audio data containing only speech segments, or None if no speech
        """
        segments = self.get_speech_segments(audio_data)
        
        if not segments:
            return None
        
        speech_audio = []
        for start, end in segments:
            speech_audio.append(audio_data[start:end])
        
        return np.concatenate(speech_audio) if speech_audio else None
    
    def get_stats(self) -> dict:
        """Get VAD statistics.
        
        Returns:
            Dictionary with VAD statistics
        """
        return {
            'is_speaking': self.is_speaking,
            'speech_frames': self.speech_frames,
            'silence_frames': self.silence_frames,
            'aggressiveness': self.aggressiveness,
            'sample_rate': self.sample_rate,
            'frame_size': self.frame_size
        }
    
    def reset_state(self) -> None:
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        logger.debug("VAD state reset") 