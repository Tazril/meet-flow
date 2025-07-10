"""Logging utilities for the Google Meet AI Agent."""

import logging
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for future records
        record.levelname = levelname
        
        return formatted

def setup_logger(name: str = "gmeet_ai_agent", level: str = "INFO") -> logging.Logger:
    """Set up a logger with colored output."""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def log_audio_info(logger: logging.Logger, device_info: dict) -> None:
    """Log audio device information."""
    logger.info("🎵 Audio Device Info:")
    logger.info(f"   Device: {device_info.get('name', 'Unknown')}")
    logger.info(f"   Channels: {device_info.get('max_input_channels', 0)} in / {device_info.get('max_output_channels', 0)} out")
    logger.info(f"   Sample Rate: {device_info.get('default_samplerate', 'Unknown')}Hz")

def log_ai_response(logger: logging.Logger, transcription: str, response: str, processing_time: float) -> None:
    """Log AI processing information."""
    logger.info("🤖 AI Processing:")
    logger.info(f"   Transcription: '{transcription[:100]}{'...' if len(transcription) > 100 else ''}'")
    logger.info(f"   Response: '{response[:100]}{'...' if len(response) > 100 else ''}'")
    logger.info(f"   Processing Time: {processing_time:.2f}s")

def log_meeting_event(logger: logging.Logger, event: str, details: Optional[str] = None) -> None:
    """Log meeting-related events."""
    logger.info(f"📞 Meeting Event: {event}")
    if details:
        logger.info(f"   Details: {details}")

# Global logger instance
logger = setup_logger() 