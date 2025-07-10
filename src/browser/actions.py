"""Meeting actions controller for orchestrating browser automation."""

import time
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from .base_interface import BrowserAutomationAgent
from .gmeet_agent import GMeetAgent
from .av_input import AudioVideoInput
from .av_output import AudioVideoOutput

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

logger = setup_logger("browser.actions")

class MeetingController:
    """High-level controller for managing meeting automation."""
    
    def __init__(self, 
                 agent_type: str = "gmeet",
                 headless: bool = False,
                 auto_setup_audio: bool = True,
                 chrome_profile_path: Optional[str] = None,
                 use_chrome_profile: bool = True):
        """Initialize meeting controller.
        
        Args:
            agent_type: Type of meeting agent ("gmeet" for now)
            headless: Whether to run browser in headless mode
            auto_setup_audio: Whether to automatically set up audio I/O
            chrome_profile_path: Path to Chrome profile directory
            use_chrome_profile: Whether to use persistent Chrome profile
        """
        self.agent_type = agent_type
        self.headless = headless
        
        # Initialize browser agent
        if agent_type.lower() == "gmeet":
            self.agent: BrowserAutomationAgent = GMeetAgent(
                headless=headless,
                chrome_profile_path=chrome_profile_path,
                use_chrome_profile=use_chrome_profile
            )
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        # Initialize audio I/O if requested
        self.av_input: Optional[AudioVideoInput] = None
        self.av_output: Optional[AudioVideoOutput] = None
        
        if auto_setup_audio:
            self.av_input = AudioVideoInput()
            self.av_output = AudioVideoOutput()
        
        # State tracking
        self.meeting_active = False
        self.audio_capture_active = False
        
        logger.info(f"🎬 Meeting Controller initialized ({agent_type}, headless={headless}, profile={use_chrome_profile})")
    
    def join_meeting(self, 
                    url: Optional[str] = None, 
                    display_name: Optional[str] = None,
                    start_audio_capture: bool = True) -> bool:
        """Join a meeting and optionally start audio capture.
        
        Args:
            url: Meeting URL (uses config if None)
            display_name: Display name (uses config if None)
            start_audio_capture: Whether to start capturing audio
            
        Returns:
            True if successfully joined
        """
        try:
            # Use config values if not provided
            url = url or Config.GMEET_URL
            display_name = display_name or Config.AGENT_NAME
            
            if not url:
                logger.error("No meeting URL provided")
                return False
            
            logger.info(f"🚀 Joining meeting as '{display_name}'...")
            
            # Join the meeting
            success = self.agent.join_meeting(url, display_name)
            
            if success:
                self.meeting_active = True
                logger.info("✅ Successfully joined meeting")
                
                # Start audio capture if requested
                if start_audio_capture and self.av_output:
                    self.start_audio_capture()
                
                return True
            else:
                logger.error("❌ Failed to join meeting")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error joining meeting: {e}")
            return False
    
    def leave_meeting(self, stop_audio_capture: bool = True) -> bool:
        """Leave the current meeting.
        
        Args:
            stop_audio_capture: Whether to stop audio capture
            
        Returns:
            True if successfully left
        """
        try:
            if not self.meeting_active:
                logger.warning("Not currently in a meeting")
                return True
            
            # Stop audio capture if requested
            if stop_audio_capture and self.audio_capture_active:
                self.stop_audio_capture()
            
            # Leave the meeting
            success = self.agent.leave_meeting()
            
            if success:
                self.meeting_active = False
                logger.info("👋 Successfully left meeting")
            else:
                logger.error("❌ Failed to leave meeting")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error leaving meeting: {e}")
            return False
    
    def start_audio_capture(self, callback: Optional[Callable] = None) -> bool:
        """Start capturing audio from the meeting.
        
        Args:
            callback: Optional callback for real-time audio processing
            
        Returns:
            True if successfully started
        """
        try:
            if not self.av_output:
                logger.error("Audio output not initialized")
                return False
            
            if self.audio_capture_active:
                logger.warning("Audio capture already active")
                return True
            
            success = self.av_output.start_audio_capture(callback)
            
            if success:
                self.audio_capture_active = True
                logger.info("🎤 Audio capture started")
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
            if not self.av_output:
                logger.error("Audio output not initialized")
                return False
            
            if not self.audio_capture_active:
                logger.warning("Audio capture not active")
                return True
            
            success = self.av_output.stop_audio_capture()
            
            if success:
                self.audio_capture_active = False
                logger.info("🛑 Audio capture stopped")
            else:
                logger.error("❌ Failed to stop audio capture")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error stopping audio capture: {e}")
            return False
    
    def speak_text(self, text: str, voice: str = "alloy") -> bool:
        """Convert text to speech and inject into meeting.
        
        Args:
            text: Text to speak
            voice: Voice to use for TTS
            
        Returns:
            True if successfully spoken
        """
        try:
            if not self.av_input:
                logger.error("Audio input not initialized")
                return False
            
            if not self.meeting_active:
                logger.warning("Not in a meeting")
                return False
            
            logger.info(f"🗣️  Speaking: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Unmute microphone
            self.agent.toggle_microphone(True)
            
            # Wait a moment for mic to activate
            time.sleep(0.5)
            
            # Inject TTS audio
            success = self.av_input.inject_tts_text(text, voice, blocking=True)
            
            # Mute microphone again (optional)
            # self.agent.toggle_microphone(False)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error speaking text: {e}")
            return False
    
    def play_audio_file(self, file_path: Path, unmute_first: bool = True) -> bool:
        """Play an audio file into the meeting.
        
        Args:
            file_path: Path to audio file
            unmute_first: Whether to unmute microphone first
            
        Returns:
            True if successfully played
        """
        try:
            if not self.av_input:
                logger.error("Audio input not initialized")
                return False
            
            if not self.meeting_active:
                logger.warning("Not in a meeting")
                return False
            
            # Unmute microphone if requested
            if unmute_first:
                self.agent.toggle_microphone(True)
                time.sleep(0.5)
            
            # Play audio file
            success = self.av_input.inject_audio_file(file_path, blocking=True)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error playing audio file: {e}")
            return False
    
    def listen_for_speech(self, 
                         max_duration: float = 10.0,
                         silence_timeout: float = 3.0,
                         save_to_file: bool = False) -> Optional[str]:
        """Listen for speech in the meeting and optionally save to file.
        
        Args:
            max_duration: Maximum duration to listen
            silence_timeout: Seconds of silence before stopping
            save_to_file: Whether to save captured audio
            
        Returns:
            Path to saved file if save_to_file=True, else "captured" or None
        """
        try:
            if not self.av_output:
                logger.error("Audio output not initialized")
                return None
            
            if not self.audio_capture_active:
                logger.warning("Audio capture not active - starting temporarily")
                temp_capture = True
                self.start_audio_capture()
            else:
                temp_capture = False
            
            # Capture speech segment
            audio_data = self.av_output.capture_speech_segment(max_duration, silence_timeout)
            
            # Stop temporary capture
            if temp_capture:
                self.stop_audio_capture()
            
            if audio_data is None:
                logger.warning("No speech captured")
                return None
            
            # Save to file if requested
            if save_to_file:
                filepath = self.av_output.save_captured_audio(audio_data)
                return filepath
            else:
                return "captured"
                
        except Exception as e:
            logger.error(f"❌ Error listening for speech: {e}")
            return None
    
    def send_chat_message(self, message: str) -> bool:
        """Send a message to the meeting chat.
        
        Args:
            message: Message to send
            
        Returns:
            True if successfully sent
        """
        try:
            if not self.meeting_active:
                logger.warning("Not in a meeting")
                return False
            
            return self.agent.send_chat_message(message)
            
        except Exception as e:
            logger.error(f"❌ Error sending chat message: {e}")
            return False
    
    def toggle_microphone(self, enabled: bool) -> bool:
        """Toggle microphone on/off.
        
        Args:
            enabled: True to enable, False to disable
            
        Returns:
            True if successfully toggled
        """
        try:
            if not self.meeting_active:
                logger.warning("Not in a meeting")
                return False
            
            return self.agent.toggle_microphone(enabled)
            
        except Exception as e:
            logger.error(f"❌ Error toggling microphone: {e}")
            return False
    
    def toggle_camera(self, enabled: bool) -> bool:
        """Toggle camera on/off.
        
        Args:
            enabled: True to enable, False to disable
            
        Returns:
            True if successfully toggled
        """
        try:
            if not self.meeting_active:
                logger.warning("Not in a meeting")
                return False
            
            return self.agent.toggle_camera(enabled)
            
        except Exception as e:
            logger.error(f"❌ Error toggling camera: {e}")
            return False
    
    def get_meeting_status(self) -> Dict[str, Any]:
        """Get comprehensive meeting status.
        
        Returns:
            Dictionary with meeting status information
        """
        try:
            status = {
                "controller": {
                    "meeting_active": self.meeting_active,
                    "audio_capture_active": self.audio_capture_active,
                    "agent_type": self.agent_type
                },
                "agent": self.agent.get_meeting_info() if self.meeting_active else {},
                "audio_input": self.av_input.get_injection_status() if self.av_input else {},
                "audio_output": self.av_output.get_capture_status() if self.av_output else {}
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting meeting status: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """Clean up and close all resources."""
        try:
            # Leave meeting if active
            if self.meeting_active:
                self.leave_meeting()
            
            # Close agent
            self.agent.close()
            
            logger.info("🔒 Meeting Controller closed")
            
        except Exception as e:
            logger.error(f"Error closing Meeting Controller: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 