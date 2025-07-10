"""Abstract interface for browser automation agents."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path

class BrowserAutomationAgent(ABC):
    """Abstract base class for browser-based meeting automation agents."""
    
    @abstractmethod
    def join_meeting(self, url: str, display_name: Optional[str] = None) -> bool:
        """Join a meeting with the given URL.
        
        Args:
            url: Meeting URL to join
            display_name: Name to display in the meeting
            
        Returns:
            True if successfully joined
        """
        pass
    
    @abstractmethod
    def leave_meeting(self) -> bool:
        """Leave the current meeting.
        
        Returns:
            True if successfully left
        """
        pass
    
    @abstractmethod
    def toggle_microphone(self, enabled: bool) -> bool:
        """Toggle microphone on/off.
        
        Args:
            enabled: True to enable mic, False to disable
            
        Returns:
            True if successfully toggled
        """
        pass
    
    @abstractmethod
    def toggle_camera(self, enabled: bool) -> bool:
        """Toggle camera on/off.
        
        Args:
            enabled: True to enable camera, False to disable
            
        Returns:
            True if successfully toggled
        """
        pass
    
    @abstractmethod
    def is_microphone_enabled(self) -> Optional[bool]:
        """Check if microphone is currently enabled.
        
        Returns:
            True if enabled, False if disabled, None if unknown
        """
        pass
    
    @abstractmethod
    def is_camera_enabled(self) -> Optional[bool]:
        """Check if camera is currently enabled.
        
        Returns:
            True if enabled, False if disabled, None if unknown
        """
        pass
    
    @abstractmethod
    def is_in_meeting(self) -> bool:
        """Check if currently in a meeting.
        
        Returns:
            True if in meeting
        """
        pass
    
    @abstractmethod
    def get_meeting_info(self) -> Dict[str, Any]:
        """Get information about the current meeting.
        
        Returns:
            Dictionary with meeting information
        """
        pass
    
    @abstractmethod
    def get_participants(self) -> list:
        """Get list of meeting participants.
        
        Returns:
            List of participant names/info
        """
        pass
    
    @abstractmethod
    def send_chat_message(self, message: str) -> bool:
        """Send a message to the meeting chat.
        
        Args:
            message: Message to send
            
        Returns:
            True if successfully sent
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Clean up and close the browser automation agent."""
        pass
    
    # Optional methods that can be overridden
    def inject_audio_file(self, file_path: Path) -> bool:
        """Inject audio from a file into the meeting.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if successfully injected
        """
        # Default implementation - can be overridden
        return False
    
    def start_audio_capture(self) -> bool:
        """Start capturing audio from the meeting.
        
        Returns:
            True if successfully started
        """
        # Default implementation - can be overridden
        return False
    
    def stop_audio_capture(self) -> bool:
        """Stop capturing audio from the meeting.
        
        Returns:
            True if successfully stopped
        """
        # Default implementation - can be overridden
        return False 