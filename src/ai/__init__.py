"""AI Integration Module for Google Meet AI Agent.

This module provides integration with Azure OpenAI services for:
- Speech-to-text using Whisper
- Text generation using GPT models
- Text-to-speech using Azure TTS
"""

from .whisper_client import WhisperClient
from .gpt_client import GPTClient
from .tts_client import TTSClient
from .conversation_manager import ConversationManager

__all__ = [
    "WhisperClient",
    "GPTClient", 
    "TTSClient",
    "ConversationManager"
] 